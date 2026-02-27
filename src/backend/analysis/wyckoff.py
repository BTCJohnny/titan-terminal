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


def _classify_phase(
    df: pd.DataFrame,
    events: List[WyckoffEvent],
    sr_levels: dict,
    volume_baseline: float
) -> tuple:
    """
    Classify current Wyckoff phase from event sequence and price position.

    Args:
        df: DataFrame with OHLCV columns
        events: List of detected WyckoffEvent objects
        sr_levels: Dict with 'support' and 'resistance' lists
        volume_baseline: Mean volume for comparison

    Returns:
        Tuple of (phase: str, confidence: int)
    """
    try:
        current_price = df['close'].iloc[-1]
        volumes = df['volume'].values
        support_levels = sr_levels.get('support', [])
        resistance_levels = sr_levels.get('resistance', [])

        # Check for recent high-volume climax (Phase A indicator)
        recent_volumes = volumes[-20:] if len(volumes) >= 20 else volumes
        climax_threshold = 2.0 * volume_baseline
        has_climax = any(v > climax_threshold for v in recent_volumes)

        # Check if price is range-bound (between support and resistance)
        in_range = False
        if support_levels and resistance_levels:
            nearest_support = max(support_levels) if support_levels else 0
            nearest_resistance = min(resistance_levels) if resistance_levels else float('inf')
            in_range = nearest_support < current_price < nearest_resistance

        # Detect event types
        has_spring = any(e.event_type == "spring" for e in events)
        has_upthrust = any(e.event_type == "upthrust" for e in events)
        has_sos = any(e.event_type == "sos" for e in events)
        has_sow = any(e.event_type == "sow" for e in events)

        # Phase classification logic
        phase = "unknown"
        confidence = 50

        # Phase E: Trending (price outside range after SOS/SOW)
        if has_sos and resistance_levels and current_price > min(resistance_levels):
            phase = "accumulation_e"
            confidence = 70
        elif has_sow and support_levels and current_price < max(support_levels):
            phase = "distribution_e"
            confidence = 70

        # Phase D: SOS or SOW detected
        elif has_sos:
            phase = "accumulation_d"
            confidence = 75
        elif has_sow:
            phase = "distribution_d"
            confidence = 75

        # Phase C: Spring or Upthrust detected
        elif has_spring:
            phase = "accumulation_c"
            confidence = 70
        elif has_upthrust:
            phase = "distribution_c"
            confidence = 70

        # Phase B: Range-bound with declining volume
        elif in_range and len(volumes) >= 50:
            recent_avg = np.mean(volumes[-20:])
            prior_avg = np.mean(volumes[-50:-30]) if len(volumes) >= 50 else np.mean(volumes)
            if recent_avg < prior_avg:
                # Determine accumulation vs distribution by volume character
                # Accumulation typically has lower volume, distribution has irregular volume
                volume_std = np.std(volumes[-20:])
                if volume_std < prior_avg * 0.3:  # Low volatility = accumulation
                    phase = "accumulation_b"
                else:
                    phase = "distribution_b"
                confidence = 60

        # Phase A: Recent climax volume
        elif has_climax:
            # Check if near support (accumulation) or resistance (distribution)
            near_support = support_levels and abs(current_price - max(support_levels)) / current_price < 0.02
            near_resistance = resistance_levels and abs(current_price - min(resistance_levels)) / current_price < 0.02

            if near_support:
                phase = "accumulation_a"
                confidence = 65
            elif near_resistance:
                phase = "distribution_a"
                confidence = 65

        return (phase, confidence)
    except (KeyError, IndexError, ValueError, AttributeError):
        return ("unknown", 30)


def _check_volume_confirmation(
    df: pd.DataFrame,
    phase: str,
    volume_baseline: float
) -> bool:
    """
    Check if volume confirms the detected phase.

    Args:
        df: DataFrame with 'volume' column
        phase: Detected Wyckoff phase
        volume_baseline: Mean volume for comparison

    Returns:
        True if volume pattern confirms phase, False otherwise
    """
    try:
        volumes = df['volume'].values
        if len(volumes) < 20:
            return False

        recent_volumes = volumes[-20:]
        recent_avg = np.mean(recent_volumes)

        # Accumulation phases: expect declining volume in B, expanding in C/D
        if phase.startswith("accumulation"):
            if phase == "accumulation_b":
                return recent_avg < volume_baseline * 0.9
            elif phase in ["accumulation_c", "accumulation_d"]:
                return recent_avg > volume_baseline * 1.1
            elif phase == "accumulation_e":
                return recent_avg > volume_baseline * 1.2

        # Distribution phases: similar pattern
        elif phase.startswith("distribution"):
            if phase == "distribution_b":
                return recent_avg < volume_baseline * 0.9
            elif phase in ["distribution_c", "distribution_d"]:
                return recent_avg > volume_baseline * 1.1
            elif phase == "distribution_e":
                return recent_avg > volume_baseline * 1.2

        return False
    except (KeyError, ValueError, AttributeError):
        return False


