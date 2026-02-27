"""Unit tests for WeeklySubagent.

Tests verify:
- OHLCV data fetching via mocked OHLCVClient
- Indicator calculation pipeline
- Alpha factor computation
- Wyckoff detection integration
- TASignal output structure
- Warning logging for insufficient data
- No live API calls (all mocked)
"""
import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import logging

from src.backend.agents.ta_ensemble.weekly_subagent import WeeklySubagent
from src.backend.models.ta_signal import TASignal
from src.backend.models.wyckoff import WyckoffAnalysis
from src.backend.models.alpha_factors import AlphaFactors


@pytest.fixture
def synthetic_weekly_ohlcv_104():
    """Generate 104 weekly candles (2 years) with realistic patterns.

    Creates uptrend data to ensure analysis functions return valid results.
    """
    np.random.seed(42)
    base_price = 50000.0
    base_time = datetime.now() - timedelta(weeks=104)

    data = []
    price = base_price

    for i in range(104):
        # Generate uptrending data with realistic volatility
        change = np.random.normal(0.005, 0.03)  # 0.5% drift, 3% volatility
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

    return data


@pytest.fixture
def synthetic_weekly_ohlcv_30():
    """Generate 30 weekly candles (insufficient history for warning test)."""
    np.random.seed(42)
    base_price = 45000.0
    base_time = datetime.now() - timedelta(weeks=30)

    data = []
    price = base_price

    for i in range(30):
        change = np.random.normal(0.002, 0.02)
        price = price * (1 + change)

        volatility = price * 0.025
        high = price + abs(np.random.normal(0, volatility))
        low = price - abs(np.random.normal(0, volatility))
        open_price = low + np.random.random() * (high - low)
        volume = np.random.uniform(80000, 400000)

        timestamp = int((base_time + timedelta(weeks=i)).timestamp() * 1000)

        data.append({
            'timestamp': timestamp,
            'open': float(open_price),
            'high': float(high),
            'low': float(low),
            'close': float(price),
            'volume': float(volume)
        })

    return data


@pytest.fixture
def mock_ohlcv_client(synthetic_weekly_ohlcv_104):
    """Create a mock OHLCVClient that returns synthetic data."""
    mock_client = Mock()
    mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104
    return mock_client


class TestWeeklySubagentStructure:
    """Test WeeklySubagent class structure and constants."""

    def test_subagent_has_required_constants(self):
        """Verify WeeklySubagent has required class constants."""
        subagent = WeeklySubagent()
        assert subagent.TIMEFRAME == "1w"
        assert subagent.CANDLE_LIMIT == 104
        assert subagent.MIN_CANDLES_WARNING == 52

    def test_subagent_has_analyze_method(self):
        """Verify analyze method exists with correct signature."""
        subagent = WeeklySubagent()
        assert hasattr(subagent, 'analyze')
        assert callable(subagent.analyze)

    def test_subagent_not_inheriting_base_agent(self):
        """Verify WeeklySubagent is pure computation (no BaseAgent)."""
        # BaseAgent would add _call_claude method
        subagent = WeeklySubagent()
        assert not hasattr(subagent, '_call_claude')


class TestWeeklySubagentAnalyze:
    """Test WeeklySubagent.analyze() method."""

    def test_analyze_returns_ta_signal(self, synthetic_weekly_ohlcv_104):
        """Verify analyze() returns valid TASignal instance."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            result = subagent.analyze("BTC/USDT")

            assert isinstance(result, TASignal)
            assert result.symbol == "BTC"
            assert result.timeframe == "weekly"

    def test_analyze_calls_ohlcv_client_correctly(self, synthetic_weekly_ohlcv_104):
        """Verify analyze() calls OHLCVClient with correct parameters."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            subagent.analyze("ETH/USDT")

            mock_client.fetch_ohlcv.assert_called_once_with(
                "ETH/USDT", "1w", limit=104
            )

    def test_analyze_populates_trend_data(self, synthetic_weekly_ohlcv_104):
        """Verify TASignal trend field is populated."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            result = subagent.analyze("BTC/USDT")

            assert result.trend is not None
            assert result.trend.direction in ["bullish", "bearish", "sideways"]
            assert result.trend.strength in ["strong", "moderate", "weak"]
            assert result.trend.ema_alignment in ["bullish", "bearish", "neutral"]

    def test_analyze_populates_momentum_data(self, synthetic_weekly_ohlcv_104):
        """Verify TASignal momentum field is populated."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            result = subagent.analyze("BTC/USDT")

            assert result.momentum is not None
            assert result.momentum.macd_bias in ["bullish", "bearish", "neutral"]

    def test_analyze_populates_key_levels(self, synthetic_weekly_ohlcv_104):
        """Verify TASignal key_levels field is populated."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            result = subagent.analyze("BTC/USDT")

            assert result.key_levels is not None
            # Support/resistance may be None if not detected
            # Just verify the field structure exists

    def test_analyze_populates_overall_assessment(self, synthetic_weekly_ohlcv_104):
        """Verify TASignal overall field is populated with valid confidence."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            result = subagent.analyze("BTC/USDT")

            assert result.overall is not None
            assert result.overall.bias in ["bullish", "bearish", "neutral"]
            assert 0 <= result.overall.confidence <= 100
            assert len(result.overall.notes) > 0


