"""
Configuration management for LogLens
Loads and validates environment variables
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables"""

    # Sentry Configuration
    sentry_auth_token: str
    sentry_org: str
    sentry_project: str

    # OpenAI Configuration
    openai_api_key: str

    # Slack Configuration
    slack_bot_token: str
    slack_signing_secret: str

    # Application Security
    app_password: str
    allowed_origins: str

    def __init__(self):
        """Load and validate all required environment variables"""
        self._load_config()
        self._validate_config()

    def _load_config(self):
        """Load all environment variables"""
        self.sentry_auth_token = os.getenv("SENTRY_AUTH_TOKEN", "")
        self.sentry_org = os.getenv("SENTRY_ORG", "")
        self.sentry_project = os.getenv("SENTRY_PROJECT", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.slack_bot_token = os.getenv("SLACK_BOT_TOKEN", "")
        self.slack_signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")
        self.app_password = os.getenv("APP_PASSWORD", "")
        self.allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")

    def _validate_config(self):
        """Validate that all required environment variables are set"""
        required_vars = {
            "SENTRY_AUTH_TOKEN": self.sentry_auth_token,
            "SENTRY_ORG": self.sentry_org,
            "SENTRY_PROJECT": self.sentry_project,
            "OPENAI_API_KEY": self.openai_api_key,
            "SLACK_BOT_TOKEN": self.slack_bot_token,
            "SLACK_SIGNING_SECRET": self.slack_signing_secret,
            "APP_PASSWORD": self.app_password,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please ensure all variables are set in your .env file or environment."
            )


# Global config instance - loaded lazily to avoid import errors in tests
config = None


def get_config() -> Config:
    """Get or create the global config instance"""
    global config
    if config is None:
        config = Config()
    return config
