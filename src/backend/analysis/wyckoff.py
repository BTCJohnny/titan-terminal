"""
Wyckoff pattern detection for accumulation and distribution analysis.

Entry point: detect_wyckoff(df) returns WyckoffAnalysis with detected phase,
events (Spring, Upthrust, SOS, SOW), and volume confirmation.

Minimum data requirement: 100 candles for reliable phase classification.
Returns None if insufficient data provided.
"""

import pandas as pd
import numpy as np
from typing import Optional, List
from src.backend.analysis.indicators import detect_support_resistance
from src.backend.models.wyckoff import WyckoffEvent, WyckoffAnalysis


def _calculate_volume_baseline(df: pd.DataFrame, period: int = 20) -> float:
    """
    Calculate volume baseline (mean volume over recent period).

    Args:
        df: DataFrame with 'volume' column
        period: Number of candles to average (default 20)

    Returns:
        Mean volume over period (or full mean if insufficient data)
    """
    try:
        if len(df) >= period:
            return float(df['volume'].iloc[-period:].mean())
        return float(df['volume'].mean())
    except (KeyError, AttributeError, ValueError):
        return 0.0


def _detect_spring(
    df: pd.DataFrame,
    support_levels: List[float],
    volume_baseline: float,
    recovery_window: int = 3
) -> List[WyckoffEvent]:
    """
    Detect Spring events: price closes below support then recovers on low volume.

    Args:
        df: DataFrame with OHLCV columns
        support_levels: List of support price levels
        volume_baseline: Mean volume for comparison
        recovery_window: Candles to check for recovery (default 3)

    Returns:
        List of WyckoffEvent objects with event_type="spring"
    """
    events = []
    if not support_levels or volume_baseline == 0:
        return events

    try:
        closes = df['close'].values
        volumes = df['volume'].values
        nearest_support = min(support_levels)

        for i in range(len(df) - recovery_window):
            # Check if price closed below support on low volume
            if closes[i] < nearest_support and volumes[i] < volume_baseline:
                # Check for recovery within window
                recovery_found = False
                for j in range(1, recovery_window + 1):
                    if i + j < len(closes) and closes[i + j] > nearest_support:
                        recovery_found = True
                        break

                if recovery_found:
                    events.append(WyckoffEvent(
                        candle_index=i,
                        event_type="spring",
                        price=float(closes[i]),
                        volume_ratio=float(volumes[i] / volume_baseline),
                        description=f"Spring below support at {nearest_support:.2f} with recovery"
                    ))

        return events
    except (KeyError, IndexError, ValueError, AttributeError):
        return []


def _detect_upthrust(
    df: pd.DataFrame,
    resistance_levels: List[float],
    volume_baseline: float,
    recovery_window: int = 3
) -> List[WyckoffEvent]:
    """
    Detect Upthrust events: price closes above resistance then fails on low volume.

    Args:
        df: DataFrame with OHLCV columns
        resistance_levels: List of resistance price levels
        volume_baseline: Mean volume for comparison
        recovery_window: Candles to check for failure (default 3)

    Returns:
        List of WyckoffEvent objects with event_type="upthrust"
    """
    events = []
    if not resistance_levels or volume_baseline == 0:
        return events

    try:
        closes = df['close'].values
        volumes = df['volume'].values
        nearest_resistance = min(resistance_levels)

        for i in range(len(df) - recovery_window):
            # Check if price closed above resistance on low volume
            if closes[i] > nearest_resistance and volumes[i] < volume_baseline:
                # Check for failure within window
                failure_found = False
                for j in range(1, recovery_window + 1):
                    if i + j < len(closes) and closes[i + j] < nearest_resistance:
                        failure_found = True
                        break

                if failure_found:
                    events.append(WyckoffEvent(
                        candle_index=i,
                        event_type="upthrust",
                        price=float(closes[i]),
                        volume_ratio=float(volumes[i] / volume_baseline),
                        description=f"Upthrust above resistance at {nearest_resistance:.2f} with failure"
                    ))

        return events
    except (KeyError, IndexError, ValueError, AttributeError):
        return []


def _detect_sos(
    df: pd.DataFrame,
    resistance_levels: List[float],
    volume_baseline: float,
    threshold: float = 1.5
) -> List[WyckoffEvent]:
    """
    Detect Sign of Strength (SOS): close above resistance with high volume.

    Args:
        df: DataFrame with OHLCV columns
        resistance_levels: List of resistance price levels
        volume_baseline: Mean volume for comparison
        threshold: Volume multiplier to qualify (default 1.5)

    Returns:
        List of WyckoffEvent objects with event_type="sos"
    """
    events = []
    if not resistance_levels or volume_baseline == 0:
        return events

    try:
        closes = df['close'].values
        volumes = df['volume'].values
        nearest_resistance = min(resistance_levels)

        for i in range(len(df)):
            # Check if price closed above resistance with high volume
            if closes[i] > nearest_resistance and volumes[i] > threshold * volume_baseline:
                events.append(WyckoffEvent(
                    candle_index=i,
                    event_type="sos",
                    price=float(closes[i]),
                    volume_ratio=float(volumes[i] / volume_baseline),
                    description=f"Sign of Strength above {nearest_resistance:.2f} with {volumes[i]/volume_baseline:.1f}x volume"
                ))

        return events
    except (KeyError, IndexError, ValueError, AttributeError):
        return []


def _detect_sow(
    df: pd.DataFrame,
    support_levels: List[float],
    volume_baseline: float,
    threshold: float = 1.5
) -> List[WyckoffEvent]:
    """
    Detect Sign of Weakness (SOW): close below support with high volume.

    Args:
        df: DataFrame with OHLCV columns
        support_levels: List of support price levels
        volume_baseline: Mean volume for comparison
        threshold: Volume multiplier to qualify (default 1.5)

    Returns:
        List of WyckoffEvent objects with event_type="sow"
    """
    events = []
    if not support_levels or volume_baseline == 0:
        return events

    try:
        closes = df['close'].values
        volumes = df['volume'].values
        nearest_support = min(support_levels)

        for i in range(len(df)):
            # Check if price closed below support with high volume
            if closes[i] < nearest_support and volumes[i] > threshold * volume_baseline:
                events.append(WyckoffEvent(
                    candle_index=i,
                    event_type="sow",
                    price=float(closes[i]),
                    volume_ratio=float(volumes[i] / volume_baseline),
                    description=f"Sign of Weakness below {nearest_support:.2f} with {volumes[i]/volume_baseline:.1f}x volume"
                ))

        return events
    except (KeyError, IndexError, ValueError, AttributeError):
        return []
