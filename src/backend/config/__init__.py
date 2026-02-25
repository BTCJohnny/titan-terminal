"""Configuration for Titan Terminal."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)


class Config:
    """Application configuration."""

    # Anthropic API
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    MODEL_NAME = "claude-sonnet-4-20250514"  # Default model
    MENTOR_MODEL = "claude-sonnet-4-20250514"  # Mentor critic model

    # Nansen API (if available)
    NANSEN_API_KEY = os.getenv("NANSEN_API_KEY", "")

    # Crypto.com Exchange (for price data)
    CRYPTOCOM_API_KEY = os.getenv("CRYPTOCOM_API_KEY", "")

    # Batch settings
    MORNING_BATCH_HOUR = 8
    MORNING_BATCH_MINUTE = 30
    REFRESH_INTERVAL_MINUTES = 15

    # Trading universe
    HYPERLIQUID_PERPS = [
        "BTC", "ETH", "SOL", "AVAX", "ARB", "OP", "MATIC", "LINK",
        "DOGE", "PEPE", "WIF", "BONK", "JUP", "TIA", "SEI", "SUI",
        "INJ", "FET", "RENDER", "TAO"
    ]

    # Risk management (The 3 Laws)
    MAX_RISK_PER_TRADE = 0.02  # 2%
    MIN_RISK_REWARD = 2.0
    MAX_POSITIONS = 5


config = Config()
