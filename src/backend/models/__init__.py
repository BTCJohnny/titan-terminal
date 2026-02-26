"""
Pydantic models for signal output structures.

Provides type-safe models for TA analysis and on-chain signals.
"""

from .ta_signal import TASignal
from .telegram_signal import TelegramChannelSignal, TelegramSignal

__all__ = ["TASignal", "TelegramChannelSignal", "TelegramSignal"]
