"""Configuration package for Titan Terminal.

- settings: Environment variables (API keys, paths)
- constants: Static trading constants (symbols, risk limits)
"""
from .settings import settings
from .constants import (
    HYPERLIQUID_PERPS,
    MAX_RISK_PER_TRADE,
    MIN_RISK_REWARD,
    MAX_POSITIONS,
    MORNING_BATCH_HOUR,
    MORNING_BATCH_MINUTE,
    REFRESH_INTERVAL_MINUTES,
)

__all__ = [
    "settings",
    "HYPERLIQUID_PERPS",
    "MAX_RISK_PER_TRADE",
    "MIN_RISK_REWARD",
    "MAX_POSITIONS",
    "MORNING_BATCH_HOUR",
    "MORNING_BATCH_MINUTE",
    "REFRESH_INTERVAL_MINUTES",
]
