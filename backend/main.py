"""
LogLens Backend API
FastAPI application for analyzing customer support logs
"""

import logging
import json
import os
import re
import time
from datetime import datetime
from typing import Callable
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator, ValidationError
from config import get_config


# Logging Configuration
class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs for production
    and human-readable logs for development.
    """

    # Patterns to redact sensitive data
    SENSITIVE_PATTERNS = [
        # Bearer tokens must be first to catch "Authorization: Bearer xyz"
        (re.compile(r'Bearer\s+([^\s,\"\'}]+)', re.IGNORECASE), r'Bearer ***REDACTED***'),
        # API keys, tokens, passwords in key=value or key: value format
        (re.compile(r'(token|password|secret|key|authorization)[\"\']?\s*[:=]\s*[\"\']?([^\s,\"\'}]+)', re.IGNORECASE), r'\1=***REDACTED***'),
        # Specific token formats
        (re.compile(r'sk-[a-zA-Z0-9]{20,}'), r'sk-***REDACTED***'),  # OpenAI API keys
        (re.compile(r'xoxb-[a-zA-Z0-9-]+'), r'xoxb-***REDACTED***'),  # Slack bot tokens
        (re.compile(r'sntrys_[a-zA-Z0-9]+'), r'sntrys_***REDACTED***'),  # Sentry tokens
    ]

    def __init__(self, use_json: bool = False):
        super().__init__()
        self.use_json = use_json

    def redact_sensitive_data(self, message: str) -> str:
        """Redact sensitive information from log messages"""
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = pattern.sub(replacement, message)
        return message

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON or human-readable text"""
        # Redact sensitive data from the message
        message = self.redact_sensitive_data(str(record.getMessage()))

        if self.use_json:
            # Structured JSON format for production (Railway)
            log_data = {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ"),
                "level": record.levelname,
                "logger": record.name,
                "message": message,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # Add exception info if present
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)

            # Add extra fields if present
            if hasattr(record, "request_id"):
                log_data["request_id"] = record.request_id
            if hasattr(record, "duration_ms"):
                log_data["duration_ms"] = record.duration_ms
            if hasattr(record, "status_code"):
                log_data["status_code"] = record.status_code
            if hasattr(record, "path"):
                log_data["path"] = record.path

            return json.dumps(log_data)
        else:
            # Human-readable format for development
            timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
            return f"{timestamp} - {record.name} - {record.levelname} - {message}"


def setup_logging():
    """
    Configure application logging based on environment.

    Uses JSON structured logging in production (Railway) and
    human-readable format in development.
    """
    # Determine if we're in production (Railway sets RAILWAY_ENVIRONMENT)
    is_production = os.getenv("RAILWAY_ENVIRONMENT") is not None
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with appropriate formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter(use_json=is_production))
    root_logger.addHandler(console_handler)

    # Reduce noise from uvicorn access logs (we have our own middleware)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


# Initialize logging
logger = setup_logging()

app = FastAPI(
    title="LogLens API",
    description="AI-powered log analysis for customer support",
    version="0.1.0"
)

# Load config on startup (only in production, tests will mock this)
try:
    config = get_config()
    allowed_origins = config.allowed_origins.split(",")
except ValueError:
    # In development/testing without full env vars, allow all origins
    allowed_origins = ["*"]

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable):
    """
    Middleware to log all HTTP requests and responses.

    Logs request method, path, and response status code with timing information.
    Sensitive data in headers is automatically redacted by the StructuredFormatter.
    """
    start_time = time.time()

    # Generate a simple request ID for tracking
    request_id = f"{int(start_time * 1000)}"

    # Log incoming request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        }
    )

    # Process request
    try:
        response = await call_next(request)
    except Exception as e:
        # Log exception and re-raise
        duration_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "duration_ms": duration_ms,
            },
            exc_info=True
        )
        raise

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} - {response.status_code}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
    )

    return response


