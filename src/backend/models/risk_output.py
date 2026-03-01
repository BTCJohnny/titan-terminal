"""
Pydantic models for Risk Agent output.

RiskOutput: Complete risk analysis with entry, stops, targets, position sizing
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class EntryZone(BaseModel):
    """Entry zone specification."""

    low: float = Field(..., description="Lower bound of entry zone")
    high: float = Field(..., description="Upper bound of entry zone")
    ideal: float = Field(..., description="Ideal entry price")
    entry_reasoning: str = Field(..., description="Why this entry zone")


class StopLoss(BaseModel):
    """Stop loss specification."""

    price: float = Field(..., description="Stop loss price")
    type: Literal["structure", "atr", "percentage"] = Field(
        ..., description="Type of stop loss"
    )
    distance_percent: float = Field(..., description="Distance from entry in %")
    reasoning: str = Field(..., description="Why this stop loss level")


class TakeProfit(BaseModel):
    """Single take profit target."""

    price: float = Field(..., description="Take profit price")
    rr_ratio: float = Field(..., description="Risk/reward ratio to this target")
    reasoning: str = Field(..., description="Why this target level")


class TakeProfits(BaseModel):
    """Take profit targets."""

    tp1: TakeProfit = Field(..., description="First take profit target")
    tp2: Optional[TakeProfit] = Field(None, description="Second take profit target")


class RiskReward(BaseModel):
    """Risk/reward analysis."""

    to_tp1: float = Field(..., description="Risk/reward ratio to TP1")
    to_tp2: Optional[float] = Field(None, description="Risk/reward ratio to TP2")
    meets_minimum: bool = Field(
        ..., description="Meets minimum 3:1 ratio per 3 Laws"
    )


class PositionSizing(BaseModel):
    """Position sizing recommendation."""

    max_risk_percent: float = Field(
        default=2.0, description="Maximum risk per trade (3 Laws)"
    )
    suggested_position_percent: float = Field(
        ..., description="Suggested position size as % of portfolio"
    )
    reasoning: str = Field(..., description="Position sizing rationale")


class FundingFilter(BaseModel):
    """Funding rate analysis for perpetuals."""

    current_funding: Optional[float] = Field(None, description="Current funding rate")
    funding_bias: Literal["favorable", "unfavorable", "neutral"] = Field(
        ..., description="Is funding aligned with trade direction"
    )
    warning: Optional[str] = Field(None, description="Warning if funding is extreme")


class ThreeLawsCheck(BaseModel):
    """3 Laws of Trading validation."""

    law_1_risk: Literal["pass", "fail"] = Field(
        ..., description="Law 1: Max 2% risk per trade"
    )
    law_2_rr: Literal["pass", "fail"] = Field(
        ..., description="Law 2: Min 3:1 risk/reward"
    )
    law_3_positions: Literal["pass", "fail"] = Field(
        ..., description="Law 3: Max 5 concurrent positions"
    )
    overall: Literal["approved", "rejected", "caution"] = Field(
        ..., description="Overall verdict"
    )


class FinalVerdict(BaseModel):
    """Final risk assessment verdict."""

    action: Literal["long_spot", "long_perp", "short_perp", "avoid"] = Field(
        ..., description="Recommended action"
    )
    confidence: int = Field(
        ..., ge=0, le=100, description="Confidence in recommendation"
    )
    notes: str = Field(default="", description="Additional notes")


class RiskOutput(BaseModel):
    """Complete risk analysis output (MODL-05).

    Satisfies requirements: position_size, stop_loss, take_profit, risk_reward_ratio
    """

    symbol: str = Field(..., description="Trading symbol")
    current_price: Optional[float] = Field(None, description="Current market price")
    trade_direction: Literal["long", "short", "avoid"] = Field(
        ..., description="Trade direction"
    )
    entry_zone: EntryZone = Field(..., description="Entry zone specification")
    stop_loss: StopLoss = Field(..., description="Stop loss (MODL-05)")
    take_profits: TakeProfits = Field(..., description="Take profits (MODL-05)")
    risk_reward: RiskReward = Field(..., description="Risk/reward (MODL-05)")
    position_sizing: Optional[PositionSizing] = Field(
        None, description="Position sizing (MODL-05), populated when account_size provided"
    )
    funding_filter: Optional[FundingFilter] = Field(
        None, description="Funding rate analysis, populated when funding data available"
    )
    three_laws_check: ThreeLawsCheck = Field(..., description="3 Laws validation")
    final_verdict: FinalVerdict = Field(..., description="Final recommendation")
    approved: bool = Field(..., description="Whether trade passes all 3 Laws")
    rejection_reasons: list[str] = Field(
        default_factory=list, description="Reasons for rejection, empty if approved"
    )
    position_size_units: Optional[float] = Field(
        None, description="Position size in units of the asset, calculated when account_size provided"
    )
