"""Unit tests for Wyckoff pattern detection."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backend.analysis.wyckoff import detect_wyckoff
from src.backend.models.wyckoff import WyckoffEvent, WyckoffAnalysis


@pytest.fixture
def synthetic_ohlcv_100():
    """Generate 100 candles of realistic OHLCV data."""
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
    """Generate 50 candles (insufficient for Wyckoff analysis, < 100)."""
    timestamps = [int((datetime.now() - timedelta(days=50-i)).timestamp() * 1000) for i in range(50)]
    data = []
    for i, timestamp in enumerate(timestamps):
        close = 100.0 + i * 0.5
        data.append({
            'timestamp': timestamp,
            'open': close - 0.5,
            'high': close + 1.0,
            'low': close - 1.0,
            'close': close,
            'volume': 1000.0
        })

    return pd.DataFrame(data)


def create_ohlcv_row(timestamp: int, base_price: float, volatility: float, volume: float) -> dict:
    """Helper to create a single OHLCV row."""
    close = base_price
    high = close + abs(np.random.normal(0, volatility))
    low = close - abs(np.random.normal(0, volatility))
    open_price = low + np.random.random() * (high - low)

    return {
        'timestamp': timestamp,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }


@pytest.fixture
def accumulation_pattern():
    """
    Generate 120 candles simulating accumulation structure.

    Candles 0-20: Downtrend (prices declining from 120 to 100)
    Candles 21-40: Selling climax (high volume spike, sharp drop to 95)
    Candles 41-80: Range-bound between 95-105 with declining volume (Phase B)
    Candles 81-90: Spring pattern: price dips to 93, recovers to 98 within 3 candles, low volume
    Candles 91-100: SOS: price breaks above 105 with high volume
    Candles 101-120: Markup: price trends upward to 115
    """
    np.random.seed(123)
    base_timestamp = int(datetime.now().timestamp() * 1000)
    data = []

    # Candles 0-20: Downtrend from 120 to 100
    for i in range(21):
        timestamp = base_timestamp + i * 3600000  # 1 hour intervals
        price = 120 - (i / 20) * 20  # Linear decline to 100
        volatility = 0.5
        volume = np.random.uniform(1000, 3000)
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 21-40: Selling climax with high volume spike
    for i in range(20):
        timestamp = base_timestamp + (21 + i) * 3600000
        price = 100 - (i / 20) * 5  # Drop to 95
        volatility = 1.0
        # High volume spike in first few candles
        volume = np.random.uniform(8000, 15000) if i < 5 else np.random.uniform(2000, 5000)
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 41-80: Range-bound 95-105 with declining volume (Phase B)
    for i in range(40):
        timestamp = base_timestamp + (41 + i) * 3600000
        # Oscillate between 95-105
        price = 95 + 10 * np.sin(i / 5) + 5
        volatility = 0.5
        # Declining volume
        volume = np.random.uniform(1000, 3000) * (1 - i / 80)
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 81-90: Spring pattern - dip to 93, recover to 98 within 3 candles, low volume
    spring_prices = [93, 94, 95, 98, 98, 97, 98, 99, 99, 100]
    for i in range(10):
        timestamp = base_timestamp + (81 + i) * 3600000
        price = spring_prices[i]
        volatility = 0.3
        volume = np.random.uniform(500, 1200)  # Low volume
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 91-100: SOS - break above 105 with high volume
    for i in range(10):
        timestamp = base_timestamp + (91 + i) * 3600000
        price = 100 + i * 0.8  # Rise to ~108
        volatility = 0.8
        volume = np.random.uniform(8000, 12000)  # High volume
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 101-120: Markup to 115
    for i in range(20):
        timestamp = base_timestamp + (101 + i) * 3600000
        price = 108 + (i / 20) * 7  # Rise to 115
        volatility = 0.5
        volume = np.random.uniform(3000, 6000)
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    return pd.DataFrame(data)


@pytest.fixture
def distribution_pattern():
    """
    Generate 120 candles simulating distribution structure.

    Candles 0-20: Uptrend (prices rising from 80 to 100)
    Candles 21-40: Buying climax (high volume spike, sharp rise to 105)
    Candles 41-80: Range-bound 95-105 with declining volume (Phase B)
    Candles 81-90: Upthrust: price spikes to 107, fails back to 102 within 3 candles, low volume
    Candles 91-100: SOW: price breaks below 95 with high volume
    Candles 101-120: Markdown: price trends downward to 85
    """
    np.random.seed(456)
    base_timestamp = int(datetime.now().timestamp() * 1000)
    data = []

    # Candles 0-20: Uptrend from 80 to 100
    for i in range(21):
        timestamp = base_timestamp + i * 3600000
        price = 80 + (i / 20) * 20  # Linear rise to 100
        volatility = 0.5
        volume = np.random.uniform(1000, 3000)
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 21-40: Buying climax with high volume spike
    for i in range(20):
        timestamp = base_timestamp + (21 + i) * 3600000
        price = 100 + (i / 20) * 5  # Rise to 105
        volatility = 1.0
        # High volume spike in first few candles
        volume = np.random.uniform(8000, 15000) if i < 5 else np.random.uniform(2000, 5000)
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 41-80: Range-bound 95-105 with declining volume (Phase B)
    for i in range(40):
        timestamp = base_timestamp + (41 + i) * 3600000
        # Oscillate between 95-105
        price = 95 + 10 * np.sin(i / 5) + 5
        volatility = 0.5
        # Declining volume
        volume = np.random.uniform(1000, 3000) * (1 - i / 80)
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 81-90: Upthrust - spike to 107, fail back to 102 within 3 candles, low volume
    upthrust_prices = [107, 106, 104, 102, 102, 103, 102, 101, 101, 100]
    for i in range(10):
        timestamp = base_timestamp + (81 + i) * 3600000
        price = upthrust_prices[i]
        volatility = 0.3
        volume = np.random.uniform(500, 1200)  # Low volume
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 91-100: SOW - break below 95 with high volume
    for i in range(10):
        timestamp = base_timestamp + (91 + i) * 3600000
        price = 100 - i * 0.8  # Drop to ~92
        volatility = 0.8
        volume = np.random.uniform(8000, 12000)  # High volume
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    # Candles 101-120: Markdown to 85
    for i in range(20):
        timestamp = base_timestamp + (101 + i) * 3600000
        price = 92 - (i / 20) * 7  # Drop to 85
        volatility = 0.5
        volume = np.random.uniform(3000, 6000)
        data.append(create_ohlcv_row(timestamp, price, volatility, volume))

    return pd.DataFrame(data)