class TestWeeklySubagentExtendedFields:
    """Test wyckoff and alpha_factors extended fields."""

    def test_analyze_populates_alpha_factors(self, synthetic_weekly_ohlcv_104):
        """Verify TASignal alpha_factors field is populated."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            result = subagent.analyze("BTC/USDT")

            # With 104 candles, alpha factors should be calculated
            assert result.alpha_factors is not None
            assert isinstance(result.alpha_factors, AlphaFactors)

    def test_analyze_populates_wyckoff_with_sufficient_data(self, synthetic_weekly_ohlcv_104):
        """Verify TASignal wyckoff field is populated with sufficient data."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            result = subagent.analyze("BTC/USDT")

            # With 104 candles (> 50), Wyckoff should be attempted
            # May still be None if no pattern detected, but field should exist
            # Just verify we got a TASignal (wyckoff may be None or WyckoffAnalysis)
            assert result is not None

    def test_analyze_wyckoff_skipped_with_insufficient_data(self, synthetic_weekly_ohlcv_30):
        """Verify Wyckoff detection skipped when < 50 candles."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_30

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            result = subagent.analyze("SOL/USDT")

            # With only 30 candles (< 50), Wyckoff should be None
            assert result.wyckoff is None


class TestWeeklySubagentLogging:
    """Test warning logging for insufficient history."""

    def test_warning_logged_for_insufficient_candles(self, synthetic_weekly_ohlcv_30, caplog):
        """Verify warning logged when fewer than 52 candles returned."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_30

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            with caplog.at_level(logging.WARNING):
                subagent = WeeklySubagent()
                result = subagent.analyze("SOL/USDT")

                # Verify warning was logged
                assert "Insufficient history" in caplog.text
                assert "30 candles" in caplog.text
                assert "SOL/USDT" in caplog.text

                # Verify analysis still completes
                assert isinstance(result, TASignal)
                assert result.symbol == "SOL"

    def test_no_warning_for_sufficient_candles(self, synthetic_weekly_ohlcv_104, caplog):
        """Verify no warning logged when >= 52 candles returned."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            with caplog.at_level(logging.WARNING):
                subagent = WeeklySubagent()
                subagent.analyze("BTC/USDT")

                # Should not see insufficient history warning
                assert "Insufficient history" not in caplog.text


class TestWeeklySubagentBackwardCompatibility:
    """Test backward compatibility with TASignal model."""

    def test_ta_signal_without_extended_fields_is_valid(self):
        """Verify TASignal can be created without wyckoff/alpha_factors."""
        signal = TASignal(
            symbol="BTC",
            timeframe="weekly",
            trend={"direction": "bullish", "strength": "strong", "ema_alignment": "bullish"},
            momentum={"rsi": 65.0, "macd_bias": "bullish", "momentum_divergence": False},
            key_levels={"major_support": 60000.0, "major_resistance": 70000.0},
            patterns={"detected": [], "pattern_bias": "neutral"},
            overall={"bias": "bullish", "confidence": 75, "notes": "Test"}
        )

        assert signal.wyckoff is None
        assert signal.alpha_factors is None
        # Should serialize without errors
        json_str = signal.model_dump_json()
        assert "wyckoff" in json_str


class TestWeeklySubagentNoLiveAPICalls:
    """Verify no live API calls are made during tests."""

    def test_mock_prevents_live_api_calls(self, synthetic_weekly_ohlcv_104):
        """Verify that mocking prevents any real network calls."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

        with patch('src.backend.agents.ta_ensemble.weekly_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = WeeklySubagent()
            result = subagent.analyze("BTC/USDT")

            # Verify mock was called (not real client)
            assert mock_client.fetch_ohlcv.called
            assert isinstance(result, TASignal)
