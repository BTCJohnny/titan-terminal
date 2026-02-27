"""
Technical indicator calculation functions using pandas-ta.

All functions accept pd.DataFrame with OHLCV columns (lowercase: timestamp, open, high, low, close, volume)
and return scalar values or dicts. Functions return None if insufficient data is available.
"""
import pandas as pd
import pandas_ta as ta
from typing import Optional


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index (RSI).

    Args:
        df: DataFrame with 'close' column
        period: RSI period (default 14)

    Returns:
        RSI value (0-100) or None if insufficient data

    Minimum data: period + 1 candles (15 for default period=14)
    """
    if df is None or len(df) < period + 1:
        return None

    try:
        rsi_series = ta.rsi(df['close'], length=period)
        if rsi_series is None or rsi_series.dropna().empty:
            return None
        return float(rsi_series.dropna().iloc[-1])
    except (KeyError, IndexError, ValueError, AttributeError):
        return None


def calculate_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Optional[dict]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        df: DataFrame with 'close' column
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line period (default 9)

    Returns:
        Dict with keys: 'macd', 'signal', 'histogram' or None if insufficient data

    Minimum data: slow + signal candles (35 for defaults)
    """
    if df is None or len(df) < slow + signal:
        return None

    try:
        macd_df = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        if macd_df is None or macd_df.dropna().empty:
            return None

        last_row = macd_df.dropna().iloc[-1]
        return {
            'macd': float(last_row[f'MACD_{fast}_{slow}_{signal}']),
            'signal': float(last_row[f'MACDs_{fast}_{slow}_{signal}']),
            'histogram': float(last_row[f'MACDh_{fast}_{slow}_{signal}'])
        }
    except (KeyError, IndexError, ValueError, AttributeError):
        return None


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std: float = 2.0
) -> Optional[dict]:
    """
    Calculate Bollinger Bands.

    Args:
        df: DataFrame with 'close' column
        period: Moving average period (default 20)
        std: Number of standard deviations (default 2.0)

    Returns:
        Dict with keys: 'upper', 'middle', 'lower' or None if insufficient data

    Minimum data: period candles (20 for default)
    """
    if df is None or len(df) < period:
        return None

    try:
        bb_df = ta.bbands(df['close'], length=period, std=std)
        if bb_df is None or bb_df.dropna().empty:
            return None

        last_row = bb_df.dropna().iloc[-1]
        # pandas-ta names columns as BBL_<length>_<std>_<std> (std appears twice)
        return {
            'upper': float(last_row[f'BBU_{period}_{std}_{std}']),
            'middle': float(last_row[f'BBM_{period}_{std}_{std}']),
            'lower': float(last_row[f'BBL_{period}_{std}_{std}'])
        }
    except (KeyError, IndexError, ValueError, AttributeError):
        return None


def calculate_adx(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    """
    Calculate Average Directional Index (ADX).

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ADX period (default 14)

    Returns:
        ADX value (>= 0) or None if insufficient data

    Minimum data: period + 1 candles (15 for default period=14)
    """
    if df is None or len(df) < period + 1:
        return None

    try:
        adx_series = ta.adx(df['high'], df['low'], df['close'], length=period)
        if adx_series is None or adx_series.empty:
            return None

        # pandas-ta returns a DataFrame with ADX_<period>, DMP_<period>, DMN_<period>
        adx_col = f'ADX_{period}'
        if adx_col not in adx_series.columns:
            return None

        adx_values = adx_series[adx_col].dropna()
        if adx_values.empty:
            return None

        return float(adx_values.iloc[-1])
    except (KeyError, IndexError, ValueError, AttributeError):
        return None


def calculate_obv(df: pd.DataFrame) -> Optional[float]:
    """
    Calculate On-Balance Volume (OBV).

    Args:
        df: DataFrame with 'close' and 'volume' columns

    Returns:
        OBV value or None if insufficient data

    Minimum data: 1 candle
    """
    if df is None or len(df) < 1:
        return None

    try:
        obv_series = ta.obv(df['close'], df['volume'])
        if obv_series is None or obv_series.dropna().empty:
            return None
        return float(obv_series.dropna().iloc[-1])
    except (KeyError, IndexError, ValueError, AttributeError):
        return None


def calculate_vwap(df: pd.DataFrame) -> Optional[float]:
    """
    Calculate Volume Weighted Average Price (VWAP).

    Args:
        df: DataFrame with 'timestamp', 'high', 'low', 'close', 'volume' columns

    Returns:
        VWAP value or None if insufficient data

    Minimum data: 1 candle
    Note: Converts timestamp column to DatetimeIndex for calculation
    """
    if df is None or len(df) < 1:
        return None

    try:
        # Create a copy to avoid modifying original
        df_copy = df.copy()

        # Convert timestamp to DatetimeIndex if needed
        if 'timestamp' in df_copy.columns:
            df_copy.index = pd.to_datetime(df_copy['timestamp'])

        vwap_series = ta.vwap(df_copy['high'], df_copy['low'], df_copy['close'], df_copy['volume'])
        if vwap_series is None or vwap_series.dropna().empty:
            return None
        return float(vwap_series.dropna().iloc[-1])
    except (KeyError, IndexError, ValueError, AttributeError):
        return None


def calculate_atr(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    """
    Calculate Average True Range (ATR).

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default 14)

    Returns:
        ATR value (> 0) or None if insufficient data

    Minimum data: period + 1 candles (15 for default period=14)
    """
    if df is None or len(df) < period + 1:
        return None

    try:
        atr_series = ta.atr(df['high'], df['low'], df['close'], length=period)
        if atr_series is None or atr_series.dropna().empty:
            return None
        return float(atr_series.dropna().iloc[-1])
    except (KeyError, IndexError, ValueError, AttributeError):
        return None
