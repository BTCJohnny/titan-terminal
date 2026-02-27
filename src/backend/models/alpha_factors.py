"""
AlphaFactors Pydantic models for alpha factor validation.

Models validate the output from alpha factor calculation functions in
src/backend/analysis/alpha_factors.py. Used by subagents to ensure data
integrity when generating trading signals.
"""

from typing import Optional
from pydantic import BaseModel, Field


class MomentumData(BaseModel):
    """Momentum score data with short and long-term rate of change."""
    short_roc: float = Field(..., description="Short-term (10-period) rate of change percentage")
    long_roc: float = Field(..., description="Long-term (20-period) rate of change percentage")
    momentum_score: float = Field(
        ...,
        ge=-100,
        le=100,
        description="Combined normalized momentum score in -100/+100 range"
    )


class VolumeAnomalyData(BaseModel):
    """Volume anomaly detection data."""
    current_volume: float = Field(..., gt=0, description="Current candle volume")
    avg_volume: float = Field(..., gt=0, description="Rolling average volume (20-period)")
    volume_ratio: float = Field(..., gt=0, description="Ratio of current to average volume")
    is_anomaly: bool = Field(..., description="True if volume exceeds 2x threshold")


class MADeviationData(BaseModel):
    """Moving average deviation data."""
    deviation_20: float = Field(..., description="Percentage deviation from 20 EMA")
    deviation_50: float = Field(..., description="Percentage deviation from 50 EMA")
    deviation_200: float = Field(..., description="Percentage deviation from 200 EMA")


class VolatilityData(BaseModel):
    """Volatility score data based on ATR."""
    atr: float = Field(..., gt=0, description="Raw Average True Range value")
    atr_percent: float = Field(..., gt=0, description="ATR as percentage of current price")
    volatility_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Normalized volatility score in 0-100 range (5% ATR = 100)"
    )


class AlphaFactors(BaseModel):
    """
    Alpha factors container model.

    Aggregates all alpha factor outputs for a given symbol/timeframe.
    All fields are optional to handle insufficient data scenarios.
    """
    momentum: Optional[MomentumData] = Field(
        None,
        description="Momentum score combining short and long-term ROC"
    )
    volume_anomaly: Optional[VolumeAnomalyData] = Field(
        None,
        description="Volume anomaly detection relative to moving average"
    )
    ma_deviation: Optional[MADeviationData] = Field(
        None,
        description="Percentage deviations from key exponential moving averages"
    )
    volatility: Optional[VolatilityData] = Field(
        None,
        description="Volatility score based on Average True Range"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "momentum": {
                        "short_roc": 5.2,
                        "long_roc": 3.8,
                        "momentum_score": 45.6
                    },
                    "volume_anomaly": {
                        "current_volume": 1500000.0,
                        "avg_volume": 800000.0,
                        "volume_ratio": 1.875,
                        "is_anomaly": False
                    },
                    "ma_deviation": {
                        "deviation_20": 2.5,
                        "deviation_50": 5.1,
                        "deviation_200": 8.3
                    },
                    "volatility": {
                        "atr": 150.5,
                        "atr_percent": 2.3,
                        "volatility_score": 46.0
                    }
                }
            ]
        }
    }
