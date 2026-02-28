"""Pytest fixtures for agent smoke tests."""
import pytest
from unittest.mock import MagicMock, patch

from src.backend.models.ta_signal import (
    TASignal, TrendData, MomentumData, KeyLevels, PatternData, OverallAssessment
)


@pytest.fixture
def ta_signal_weekly_response():
    """Valid TASignal JSON response for weekly timeframe."""
    return {
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
            "notes": "Strong weekly uptrend"
        }
    }


@pytest.fixture
def ta_signal_daily_response():
    """Valid TASignal JSON response for daily timeframe."""
    return {
        "symbol": "BTC",
        "timeframe": "daily",
        "trend": {
            "direction": "bullish",
            "strength": "moderate",
            "ema_alignment": "bullish"
        },
        "momentum": {
            "rsi": 55.0,
            "macd_bias": "neutral",
            "momentum_divergence": False
        },
        "key_levels": {
            "major_support": 62000.0,
            "major_resistance": 68000.0
        },
        "patterns": {
            "detected": [],
            "pattern_bias": "neutral"
        },
        "overall": {
            "bias": "bullish",
            "confidence": 65,
            "notes": "Daily uptrend continuation"
        }
    }


@pytest.fixture
def ta_signal_fourhour_response():
    """Valid TASignal JSON response for 4h timeframe."""
    return {
        "symbol": "BTC",
        "timeframe": "4h",
        "trend": {
            "direction": "sideways",
            "strength": "weak",
            "ema_alignment": "neutral"
        },
        "momentum": {
            "rsi": 50.0,
            "macd_bias": "neutral",
            "momentum_divergence": False
        },
        "key_levels": {
            "major_support": 63000.0,
            "major_resistance": 66000.0
        },
        "patterns": {
            "detected": ["consolidation"],
            "pattern_bias": "neutral"
        },
        "overall": {
            "bias": "neutral",
            "confidence": 50,
            "notes": "4H consolidation phase"
        }
    }


@pytest.fixture
def ta_mentor_response():
    """Valid TAMentorSignal JSON response."""
    return {
        "symbol": "BTC",
        "timeframe_alignment": {
            "weekly_bias": "bullish",
            "daily_bias": "bullish",
            "fourhour_bias": "neutral",
            "alignment_score": 80,
            "confluence": "strong"
        },
        "conflicts_detected": [],
        "confidence_adjustment": {
            "base_confidence": 70,
            "confluence_bonus": 10,
            "conflict_penalty": 0,
            "final_confidence": 80,
            "reasoning": "Strong alignment across higher timeframes"
        },
        "unified_signal": {
            "bias": "bullish",
            "strength": "strong",
            "confidence": 80,
            "recommended_action": "long",
            "entry_timing": "wait_for_pullback",
            "key_levels": {
                "support": 60000.0,
                "resistance": 70000.0,
                "invalidation": 58000.0
            }
        },
        "synthesis_notes": "Multi-timeframe analysis shows bullish confluence"
    }


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    with patch('src.backend.agents.telegram_agent.get_connection') as mock:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock.return_value = mock_conn
        yield mock


# TASignal fixtures for conflict scenarios


@pytest.fixture
def weekly_bearish_signal():
    """Weekly TASignal with bearish bias."""
    return TASignal(
        symbol="BTC",
        timeframe="weekly",
        trend=TrendData(direction="bearish", strength="strong", ema_alignment="bearish"),
        momentum=MomentumData(rsi=35.0, macd_bias="bearish", momentum_divergence=False),
        key_levels=KeyLevels(major_support=60000.0, major_resistance=70000.0),
        patterns=PatternData(detected=[], pattern_bias="bearish"),
        overall=OverallAssessment(bias="bearish", confidence=75, notes="Weekly downtrend")
    )


@pytest.fixture
def daily_bearish_signal():
    """Daily TASignal with bearish bias."""
    return TASignal(
        symbol="BTC",
        timeframe="daily",
        trend=TrendData(direction="bearish", strength="moderate", ema_alignment="bearish"),
        momentum=MomentumData(rsi=40.0, macd_bias="bearish", momentum_divergence=False),
        key_levels=KeyLevels(major_support=62000.0, major_resistance=68000.0),
        patterns=PatternData(detected=[], pattern_bias="bearish"),
        overall=OverallAssessment(bias="bearish", confidence=70, notes="Daily downtrend")
    )


@pytest.fixture
def four_hour_bullish_signal():
    """4H TASignal with bullish bias (counter-trend)."""
    return TASignal(
        symbol="BTC",
        timeframe="4h",
        trend=TrendData(direction="bullish", strength="weak", ema_alignment="bullish"),
        momentum=MomentumData(rsi=55.0, macd_bias="bullish", momentum_divergence=False),
        key_levels=KeyLevels(major_support=63000.0, major_resistance=66000.0),
        patterns=PatternData(detected=[], pattern_bias="bullish"),
        overall=OverallAssessment(bias="bullish", confidence=55, notes="4H bounce")
    )


@pytest.fixture
def weekly_bullish_signal():
    """Weekly TASignal with bullish bias."""
    return TASignal(
        symbol="BTC",
        timeframe="weekly",
        trend=TrendData(direction="bullish", strength="strong", ema_alignment="bullish"),
        momentum=MomentumData(rsi=65.0, macd_bias="bullish", momentum_divergence=False),
        key_levels=KeyLevels(major_support=60000.0, major_resistance=70000.0),
        patterns=PatternData(detected=[], pattern_bias="bullish"),
        overall=OverallAssessment(bias="bullish", confidence=75, notes="Weekly uptrend")
    )


@pytest.fixture
def daily_bullish_signal():
    """Daily TASignal with bullish bias."""
    return TASignal(
        symbol="BTC",
        timeframe="daily",
        trend=TrendData(direction="bullish", strength="moderate", ema_alignment="bullish"),
        momentum=MomentumData(rsi=60.0, macd_bias="bullish", momentum_divergence=False),
        key_levels=KeyLevels(major_support=62000.0, major_resistance=68000.0),
        patterns=PatternData(detected=[], pattern_bias="bullish"),
        overall=OverallAssessment(bias="bullish", confidence=70, notes="Daily uptrend")
    )


@pytest.fixture
def four_hour_bearish_signal():
    """4H TASignal with bearish bias (pullback)."""
    return TASignal(
        symbol="BTC",
        timeframe="4h",
        trend=TrendData(direction="bearish", strength="weak", ema_alignment="bearish"),
        momentum=MomentumData(rsi=45.0, macd_bias="bearish", momentum_divergence=False),
        key_levels=KeyLevels(major_support=63000.0, major_resistance=66000.0),
        patterns=PatternData(detected=[], pattern_bias="bearish"),
        overall=OverallAssessment(bias="bearish", confidence=55, notes="4H pullback")
    )


@pytest.fixture
def four_hour_neutral_signal():
    """4H TASignal with neutral bias."""
    return TASignal(
        symbol="BTC",
        timeframe="4h",
        trend=TrendData(direction="sideways", strength="weak", ema_alignment="neutral"),
        momentum=MomentumData(rsi=50.0, macd_bias="neutral", momentum_divergence=False),
        key_levels=KeyLevels(major_support=63000.0, major_resistance=66000.0),
        patterns=PatternData(detected=[], pattern_bias="neutral"),
        overall=OverallAssessment(bias="neutral", confidence=50, notes="4H consolidation")
    )
