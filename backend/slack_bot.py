"""
Slack Bot Handler
Handles /loglens slash command and formats responses for Slack
"""

import logging
import hmac
import hashlib
import time
from typing import Dict, Any
from config import get_config

logger = logging.getLogger(__name__)


class SlackSignatureVerificationError(Exception):
    """Raised when Slack signature verification fails"""
    pass


def verify_slack_signature(
    body: bytes,
    timestamp: str,
    signature: str,
    signing_secret: str
) -> None:
    """
    Verify that a request came from Slack using the signing secret.

    Slack signs requests using HMAC-SHA256. We need to verify the signature
    to ensure the request is authentic.

    Args:
        body: Raw request body as bytes
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header
        signing_secret: Slack app signing secret from config

    Raises:
        SlackSignatureVerificationError: If signature verification fails
    """
    # Verify timestamp is recent (within 5 minutes)
    current_timestamp = int(time.time())
    request_timestamp = int(timestamp)

    if abs(current_timestamp - request_timestamp) > 60 * 5:
        logger.warning(f"Slack request timestamp too old: {timestamp}")
        raise SlackSignatureVerificationError("Request timestamp too old")

    # Construct the signature base string
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"

    # Calculate expected signature
    expected_signature = 'v0=' + hmac.new(
        signing_secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Compare signatures using constant-time comparison
    if not hmac.compare_digest(expected_signature, signature):
        logger.warning("Slack signature verification failed")
        raise SlackSignatureVerificationError("Invalid signature")

    logger.info("Slack signature verified successfully")


def parse_slack_command(command_text: str) -> Dict[str, str]:
    """
    Parse /loglens command text into components.

    Expected format: /loglens [description] | [timestamp] | [customer_id]
    Example: /loglens User can't checkout | 2025-01-19T14:30:00Z | usr_abc123

    Args:
        command_text: Raw command text from Slack

    Returns:
        Dictionary with 'description', 'timestamp', and 'customer_id' keys

    Raises:
        ValueError: If command format is invalid
    """
    # Split by pipe character
    parts = [part.strip() for part in command_text.split('|')]

    if len(parts) != 3:
        raise ValueError(
            "Invalid command format. Use: /loglens [description] | [timestamp] | [customer_id]"
        )

    description, timestamp, customer_id = parts

    # Validate that none of the parts are empty
    if not description:
        raise ValueError("Description cannot be empty")
    if not timestamp:
        raise ValueError("Timestamp cannot be empty")
    if not customer_id:
        raise ValueError("Customer ID cannot be empty")

    return {
        "description": description,
        "timestamp": timestamp,
        "customer_id": customer_id
    }


def format_slack_response(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format analysis results for Slack display using Block Kit.

    Args:
        analysis_result: Analysis results from /analyze endpoint

    Returns:
        Slack-formatted message with blocks
    """
    # Extract data from analysis result
    causes = analysis_result.get("causes", [])
    suggested_response = analysis_result.get("suggested_response", "")
    events_found = analysis_result.get("events_found", 0)
    sentry_links = analysis_result.get("sentry_links", [])

    # Build blocks for Slack message
    blocks = []

    # Header
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "🔍 LogLens Analysis"
        }
    })

    # Probable Causes section
    if causes:
        causes_text = "*Probable Causes:*\n\n"
        emoji_map = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣"}

        for cause in causes:
            rank = cause.get("rank", 0)
            confidence = cause.get("confidence", "").upper()
            cause_text = cause.get("cause", "")
            explanation = cause.get("explanation", "")

            emoji = emoji_map.get(rank, "•")
            causes_text += f"{emoji} *[{confidence}]* {cause_text}\n"
            causes_text += f"   └ {explanation}\n\n"

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": causes_text.strip()
            }
        })

    blocks.append({"type": "divider"})

    # Suggested Response section
    if suggested_response:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Suggested Response:*\n> {suggested_response}"
            }
        })

        blocks.append({"type": "divider"})

    # Logs summary
    logs_text = f"*Logs:* Found {events_found} event"
    if events_found != 1:
        logs_text += "s"

    # Add Sentry link if available
    if sentry_links:
        # Use first Sentry link
        logs_text += f" | <{sentry_links[0]}|View in Sentry>"

    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": logs_text
        }
    })

    return {
        "response_type": "in_channel",  # Make response visible to channel
        "blocks": blocks
    }


def format_slack_error(error_message: str, suggestion: str = "") -> Dict[str, Any]:
    """
    Format an error message for Slack display.

    Args:
        error_message: The error message to display
        suggestion: Optional suggestion for how to fix the error

    Returns:
        Slack-formatted error message
    """
    text = f"❌ *Error:* {error_message}"

    if suggestion:
        text += f"\n\n💡 *Suggestion:* {suggestion}"

    return {
        "response_type": "ephemeral",  # Only visible to user who ran command
        "text": text
    }


async def handle_slack_command(command_text: str) -> dict:
    """
    Handle /loglens slash command from Slack

    This function:
    1. Parses the command text
    2. Calls the analysis logic (Sentry + LLM)
    3. Formats the response for Slack

    Args:
        command_text: Raw command text from Slack

    Returns:
        Dictionary containing Slack-formatted response
    """
    # Parse and validate the command
    try:
        parsed = parse_slack_command(command_text)
    except ValueError as e:
        return format_slack_error(str(e), "Use format: /loglens [description] | [timestamp] | [customer_id]")

    # Import analysis modules
    try:
        from sentry_client import fetch_sentry_events, format_events_for_llm, SentryAuthError, SentryRateLimitError, SentryAPIError
        from analyzer import analyze_logs, LLMAnalysisError, LLMResponseFormatError, LLMAPIError
        from datetime import datetime, timedelta
        import os
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        return format_slack_error(
            "Internal error: Missing dependencies",
            "Please contact support"
        )

    # Extract parsed values
    description = parsed["description"]
    timestamp_str = parsed["timestamp"]
    customer_id = parsed["customer_id"]

    # Parse timestamp and calculate time range (±5 minutes)
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        start_time = timestamp - timedelta(minutes=5)
        end_time = timestamp + timedelta(minutes=5)
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid timestamp format: {timestamp_str}")
        return format_slack_error(
            f"Invalid timestamp: {timestamp_str}",
            "Use ISO 8601 format, e.g., 2025-01-19T14:30:00Z"
        )

    # Fetch Sentry events
    try:
        events = await fetch_sentry_events(customer_id, start_time, end_time)
        formatted_events = format_events_for_llm(events)

        # Generate Sentry links from events
        sentry_links = []
        config = get_config()
        for event in events:
            event_id = event.get("id", "")
            if event_id:
                link = f"https://sentry.io/organizations/{config.sentry_org}/issues/?project={config.sentry_project}&query={event_id}"
                sentry_links.append(link)

        events_found = len(events)
    except SentryAuthError as e:
        logger.error(f"Sentry authentication failed: {e}")
        return format_slack_error(
            "Sentry authentication failed",
            "Please verify Sentry credentials are configured correctly"
        )
    except SentryRateLimitError as e:
        logger.error(f"Sentry rate limit exceeded: {e}")
        return format_slack_error(
            "Sentry rate limit exceeded",
            "Please try again in a few minutes"
        )
    except SentryAPIError as e:
        # Don't fail completely - continue with no events
        logger.warning(f"Sentry API error (continuing without events): {e}")
        formatted_events = ""
        sentry_links = []
        events_found = 0
    except Exception as e:
        logger.error(f"Unexpected error fetching Sentry events: {e}", exc_info=True)
        return format_slack_error(
            "Failed to fetch Sentry events",
            "An unexpected error occurred. Please try again."
        )

    # Load knowledge base files
    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(backend_dir, "docs", "workflow.md")
        known_errors_path = os.path.join(backend_dir, "docs", "known_errors.md")

        with open(workflow_path, "r") as f:
            workflow_docs = f.read()
        with open(known_errors_path, "r") as f:
            known_errors_docs = f.read()
    except FileNotFoundError as e:
        logger.error(f"Knowledge base file not found: {e}")
        return format_slack_error(
            "Internal error: Knowledge base not found",
            "Please contact support"
        )

    # Run LLM analysis
    try:
        llm_response = await analyze_logs(
            description=description,
            formatted_events=formatted_events,
            workflow_docs=workflow_docs,
            known_errors_docs=known_errors_docs
        )
    except LLMResponseFormatError as e:
        logger.error(f"LLM returned invalid response format: {e}")
        return format_slack_error(
            "Analysis failed: Invalid response from AI",
            "Please try again or contact support"
        )
    except LLMAPIError as e:
        logger.error(f"OpenAI API error: {e}")
        return format_slack_error(
            "Analysis failed: AI service error",
            "Please try again in a few moments"
        )
    except LLMAnalysisError as e:
        logger.error(f"LLM analysis failed: {e}")
        return format_slack_error(
            "Analysis failed",
            str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during LLM analysis: {e}", exc_info=True)
        return format_slack_error(
            "Analysis failed: Unexpected error",
            "Please try again or contact support"
        )

    # Build analysis result for formatting
    analysis_result = {
        "success": True,
        "causes": llm_response.get("causes", []),
        "suggested_response": llm_response.get("suggested_response", ""),
        "sentry_links": sentry_links,
        "logs_summary": llm_response.get("logs_summary", ""),
        "events_found": events_found
    }

    # Format and return Slack response
    return format_slack_response(analysis_result)
