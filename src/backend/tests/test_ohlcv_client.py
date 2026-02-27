"""Unit tests for OHLCV data client."""
import pytest
from unittest.mock import patch, MagicMock
import ccxt

from src.backend.data.ohlcv_client import OHLCVClient, get_ohlcv_client


@pytest.fixture
def mock_ohlcv_response():
    """Mock CCXT OHLCV response format: [[timestamp, o, h, l, c, v], ...]"""
    return [
        [1704067200000, 42000.0, 42500.0, 41800.0, 42300.0, 1000.0],
        [1704153600000, 42300.0, 42800.0, 42100.0, 42600.0, 1100.0],
        [1704240000000, 42600.0, 43000.0, 42400.0, 42800.0, 1050.0],
        [1704326400000, 42800.0, 43200.0, 42700.0, 43000.0, 1200.0],
        [1704412800000, 43000.0, 43500.0, 42900.0, 43200.0, 1150.0],
    ]


@pytest.fixture
def client():
    """Create a fresh OHLCVClient instance for each test."""
    return OHLCVClient()


class TestOHLCVClient:
    """Unit tests for OHLCVClient with mocked exchange calls."""

    # Data structure tests (TEST-01)

    def test_fetch_ohlcv_returns_correct_structure(self, client, mock_ohlcv_response):
        """Verify fetch_ohlcv returns dicts with all 6 required keys."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response):
            result = client.fetch_ohlcv("BTC/USDT", "1d")

        assert len(result) == 5
        for candle in result:
            assert isinstance(candle, dict)
            assert set(candle.keys()) == {'timestamp', 'open', 'high', 'low', 'close', 'volume'}

    def test_fetch_ohlcv_converts_to_float(self, client, mock_ohlcv_response):
        """Verify open/high/low/close/volume are converted to float."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response):
            result = client.fetch_ohlcv("BTC/USDT", "1d")

        candle = result[0]
        assert isinstance(candle['open'], float)
        assert isinstance(candle['high'], float)
        assert isinstance(candle['low'], float)
        assert isinstance(candle['close'], float)
        assert isinstance(candle['volume'], float)

    def test_fetch_ohlcv_timestamp_preserved(self, client, mock_ohlcv_response):
        """Verify timestamp is preserved as int (milliseconds)."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response):
            result = client.fetch_ohlcv("BTC/USDT", "1d")

        candle = result[0]
        assert isinstance(candle['timestamp'], int)
        assert candle['timestamp'] == 1704067200000

    # Symbol coverage tests

    def test_fetch_ohlcv_btc_usdt(self, client, mock_ohlcv_response):
        """Verify BTC/USDT symbol works."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response) as mock_fetch:
            result = client.fetch_ohlcv("BTC/USDT", "1d")

        mock_fetch.assert_called_once_with("BTC/USDT", "1d", limit=100)
        assert len(result) == 5

    def test_fetch_ohlcv_eth_usdt(self, client, mock_ohlcv_response):
        """Verify ETH/USDT symbol works."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response) as mock_fetch:
            result = client.fetch_ohlcv("ETH/USDT", "1d")

        mock_fetch.assert_called_once_with("ETH/USDT", "1d", limit=100)
        assert len(result) == 5

    def test_fetch_ohlcv_sol_usdt(self, client, mock_ohlcv_response):
        """Verify SOL/USDT symbol works."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response) as mock_fetch:
            result = client.fetch_ohlcv("SOL/USDT", "1d")

        mock_fetch.assert_called_once_with("SOL/USDT", "1d", limit=100)
        assert len(result) == 5

    # Timeframe coverage tests

    def test_fetch_ohlcv_1w_timeframe(self, client, mock_ohlcv_response):
        """Verify 1w timeframe works."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response) as mock_fetch:
            result = client.fetch_ohlcv("BTC/USDT", "1w")

        mock_fetch.assert_called_once_with("BTC/USDT", "1w", limit=100)
        assert len(result) == 5

    def test_fetch_ohlcv_1d_timeframe(self, client, mock_ohlcv_response):
        """Verify 1d timeframe works."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response) as mock_fetch:
            result = client.fetch_ohlcv("BTC/USDT", "1d")

        mock_fetch.assert_called_once_with("BTC/USDT", "1d", limit=100)
        assert len(result) == 5

    def test_fetch_ohlcv_4h_timeframe(self, client, mock_ohlcv_response):
        """Verify 4h timeframe works."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response) as mock_fetch:
            result = client.fetch_ohlcv("BTC/USDT", "4h")

        mock_fetch.assert_called_once_with("BTC/USDT", "4h", limit=100)
        assert len(result) == 5

    # Input validation tests

    def test_fetch_ohlcv_invalid_symbol_raises_valueerror(self, client):
        """Verify invalid symbol raises ValueError."""
        with pytest.raises(ValueError, match="Symbol 'DOGE/USDT' not supported"):
            client.fetch_ohlcv("DOGE/USDT", "1d")

    def test_fetch_ohlcv_invalid_timeframe_raises_valueerror(self, client):
        """Verify invalid timeframe raises ValueError."""
        with pytest.raises(ValueError, match="Timeframe '1m' not supported"):
            client.fetch_ohlcv("BTC/USDT", "1m")

    # fetch_all_timeframes tests

    def test_fetch_all_timeframes_returns_all_three(self, client, mock_ohlcv_response):
        """Verify fetch_all_timeframes returns data for all 3 timeframes."""
        with patch.object(client.exchange, 'fetch_ohlcv', return_value=mock_ohlcv_response):
            result = client.fetch_all_timeframes("BTC/USDT")

        assert set(result.keys()) == {"1w", "1d", "4h"}
        for timeframe, candles in result.items():
            assert len(candles) == 5
            assert all(isinstance(c, dict) for c in candles)

    def test_fetch_all_timeframes_invalid_symbol_raises_valueerror(self, client):
        """Verify fetch_all_timeframes raises ValueError for invalid symbol."""
        with pytest.raises(ValueError, match="Symbol 'DOGE/USDT' not supported"):
            client.fetch_all_timeframes("DOGE/USDT")

    # Retry behavior tests (TEST-02)

    def test_retry_on_rate_limit_exceeded(self, client, mock_ohlcv_response):
        """Verify retry happens on ccxt.RateLimitExceeded."""
        with patch.object(client.exchange, 'fetch_ohlcv') as mock_fetch:
            # First call raises RateLimitExceeded, second succeeds
            mock_fetch.side_effect = [
                ccxt.RateLimitExceeded('rate limit'),
                mock_ohlcv_response
            ]

            with patch('time.sleep', return_value=None):
                result = client.fetch_ohlcv("BTC/USDT", "1d")

        # Verify retry occurred (called twice)
        assert mock_fetch.call_count == 2
        assert len(result) == 5

    def test_retry_on_request_timeout(self, client, mock_ohlcv_response):
        """Verify retry happens on ccxt.RequestTimeout."""
        with patch.object(client.exchange, 'fetch_ohlcv') as mock_fetch:
            # First call times out, second succeeds
            mock_fetch.side_effect = [
                ccxt.RequestTimeout('timeout'),
                mock_ohlcv_response
            ]

            with patch('time.sleep', return_value=None):
                result = client.fetch_ohlcv("BTC/USDT", "1d")

        # Verify retry occurred (called twice)
        assert mock_fetch.call_count == 2
        assert len(result) == 5

    def test_retry_max_attempts_then_raises(self, client):
        """Verify exception raised after max retries."""
        with patch.object(client.exchange, 'fetch_ohlcv') as mock_fetch:
            # All attempts fail with rate limit
            mock_fetch.side_effect = ccxt.RateLimitExceeded('rate limit')

            with patch('time.sleep', return_value=None):
                with pytest.raises(ccxt.RateLimitExceeded):
                    client.fetch_ohlcv("BTC/USDT", "1d")

        # Verify it tried max_retries + 1 times (3 retries + 1 initial = 4 total)
        assert mock_fetch.call_count == 4

    def test_retry_succeeds_on_second_attempt(self, client, mock_ohlcv_response):
        """Verify success after one failure."""
        with patch.object(client.exchange, 'fetch_ohlcv') as mock_fetch:
            # First call fails, second succeeds
            mock_fetch.side_effect = [
                ccxt.RequestTimeout('timeout'),
                mock_ohlcv_response
            ]

            with patch('time.sleep', return_value=None):
                result = client.fetch_ohlcv("BTC/USDT", "1d")

        # Verify exactly 2 attempts
        assert mock_fetch.call_count == 2
        # Verify data returned correctly
        assert len(result) == 5
        assert result[0]['close'] == 42300.0
