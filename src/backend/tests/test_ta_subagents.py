"""Smoke tests for TA Ensemble subagents."""
import json
import pytest
from unittest.mock import patch

from src.backend.agents.ta_ensemble import WeeklySubagent, DailySubagent, FourHourSubagent
from src.backend.models.ta_signal import TASignal


class TestWeeklySubagent:
    """Smoke tests for WeeklySubagent."""

    def test_weekly_subagent_smoke(self, ta_signal_weekly_response):
        """Verify WeeklySubagent can instantiate and return valid TASignal."""
        agent = WeeklySubagent()

        with patch.object(agent, '_call_claude', return_value=json.dumps(ta_signal_weekly_response)):
            result = agent.analyze("BTC", {"current_price": 65000})

        # Verify result can be validated as TASignal
        signal = TASignal.model_validate(result)
        assert signal.symbol == "BTC"
        assert signal.timeframe == "weekly"
        assert 0 <= signal.overall.confidence <= 100


class TestDailySubagent:
    """Smoke tests for DailySubagent."""

    def test_daily_subagent_smoke(self):
        """Verify DailySubagent can instantiate and return valid TASignal."""
        response = {
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

        agent = DailySubagent()

        with patch.object(agent, '_call_claude', return_value=json.dumps(response)):
            result = agent.analyze("BTC", {"current_price": 65000})

        signal = TASignal.model_validate(result)
        assert signal.symbol == "BTC"
        assert signal.timeframe == "daily"


class TestFourHourSubagent:
    """Smoke tests for FourHourSubagent."""

    def test_fourhour_subagent_smoke(self):
        """Verify FourHourSubagent can instantiate and return valid TASignal."""
        response = {
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

        agent = FourHourSubagent()

        with patch.object(agent, '_call_claude', return_value=json.dumps(response)):
            result = agent.analyze("BTC", {"current_price": 65000})

        signal = TASignal.model_validate(result)
        assert signal.symbol == "BTC"
        assert signal.timeframe == "4h"
