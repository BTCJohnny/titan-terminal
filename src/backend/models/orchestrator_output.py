"""
Pydantic models for Orchestrator output.

OrchestratorOutput: Final combined signal with recommendation
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field



class KeyLevels(BaseModel):
    """Key price levels."""

    support: Optional[float] = Field(None, description="Support level")
    resistance: Optional[float] = Field(None, description="Resistance level")
    invalidation: Optional[float] = Field(None, description="Invalidation level")


class EntryZoneSimple(BaseModel):
    """Simplified entry zone for orchestrator output."""

    low: Optional[float] = Field(None, description="Lower bound")
    high: Optional[float] = Field(None, description="Upper bound")
    ideal: Optional[float] = Field(None, description="Ideal entry")


class ThreeLawsCheckSimple(BaseModel):
    """Simplified 3 Laws check."""

    law_1_risk: Literal["pass", "fail"] = Field(..., description="Law 1: Max 2% risk")
    law_2_rr: Literal["pass", "fail"] = Field(..., description="Law 2: Min 2:1 RR")
    law_3_positions: Literal["pass", "check_current_positions"] = Field(
        ..., description="Law 3: Max 3 positions"
    )
    overall: Literal["approved", "rejected", "caution"] = Field(
        ..., description="Overall verdict"
    )


class MentorAssessment(BaseModel):
    """Mentor's assessment of the signal."""

    verdict: Optional[str] = Field(None, description="Mentor verdict")
    concerns: list[str] = Field(
        default_factory=list, description="List of concerns"
    )
    notes: Optional[str] = Field(None, description="Additional notes")


class OrchestratorOutput(BaseModel):
    """Final orchestrator output (MODL-06).

    Combines all agent signals into a final recommendation.
    Satisfies requirements: combined signals, final recommendation
    """

    # Identity
    symbol: str = Field(..., description="Trading symbol")
    signal_id: Optional[int] = Field(None, description="Signal ID from journal")
    timestamp: datetime = Field(..., description="Signal timestamp")

    # Combined signals (MODL-06 requirement)
    accumulation_score: int = Field(
        ..., ge=0, le=100, description="Accumulation score"
    )
    distribution_score: int = Field(
        ..., ge=0, le=100, description="Distribution score"
    )
    confidence: int = Field(..., ge=0, le=100, description="Overall confidence")

    # Source summaries (combined from all agents)
    wyckoff_phase: Optional[str] = Field(None, description="Wyckoff phase")
    wyckoff_summary: Optional[str] = Field(None, description="Wyckoff summary")
    nansen_summary: list[str] = Field(
        default_factory=list, description="Nansen insights"
    )
    ta_summary: Optional[str] = Field(None, description="TA summary")
    telegram_signals: list[dict] = Field(
        default_factory=list, description="Raw telegram signals"
    )

    # Final recommendation (MODL-06 requirement)
    suggested_action: Literal[
        "Long Spot", "Long Hyperliquid", "Short Hyperliquid", "Avoid"
    ] = Field(..., description="Final action recommendation")

    # Trade execution details
    entry_zone: Optional[EntryZoneSimple] = Field(None, description="Entry zone")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    tp1: Optional[float] = Field(None, description="First take profit")
    tp2: Optional[float] = Field(None, description="Second take profit")
    risk_reward: Optional[float] = Field(None, description="Risk/reward ratio")
    key_levels: Optional[KeyLevels] = Field(None, description="Key price levels")
    three_laws_check: Optional[ThreeLawsCheckSimple] = Field(
        None, description="3 Laws validation"
    )

    # Self-learning context
    learning_context: Optional[str] = Field(
        None, description="Learning context for journal"
    )

    # Mentor critique
    mentor: Optional[MentorAssessment] = Field(None, description="Mentor assessment")

    # Mentor synthesis fields
    direction: Optional[Literal["BULLISH", "BEARISH", "NO SIGNAL"]] = Field(
        None, description="Directional bias from Mentor synthesis"
    )
    # Full Mentor reasoning text — stored in journal for future dashboard display
    reasoning: Optional[str] = Field(None, description="Full Mentor reasoning text from synthesis call")

    @property
    def is_actionable(self) -> bool:
        """Check if signal is actionable (not Avoid)."""
        return self.suggested_action != "Avoid"
