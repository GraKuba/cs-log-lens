"""
Tests for configuration management
Validates environment variable loading and validation
"""

import os
import pytest
from config import Config


class TestConfigLoading:
    """Test that config loads environment variables correctly"""

    def test_config_loads_all_required_vars(self, monkeypatch):
        """Test config loads successfully when all vars are set"""
        # Set all required environment variables
        env_vars = {
            "SENTRY_AUTH_TOKEN": "sntrys_test123",
            "SENTRY_ORG": "test-org",
            "SENTRY_PROJECT": "test-project",
            "OPENAI_API_KEY": "sk-test123",
            "SLACK_BOT_TOKEN": "xoxb-test123",
            "SLACK_SIGNING_SECRET": "test-secret",
            "APP_PASSWORD": "test-password",
            "ALLOWED_ORIGINS": "https://test.com",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Should not raise any errors
        config = Config()

        # Verify all values are loaded correctly
        assert config.sentry_auth_token == "sntrys_test123"
        assert config.sentry_org == "test-org"
        assert config.sentry_project == "test-project"
        assert config.openai_api_key == "sk-test123"
        assert config.slack_bot_token == "xoxb-test123"
        assert config.slack_signing_secret == "test-secret"
        assert config.app_password == "test-password"
        assert config.allowed_origins == "https://test.com"

    def test_config_uses_default_for_allowed_origins(self, monkeypatch):
        """Test ALLOWED_ORIGINS defaults to * if not set"""
        # Set all required vars except ALLOWED_ORIGINS
        required_vars = {
            "SENTRY_AUTH_TOKEN": "sntrys_test123",
            "SENTRY_ORG": "test-org",
            "SENTRY_PROJECT": "test-project",
            "OPENAI_API_KEY": "sk-test123",
            "SLACK_BOT_TOKEN": "xoxb-test123",
            "SLACK_SIGNING_SECRET": "test-secret",
            "APP_PASSWORD": "test-password",
        }

        for key, value in required_vars.items():
            monkeypatch.setenv(key, value)

        # Ensure ALLOWED_ORIGINS is not set
        monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)

        config = Config()
        assert config.allowed_origins == "*"


