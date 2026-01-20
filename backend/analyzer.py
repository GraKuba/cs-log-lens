"""
LLM Analyzer
Analyzes logs using Google Gemini to identify probable causes
"""

import json
import logging
from typing import Dict, Any
from google import genai
from google.genai import types
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
    """Raised when Gemini API returns an error"""
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
If logs don't clearly indicate the cause, say so and suggest next steps.

IMPORTANT: You must respond with valid JSON only, no markdown formatting or code blocks."""


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

Analyze and respond in JSON format (no markdown, just raw JSON):
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
async def _call_gemini_api(client: genai.Client, prompt: str) -> str:
    """
    Call Gemini API with retry logic

    Args:
        client: Gemini client instance
        prompt: Full prompt to send to Gemini

    Returns:
        Response content from Gemini

    Raises:
        LLMAPIError: If API call fails after retries
    """
    try:
        logger.info("Calling Gemini API with gemini-2.5-flash")

        # Generate content using Gemini
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=8000,
            )
        )

        # Check if response was completed
        if response.candidates:
            finish_reason = response.candidates[0].finish_reason
            logger.info(f"Response finish reason: {finish_reason}")
            if finish_reason and finish_reason != 'STOP':
                logger.warning(f"Response may be incomplete. Finish reason: {finish_reason}")

        content = response.text
        if not content:
            raise LLMAPIError("Empty response from Gemini API")

        logger.info(f"Successfully received response from Gemini ({len(content)} characters)")
        logger.debug(f"Full response: {content}")
        return content

    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise LLMAPIError(f"Gemini API call failed: {str(e)}") from e


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
        Dict containing analysis results with causes, suggested_response, logs_summary

    Raises:
        LLMResponseFormatError: If LLM response format is invalid
        LLMAPIError: If LLM API call fails
        LLMAnalysisError: For other analysis errors
    """
    config = get_config()

    # Configure Gemini client
    client = genai.Client(api_key=config.gemini_api_key)

    logger.info(f"Analyzing logs for customer {customer_id}")

    # Construct full prompt (Gemini doesn't have separate system/user messages in the same way)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{_construct_user_prompt(description, timestamp, customer_id, formatted_events, workflow_docs, known_errors)}"

    # Call Gemini API with retry logic
    try:
        response_content = await _call_gemini_api(client, full_prompt)
    except LLMAPIError:
        # Let retry errors bubble up
        raise

    # Parse JSON response
    try:
        # Clean up response if it has markdown code blocks
        response_content = response_content.strip()
        if response_content.startswith("```json"):
            response_content = response_content[7:]  # Remove ```json
        if response_content.startswith("```"):
            response_content = response_content[3:]  # Remove ```
        if response_content.endswith("```"):
            response_content = response_content[:-3]  # Remove trailing ```
        response_content = response_content.strip()

        response_data = json.loads(response_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response content: {response_content[:500]}")
        raise LLMResponseFormatError(f"Invalid JSON in LLM response: {str(e)}") from e

    # Validate response structure
    try:
        _validate_llm_response(response_data)
    except LLMResponseFormatError:
        # Log the invalid response for debugging
        logger.error(f"Invalid LLM response structure: {json.dumps(response_data, indent=2)}")
        raise

    logger.info("Successfully analyzed logs and validated response")
    return response_data
