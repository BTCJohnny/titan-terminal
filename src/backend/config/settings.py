"""Settings module for Titan Terminal configuration.

This module provides centralized access to all environment variables.
Uses python-dotenv to load .env from project root.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load .env from project root
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)


class Settings:
    """Centralized settings for all environment variables."""

    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    NANSEN_API_KEY: str = os.getenv("NANSEN_API_KEY", "")
    HYPERLIQUID_API_KEY: str = os.getenv("HYPERLIQUID_API_KEY", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Database
    SIGNALS_DB_PATH: str = os.getenv("SIGNALS_DB_PATH", "data/signals.db")

    def validate(self) -> None:
        """Validate critical settings and log warnings for missing keys."""
        if not self.ANTHROPIC_API_KEY:
            logger.warning(
                "ANTHROPIC_API_KEY is not set. Claude API calls will fail. "
                "Set this in your .env file."
            )


# Singleton instance for easy import
settings = Settings()

# Validate on import
settings.validate()
