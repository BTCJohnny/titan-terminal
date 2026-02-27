"""
Alpha factor calculation functions for quantitative market analysis.

All functions accept pd.DataFrame with OHLCV columns (lowercase: timestamp, open, high, low, close, volume)
and return dict or None. Functions return None if insufficient data is available.

These factors are used by subagents to generate trading signals based on:
- Momentum (rate of change analysis)
- Volume anomalies (unusual volume activity)
- Moving average deviations (price distance from trend)
- Volatility (normalized ATR-based scoring)
"""
import pandas as pd
import numpy as np
from typing import Optional

from src.backend.analysis.indicators import calculate_atr


def calculate_momentum_score(
    df: pd.DataFrame,
    short_period: int = 10,
    long_period: int = 20
) -> Optional[dict]:
    """
    Calculate momentum score combining short and long-term rate of change.

    Computes ROC for two periods and combines them with weighted average,
    then normalizes to -100/+100 range using hyperbolic tangent.

    Args:
        df: DataFrame with 'close' column
        short_period: Short ROC period (default 10)
        long_period: Long ROC period (default 20)

    Returns:
        Dict with keys:
        - 'short_roc': Short-term ROC percentage
        - 'long_roc': Long-term ROC percentage
        - 'momentum_score': Combined normalized score in -100/+100 range
        Returns None if insufficient data

    Minimum data: long_period + 1 candles (21 for defaults)
    """
    if df is None or len(df) < long_period + 1:
        return None

    try:
        close = df['close'].values

        # Calculate ROC: ((close[-1] - close[-n]) / close[-n]) * 100
        current_price = close[-1]

        short_price = close[-short_period - 1]
        long_price = close[-long_period - 1]

        # Handle zero price edge case
        if short_price == 0 or long_price == 0:
            return None

        short_roc = ((current_price - short_price) / short_price) * 100
        long_roc = ((current_price - long_price) / long_price) * 100

        # Combine: 60% short + 40% long
        combined = 0.6 * short_roc + 0.4 * long_roc

        # Normalize using tanh(combined / 10) * 100 to bound to -100/+100
        momentum_score = np.tanh(combined / 10) * 100

        # Safety clip for edge cases
        momentum_score = np.clip(momentum_score, -100, 100)

        return {
            'short_roc': float(short_roc),
            'long_roc': float(long_roc),
            'momentum_score': float(momentum_score)
        }
    except (KeyError, IndexError, ValueError, ZeroDivisionError):
        return None


def detect_volume_anomaly(
    df: pd.DataFrame,
    ma_period: int = 20,
    threshold: float = 2.0
) -> Optional[dict]:
    """
    Detect volume anomalies by comparing current volume to moving average.

    Args:
        df: DataFrame with 'volume' column
        ma_period: Moving average period (default 20)
        threshold: Anomaly threshold multiplier (default 2.0)

    Returns:
        Dict with keys:
        - 'current_volume': Current candle volume
        - 'avg_volume': Rolling average volume
        - 'volume_ratio': Ratio of current to average
        - 'is_anomaly': True if ratio exceeds threshold
        Returns None if insufficient data

    Minimum data: ma_period candles (20 for default)
    """
    if df is None or len(df) < ma_period:
        return None

    try:
        volume = df['volume'].values
        current_volume = float(volume[-1])

        # Calculate rolling mean of volume
        avg_volume = float(np.mean(volume[-ma_period:]))

        # Handle zero avg_volume edge case
        if avg_volume == 0:
            return None

        volume_ratio = current_volume / avg_volume
        is_anomaly = volume_ratio > threshold

        return {
            'current_volume': current_volume,
            'avg_volume': avg_volume,
            'volume_ratio': float(volume_ratio),
            'is_anomaly': bool(is_anomaly)
        }
    except (KeyError, IndexError, ValueError, ZeroDivisionError):
        return None


def calculate_ma_deviation(df: pd.DataFrame) -> Optional[dict]:
    """
    Calculate percentage deviation from exponential moving averages.

    Uses adjust=False for TradingView-compatible EMA calculation.

    Args:
        df: DataFrame with 'close' column

    Returns:
        Dict with keys:
        - 'deviation_20': Percentage deviation from 20 EMA
        - 'deviation_50': Percentage deviation from 50 EMA
        - 'deviation_200': Percentage deviation from 200 EMA
        Returns None if insufficient data

    Minimum data: 200 candles
    """
    if df is None or len(df) < 200:
        return None

    try:
        close = df['close']
        current_price = float(close.iloc[-1])

        # Calculate EMAs with adjust=False for TradingView compatibility
        ema_20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        ema_50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
        ema_200 = close.ewm(span=200, adjust=False).mean().iloc[-1]

        # Calculate percentage deviations: ((price - EMA) / EMA) * 100
        deviation_20 = ((current_price - ema_20) / ema_20) * 100
        deviation_50 = ((current_price - ema_50) / ema_50) * 100
        deviation_200 = ((current_price - ema_200) / ema_200) * 100

        return {
            'deviation_20': float(deviation_20),
            'deviation_50': float(deviation_50),
            'deviation_200': float(deviation_200)
        }
    except (KeyError, IndexError, ValueError, ZeroDivisionError):
        return None


def calculate_volatility_score(
    df: pd.DataFrame,
    atr_period: int = 14
) -> Optional[dict]:
    """
    Calculate volatility score using Average True Range (ATR).

    Imports calculate_atr from indicators.py and normalizes to 0-100 scale.

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        atr_period: ATR period (default 14)

    Returns:
        Dict with keys:
        - 'atr': Raw ATR value
        - 'atr_percent': ATR as percentage of current price
        - 'volatility_score': Normalized score in 0-100 range (5% ATR = 100)
        Returns None if insufficient data

    Minimum data: atr_period + 1 candles (15 for default)
    """
    if df is None or len(df) < atr_period + 1:
        return None

    try:
        # Import and call calculate_atr from indicators.py
        atr = calculate_atr(df, period=atr_period)
        if atr is None:
            return None

        current_price = float(df['close'].iloc[-1])

        # Handle zero price edge case
        if current_price == 0:
            return None

        # Normalize: atr_percent = (atr / current_price) * 100
        atr_percent = (atr / current_price) * 100

        # Scale: volatility_score = min(atr_percent * 20, 100.0)
        # 5% ATR maps to 100, anything above 5% caps at 100
        volatility_score = min(atr_percent * 20, 100.0)

        return {
            'atr': float(atr),
            'atr_percent': float(atr_percent),
            'volatility_score': float(volatility_score)
        }
    except (KeyError, IndexError, ValueError, ZeroDivisionError):
        return None