# Exception Handlers

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors (422) with detailed error messages.

    Logs the full error server-side but returns safe, user-friendly messages.
    """
    # Log full error details server-side
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")

    # Extract first error for user-friendly message
    first_error = exc.errors()[0] if exc.errors() else {}
    field = first_error.get('loc', ['unknown'])[-1]
    msg = first_error.get('msg', 'Invalid input')

    # Build user-friendly error message
    error_msg = f"Invalid {field}: {msg}"
    suggestion = "Please check your input and try again"

    # Specific suggestions based on field
    if field == 'timestamp':
        suggestion = "Timestamp must be in ISO 8601 format (e.g., 2025-01-19T14:30:00Z)"
    elif field == 'customer_id':
        suggestion = "Customer ID must not be empty"
    elif field == 'description':
        suggestion = "Description must not be empty"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": error_msg,
            "suggestion": suggestion
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions (401, 404, etc.) with consistent format.

    Logs errors server-side but returns safe messages to clients.
    """
    # Log the error (use different levels based on status code)
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    else:
        logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")

    # Build error response based on status code
    error_msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    suggestion = ""

    if exc.status_code == 401:
        error_msg = "Authentication failed"
        suggestion = "Please check your authentication token"
    elif exc.status_code == 404:
        error_msg = "Endpoint not found"
        suggestion = "Please check the URL and try again"
    elif exc.status_code >= 500:
        error_msg = "An internal error occurred"
        suggestion = "Please try again later or contact support if the issue persists"

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": error_msg,
            "suggestion": suggestion
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """
    Handle internal server errors (500) with safe error messages.

    Logs full error details server-side but never exposes sensitive information
    or internal details to clients.
    """
    # Log full error server-side (includes stack trace)
    logger.error(f"Internal server error on {request.url.path}: {exc}", exc_info=True)

    # Return safe, generic error message to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An internal error occurred",
            "suggestion": "Please try again later or contact support if the issue persists"
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for any unhandled exceptions.

    Logs full error details server-side but never exposes sensitive information
    or internal details to clients.
    """
    # Log full error server-side (includes stack trace)
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)

    # Return safe, generic error message to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An internal error occurred",
            "suggestion": "Please try again later or contact support if the issue persists"
        }
    )


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """
    Request model for the /analyze endpoint
    """
    description: str = Field(..., min_length=1, description="Description of the customer issue")
    timestamp: str = Field(..., description="ISO 8601 timestamp of when the issue occurred")
    customer_id: str = Field(..., min_length=1, description="Customer ID (e.g., usr_abc123)")

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate that timestamp is a valid ISO 8601 datetime"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("timestamp must be a valid ISO 8601 datetime string")
        return v

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        """Validate that customer_id is not empty and has reasonable format"""
        if not v or not v.strip():
            raise ValueError("customer_id cannot be empty")
        return v.strip()


class Cause(BaseModel):
    """A probable cause of the issue"""
    rank: int
    cause: str
    explanation: str
    confidence: str  # "high", "medium", or "low"


class AnalyzeResponse(BaseModel):
    """
    Response model for the /analyze endpoint
    """
    success: bool
    causes: list[Cause] = []
    suggested_response: str = ""
    sentry_links: list[str] = []
    logs_summary: str = ""
    events_found: int = 0


class ErrorResponse(BaseModel):
    """
    Error response model
    """
    success: bool = False
    error: str
    suggestion: str = ""


# Authentication dependency
async def verify_auth(request: Request):
    """
    Verify that the request includes a valid authentication token.

    Checks the X-Auth-Token header against the configured APP_PASSWORD.
    Raises 401 Unauthorized if the token is missing or invalid.

    Args:
        request: The FastAPI Request object

    Raises:
        HTTPException: 401 if authentication fails
    """
    token = request.headers.get("X-Auth-Token")

    # Get the app password from config (reload to pick up env changes in tests)
    import config as config_module
    config_module.config = None  # Reset to force reload
    try:
        app_config = get_config()
        expected_password = app_config.app_password
    except ValueError:
        # Config not available (e.g., in tests), raise unauthorized
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Verify token matches password
    if not token or token != expected_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify service is running
    """
    return {
        "status": "healthy",
        "version": "0.1.0"
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    analyze_request: AnalyzeRequest,
    request: Request
):
    """
    Analyze logs for a customer issue (requires authentication)

    This endpoint accepts a description of a customer issue, along with a timestamp
    and customer ID, and returns AI-powered analysis of probable causes.

    Authentication is required via the X-Auth-Token header.

    Args:
        analyze_request: The analysis request containing description, timestamp, and customer_id
        request: The FastAPI Request object (used for auth)

    Returns:
        AnalyzeResponse: Analysis results with probable causes and suggestions

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 422 if request validation fails
    """
    # Verify authentication
    await verify_auth(request)

    # Import Sentry client functions
    from sentry_client import (
        fetch_sentry_events,
        format_events_for_llm,
        generate_sentry_link,
        SentryAuthError,
        SentryRateLimitError,
        SentryAPIError,
    )

    # Fetch Sentry events for the customer
    try:
        events = await fetch_sentry_events(
            customer_id=analyze_request.customer_id,
            timestamp=analyze_request.timestamp,
            time_window_minutes=5,
        )
    except SentryAuthError:
        # Authentication failed - return error to user
        logger.error("Sentry authentication failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sentry authentication failed. Please check configuration."
        )
    except SentryRateLimitError as e:
        # Rate limit exceeded - return error with suggestion
        logger.warning(f"Sentry rate limit exceeded: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Sentry rate limit exceeded. {str(e)}"
        )
    except SentryAPIError as e:
        # Sentry API error - don't fail entire request, return empty events
        logger.error(f"Sentry API error: {e}")
        events = []
    except Exception as e:
        # Unexpected error - log but don't fail entire request
        logger.error(f"Unexpected error fetching Sentry events: {e}", exc_info=True)
        events = []

    # Generate Sentry links for all events
    sentry_links = []
    if events:
        for event in events:
            event_id = event.get("id")
            if event_id:
                sentry_links.append(generate_sentry_link(event_id))

    # Format events for LLM
    logs_summary = format_events_for_llm(events)

    # Import analyzer functions
    from analyzer import analyze_logs, LLMAnalysisError, LLMResponseFormatError, LLMAPIError
    import os

    # Load knowledge base files
    workflow_path = os.path.join(os.path.dirname(__file__), "docs", "workflow.md")
    known_errors_path = os.path.join(os.path.dirname(__file__), "docs", "known_errors.md")

    try:
        with open(workflow_path, "r") as f:
            workflow_docs = f.read()
    except FileNotFoundError:
        logger.warning(f"Workflow documentation not found at {workflow_path}")
        workflow_docs = "No workflow documentation available."

    try:
        with open(known_errors_path, "r") as f:
            known_errors = f.read()
    except FileNotFoundError:
        logger.warning(f"Known errors documentation not found at {known_errors_path}")
        known_errors = "No known error patterns available."

    # Call LLM analyzer
    try:
        llm_response = await analyze_logs(
            description=analyze_request.description,
            timestamp=analyze_request.timestamp,
            customer_id=analyze_request.customer_id,
            formatted_events=logs_summary,
            workflow_docs=workflow_docs,
            known_errors=known_errors
        )
    except LLMResponseFormatError as e:
        # LLM returned invalid format - return error
        logger.error(f"LLM response format error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: Invalid response format from AI. {str(e)}"
        )
    except LLMAPIError as e:
        # OpenAI API error - return error
        logger.error(f"LLM API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Analysis failed: AI service unavailable. {str(e)}"
        )
    except LLMAnalysisError as e:
        # Generic LLM error - return error
        logger.error(f"LLM analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed: An unexpected error occurred"
        )

    # Parse causes from LLM response
    causes = []
    for cause_data in llm_response.get("causes", []):
        causes.append(Cause(
            rank=cause_data.get("rank"),
            cause=cause_data.get("cause"),
            explanation=cause_data.get("explanation"),
            confidence=cause_data.get("confidence")
        ))

    # Return structured response with LLM analysis and Sentry links
    return AnalyzeResponse(
        success=True,
        causes=causes,
        suggested_response=llm_response.get("suggested_response", ""),
        sentry_links=sentry_links,
        logs_summary=llm_response.get("logs_summary", ""),
        events_found=len(events)
    )


