"""Market data fetcher for price and OHLCV data.

.. deprecated::
    This module is deprecated. Use `src.backend.data.ohlcv_client` instead.
    This file is kept as a backup reference and will be removed in a future version.
"""
import warnings
warnings.warn(
    "market_data.py is deprecated. Use src.backend.data.ohlcv_client instead.",
    DeprecationWarning,
    stacklevel=2
)
import httpx
from typing import Optional
from datetime import datetime, timedelta


class MarketDataFetcher:
    """Fetches market data from various sources."""

    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
        # Crypto.com Exchange API base URL
        self.cryptocom_base = "https://api.crypto.com/exchange/v1"

    def fetch(self, symbol: str) -> dict:
        """Fetch all market data for a symbol."""
        # Normalize symbol format
        instrument = f"{symbol}_USDT" if not symbol.endswith("_USDT") else symbol

        data = {
            'symbol': symbol,
            'current_price': None,
            'ohlcv_weekly': [],
            'ohlcv_daily': [],
            'ohlcv_4h': [],
            'funding_rate': None,
            'volume_24h': None,
        }

        # Try to fetch current price
        try:
            ticker = self._get_ticker(instrument)
            if ticker:
                data['current_price'] = ticker.get('last_trade_price')
                data['volume_24h'] = ticker.get('total_volume')
        except Exception as e:
            print(f"Error fetching ticker for {symbol}: {e}")

        # Fetch candlestick data
        try:
            data['ohlcv_daily'] = self._get_candlesticks(instrument, 'D', 30)
            data['ohlcv_4h'] = self._get_candlesticks(instrument, '4H', 50)
            data['ohlcv_weekly'] = self._get_candlesticks(instrument, 'W', 20)
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")

        return data

    def _get_ticker(self, instrument: str) -> Optional[dict]:
        """Get current ticker data."""
        try:
            response = self.client.get(
                f"{self.cryptocom_base}/public/get-ticker",
                params={"instrument_name": instrument}
            )
            if response.status_code == 200:
                result = response.json().get('result', {})
                return result.get('data', [{}])[0] if result.get('data') else None
        except Exception:
            pass
        return None

    def _get_candlesticks(self, instrument: str, timeframe: str, count: int) -> list:
        """Get candlestick (OHLCV) data."""
        try:
            # Map timeframes to API format
            tf_map = {
                '4H': '4h',
                'D': '1D',
                'W': '1W'
            }
            tf = tf_map.get(timeframe, timeframe)

            response = self.client.get(
                f"{self.cryptocom_base}/public/get-candlestick",
                params={
                    "instrument_name": instrument,
                    "timeframe": tf,
                    "count": count
                }
            )
            if response.status_code == 200:
                result = response.json().get('result', {})
                data = result.get('data', [])
                # Convert to standard format
                candles = []
                for c in data:
                    candles.append({
                        'timestamp': c.get('t'),
                        'open': float(c.get('o', 0)),
                        'high': float(c.get('h', 0)),
                        'low': float(c.get('l', 0)),
                        'close': float(c.get('c', 0)),
                        'volume': float(c.get('v', 0))
                    })
                return candles
        except Exception as e:
            print(f"Error fetching candlesticks: {e}")
        return []

    def get_funding_rate(self, symbol: str) -> Optional[float]:
        """Get current funding rate for perpetual."""
        # This would need a derivatives exchange API
        # For MVP, return None and let agents handle
        return None

    def close(self):
        """Close the HTTP client."""
        self.client.close()


# Singleton instance
_fetcher = None


def get_market_data_fetcher() -> MarketDataFetcher:
    """Get singleton market data fetcher."""
    global _fetcher
    if _fetcher is None:
        _fetcher = MarketDataFetcher()
    return _fetcher