class TestConfigValidation:
    """Test that config validates required variables"""

    def test_config_raises_error_when_sentry_token_missing(self, monkeypatch):
        """Test config raises error when SENTRY_AUTH_TOKEN is missing"""
        # Set all vars except SENTRY_AUTH_TOKEN
        env_vars = {
            "SENTRY_ORG": "test-org",
            "SENTRY_PROJECT": "test-project",
            "OPENAI_API_KEY": "sk-test123",
            "SLACK_BOT_TOKEN": "xoxb-test123",
            "SLACK_SIGNING_SECRET": "test-secret",
            "APP_PASSWORD": "test-password",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        monkeypatch.delenv("SENTRY_AUTH_TOKEN", raising=False)

        with pytest.raises(ValueError) as exc_info:
            Config()

        assert "SENTRY_AUTH_TOKEN" in str(exc_info.value)
        assert "Missing required environment variables" in str(exc_info.value)

    def test_config_raises_error_when_multiple_vars_missing(self, monkeypatch):
        """Test config raises error listing all missing vars"""
        # Set only some vars
        env_vars = {
            "SENTRY_AUTH_TOKEN": "sntrys_test123",
            "SENTRY_ORG": "test-org",
            "OPENAI_API_KEY": "sk-test123",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Clear the rest
        for key in [
            "SENTRY_PROJECT",
            "SLACK_BOT_TOKEN",
            "SLACK_SIGNING_SECRET",
            "APP_PASSWORD",
        ]:
            monkeypatch.delenv(key, raising=False)

        with pytest.raises(ValueError) as exc_info:
            Config()

        error_message = str(exc_info.value)
        assert "SENTRY_PROJECT" in error_message
        assert "SLACK_BOT_TOKEN" in error_message
        assert "SLACK_SIGNING_SECRET" in error_message
        assert "APP_PASSWORD" in error_message

    def test_config_raises_error_when_all_vars_missing(self, monkeypatch):
        """Test config raises error when all required vars are missing"""
        # Clear all required vars
        for key in [
            "SENTRY_AUTH_TOKEN",
            "SENTRY_ORG",
            "SENTRY_PROJECT",
            "OPENAI_API_KEY",
            "SLACK_BOT_TOKEN",
            "SLACK_SIGNING_SECRET",
            "APP_PASSWORD",
        ]:
            monkeypatch.delenv(key, raising=False)

        with pytest.raises(ValueError) as exc_info:
            Config()

        assert "Missing required environment variables" in str(exc_info.value)


class TestConfigTypes:
    """Test that config values have correct types"""

    def test_all_config_values_are_strings(self, monkeypatch):
        """Test that all config values are loaded as strings"""
        env_vars = {
            "SENTRY_AUTH_TOKEN": "sntrys_test123",
            "SENTRY_ORG": "test-org",
            "SENTRY_PROJECT": "test-project",
            "OPENAI_API_KEY": "sk-test123",
            "SLACK_BOT_TOKEN": "xoxb-test123",
            "SLACK_SIGNING_SECRET": "test-secret",
            "APP_PASSWORD": "test-password",
            "ALLOWED_ORIGINS": "https://test.com",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        config = Config()

        # Verify all are strings
        assert isinstance(config.sentry_auth_token, str)
        assert isinstance(config.sentry_org, str)
        assert isinstance(config.sentry_project, str)
        assert isinstance(config.openai_api_key, str)
        assert isinstance(config.slack_bot_token, str)
        assert isinstance(config.slack_signing_secret, str)
        assert isinstance(config.app_password, str)
        assert isinstance(config.allowed_origins, str)

    def test_config_handles_empty_string_as_missing(self, monkeypatch):
        """Test that empty strings are treated as missing values"""
        # Set all required vars except one set to empty string
        env_vars = {
            "SENTRY_AUTH_TOKEN": "",  # Empty string
            "SENTRY_ORG": "test-org",
            "SENTRY_PROJECT": "test-project",
            "OPENAI_API_KEY": "sk-test123",
            "SLACK_BOT_TOKEN": "xoxb-test123",
            "SLACK_SIGNING_SECRET": "test-secret",
            "APP_PASSWORD": "test-password",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        with pytest.raises(ValueError) as exc_info:
            Config()

        assert "SENTRY_AUTH_TOKEN" in str(exc_info.value)


class TestConfigErrorMessages:
    """Test that error messages are clear and actionable"""

    def test_error_message_provides_guidance(self, monkeypatch):
        """Test that error message suggests checking .env file"""
        # Clear all vars
        for key in [
            "SENTRY_AUTH_TOKEN",
            "SENTRY_ORG",
            "SENTRY_PROJECT",
            "OPENAI_API_KEY",
            "SLACK_BOT_TOKEN",
            "SLACK_SIGNING_SECRET",
            "APP_PASSWORD",
        ]:
            monkeypatch.delenv(key, raising=False)

        with pytest.raises(ValueError) as exc_info:
            Config()

        error_message = str(exc_info.value)
        assert ".env file" in error_message or "environment" in error_message
        assert "Please ensure" in error_message

    def test_error_message_lists_specific_missing_vars(self, monkeypatch):
        """Test that error message lists exactly which vars are missing"""
        # Set half the vars
        env_vars = {
            "SENTRY_AUTH_TOKEN": "test",
            "OPENAI_API_KEY": "test",
            "SLACK_BOT_TOKEN": "test",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        # Clear the others
        for key in ["SENTRY_ORG", "SENTRY_PROJECT", "SLACK_SIGNING_SECRET", "APP_PASSWORD"]:
            monkeypatch.delenv(key, raising=False)

        with pytest.raises(ValueError) as exc_info:
            Config()

        error_message = str(exc_info.value)
        # Should mention the missing vars
        assert "SENTRY_ORG" in error_message
        assert "SENTRY_PROJECT" in error_message
        assert "SLACK_SIGNING_SECRET" in error_message
        assert "APP_PASSWORD" in error_message
        # Should not mention the vars that are set
        assert error_message.count("SENTRY_AUTH_TOKEN") <= 1  # May appear in general message
        assert error_message.count("OPENAI_API_KEY") <= 1
        assert error_message.count("SLACK_BOT_TOKEN") <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
