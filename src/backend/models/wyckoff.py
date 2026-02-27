"""
Wyckoff Pydantic models for pattern detection output validation.

Models validate the output from Wyckoff phase detection functions in
src/backend/analysis/wyckoff.py. Used by subagents to ensure data
integrity when analyzing accumulation/distribution patterns.
"""

from typing import List, Literal
from pydantic import BaseModel, Field, field_validator


class WyckoffEvent(BaseModel):
    """Individual Wyckoff event within a phase."""
    candle_index: int = Field(..., ge=0, description="Index in DataFrame where event occurred")
    event_type: Literal["spring", "upthrust", "sos", "sow", "lps", "lpsy"] = Field(
        ...,
        description="Type of Wyckoff event detected"
    )
    price: float = Field(..., gt=0, description="Price at event")
    volume_ratio: float = Field(..., gt=0, description="Volume as multiple of baseline")
    description: str = Field(..., min_length=1, description="Human-readable event description")


class WyckoffAnalysis(BaseModel):
    """
    Wyckoff phase analysis output.

    Contains detected phase, confidence score, key events, and volume confirmation.
    Events are automatically sorted chronologically by candle_index.
    """
    phase: Literal[
        "accumulation_a",
        "accumulation_b",
        "accumulation_c",
        "accumulation_d",
        "accumulation_e",
        "distribution_a",
        "distribution_b",
        "distribution_c",
        "distribution_d",
        "distribution_e",
        "unknown"
    ] = Field(..., description="Detected Wyckoff phase")
    phase_confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score for phase detection (0-100)"
    )
    events: List[WyckoffEvent] = Field(
        default_factory=list,
        description="Chronologically ordered list of detected Wyckoff events"
    )
    volume_confirms: bool = Field(..., description="Whether volume confirms price action")
    analysis_notes: str = Field(default="", description="Additional analysis context")

    @field_validator('events')
    @classmethod
    def sort_events_chronologically(cls, v: List[WyckoffEvent]) -> List[WyckoffEvent]:
        """Sort events by candle_index to ensure chronological order."""
        return sorted(v, key=lambda e: e.candle_index)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "phase": "accumulation_c",
                    "phase_confidence": 75,
                    "events": [
                        {
                            "candle_index": 10,
                            "event_type": "spring",
                            "price": 98.5,
                            "volume_ratio": 0.7,
                            "description": "Spring below trading range on low volume"
                        },
                        {
                            "candle_index": 15,
                            "event_type": "lps",
                            "price": 99.8,
                            "volume_ratio": 1.2,
                            "description": "Last Point of Support retest successful"
                        }
                    ],
                    "volume_confirms": True,
                    "analysis_notes": "Strong accumulation pattern with volume confirmation"
                }
            ]
        }
    }
