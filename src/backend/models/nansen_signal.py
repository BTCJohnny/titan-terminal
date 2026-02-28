"""
NansenSignal Pydantic model for on-chain analysis output.

Represents the structured output from the Nansen agent using the 5-signal framework:
exchange_flows, fresh_wallets, smart_money, top_pnl, whale_activity.
"""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ExchangeFlows(BaseModel):
    """Exchange inflow/outflow analysis."""
    net_direction: Literal["inflow", "outflow", "neutral"]
    magnitude: Literal["high", "medium", "low"]
    interpretation: str = Field(..., description="Interpretation of exchange flow activity")
    confidence: int = Field(..., ge=0, le=100, description="Confidence in this signal 0-100")


class FreshWallets(BaseModel):
    """Fresh wallet activity analysis."""
    activity_level: Literal["high", "medium", "low", "none"]
    trend: Literal["increasing", "decreasing", "stable"]
    notable_count: int = Field(default=0, ge=0, description="Count of notable fresh wallets")
    interpretation: str = Field(..., description="Interpretation of fresh wallet activity")


class SmartMoney(BaseModel):
    """Smart money flow analysis."""
    direction: Literal["accumulating", "distributing", "neutral"]
    confidence: int = Field(..., ge=0, le=100, description="Confidence in this signal 0-100")
    notable_wallets: list[str] = Field(
        default_factory=list, description="List of notable smart money wallet addresses"
    )
    interpretation: str = Field(..., description="Interpretation of smart money behavior")


class TopPnL(BaseModel):
    """Top PnL traders analysis."""
    traders_bias: Literal["bullish", "bearish", "mixed", "neutral"]
    average_position: Literal["long", "short", "neutral"]
    confidence: int = Field(..., ge=0, le=100, description="Confidence in this signal 0-100")
    interpretation: str = Field(..., description="Interpretation of top trader positioning")


class WhaleActivity(BaseModel):
    """Whale transaction analysis."""
    summary: str = Field(..., description="Summary of whale activity")
    notable_transactions: list[str] = Field(
        default_factory=list, description="List of notable whale transaction IDs"
    )
    net_flow: Literal["accumulating", "distributing", "neutral"]
    confidence: int = Field(..., ge=0, le=100, description="Confidence in this signal 0-100")


class OnChainOverall(BaseModel):
    """Overall on-chain signal assessment."""
    bias: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(..., ge=0, le=100, description="Overall confidence 0-100")
    key_insights: list[str] = Field(
        default_factory=list, description="Key insights from on-chain analysis"
    )


class FundingRate(BaseModel):
    """Funding rate data from Hyperliquid (via MCP)."""
    rate: Optional[float] = Field(None, description="Funding rate value")
    available: bool = Field(default=True, description="Whether funding rate data was available")
    interpretation: str = Field(..., description="Interpretation of funding rate for positioning")


class NansenSignal(BaseModel):
    """
    Nansen on-chain signal using 5-signal framework.

    Combines exchange flows, fresh wallets, smart money, top PnL traders,
    and whale activity into a unified on-chain assessment.
    """
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC')")
    exchange_flows: ExchangeFlows
    fresh_wallets: FreshWallets
    smart_money: SmartMoney
    top_pnl: TopPnL
    whale_activity: WhaleActivity
    funding_rate: Optional[FundingRate] = Field(None, description="Hyperliquid funding rate data")
    overall_signal: OnChainOverall
    signal_count_bullish: int = Field(..., ge=0, le=5, description="Count of bullish signals (0-5)")
    signal_count_bearish: int = Field(..., ge=0, le=5, description="Count of bearish signals (0-5)")
    reasoning: str = Field(..., description="Explanation of overall signal derivation")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When signal was generated")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTC",
                    "exchange_flows": {
                        "net_direction": "outflow",
                        "magnitude": "high",
                        "interpretation": "Bullish - significant coins leaving exchanges indicating accumulation",
                        "confidence": 75
                    },
                    "fresh_wallets": {
                        "activity_level": "medium",
                        "trend": "increasing",
                        "notable_count": 150,
                        "interpretation": "Growing number of new accumulation wallets"
                    },
                    "smart_money": {
                        "direction": "accumulating",
                        "confidence": 80,
                        "notable_wallets": ["0xabc...123", "0xdef...456"],
                        "interpretation": "Smart money showing strong accumulation pattern"
                    },
                    "top_pnl": {
                        "traders_bias": "bullish",
                        "average_position": "long",
                        "confidence": 70,
                        "interpretation": "Top traders predominantly positioned long"
                    },
                    "whale_activity": {
                        "summary": "Large accumulation by multiple whale wallets",
                        "notable_transactions": ["txn_123", "txn_456"],
                        "net_flow": "accumulating",
                        "confidence": 85
                    },
                    "funding_rate": {
                        "rate": 0.0012,
                        "available": True,
                        "interpretation": "Moderate positive funding suggests slight long bias in market"
                    },
                    "overall_signal": {
                        "bias": "bullish",
                        "confidence": 78,
                        "key_insights": [
                            "Strong exchange outflows indicating accumulation",
                            "Smart money actively accumulating",
                            "Whale activity confirms bullish positioning"
                        ]
                    },
                    "signal_count_bullish": 4,
                    "signal_count_bearish": 1,
                    "reasoning": "4 out of 5 on-chain signals show bullish bias (exchange flows, smart money, top PnL, whale activity). Fresh wallets show neutral/increasing activity. Funding rate confirms slight market long bias.",
                    "timestamp": "2026-02-28T15:30:00Z"
                }
            ]
        }
    }
