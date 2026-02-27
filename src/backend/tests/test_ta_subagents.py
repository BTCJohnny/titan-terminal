"""Smoke tests for TA Ensemble subagents."""
import json
import pytest
from unittest.mock import patch

from src.backend.agents.ta_ensemble import WeeklySubagent, DailySubagent, FourHourSubagent
from src.backend.models.ta_signal import TASignal


class TestWeeklySubagent:
    """Smoke tests for WeeklySubagent."""

    def test_weekly_subagent_smoke(self):
        """Verify WeeklySubagent can instantiate and return valid TASignal."""
        from unittest.mock import Mock
        import numpy as np
        from datetime import datetime, timedelta

        # Create synthetic OHLCV data for smoke test
        np.random.seed(42)
        base_price = 50000.0
        base_time = datetime.now() - timedelta(weeks=104)
        data = []
        price = base_price

        for i in range(104):
            change = np.random.normal(0.005, 0.03)
            price = price * (1 + change)
            volatility = price * 0.03
            high = price + abs(np.random.normal(0, volatility))
            low = price - abs(np.random.normal(0, volatility))
            open_price = low + np.random.random() * (high - low)
            volume = np.random.uniform(100000, 500000)
            timestamp = int((base_time + timedelta(weeks=i)).timestamp() * 1000)

            data.append({
                'timestamp': timestamp,
                'open': float(open_price),
                'high': float(high),
                'low': float(low),
                'close': float(price),
                'volume': float(volume)
            })

        # Mock OHLCVClient to return synthetic data
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = data

        agent = WeeklySubagent()

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client', return_value=mock_client):
            result = agent.analyze("BTC/USDT")

        # Verify result is TASignal
        assert isinstance(result, TASignal)
        assert result.symbol == "BTC"
        assert result.timeframe == "weekly"
        assert 0 <= result.overall.confidence <= 100


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
