"""
LLM Analyzer
Analyzes logs using OpenAI GPT-4o to identify probable causes
"""

import json
import logging
from typing import Dict, Any
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import get_config

logger = logging.getLogger(__name__)

# Custom exceptions
class LLMAnalysisError(Exception):
    """Base exception for LLM analysis errors"""
    pass

class LLMResponseFormatError(LLMAnalysisError):
    """Raised when LLM response is not valid JSON or missing required fields"""
    pass

class LLMAPIError(LLMAnalysisError):
    """Raised when OpenAI API returns an error"""
    pass

# System prompt as per Tech Spec lines 233-252
SYSTEM_PROMPT = """You are LogLens, a log analysis assistant. Your job is to analyze application
logs and help identify why a user experienced a problem.

Given:
1. Workflow documentation describing expected system behavior
2. Known error patterns and their resolutions
3. Sentry log events from the relevant time period
4. A problem description from customer support

You must return:
1. Top 3 most likely causes, ranked by probability
2. Confidence level for each (high/medium/low)
3. A suggested response that CS can send to the customer
4. Brief summary of relevant log findings

Be specific and actionable. Reference actual error messages from the logs.
If logs don't clearly indicate the cause, say so and suggest next steps."""


def _construct_user_prompt(
    description: str,
    timestamp: str,
    customer_id: str,
    formatted_events: str,
    workflow_docs: str,
    known_errors: str
) -> str:
    """
    Construct the user prompt as per Tech Spec lines 254-276

    Args:
        description: User-provided problem description
        timestamp: When the issue occurred
        customer_id: Customer identifier
        formatted_events: Formatted Sentry events
        workflow_docs: Content from workflow.md
        known_errors: Content from known_errors.md

    Returns:
        Formatted user prompt string
    """
    return f"""## Workflow Documentation
{workflow_docs}

## Known Error Patterns
{known_errors}

## Sentry Events
{formatted_events}

## Problem Report
- Description: {description}
- Timestamp: {timestamp}
- Customer ID: {customer_id}

Analyze and respond in JSON format:
{{
  "causes": [{{"rank": 1, "cause": "", "explanation": "", "confidence": ""}}],
  "suggested_response": "",
  "logs_summary": ""
}}"""


def _validate_llm_response(response_data: Dict[str, Any]) -> None:
    """
    Validate that LLM response has required fields and correct format

    Args:
        response_data: Parsed JSON response from LLM

    Raises:
        LLMResponseFormatError: If response is missing required fields or has invalid format
    """
    # Check required top-level fields
    required_fields = ["causes", "suggested_response", "logs_summary"]
    missing_fields = [field for field in required_fields if field not in response_data]

    if missing_fields:
        raise LLMResponseFormatError(f"Missing required fields: {missing_fields}")

    # Validate causes array
    causes = response_data.get("causes", [])
    if not isinstance(causes, list):
        raise LLMResponseFormatError("'causes' must be an array")

    if len(causes) != 3:
        logger.warning(f"Expected 3 causes but got {len(causes)}")

    # Validate each cause
    valid_confidences = {"high", "medium", "low"}
    for i, cause in enumerate(causes):
        if not isinstance(cause, dict):
            raise LLMResponseFormatError(f"Cause {i} must be an object")

        cause_required = ["rank", "cause", "explanation", "confidence"]
        cause_missing = [field for field in cause_required if field not in cause]

        if cause_missing:
            raise LLMResponseFormatError(f"Cause {i} missing fields: {cause_missing}")

        # Validate confidence level
        confidence = cause.get("confidence", "").lower()
        if confidence not in valid_confidences:
            logger.warning(f"Invalid confidence level '{confidence}' in cause {i}, expected one of {valid_confidences}")

    # Validate string fields are not empty
    if not response_data.get("suggested_response", "").strip():
        raise LLMResponseFormatError("'suggested_response' cannot be empty")

    if not response_data.get("logs_summary", "").strip():
        raise LLMResponseFormatError("'logs_summary' cannot be empty")


@retry(
    retry=retry_if_exception_type((LLMAPIError,)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def _call_openai_api(client: AsyncOpenAI, messages: list) -> str:
    """
    Call OpenAI API with retry logic

    Args:
        client: AsyncOpenAI client instance
        messages: List of message objects for the chat completion

    Returns:
        Response content from OpenAI

    Raises:
        LLMAPIError: If API call fails after retries
    """
    try:
        logger.info("Calling OpenAI API with GPT-4o")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1500
        )

        content = response.choices[0].message.content
        if not content:
            raise LLMAPIError("Empty response from OpenAI API")

        logger.info("Successfully received response from OpenAI")
        return content

    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise LLMAPIError(f"OpenAI API call failed: {str(e)}") from e


async def analyze_logs(
    description: str,
    timestamp: str,
    customer_id: str,
    formatted_events: str,
    workflow_docs: str,
    known_errors: str
) -> Dict[str, Any]:
    """
    Analyze logs using LLM to determine probable causes

    Args:
        description: User-provided problem description
        timestamp: When the issue occurred
        customer_id: Customer identifier
        formatted_events: Formatted Sentry events
        workflow_docs: Content from workflow.md
        known_errors: Content from known_errors.md

    Returns:
        Dictionary containing analysis results with causes and suggestions
        Format:
        {
            "causes": [
                {"rank": 1, "cause": "...", "explanation": "...", "confidence": "high/medium/low"}
            ],
            "suggested_response": "...",
            "logs_summary": "..."
        }

    Raises:
        LLMAnalysisError: If analysis fails
        LLMResponseFormatError: If LLM response is malformed
        LLMAPIError: If OpenAI API fails after retries
    """
    config = get_config()

    try:
        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=config.openai_api_key)

        # Construct user prompt
        user_prompt = _construct_user_prompt(
            description=description,
            timestamp=timestamp,
            customer_id=customer_id,
            formatted_events=formatted_events,
            workflow_docs=workflow_docs,
            known_errors=known_errors
        )

        logger.info(f"Analyzing logs for customer {customer_id}")

        # Prepare messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # Call OpenAI API with retry logic
        response_content = await _call_openai_api(client, messages)

        # Parse JSON response
        try:
            response_data = json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise LLMResponseFormatError(f"Invalid JSON response from LLM: {str(e)}") from e

        # Validate response format
        _validate_llm_response(response_data)

        logger.info(f"Successfully analyzed logs for customer {customer_id}")
        return response_data

    except (LLMAPIError, LLMResponseFormatError):
        # Re-raise our custom exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error during LLM analysis: {str(e)}")
        raise LLMAnalysisError(f"Analysis failed: {str(e)}") from e
