"""
TASignal Pydantic model for timeframe-specific technical analysis output.

Represents the structured output from weekly, daily, and 4-hour TA subagents.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

from src.backend.models.wyckoff import WyckoffAnalysis
from src.backend.models.alpha_factors import AlphaFactors


class TrendData(BaseModel):
    """Trend analysis data."""
    direction: Literal["bullish", "bearish", "sideways", "neutral"]
    strength: Literal["strong", "moderate", "weak"]
    ema_alignment: Literal["bullish", "bearish", "neutral"]


class MomentumData(BaseModel):
    """Momentum indicators data."""
    rsi: Optional[float] = Field(None, description="RSI value for the timeframe")
    macd_bias: Literal["bullish", "bearish", "neutral"]
    momentum_divergence: bool = Field(
        default=False, description="Whether momentum divergence is detected"
    )


class KeyLevels(BaseModel):
    """Key support and resistance levels."""
    major_support: Optional[float] = Field(None, description="Major support level")
    major_resistance: Optional[float] = Field(None, description="Major resistance level")


class PatternData(BaseModel):
    """Pattern detection data."""
    detected: list[str] = Field(default_factory=list, description="List of detected patterns")
    pattern_bias: Literal["bullish", "bearish", "neutral"]


class OverallAssessment(BaseModel):
    """Overall assessment for the timeframe."""
    bias: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    notes: str = Field(..., description="Analysis notes")


class TASignal(BaseModel):
    """
    Technical Analysis signal for a specific timeframe.

    Output structure for weekly, daily, and 4-hour TA subagents.
    """
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC')")
    timeframe: Literal["weekly", "daily", "4h"] = Field(
        ..., description="Timeframe for this analysis"
    )
    trend: TrendData
    momentum: MomentumData
    key_levels: KeyLevels
    patterns: PatternData
    overall: OverallAssessment

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTC",
                    "timeframe": "weekly",
                    "trend": {
                        "direction": "bullish",
                        "strength": "strong",
                        "ema_alignment": "bullish"
                    },
                    "momentum": {
                        "rsi": 65.0,
                        "macd_bias": "bullish",
                        "momentum_divergence": False
                    },
                    "key_levels": {
                        "major_support": 60000.0,
                        "major_resistance": 70000.0
                    },
                    "patterns": {
                        "detected": ["ascending_triangle"],
                        "pattern_bias": "bullish"
                    },
                    "overall": {
                        "bias": "bullish",
                        "confidence": 75,
                        "notes": "Strong weekly uptrend with bullish EMA alignment"
                    }
                }
            ]
        }
    }

    @field_validator("overall")
    @classmethod
    def validate_confidence(cls, v: OverallAssessment) -> OverallAssessment:
        """Ensure confidence is within 0-100 range."""
        if not 0 <= v.confidence <= 100:
            raise ValueError(f"Confidence must be between 0 and 100, got {v.confidence}")
        return v