@app.post("/slack/commands")
async def slack_commands(request: Request):
    """
    Handle Slack slash commands (e.g., /loglens)

    This endpoint receives slash commands from Slack and processes them.
    Slack signature verification is performed to ensure requests are authentic.

    Args:
        request: The FastAPI Request object containing Slack command data

    Returns:
        JSON response formatted for Slack

    Raises:
        HTTPException: 401 if signature verification fails
        HTTPException: 400 if command format is invalid
    """
    # Import Slack bot functions
    from slack_bot import (
        verify_slack_signature,
        handle_slack_command,
        format_slack_error,
        SlackSignatureVerificationError
    )

    # Get Slack signature headers
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")

    if not timestamp or not signature:
        logger.warning("Missing Slack signature headers")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature headers"
        )

    # Read raw body for signature verification
    body = await request.body()

    # Get signing secret from config
    import config as config_module
    config_module.config = None  # Reset to force reload
    try:
        slack_config = get_config()
        signing_secret = slack_config.slack_signing_secret
    except ValueError:
        logger.error("Slack signing secret not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Slack integration not configured"
        )

    # Verify Slack signature
    try:
        verify_slack_signature(body, timestamp, signature, signing_secret)
    except SlackSignatureVerificationError as e:
        logger.warning(f"Slack signature verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )

    # Parse form data from Slack
    from urllib.parse import parse_qs
    form_data = parse_qs(body.decode('utf-8'))

    # Extract command text
    command_text = form_data.get('text', [''])[0]

    logger.info(f"Received Slack command: {command_text}")

    # Handle the command
    try:
        response = await handle_slack_command(command_text)
        return response
    except Exception as e:
        logger.error(f"Error handling Slack command: {e}", exc_info=True)
        return format_slack_error(
            "An error occurred while processing your request",
            "Please try again or contact support if the issue persists"
        )
