"""Unit tests for technical indicator calculations."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backend.analysis import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_adx,
    calculate_obv,
    calculate_vwap,
    calculate_atr,
    detect_support_resistance,
)


@pytest.fixture
def synthetic_ohlcv():
    """Generate synthetic OHLCV data for indicator testing (100 candles)."""
    np.random.seed(42)
    base_price = 100.0
    timestamps = [int((datetime.now() - timedelta(days=100-i)).timestamp() * 1000) for i in range(100)]

    # Generate realistic price movement with trend and volatility
    prices = [base_price]
    for _ in range(99):
        change = np.random.normal(0.001, 0.02)  # 0.1% drift, 2% volatility
        prices.append(prices[-1] * (1 + change))

    data = []
    for i, timestamp in enumerate(timestamps):
        close = prices[i]
        volatility = close * 0.02
        high = close + abs(np.random.normal(0, volatility))
        low = close - abs(np.random.normal(0, volatility))
        open_price = low + np.random.random() * (high - low)
        volume = np.random.uniform(1000, 10000)

        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    return pd.DataFrame(data)


@pytest.fixture
def small_ohlcv():
    """Generate small OHLCV dataset (5 candles) - insufficient for most indicators."""
    timestamps = [int((datetime.now() - timedelta(days=5-i)).timestamp() * 1000) for i in range(5)]
    data = []
    for i, timestamp in enumerate(timestamps):
        close = 100.0 + i
        data.append({
            'timestamp': timestamp,
            'open': close - 0.5,
            'high': close + 1.0,
            'low': close - 1.0,
            'close': close,
            'volume': 1000.0
        })

    return pd.DataFrame(data)


class TestRSI:
    """Tests for calculate_rsi function."""

    def test_calculate_rsi_returns_valid_range(self, synthetic_ohlcv):
        """Verify RSI returns value in valid range (0-100)."""
        rsi = calculate_rsi(synthetic_ohlcv)

        assert rsi is not None
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    def test_calculate_rsi_insufficient_data_returns_none(self, small_ohlcv):
        """Verify RSI returns None for insufficient data."""
        rsi = calculate_rsi(small_ohlcv)

        assert rsi is None

    def test_calculate_rsi_custom_period(self, synthetic_ohlcv):
        """Verify RSI works with custom period."""
        rsi = calculate_rsi(synthetic_ohlcv, period=7)

        assert rsi is not None
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100


class TestMACD:
    """Tests for calculate_macd function."""

    def test_calculate_macd_returns_dict_with_keys(self, synthetic_ohlcv):
        """Verify MACD returns dict with correct keys."""
        macd = calculate_macd(synthetic_ohlcv)

        assert macd is not None
        assert isinstance(macd, dict)
        assert set(macd.keys()) == {'macd', 'signal', 'histogram'}
        assert all(isinstance(v, float) for v in macd.values())

    def test_calculate_macd_insufficient_data_returns_none(self, small_ohlcv):
        """Verify MACD returns None for insufficient data."""
        macd = calculate_macd(small_ohlcv)

        assert macd is None

    def test_calculate_macd_histogram_is_difference(self, synthetic_ohlcv):
        """Verify MACD histogram equals macd - signal."""
        macd = calculate_macd(synthetic_ohlcv)

        assert macd is not None
        # Histogram should be close to macd - signal (within floating point precision)
        expected_histogram = macd['macd'] - macd['signal']
        assert abs(macd['histogram'] - expected_histogram) < 1e-6


class TestBollingerBands:
    """Tests for calculate_bollinger_bands function."""

    def test_calculate_bollinger_bands_returns_dict_with_keys(self, synthetic_ohlcv):
        """Verify Bollinger Bands returns dict with correct keys."""
        bb = calculate_bollinger_bands(synthetic_ohlcv)

        assert bb is not None
        assert isinstance(bb, dict)
        assert set(bb.keys()) == {'upper', 'middle', 'lower'}
        assert all(isinstance(v, float) for v in bb.values())

    def test_calculate_bollinger_bands_upper_above_lower(self, synthetic_ohlcv):
        """Verify upper band is above lower band."""
        bb = calculate_bollinger_bands(synthetic_ohlcv)

        assert bb is not None
        assert bb['upper'] > bb['middle']
        assert bb['middle'] > bb['lower']

    def test_calculate_bollinger_bands_insufficient_data_returns_none(self, small_ohlcv):
        """Verify Bollinger Bands returns None for insufficient data."""
        bb = calculate_bollinger_bands(small_ohlcv)

        assert bb is None


class TestADX:
    """Tests for calculate_adx function."""

    def test_calculate_adx_returns_positive_value(self, synthetic_ohlcv):
        """Verify ADX returns non-negative value."""
        adx = calculate_adx(synthetic_ohlcv)

        assert adx is not None
        assert isinstance(adx, float)
        assert adx >= 0

    def test_calculate_adx_insufficient_data_returns_none(self, small_ohlcv):
        """Verify ADX returns None for insufficient data."""
        adx = calculate_adx(small_ohlcv)

        assert adx is None

    def test_calculate_adx_custom_period(self, synthetic_ohlcv):
        """Verify ADX works with custom period."""
        adx = calculate_adx(synthetic_ohlcv, period=7)

        assert adx is not None
        assert isinstance(adx, float)
        assert adx >= 0


class TestOBV:
    """Tests for calculate_obv function."""

    def test_calculate_obv_returns_numeric(self, synthetic_ohlcv):
        """Verify OBV returns numeric value."""
        obv = calculate_obv(synthetic_ohlcv)

        assert obv is not None
        assert isinstance(obv, float)

    def test_calculate_obv_minimal_data(self, small_ohlcv):
        """Verify OBV works with minimal data (1 candle requirement)."""
        obv = calculate_obv(small_ohlcv)

        assert obv is not None
        assert isinstance(obv, float)


class TestVWAP:
    """Tests for calculate_vwap function."""

    def test_calculate_vwap_returns_numeric(self, synthetic_ohlcv):
        """Verify VWAP returns numeric value."""
        vwap = calculate_vwap(synthetic_ohlcv)

        assert vwap is not None
        assert isinstance(vwap, float)

    def test_calculate_vwap_value_within_price_range(self, synthetic_ohlcv):
        """Verify VWAP is within reasonable range of prices."""
        vwap = calculate_vwap(synthetic_ohlcv)

        assert vwap is not None
        min_price = synthetic_ohlcv['low'].min()
        max_price = synthetic_ohlcv['high'].max()
        assert min_price <= vwap <= max_price

    def test_calculate_vwap_minimal_data(self, small_ohlcv):
        """Verify VWAP works with minimal data (1 candle requirement)."""
        vwap = calculate_vwap(small_ohlcv)

        assert vwap is not None
        assert isinstance(vwap, float)


class TestATR:
    """Tests for calculate_atr function."""

    def test_calculate_atr_returns_positive_value(self, synthetic_ohlcv):
        """Verify ATR returns positive value."""
        atr = calculate_atr(synthetic_ohlcv)

        assert atr is not None
        assert isinstance(atr, float)
        assert atr > 0

    def test_calculate_atr_insufficient_data_returns_none(self, small_ohlcv):
        """Verify ATR returns None for insufficient data."""
        atr = calculate_atr(small_ohlcv)

        assert atr is None

    def test_calculate_atr_custom_period(self, synthetic_ohlcv):
        """Verify ATR works with custom period."""
        atr = calculate_atr(synthetic_ohlcv, period=7)

        assert atr is not None
        assert isinstance(atr, float)
        assert atr > 0


class TestSupportResistance:
    """Tests for detect_support_resistance function."""

    def test_detect_support_resistance_returns_dict_with_keys(self, synthetic_ohlcv):
        """Verify support/resistance returns dict with correct keys."""
        sr = detect_support_resistance(synthetic_ohlcv)

        assert isinstance(sr, dict)
        assert set(sr.keys()) == {'support', 'resistance'}
        assert isinstance(sr['support'], list)
        assert isinstance(sr['resistance'], list)

    def test_detect_support_resistance_support_below_price(self, synthetic_ohlcv):
        """Verify all support levels are below current price."""
        sr = detect_support_resistance(synthetic_ohlcv)
        current_price = synthetic_ohlcv['close'].iloc[-1]

        for support_level in sr['support']:
            assert isinstance(support_level, float)
            assert support_level < current_price

    def test_detect_support_resistance_resistance_above_price(self, synthetic_ohlcv):
        """Verify all resistance levels are above current price."""
        sr = detect_support_resistance(synthetic_ohlcv)
        current_price = synthetic_ohlcv['close'].iloc[-1]

        for resistance_level in sr['resistance']:
            assert isinstance(resistance_level, float)
            assert resistance_level > current_price

    def test_detect_support_resistance_max_levels(self, synthetic_ohlcv):
        """Verify support/resistance returns at most num_levels."""
        sr = detect_support_resistance(synthetic_ohlcv, num_levels=3)

        assert len(sr['support']) <= 3
        assert len(sr['resistance']) <= 3

    def test_detect_support_resistance_insufficient_data_returns_empty(self, small_ohlcv):
        """Verify support/resistance returns empty lists for insufficient data."""
        sr = detect_support_resistance(small_ohlcv)

        assert sr == {'support': [], 'resistance': []}

    def test_detect_support_resistance_custom_parameters(self, synthetic_ohlcv):
        """Verify support/resistance works with custom parameters."""
        sr = detect_support_resistance(
            synthetic_ohlcv,
            num_levels=5,
            distance=10,
            prominence_pct=0.01
        )

        assert isinstance(sr, dict)
        assert set(sr.keys()) == {'support', 'resistance'}
        assert len(sr['support']) <= 5
        assert len(sr['resistance']) <= 5