def _calculate_confidence(
    df: pd.DataFrame,
    events: List[WyckoffEvent],
    phase: str
) -> int:
    """
    Calculate confidence score for phase detection.

    Args:
        df: DataFrame (used for length check)
        events: List of detected events
        phase: Detected phase

    Returns:
        Confidence score (0-100)
    """
    base_confidence = 50
    event_count = len(events)

    # Adjust for data quantity
    if len(df) >= 100:
        base_confidence += 20
    elif len(df) < 50:
        base_confidence -= 20

    # Adjust for event detection quality
    if 2 <= event_count <= 8:
        base_confidence += 15
    elif event_count == 0:
        base_confidence -= 30
    elif event_count > 15:
        base_confidence -= 20  # Over-detection

    # Adjust for phase certainty
    if phase != "unknown":
        base_confidence += 15

    # Clip to valid range
    return max(0, min(100, base_confidence))


def detect_wyckoff(df: pd.DataFrame) -> Optional[WyckoffAnalysis]:
    """
    Detect Wyckoff accumulation/distribution phase from OHLCV data.

    Analyzes price-volume patterns to identify Wyckoff phases (A-E) for both
    accumulation and distribution cycles. Detects key events including Spring,
    Upthrust, Sign of Strength (SOS), and Sign of Weakness (SOW).

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
            Minimum 100 candles required for reliable detection.

    Returns:
        WyckoffAnalysis object with:
            - phase: Current Wyckoff phase (accumulation/distribution A-E or unknown)
            - phase_confidence: Confidence score 0-100
            - events: List of detected Wyckoff events (chronologically sorted)
            - volume_confirms: Whether volume pattern confirms phase
            - analysis_notes: Human-readable summary

        Returns None if:
            - df is None
            - Insufficient data (< 100 candles)
            - Required columns missing
            - Volume baseline is zero (no trading activity)

    Example:
        >>> df = fetch_ohlcv("BTC/USDT", "1h", limit=200)
        >>> analysis = detect_wyckoff(df)
        >>> if analysis:
        ...     print(f"Phase: {analysis.phase}, Confidence: {analysis.phase_confidence}%")
        ...     print(f"Events detected: {len(analysis.events)}")
    """
    # Validate input
    if df is None or len(df) < 100:
        return None

    try:
        # Step 1: Detect support and resistance levels
        sr_levels = detect_support_resistance(df, num_levels=3)

        # Step 2: Calculate volume baseline
        volume_baseline = _calculate_volume_baseline(df, period=20)
        if volume_baseline == 0:
            return None

        # Step 3: Detect all event types
        all_events = []
        all_events.extend(_detect_spring(df, sr_levels['support'], volume_baseline))
        all_events.extend(_detect_upthrust(df, sr_levels['resistance'], volume_baseline))
        all_events.extend(_detect_sos(df, sr_levels['resistance'], volume_baseline))
        all_events.extend(_detect_sow(df, sr_levels['support'], volume_baseline))

        # Step 4: Deduplicate events by candle_index (keep first)
        seen_indices = set()
        unique_events = []
        for event in all_events:
            if event.candle_index not in seen_indices:
                unique_events.append(event)
                seen_indices.add(event.candle_index)

        # Step 5: Classify phase
        phase, base_confidence = _classify_phase(df, unique_events, sr_levels, volume_baseline)

        # Step 6: Calculate final confidence
        confidence = _calculate_confidence(df, unique_events, phase)

        # Step 7: Check volume confirmation
        volume_confirms = _check_volume_confirmation(df, phase, volume_baseline)

        # Step 8: Build analysis notes
        event_summary = f"Detected {len(unique_events)} Wyckoff events"
        if unique_events:
            event_types = {}
            for event in unique_events:
                event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
            type_str = ", ".join([f"{count} {etype}" for etype, count in event_types.items()])
            event_summary += f" ({type_str})"

        analysis_notes = f"{event_summary}. Volume {'confirms' if volume_confirms else 'does not confirm'} phase."

        # Step 9: Return WyckoffAnalysis
        return WyckoffAnalysis(
            phase=phase,
            phase_confidence=confidence,
            events=unique_events,  # Will be auto-sorted by model validator
            volume_confirms=volume_confirms,
            analysis_notes=analysis_notes
        )

    except (KeyError, ValueError, AttributeError):
        return None
