"""
Sentry API Client
Fetches error events from Sentry for analysis
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import hashlib
import json

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from config import get_config

logger = logging.getLogger(__name__)

# Simple in-memory cache for Sentry responses
# Key: hash of (url, customer_id, timestamp, time_window_minutes)
# Value: list of events
_sentry_cache: Dict[str, List[Dict[str, Any]]] = {}


class SentryClientError(Exception):
    """Base exception for Sentry client errors"""
    pass


class SentryAuthError(SentryClientError):
    """Raised when authentication fails"""
    pass


class SentryRateLimitError(SentryClientError):
    """Raised when rate limit is exceeded"""
    pass


class SentryAPIError(SentryClientError):
    """Raised when Sentry API returns an error"""
    pass


def _parse_iso_timestamp(timestamp: str) -> datetime:
    """
    Parse ISO 8601 timestamp string to datetime object

    Args:
        timestamp: ISO format timestamp string

    Returns:
        datetime object

    Raises:
        ValueError: If timestamp format is invalid
    """
    try:
        # Handle both with and without timezone
        if timestamp.endswith('Z'):
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return datetime.fromisoformat(timestamp)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid timestamp format: {timestamp}") from e


def _format_datetime_for_sentry(dt: datetime) -> str:
    """
    Format datetime for Sentry API query

    Args:
        dt: datetime object

    Returns:
        ISO format string suitable for Sentry API
    """
    return dt.isoformat()


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
)
async def _make_sentry_request(
    url: str,
    headers: Dict[str, str],
    params: Dict[str, Any],
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Make HTTP request to Sentry API with retry logic

    Args:
        url: Sentry API endpoint URL
        headers: Request headers
        params: Query parameters
        timeout: Request timeout in seconds

    Returns:
        JSON response from Sentry API

    Raises:
        SentryAuthError: If authentication fails
        SentryRateLimitError: If rate limit is exceeded
        SentryAPIError: If API returns an error
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                logger.warning(f"Sentry rate limit exceeded. Retry after: {retry_after}s")
                raise SentryRateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds."
                )

            # Handle authentication errors
            if response.status_code == 401:
                logger.error("Sentry authentication failed")
                raise SentryAuthError("Invalid or expired Sentry auth token")

            # Handle other client errors
            if response.status_code == 404:
                logger.error(f"Sentry project not found: {url}")
                raise SentryAPIError("Sentry project not found. Check org/project names.")

            # Handle server errors
            if response.status_code >= 500:
                logger.error(f"Sentry server error: {response.status_code}")
                raise SentryAPIError(f"Sentry server error: {response.status_code}")

            # Raise for other error status codes
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Sentry API: {e}")
            raise SentryAPIError(f"Sentry API error: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error to Sentry API: {e}")
            raise


async def fetch_sentry_events(
    customer_id: str,
    timestamp: str,
    time_window_minutes: int = 5,
) -> List[Dict[str, Any]]:
    """
    Fetch Sentry events for a specific customer around a given timestamp

    Args:
        customer_id: Customer ID to filter events (will be used in user.id filter)
        timestamp: ISO timestamp around which to search
        time_window_minutes: Time window in minutes (±N minutes from timestamp)

    Returns:
        List of Sentry event dictionaries

    Raises:
        ValueError: If timestamp format is invalid
        SentryAuthError: If authentication fails
        SentryRateLimitError: If rate limit is exceeded
        SentryAPIError: If API returns an error
    """
    config = get_config()

    # Validate and parse timestamp
    try:
        center_time = _parse_iso_timestamp(timestamp)
    except ValueError as e:
        logger.error(f"Invalid timestamp: {timestamp}")
        raise

    # Calculate time range (±5 minutes by default)
    start_time = center_time - timedelta(minutes=time_window_minutes)
    end_time = center_time + timedelta(minutes=time_window_minutes)

    # Build Sentry API URL
    url = f"https://sentry.io/api/0/projects/{config.sentry_org}/{config.sentry_project}/events/"

    # Build headers
    headers = {
        "Authorization": f"Bearer {config.sentry_auth_token}",
    }

    # Build query parameters
    params = {
        "query": f"user.id:{customer_id}",
        "start": _format_datetime_for_sentry(start_time),
        "end": _format_datetime_for_sentry(end_time),
        "full": "true",
    }

    logger.info(
        f"Fetching Sentry events for customer {customer_id} "
        f"from {start_time} to {end_time}"
    )

    try:
        # Make request with caching (see _cached_fetch_events)
        response_data = await _cached_fetch_events(
            url=url,
            customer_id=customer_id,
            timestamp=timestamp,
            time_window_minutes=time_window_minutes,
        )

        events = response_data if isinstance(response_data, list) else []

        logger.info(f"Found {len(events)} Sentry events for customer {customer_id}")
        return events

    except (SentryAuthError, SentryRateLimitError, SentryAPIError) as e:
        # Re-raise known Sentry errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching Sentry events: {e}")
        raise SentryAPIError(f"Failed to fetch Sentry events: {e}") from e


def _generate_cache_key(
    url: str,
    customer_id: str,
    timestamp: str,
    time_window_minutes: int,
) -> str:
    """
    Generate a cache key for Sentry request parameters

    Args:
        url: Sentry API endpoint URL
        customer_id: Customer ID
        timestamp: ISO timestamp
        time_window_minutes: Time window in minutes

    Returns:
        Cache key string (hash of parameters)
    """
    cache_data = {
        "url": url,
        "customer_id": customer_id,
        "timestamp": timestamp,
        "time_window_minutes": time_window_minutes,
    }
    cache_str = json.dumps(cache_data, sort_keys=True)
    return hashlib.sha256(cache_str.encode()).hexdigest()


async def _cached_fetch_events(
    url: str,
    customer_id: str,
    timestamp: str,
    time_window_minutes: int,
) -> List[Dict[str, Any]]:
    """
    Cached version of Sentry event fetching to avoid rate limits

    Uses simple in-memory cache to store recent queries. Cache key includes all
    relevant parameters to ensure accuracy.

    Args:
        url: Sentry API endpoint URL
        customer_id: Customer ID
        timestamp: ISO timestamp
        time_window_minutes: Time window in minutes

    Returns:
        List of Sentry events
    """
    # Generate cache key
    cache_key = _generate_cache_key(url, customer_id, timestamp, time_window_minutes)

    # Check cache first
    if cache_key in _sentry_cache:
        logger.info(f"Using cached Sentry events for key {cache_key[:16]}...")
        return _sentry_cache[cache_key]

    # Not in cache, fetch from API
    config = get_config()

    # Recalculate parameters
    center_time = _parse_iso_timestamp(timestamp)
    start_time = center_time - timedelta(minutes=time_window_minutes)
    end_time = center_time + timedelta(minutes=time_window_minutes)

    headers = {
        "Authorization": f"Bearer {config.sentry_auth_token}",
    }

    params = {
        "query": f"user.id:{customer_id}",
        "start": _format_datetime_for_sentry(start_time),
        "end": _format_datetime_for_sentry(end_time),
        "full": "true",
    }

    events = await _make_sentry_request(url, headers, params)

    # Store in cache (limit cache size to 100 entries)
    if len(_sentry_cache) >= 100:
        # Remove oldest entry (first key)
        oldest_key = next(iter(_sentry_cache))
        del _sentry_cache[oldest_key]

    _sentry_cache[cache_key] = events
    logger.info(f"Cached Sentry events with key {cache_key[:16]}...")

    return events


def clear_sentry_cache():
    """Clear the Sentry response cache (useful for testing)"""
    global _sentry_cache
    _sentry_cache = {}


def generate_sentry_link(event_id: str, org: Optional[str] = None, project: Optional[str] = None) -> str:
    """
    Generate a direct link to a Sentry event in the UI

    Args:
        event_id: Sentry event ID
        org: Sentry organization slug (defaults to config)
        project: Sentry project slug (defaults to config)

    Returns:
        URL to the event in Sentry UI
    """
    config = get_config()
    org_slug = org or config.sentry_org
    project_slug = project or config.sentry_project
    return f"https://sentry.io/organizations/{org_slug}/issues/?project={project_slug}&query={event_id}"


def format_events_for_llm(events: List[Dict[str, Any]]) -> str:
    """
    Format Sentry events into a readable format for LLM analysis

    Extracts and formats:
    - Error message and type
    - Stack traces (if available)
    - Breadcrumbs (if available)
    - Timestamps
    - Event metadata

    Args:
        events: List of Sentry event dictionaries

    Returns:
        Formatted string representation of events suitable for LLM analysis
    """
    if not events:
        return "No Sentry events found."

    formatted_output = []

    for idx, event in enumerate(events, 1):
        event_lines = [f"Event {idx}:"]

        # Extract timestamp
        timestamp = event.get("dateCreated") or event.get("datetime", "Unknown")
        event_lines.append(f"- Time: {timestamp}")

        # Extract error type and message
        # Sentry events can have different structures, handle gracefully
        error_type = event.get("type", "Unknown")
        title = event.get("title", "")
        message = event.get("message", "")

        # Try to extract exception info from metadata if available
        if "metadata" in event:
            metadata = event["metadata"]
            if "type" in metadata:
                error_type = metadata["type"]
            if "value" in metadata:
                message = metadata["value"]

        event_lines.append(f"- Error: {error_type}")
        if message and message != title:
            event_lines.append(f'- Message: "{message}"')
        elif title:
            event_lines.append(f'- Message: "{title}"')

        # Extract stack trace if available
        # Sentry stores stack traces in entries -> exception -> values -> stacktrace
        stack_trace = _extract_stack_trace(event)
        if stack_trace:
            event_lines.append(f"- Stack Trace:")
            for frame in stack_trace[:5]:  # Limit to top 5 frames for brevity
                event_lines.append(f"  {frame}")
            if len(stack_trace) > 5:
                event_lines.append(f"  ... ({len(stack_trace) - 5} more frames)")

        # Extract breadcrumbs if available
        breadcrumbs = _extract_breadcrumbs(event)
        if breadcrumbs:
            event_lines.append(f"- Breadcrumbs (user actions leading to error):")
            for crumb in breadcrumbs[-5:]:  # Show last 5 breadcrumbs
                event_lines.append(f"  {crumb}")

        # Add context tags if available
        tags = event.get("tags", [])
        if tags:
            relevant_tags = [
                tag for tag in tags
                if tag.get("key") in ["environment", "release", "browser", "os"]
            ]
            if relevant_tags:
                tag_strs = [f"{t.get('key')}={t.get('value')}" for t in relevant_tags]
                event_lines.append(f"- Context: {', '.join(tag_strs)}")

        # Add Sentry link
        event_id = event.get("id", "")
        if event_id:
            sentry_link = generate_sentry_link(event_id)
            event_lines.append(f"- Link: {sentry_link}")

        formatted_output.append("\n".join(event_lines))

    return "\n\n".join(formatted_output)


def _extract_stack_trace(event: Dict[str, Any]) -> List[str]:
    """
    Extract and format stack trace from a Sentry event

    Args:
        event: Sentry event dictionary

    Returns:
        List of formatted stack trace frames
    """
    frames = []

    # Try to extract from entries
    entries = event.get("entries", [])
    for entry in entries:
        if entry.get("type") == "exception":
            values = entry.get("data", {}).get("values", [])
            for value in values:
                stacktrace = value.get("stacktrace", {})
                raw_frames = stacktrace.get("frames", [])

                # Format frames (most recent last)
                for frame in raw_frames:
                    filename = frame.get("filename", "unknown")
                    function = frame.get("function", "unknown")
                    lineno = frame.get("lineNo", "?")
                    context = frame.get("context", [])

                    # Get the actual code line if available
                    code_line = ""
                    if context:
                        # Context is usually [line_before, actual_line, line_after]
                        middle_idx = len(context) // 2
                        if middle_idx < len(context):
                            code_line = context[middle_idx][1].strip()

                    if code_line:
                        frames.append(f"{filename}:{lineno} in {function}() -> {code_line}")
                    else:
                        frames.append(f"{filename}:{lineno} in {function}()")

    return frames


def _extract_breadcrumbs(event: Dict[str, Any]) -> List[str]:
    """
    Extract and format breadcrumbs from a Sentry event

    Breadcrumbs show user actions and events leading up to the error

    Args:
        event: Sentry event dictionary

    Returns:
        List of formatted breadcrumb strings
    """
    crumbs = []

    # Try to extract from entries
    entries = event.get("entries", [])
    for entry in entries:
        if entry.get("type") == "breadcrumbs":
            values = entry.get("data", {}).get("values", [])
            for breadcrumb in values:
                timestamp = breadcrumb.get("timestamp", "")
                category = breadcrumb.get("category", "")
                message = breadcrumb.get("message", "")
                level = breadcrumb.get("level", "info")

                # Format breadcrumb
                if message:
                    crumbs.append(f"[{level}] {category}: {message}")
                else:
                    # Some breadcrumbs might have data instead of message
                    data = breadcrumb.get("data", {})
                    if data:
                        data_str = ", ".join(f"{k}={v}" for k, v in list(data.items())[:3])
                        crumbs.append(f"[{level}] {category}: {data_str}")
                    else:
                        crumbs.append(f"[{level}] {category}")

    return crumbs
