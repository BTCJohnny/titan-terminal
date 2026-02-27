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
