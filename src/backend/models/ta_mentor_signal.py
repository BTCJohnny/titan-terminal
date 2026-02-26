"""
TAMentorSignal Pydantic model for multi-timeframe synthesis output.

Represents the structured output from the TA Mentor agent that synthesizes
weekly, daily, and 4-hour signals into a unified trading recommendation.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class TimeframeAlignment(BaseModel):
    """Alignment assessment across three timeframes."""
    weekly_bias: Literal["bullish", "bearish", "neutral"]
    daily_bias: Literal["bullish", "bearish", "neutral"]
    fourhour_bias: Literal["bullish", "bearish", "neutral"]
    alignment_score: int = Field(..., ge=0, le=100, description="Alignment score 0-100")
    confluence: Literal["perfect", "strong", "moderate", "weak", "conflicting"]


class ConflictDetail(BaseModel):
    """Details about detected conflicts between timeframes."""
    type: Literal["trend", "momentum", "pattern"]
    description: str = Field(..., description="Description of the conflict")
    severity: Literal["high", "medium", "low"]


class ConfidenceAdjustment(BaseModel):
    """Confidence calculation breakdown."""
    base_confidence: int = Field(..., description="Base confidence before adjustments")
    confluence_bonus: int = Field(..., description="Bonus for timeframe alignment")
    conflict_penalty: int = Field(..., description="Penalty for conflicts")
    final_confidence: int = Field(..., ge=0, le=100, description="Final confidence 0-100")
    reasoning: str = Field(..., description="Explanation of confidence calculation")


class UnifiedSignalLevels(BaseModel):
    """Key price levels for the unified signal."""
    support: Optional[float] = Field(None, description="Key support level")
    resistance: Optional[float] = Field(None, description="Key resistance level")
    invalidation: Optional[float] = Field(None, description="Signal invalidation level")


class UnifiedSignal(BaseModel):
    """Unified trading signal combining all timeframes."""
    bias: Literal["bullish", "bearish", "neutral"]
    strength: Literal["strong", "moderate", "weak"]
    confidence: int = Field(..., ge=0, le=100, description="Overall confidence 0-100")
    recommended_action: Literal["long", "short", "wait"]
    entry_timing: Literal["immediate", "wait_for_pullback", "wait_for_confirmation"]
    key_levels: UnifiedSignalLevels


class TAMentorSignal(BaseModel):
    """
    TA Mentor signal synthesizing multi-timeframe technical analysis.

    Combines weekly, daily, and 4-hour signals into a unified recommendation
    with conflict detection and confidence adjustments.
    """
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC')")
    timeframe_alignment: TimeframeAlignment
    conflicts_detected: list[ConflictDetail] = Field(
        default_factory=list, description="Detected conflicts between timeframes"
    )
    confidence_adjustment: ConfidenceAdjustment
    unified_signal: UnifiedSignal
    synthesis_notes: str = Field(..., description="Overall synthesis explanation")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTC",
                    "timeframe_alignment": {
                        "weekly_bias": "bullish",
                        "daily_bias": "bullish",
                        "fourhour_bias": "neutral",
                        "alignment_score": 80,
                        "confluence": "strong"
                    },
                    "conflicts_detected": [
                        {
                            "type": "momentum",
                            "description": "4h timeframe showing momentum divergence while higher timeframes remain strong",
                            "severity": "low"
                        }
                    ],
                    "confidence_adjustment": {
                        "base_confidence": 70,
                        "confluence_bonus": 10,
                        "conflict_penalty": 5,
                        "final_confidence": 75,
                        "reasoning": "Strong alignment on higher timeframes with minor 4h divergence"
                    },
                    "unified_signal": {
                        "bias": "bullish",
                        "strength": "strong",
                        "confidence": 75,
                        "recommended_action": "long",
                        "entry_timing": "wait_for_pullback",
                        "key_levels": {
                            "support": 60000.0,
                            "resistance": 70000.0,
                            "invalidation": 58000.0
                        }
                    },
                    "synthesis_notes": "Weekly and daily timeframes aligned bullish with strong momentum. 4h showing consolidation but not concerning given higher timeframe strength. Wait for pullback to support for optimal entry."
                }
            ]
        }
    }
