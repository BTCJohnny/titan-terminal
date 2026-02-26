"""
Pydantic models for Telegram signal aggregation.

TelegramChannelSignal: Individual signal from a single channel
TelegramSignal: Aggregated signal output from Telegram agent
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TelegramChannelSignal(BaseModel):
    """Individual signal from a Telegram channel."""

    channel: str = Field(..., description="Source channel name")
    action: Literal["long", "short", "buy", "sell"] = Field(
        ..., description="Trade action signaled"
    )
    entry_price: Optional[float] = Field(None, description="Suggested entry price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profits: list[float] = Field(
        default_factory=list, description="List of take profit targets"
    )
    signal_quality: int = Field(..., ge=0, le=100, description="Signal quality score")
    freshness: Literal["fresh", "stale"] = Field(
        ..., description="Signal age indicator"
    )
    timestamp: Optional[datetime] = Field(None, description="When signal was posted")
    raw_text: Optional[str] = Field(None, description="Original message text")
    notes: str = Field(default="", description="Additional notes about the signal")


class TelegramSignal(BaseModel):
    """Aggregated Telegram signal output (MODL-04).

    Combines multiple channel signals into a unified sentiment view.
    """

    symbol: str = Field(..., description="Trading symbol (e.g., BTC)")
    signals_found: int = Field(..., ge=0, description="Total signals found")
    relevant_signals: list[TelegramChannelSignal] = Field(
        default_factory=list, description="List of relevant channel signals"
    )
    overall_sentiment: Literal["bullish", "bearish", "mixed", "neutral"] = Field(
        ..., description="Aggregated sentiment from all signals"
    )
    confluence_count: int = Field(
        ..., ge=0, description="Number of signals that agree"
    )
    confidence: int = Field(
        ..., ge=0, le=100, description="Overall confidence in sentiment"
    )
    notes: str = Field(default="", description="Summary notes")
