"""OHLCV data client using CCXT with Binance exchange.

This module provides a production-ready client for fetching OHLCV (candlestick) data
from Binance via the CCXT library. It includes automatic retry logic with exponential
backoff for handling rate limits.
"""
import time
import random
from typing import Optional
from functools import wraps
import ccxt


# Supported trading pairs
SUPPORTED_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

# Supported timeframes
SUPPORTED_TIMEFRAMES = ["1w", "1d", "4h"]


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, factor: float = 2.0, jitter_ms: int = 500):
    """Decorator that retries a function with exponential backoff on rate limit errors.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        factor: Exponential backoff factor (default: 2.0)
        jitter_ms: Random jitter in milliseconds to add to delay (default: 500)

    Raises:
        The last exception encountered if all retries fail
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (ccxt.RateLimitExceeded, ccxt.RequestTimeout) as e:
                    last_exception = e

                    if attempt == max_retries:
                        # Final attempt failed, raise the exception
                        raise

                    # Calculate delay with jitter
                    jitter = random.uniform(0, jitter_ms / 1000.0)
                    sleep_time = delay + jitter

                    print(f"Rate limit or timeout hit (attempt {attempt + 1}/{max_retries + 1}). "
                          f"Retrying in {sleep_time:.2f}s...")

                    time.sleep(sleep_time)
                    delay *= factor

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class OHLCVClient:
    """Client for fetching OHLCV data from Binance via CCXT.

    This client uses Binance's public API which does not require authentication
    for OHLCV data. It includes automatic retry logic with exponential backoff
    to handle rate limiting gracefully.

    Example:
        >>> client = OHLCVClient()
        >>> candles = client.fetch_ohlcv("BTC/USDT", "1d", limit=30)
        >>> print(f"Fetched {len(candles)} daily candles")
    """

    SUPPORTED_SYMBOLS = SUPPORTED_SYMBOLS
    SUPPORTED_TIMEFRAMES = SUPPORTED_TIMEFRAMES

    def __init__(self):
        """Initialize the OHLCV client with Binance exchange.

        The exchange is configured for public API access only (no API key required).
        """
        self.exchange = ccxt.binance({
            'enableRateLimit': True,  # Built-in rate limiting
            'options': {
                'defaultType': 'spot',  # Use spot market
            }
        })

    @retry_with_backoff(max_retries=3, base_delay=1.0, factor=2.0, jitter_ms=500)
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> list[dict]:
        """Fetch OHLCV candlestick data for a symbol and timeframe.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            timeframe: Candlestick timeframe (e.g., "1d", "4h", "1w")
            limit: Number of candles to fetch (default: 100)

        Returns:
            List of candlestick dictionaries with keys:
                - timestamp: Unix timestamp in milliseconds
                - open: Opening price
                - high: Highest price
                - low: Lowest price
                - close: Closing price
                - volume: Trading volume

        Raises:
            ValueError: If symbol or timeframe is not supported
            ccxt.RateLimitExceeded: If rate limit is hit after all retries
            ccxt.RequestTimeout: If request times out after all retries

        Example:
            >>> client = OHLCVClient()
            >>> candles = client.fetch_ohlcv("ETH/USDT", "4h", limit=50)
        """
        # Validate inputs
        if symbol not in self.SUPPORTED_SYMBOLS:
            raise ValueError(
                f"Symbol '{symbol}' not supported. "
                f"Supported symbols: {', '.join(self.SUPPORTED_SYMBOLS)}"
            )

        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            raise ValueError(
                f"Timeframe '{timeframe}' not supported. "
                f"Supported timeframes: {', '.join(self.SUPPORTED_TIMEFRAMES)}"
            )

        # Fetch data from exchange
        ohlcv_data = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

        # Convert from CCXT array format to dictionary format
        candles = []
        for candle in ohlcv_data:
            candles.append({
                'timestamp': candle[0],
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5])
            })

        return candles

    def fetch_all_timeframes(self, symbol: str, limit: int = 100) -> dict[str, list[dict]]:
        """Fetch OHLCV data for all supported timeframes for a given symbol.

        This is a convenience method that fetches data for all three supported
        timeframes (1w, 1d, 4h) in sequence.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            limit: Number of candles to fetch per timeframe (default: 100)

        Returns:
            Dictionary mapping timeframe to list of candle dictionaries:
                {
                    "1w": [...],
                    "1d": [...],
                    "4h": [...]
                }

        Raises:
            ValueError: If symbol is not supported
            ccxt.RateLimitExceeded: If rate limit is hit after all retries

        Example:
            >>> client = OHLCVClient()
            >>> data = client.fetch_all_timeframes("SOL/USDT", limit=50)
            >>> print(f"Weekly candles: {len(data['1w'])}")
        """
        if symbol not in self.SUPPORTED_SYMBOLS:
            raise ValueError(
                f"Symbol '{symbol}' not supported. "
                f"Supported symbols: {', '.join(self.SUPPORTED_SYMBOLS)}"
            )

        result = {}
        for timeframe in self.SUPPORTED_TIMEFRAMES:
            result[timeframe] = self.fetch_ohlcv(symbol, timeframe, limit=limit)

        return result


# Singleton instance
_client: Optional[OHLCVClient] = None


def get_ohlcv_client() -> OHLCVClient:
    """Get singleton OHLCV client instance.

    This function implements the singleton pattern to ensure only one
    OHLCVClient instance is created and reused across the application.

    Returns:
        The singleton OHLCVClient instance

    Example:
        >>> client = get_ohlcv_client()
        >>> candles = client.fetch_ohlcv("BTC/USDT", "1d")
    """
    global _client
    if _client is None:
        _client = OHLCVClient()
    return _client
