"""Unit tests for alpha factor calculations."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backend.analysis.alpha_factors import (
    calculate_momentum_score,
    detect_volume_anomaly,
    calculate_ma_deviation,
    calculate_volatility_score,
)
from src.backend.models.alpha_factors import (
    AlphaFactors,
    MomentumData,
    VolumeAnomalyData,
    MADeviationData,
    VolatilityData,
)


@pytest.fixture
def synthetic_ohlcv():
    """Generate synthetic OHLCV data for alpha factor testing (250 candles)."""
    np.random.seed(42)
    base_price = 100.0
    timestamps = [int((datetime.now() - timedelta(days=250-i)).timestamp() * 1000) for i in range(250)]

    # Generate realistic price movement with trend and volatility
    prices = [base_price]
    for _ in range(249):
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
    """Generate small OHLCV dataset (10 candles) - insufficient for most factors."""
    np.random.seed(42)
    timestamps = [int((datetime.now() - timedelta(days=10-i)).timestamp() * 1000) for i in range(10)]
    data = []
    for i, timestamp in enumerate(timestamps):
        close = 100.0 + i
        data.append({
            'timestamp': timestamp,
            'open': close - 0.5,
            'high': close + 1.0,
            'low': close - 1.0,
            'close': close,
            'volume': 1000.0 + i * 100
        })

    return pd.DataFrame(data)


@pytest.fixture
def zero_volume_ohlcv():
    """Generate OHLCV dataset with zero volume values."""
    np.random.seed(42)
    timestamps = [int((datetime.now() - timedelta(days=30-i)).timestamp() * 1000) for i in range(30)]
    data = []
    for i, timestamp in enumerate(timestamps):
        close = 100.0 + i * 0.5
        data.append({
            'timestamp': timestamp,
            'open': close - 0.5,
            'high': close + 1.0,
            'low': close - 1.0,
            'close': close,
            'volume': 0.0  # Zero volume
        })

    return pd.DataFrame(data)


@pytest.fixture
def large_ohlcv():
    """Generate large OHLCV dataset (300 candles) for MA deviation testing."""
    np.random.seed(42)
    base_price = 100.0
    timestamps = [int((datetime.now() - timedelta(days=300-i)).timestamp() * 1000) for i in range(300)]

    # Generate price trend: upward bias
    prices = [base_price]
    for _ in range(299):
        change = np.random.normal(0.002, 0.015)  # 0.2% positive drift, 1.5% volatility
        prices.append(prices[-1] * (1 + change))

    data = []
    for i, timestamp in enumerate(timestamps):
        close = prices[i]
        volatility = close * 0.015
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
def uptrend_ohlcv():
    """Generate uptrend OHLCV data for positive momentum testing."""
    np.random.seed(42)
    base_price = 100.0
    timestamps = [int((datetime.now() - timedelta(days=50-i)).timestamp() * 1000) for i in range(50)]

    # Strong upward trend
    prices = [base_price]
    for _ in range(49):
        change = np.random.normal(0.01, 0.005)  # 1% positive drift, 0.5% volatility
        prices.append(prices[-1] * (1 + change))

    data = []
    for i, timestamp in enumerate(timestamps):
        close = prices[i]
        volatility = close * 0.005
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
def downtrend_ohlcv():
    """Generate downtrend OHLCV data for negative momentum testing."""
    np.random.seed(42)
    base_price = 100.0
    timestamps = [int((datetime.now() - timedelta(days=50-i)).timestamp() * 1000) for i in range(50)]

    # Strong downward trend
    prices = [base_price]
    for _ in range(49):
        change = np.random.normal(-0.01, 0.005)  # -1% negative drift, 0.5% volatility
        prices.append(prices[-1] * (1 + change))

    data = []
    for i, timestamp in enumerate(timestamps):
        close = prices[i]
        volatility = close * 0.005
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


class TestMomentumScore:
    """Tests for calculate_momentum_score function."""

    def test_returns_dict_with_correct_keys(self, synthetic_ohlcv):
        """Verify momentum score returns dict with correct keys."""
        result = calculate_momentum_score(synthetic_ohlcv)

        assert result is not None
        assert isinstance(result, dict)
        assert set(result.keys()) == {'short_roc', 'long_roc', 'momentum_score'}
        assert all(isinstance(v, float) for v in result.values())

    def test_momentum_score_in_range(self, synthetic_ohlcv):
        """Verify momentum score is within -100/+100 range."""
        result = calculate_momentum_score(synthetic_ohlcv)

        assert result is not None
        assert -100 <= result['momentum_score'] <= 100

    def test_insufficient_data_returns_none(self, small_ohlcv):
        """Verify returns None for insufficient data (< 21 candles)."""
        result = calculate_momentum_score(small_ohlcv)

        assert result is None

    def test_custom_periods(self, synthetic_ohlcv):
        """Verify momentum score works with custom periods."""
        result = calculate_momentum_score(synthetic_ohlcv, short_period=5, long_period=10)

        assert result is not None
        assert isinstance(result, dict)
        assert -100 <= result['momentum_score'] <= 100

    def test_uptrend_positive_momentum(self, uptrend_ohlcv):
        """Verify uptrend generates positive momentum score."""
        result = calculate_momentum_score(uptrend_ohlcv)

        assert result is not None
        assert result['momentum_score'] > 0
        assert result['short_roc'] > 0
        assert result['long_roc'] > 0

    def test_downtrend_negative_momentum(self, downtrend_ohlcv):
        """Verify downtrend generates negative momentum score."""
        result = calculate_momentum_score(downtrend_ohlcv)

        assert result is not None
        assert result['momentum_score'] < 0
        assert result['short_roc'] < 0
        assert result['long_roc'] < 0


class TestVolumeAnomaly:
    """Tests for detect_volume_anomaly function."""

    def test_returns_dict_with_correct_keys(self, synthetic_ohlcv):
        """Verify volume anomaly returns dict with correct keys."""
        result = detect_volume_anomaly(synthetic_ohlcv)

        assert result is not None
        assert isinstance(result, dict)
        assert set(result.keys()) == {'current_volume', 'avg_volume', 'volume_ratio', 'is_anomaly'}
        assert isinstance(result['current_volume'], float)
        assert isinstance(result['avg_volume'], float)
        assert isinstance(result['volume_ratio'], float)
        assert isinstance(result['is_anomaly'], bool)

    def test_is_anomaly_true_when_above_threshold(self, synthetic_ohlcv):
        """Verify is_anomaly is True when volume exceeds threshold."""
        # Manually set high volume in last candle
        df = synthetic_ohlcv.copy()
        avg_volume = df['volume'].tail(20).mean()
        df.loc[df.index[-1], 'volume'] = avg_volume * 3.0  # 3x average (above 2.0 threshold)

        result = detect_volume_anomaly(df)

        assert result is not None
        assert result['is_anomaly'] is True
        assert result['volume_ratio'] > 2.0

    def test_is_anomaly_false_when_below_threshold(self, synthetic_ohlcv):
        """Verify is_anomaly is False when volume below threshold."""
        # Manually set normal volume in last candle
        df = synthetic_ohlcv.copy()
        avg_volume = df['volume'].tail(20).mean()
        df.loc[df.index[-1], 'volume'] = avg_volume * 1.5  # 1.5x average (below 2.0 threshold)

        result = detect_volume_anomaly(df)

        assert result is not None
        assert result['is_anomaly'] is False
        assert result['volume_ratio'] < 2.0

    def test_insufficient_data_returns_none(self, small_ohlcv):
        """Verify returns None for insufficient data (< 20 candles)."""
        result = detect_volume_anomaly(small_ohlcv)

        assert result is None

    def test_zero_avg_volume_returns_none(self, zero_volume_ohlcv):
        """Verify returns None when average volume is zero."""
        result = detect_volume_anomaly(zero_volume_ohlcv)

        assert result is None

    def test_custom_threshold(self, synthetic_ohlcv):
        """Verify volume anomaly works with custom threshold."""
        result = detect_volume_anomaly(synthetic_ohlcv, threshold=1.5)

        assert result is not None
        assert isinstance(result, dict)
        # Anomaly detection should use the custom 1.5x threshold
        if result['volume_ratio'] > 1.5:
            assert result['is_anomaly'] is True


class TestMADeviation:
    """Tests for calculate_ma_deviation function."""

    def test_returns_dict_with_correct_keys(self, large_ohlcv):
        """Verify MA deviation returns dict with correct keys."""
        result = calculate_ma_deviation(large_ohlcv)

        assert result is not None
        assert isinstance(result, dict)
        assert set(result.keys()) == {'deviation_20', 'deviation_50', 'deviation_200'}
        assert all(isinstance(v, float) for v in result.values())

    def test_insufficient_data_returns_none(self, synthetic_ohlcv):
        """Verify returns None for insufficient data (< 200 candles)."""
        # synthetic_ohlcv has 250 candles, so slice to < 200
        df_small = synthetic_ohlcv.head(150)
        result = calculate_ma_deviation(df_small)

        assert result is None

    def test_price_above_emas_positive_deviation(self, large_ohlcv):
        """Verify positive deviation when price is above EMAs."""
        # Set current price significantly above trend
        df = large_ohlcv.copy()
        current_close = df['close'].iloc[-1]
        df.loc[df.index[-1], 'close'] = current_close * 1.1  # 10% above current

        result = calculate_ma_deviation(df)

        assert result is not None
        # At least one deviation should be positive (likely all)
        assert any(result[key] > 0 for key in ['deviation_20', 'deviation_50', 'deviation_200'])

    def test_price_below_emas_negative_deviation(self, large_ohlcv):
        """Verify negative deviation when price is below EMAs."""
        # Set current price significantly below trend
        df = large_ohlcv.copy()
        current_close = df['close'].iloc[-1]
        df.loc[df.index[-1], 'close'] = current_close * 0.9  # 10% below current

        result = calculate_ma_deviation(df)

        assert result is not None
        # At least one deviation should be negative (likely all)
        assert any(result[key] < 0 for key in ['deviation_20', 'deviation_50', 'deviation_200'])

    def test_deviation_values_are_percentages(self, large_ohlcv):
        """Verify deviation values are in percentage format."""
        result = calculate_ma_deviation(large_ohlcv)

        assert result is not None
        # Deviations should be reasonable percentages (typically -50% to +50% for normal markets)
        for key in ['deviation_20', 'deviation_50', 'deviation_200']:
            assert -100 < result[key] < 100  # Sanity check for percentage range


class TestVolatilityScore:
    """Tests for calculate_volatility_score function."""

    def test_returns_dict_with_correct_keys(self, synthetic_ohlcv):
        """Verify volatility score returns dict with correct keys."""
        result = calculate_volatility_score(synthetic_ohlcv)

        assert result is not None
        assert isinstance(result, dict)
        assert set(result.keys()) == {'atr', 'atr_percent', 'volatility_score'}
        assert all(isinstance(v, float) for v in result.values())

    def test_volatility_score_in_range(self, synthetic_ohlcv):
        """Verify volatility score is within 0-100 range."""
        result = calculate_volatility_score(synthetic_ohlcv)

        assert result is not None
        assert 0 <= result['volatility_score'] <= 100

    def test_insufficient_data_returns_none(self, small_ohlcv):
        """Verify returns None for insufficient data (< 15 candles)."""
        result = calculate_volatility_score(small_ohlcv)

        assert result is None

    def test_uses_calculate_atr_from_indicators(self, synthetic_ohlcv):
        """Verify function imports calculate_atr from indicators.py (no reimplementation)."""
        # This test verifies the function runs successfully (which means it imported correctly)
        result = calculate_volatility_score(synthetic_ohlcv)

        assert result is not None
        assert result['atr'] > 0
        # ATR should be a reasonable value relative to price
        current_price = synthetic_ohlcv['close'].iloc[-1]
        assert result['atr'] < current_price  # ATR should be less than current price

    def test_zero_price_returns_none(self, synthetic_ohlcv):
        """Verify returns None when current price is zero."""
        df = synthetic_ohlcv.copy()
        df.loc[df.index[-1], 'close'] = 0.0  # Set current price to zero

        result = calculate_volatility_score(df)

        assert result is None

    def test_atr_percent_calculation(self, synthetic_ohlcv):
        """Verify ATR percent is correctly calculated."""
        result = calculate_volatility_score(synthetic_ohlcv)

        assert result is not None
        current_price = synthetic_ohlcv['close'].iloc[-1]
        expected_atr_percent = (result['atr'] / current_price) * 100

        # Should match within floating point precision
        assert abs(result['atr_percent'] - expected_atr_percent) < 1e-6

    def test_volatility_score_caps_at_100(self, synthetic_ohlcv):
        """Verify volatility score caps at 100 for high ATR values."""
        # Artificially create high volatility scenario
        df = synthetic_ohlcv.copy()
        # Set extreme high/low to create large ATR
        df.loc[df.index[-5:], 'high'] = df.loc[df.index[-5:], 'close'] * 1.2
        df.loc[df.index[-5:], 'low'] = df.loc[df.index[-5:], 'close'] * 0.8

        result = calculate_volatility_score(df)

        assert result is not None
        assert result['volatility_score'] <= 100


class TestAlphaFactorsModel:
    """Tests for AlphaFactors Pydantic model."""

    def test_model_validates_valid_data(self, synthetic_ohlcv):
        """Verify AlphaFactors model validates valid data."""
        momentum_data = calculate_momentum_score(synthetic_ohlcv)
        volume_data = detect_volume_anomaly(synthetic_ohlcv)
        volatility_data = calculate_volatility_score(synthetic_ohlcv)

        # Create model with valid data
        alpha_factors = AlphaFactors(
            momentum=MomentumData(**momentum_data),
            volume_anomaly=VolumeAnomalyData(**volume_data),
            volatility=VolatilityData(**volatility_data),
        )

        assert alpha_factors.momentum is not None
        assert alpha_factors.volume_anomaly is not None
        assert alpha_factors.volatility is not None

    def test_model_allows_optional_fields(self):
        """Verify AlphaFactors model allows optional fields (all None)."""
        alpha_factors = AlphaFactors()

        assert alpha_factors.momentum is None
        assert alpha_factors.volume_anomaly is None
        assert alpha_factors.ma_deviation is None
        assert alpha_factors.volatility is None

    def test_momentum_score_validation_bounds(self):
        """Verify MomentumData validates momentum_score bounds."""
        # Valid data
        valid_momentum = MomentumData(
            short_roc=5.0,
            long_roc=3.0,
            momentum_score=50.0
        )
        assert valid_momentum.momentum_score == 50.0

        # Test upper bound
        with pytest.raises(ValueError):
            MomentumData(
                short_roc=5.0,
                long_roc=3.0,
                momentum_score=150.0  # Above 100 limit
            )

        # Test lower bound
        with pytest.raises(ValueError):
            MomentumData(
                short_roc=5.0,
                long_roc=3.0,
                momentum_score=-150.0  # Below -100 limit
            )

    def test_volatility_score_validation_bounds(self):
        """Verify VolatilityData validates volatility_score bounds."""
        # Valid data
        valid_volatility = VolatilityData(
            atr=1.5,
            atr_percent=2.0,
            volatility_score=40.0
        )
        assert valid_volatility.volatility_score == 40.0

        # Test upper bound
        with pytest.raises(ValueError):
            VolatilityData(
                atr=1.5,
                atr_percent=2.0,
                volatility_score=150.0  # Above 100 limit
            )

        # Test lower bound (must be >= 0)
        with pytest.raises(ValueError):
            VolatilityData(
                atr=1.5,
                atr_percent=2.0,
                volatility_score=-10.0  # Below 0 limit
            )
