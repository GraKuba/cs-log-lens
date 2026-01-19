"""
Tests for LLM Analyzer (Task 4.1)
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from analyzer import (
    analyze_logs,
    _construct_user_prompt,
    _validate_llm_response,
    _call_openai_api,
    LLMAnalysisError,
    LLMResponseFormatError,
    LLMAPIError,
    SYSTEM_PROMPT,
)


# Sample test data
SAMPLE_DESCRIPTION = "User can't complete checkout"
SAMPLE_TIMESTAMP = "2025-01-19T14:30:00Z"
SAMPLE_CUSTOMER_ID = "usr_test123"
SAMPLE_FORMATTED_EVENTS = """Event 1:
- Time: 2025-01-19T14:30:15Z
- Error: PaymentTokenExpiredError
- Message: "Token expired after 10 minutes"
"""
SAMPLE_WORKFLOW = "# Checkout Flow\n1. User adds items to cart\n2. User clicks Checkout"
SAMPLE_KNOWN_ERRORS = "# Payment Token Expired\nUser took too long on payment page"

VALID_LLM_RESPONSE = {
    "causes": [
        {
            "rank": 1,
            "cause": "Payment token expired",
            "explanation": "User took longer than 10 minutes on payment page",
            "confidence": "high"
        },
        {
            "rank": 2,
            "cause": "Session timeout",
            "explanation": "User session may have expired",
            "confidence": "medium"
        },
        {
            "rank": 3,
            "cause": "Network interruption",
            "explanation": "Connection may have been lost",
            "confidence": "low"
        }
    ],
    "suggested_response": "Hi! It looks like your payment session timed out. Please try again.",
    "logs_summary": "Found PaymentTokenExpiredError at 14:30:15Z indicating token expiration"
}


class TestConstructUserPrompt:
    """Test prompt construction"""

    def test_construct_user_prompt_includes_all_sections(self):
        """Test that user prompt includes all required sections"""
        prompt = _construct_user_prompt(
            description=SAMPLE_DESCRIPTION,
            timestamp=SAMPLE_TIMESTAMP,
            customer_id=SAMPLE_CUSTOMER_ID,
            formatted_events=SAMPLE_FORMATTED_EVENTS,
            workflow_docs=SAMPLE_WORKFLOW,
            known_errors=SAMPLE_KNOWN_ERRORS
        )

        # Check all sections are present
        assert "## Workflow Documentation" in prompt
        assert "## Known Error Patterns" in prompt
        assert "## Sentry Events" in prompt
        assert "## Problem Report" in prompt
        assert SAMPLE_WORKFLOW in prompt
        assert SAMPLE_KNOWN_ERRORS in prompt
        assert SAMPLE_FORMATTED_EVENTS in prompt
        assert SAMPLE_DESCRIPTION in prompt
        assert SAMPLE_TIMESTAMP in prompt
        assert SAMPLE_CUSTOMER_ID in prompt

    def test_construct_user_prompt_includes_json_format(self):
        """Test that prompt includes JSON format instructions"""
        prompt = _construct_user_prompt(
            description=SAMPLE_DESCRIPTION,
            timestamp=SAMPLE_TIMESTAMP,
            customer_id=SAMPLE_CUSTOMER_ID,
            formatted_events=SAMPLE_FORMATTED_EVENTS,
            workflow_docs=SAMPLE_WORKFLOW,
            known_errors=SAMPLE_KNOWN_ERRORS
        )

        assert "Analyze and respond in JSON format:" in prompt
        assert '"causes"' in prompt
        assert '"suggested_response"' in prompt
        assert '"logs_summary"' in prompt


class TestValidateLLMResponse:
    """Test LLM response validation"""

    def test_validate_valid_response(self):
        """Test validation passes for valid response"""
        # Should not raise any exception
        _validate_llm_response(VALID_LLM_RESPONSE)

    def test_validate_missing_causes(self):
        """Test validation fails when causes is missing"""
        invalid_response = {
            "suggested_response": "Test",
            "logs_summary": "Test"
        }
        with pytest.raises(LLMResponseFormatError, match="Missing required fields.*causes"):
            _validate_llm_response(invalid_response)

    def test_validate_missing_suggested_response(self):
        """Test validation fails when suggested_response is missing"""
        invalid_response = {
            "causes": VALID_LLM_RESPONSE["causes"],
            "logs_summary": "Test"
        }
        with pytest.raises(LLMResponseFormatError, match="Missing required fields.*suggested_response"):
            _validate_llm_response(invalid_response)

    def test_validate_missing_logs_summary(self):
        """Test validation fails when logs_summary is missing"""
        invalid_response = {
            "causes": VALID_LLM_RESPONSE["causes"],
            "suggested_response": "Test"
        }
        with pytest.raises(LLMResponseFormatError, match="Missing required fields.*logs_summary"):
            _validate_llm_response(invalid_response)

    def test_validate_causes_not_array(self):
        """Test validation fails when causes is not an array"""
        invalid_response = {
            "causes": "not an array",
            "suggested_response": "Test",
            "logs_summary": "Test"
        }
        with pytest.raises(LLMResponseFormatError, match="'causes' must be an array"):
            _validate_llm_response(invalid_response)

    def test_validate_cause_missing_fields(self):
        """Test validation fails when cause is missing required fields"""
        invalid_response = {
            "causes": [
                {"rank": 1, "cause": "Test"}  # Missing explanation and confidence
            ],
            "suggested_response": "Test",
            "logs_summary": "Test"
        }
        with pytest.raises(LLMResponseFormatError, match="Cause 0 missing fields"):
            _validate_llm_response(invalid_response)

    def test_validate_empty_suggested_response(self):
        """Test validation fails when suggested_response is empty"""
        invalid_response = {
            "causes": VALID_LLM_RESPONSE["causes"],
            "suggested_response": "   ",  # Empty/whitespace
            "logs_summary": "Test"
        }
        with pytest.raises(LLMResponseFormatError, match="'suggested_response' cannot be empty"):
            _validate_llm_response(invalid_response)

    def test_validate_empty_logs_summary(self):
        """Test validation fails when logs_summary is empty"""
        invalid_response = {
            "causes": VALID_LLM_RESPONSE["causes"],
            "suggested_response": "Test",
            "logs_summary": ""
        }
        with pytest.raises(LLMResponseFormatError, match="'logs_summary' cannot be empty"):
            _validate_llm_response(invalid_response)

    def test_validate_invalid_confidence_level(self):
        """Test validation logs warning for invalid confidence level"""
        invalid_response = {
            "causes": [
                {
                    "rank": 1,
                    "cause": "Test",
                    "explanation": "Test explanation",
                    "confidence": "very-high"  # Invalid confidence
                },
                VALID_LLM_RESPONSE["causes"][1],
                VALID_LLM_RESPONSE["causes"][2]
            ],
            "suggested_response": "Test",
            "logs_summary": "Test"
        }
        # Should log warning but not raise exception
        # (validation is lenient for confidence levels)
        _validate_llm_response(invalid_response)


@pytest.mark.asyncio
class TestCallOpenAIAPI:
    """Test OpenAI API calls with retry logic"""

    async def test_successful_api_call(self):
        """Test successful API call"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"test": "response"}'))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [{"role": "system", "content": "test"}]
        result = await _call_openai_api(mock_client, messages)

        assert result == '{"test": "response"}'
        mock_client.chat.completions.create.assert_called_once()

    async def test_api_call_with_empty_response(self):
        """Test API call with empty response raises error"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [{"role": "system", "content": "test"}]

        with pytest.raises(LLMAPIError, match="Empty response from OpenAI API"):
            await _call_openai_api(mock_client, messages)

    async def test_api_call_with_exception(self):
        """Test API call raises LLMAPIError on exception"""
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))

        messages = [{"role": "system", "content": "test"}]

        with pytest.raises(LLMAPIError, match="OpenAI API call failed"):
            await _call_openai_api(mock_client, messages)


@pytest.mark.asyncio
class TestAnalyzeLogs:
    """Test main analyze_logs function"""

    @patch("analyzer.AsyncOpenAI")
    @patch("analyzer.get_config")
    async def test_successful_analysis(self, mock_get_config, mock_openai_class):
        """Test successful log analysis"""
        # Mock config
        mock_config = MagicMock()
        mock_config.openai_api_key = "test-key"
        mock_get_config.return_value = mock_config

        # Mock OpenAI client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(VALID_LLM_RESPONSE)))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client

        result = await analyze_logs(
            description=SAMPLE_DESCRIPTION,
            timestamp=SAMPLE_TIMESTAMP,
            customer_id=SAMPLE_CUSTOMER_ID,
            formatted_events=SAMPLE_FORMATTED_EVENTS,
            workflow_docs=SAMPLE_WORKFLOW,
            known_errors=SAMPLE_KNOWN_ERRORS
        )

        # Verify result
        assert result == VALID_LLM_RESPONSE
        assert len(result["causes"]) == 3
        assert result["causes"][0]["rank"] == 1
        assert result["suggested_response"]
        assert result["logs_summary"]

        # Verify OpenAI client was initialized with correct API key
        mock_openai_class.assert_called_once_with(api_key="test-key")

        # Verify API was called with correct model and parameters
        create_call = mock_client.chat.completions.create
        create_call.assert_called_once()
        call_kwargs = create_call.call_args[1]
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["response_format"] == {"type": "json_object"}
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_tokens"] == 1500

    @patch("analyzer.AsyncOpenAI")
    @patch("analyzer.get_config")
    async def test_analysis_with_no_sentry_events(self, mock_get_config, mock_openai_class):
        """Test analysis with no Sentry events"""
        # Mock config
        mock_config = MagicMock()
        mock_config.openai_api_key = "test-key"
        mock_get_config.return_value = mock_config

        # Mock OpenAI to return response indicating no events
        no_events_response = {
            "causes": [
                {
                    "rank": 1,
                    "cause": "Insufficient log data",
                    "explanation": "No Sentry events found in the time range",
                    "confidence": "low"
                },
                {
                    "rank": 2,
                    "cause": "User error not captured",
                    "explanation": "Error may not have been logged",
                    "confidence": "low"
                },
                {
                    "rank": 3,
                    "cause": "Time range too narrow",
                    "explanation": "Error may have occurred outside the search window",
                    "confidence": "low"
                }
            ],
            "suggested_response": "We couldn't find specific errors in our logs. Can you provide more details?",
            "logs_summary": "No events found"
        }

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(no_events_response)))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client

        result = await analyze_logs(
            description=SAMPLE_DESCRIPTION,
            timestamp=SAMPLE_TIMESTAMP,
            customer_id=SAMPLE_CUSTOMER_ID,
            formatted_events="No events found",
            workflow_docs=SAMPLE_WORKFLOW,
            known_errors=SAMPLE_KNOWN_ERRORS
        )

        assert result["logs_summary"] == "No events found"
        assert len(result["causes"]) == 3

    @patch("analyzer.AsyncOpenAI")
    @patch("analyzer.get_config")
    async def test_analysis_with_malformed_json(self, mock_get_config, mock_openai_class):
        """Test analysis with malformed JSON response"""
        mock_config = MagicMock()
        mock_config.openai_api_key = "test-key"
        mock_get_config.return_value = mock_config

        # Mock OpenAI to return invalid JSON
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Not valid JSON{"))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client

        with pytest.raises(LLMResponseFormatError, match="Invalid JSON response from LLM"):
            await analyze_logs(
                description=SAMPLE_DESCRIPTION,
                timestamp=SAMPLE_TIMESTAMP,
                customer_id=SAMPLE_CUSTOMER_ID,
                formatted_events=SAMPLE_FORMATTED_EVENTS,
                workflow_docs=SAMPLE_WORKFLOW,
                known_errors=SAMPLE_KNOWN_ERRORS
            )

    @patch("analyzer.AsyncOpenAI")
    @patch("analyzer.get_config")
    async def test_analysis_with_openai_api_error(self, mock_get_config, mock_openai_class):
        """Test analysis handles OpenAI API errors"""
        mock_config = MagicMock()
        mock_config.openai_api_key = "test-key"
        mock_get_config.return_value = mock_config

        # Mock OpenAI to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Rate limit exceeded"))
        mock_openai_class.return_value = mock_client

        with pytest.raises(LLMAPIError):
            await analyze_logs(
                description=SAMPLE_DESCRIPTION,
                timestamp=SAMPLE_TIMESTAMP,
                customer_id=SAMPLE_CUSTOMER_ID,
                formatted_events=SAMPLE_FORMATTED_EVENTS,
                workflow_docs=SAMPLE_WORKFLOW,
                known_errors=SAMPLE_KNOWN_ERRORS
            )

    @patch("analyzer.AsyncOpenAI")
    @patch("analyzer.get_config")
    async def test_prompt_construction_in_analysis(self, mock_get_config, mock_openai_class):
        """Test that prompts are correctly constructed in analysis"""
        mock_config = MagicMock()
        mock_config.openai_api_key = "test-key"
        mock_get_config.return_value = mock_config

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps(VALID_LLM_RESPONSE)))]
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai_class.return_value = mock_client

        await analyze_logs(
            description=SAMPLE_DESCRIPTION,
            timestamp=SAMPLE_TIMESTAMP,
            customer_id=SAMPLE_CUSTOMER_ID,
            formatted_events=SAMPLE_FORMATTED_EVENTS,
            workflow_docs=SAMPLE_WORKFLOW,
            known_errors=SAMPLE_KNOWN_ERRORS
        )

        # Verify messages passed to OpenAI
        create_call = mock_client.chat.completions.create
        messages = create_call.call_args[1]["messages"]

        # Check system prompt
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT

        # Check user prompt contains all required sections
        user_content = messages[1]["content"]
        assert messages[1]["role"] == "user"
        assert SAMPLE_DESCRIPTION in user_content
        assert SAMPLE_TIMESTAMP in user_content
        assert SAMPLE_CUSTOMER_ID in user_content
        assert SAMPLE_FORMATTED_EVENTS in user_content
        assert SAMPLE_WORKFLOW in user_content
        assert SAMPLE_KNOWN_ERRORS in user_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
