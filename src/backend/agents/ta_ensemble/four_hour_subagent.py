"""Four-Hour Timeframe TA Subagent - Pure computational analysis pipeline.

This subagent fetches 2 years of 4-hour OHLCV data and produces comprehensive
technical analysis including indicators, alpha factors, and Wyckoff detection.
No LLM calls are made - all analysis is deterministic computation.
"""
import logging
from typing import Optional

import pandas as pd

from src.backend.data.ohlcv_client import get_ohlcv_client
from src.backend.models.ta_signal import (
    TASignal, TrendData, MomentumData as TAMomentumData,
    KeyLevels, PatternData, OverallAssessment
)
from src.backend.models.wyckoff import WyckoffAnalysis
from src.backend.models.alpha_factors import (
    AlphaFactors,
    MomentumData as AlphaMomentumData,
    VolumeAnomalyData,
    MADeviationData,
    VolatilityData
)
from src.backend.analysis import (
    calculate_rsi, calculate_macd, calculate_adx,
    detect_support_resistance,
    calculate_momentum_score, detect_volume_anomaly,
    calculate_ma_deviation, calculate_volatility_score,
    detect_wyckoff
)

logger = logging.getLogger(__name__)


class FourHourSubagent:
    """Four-hour timeframe technical analysis subagent.

    Pure computational pipeline that:
    1. Fetches 4380 4-hour candles (2 years) via OHLCVClient
    2. Calculates all technical indicators
    3. Computes alpha factors
    4. Detects Wyckoff patterns
    5. Synthesizes into extended TASignal
    """

    TIMEFRAME = "4h"
    CANDLE_LIMIT = 4380  # 2 years of 4-hour candles (6/day * 365 * 2)
    MIN_CANDLES_WARNING = 720  # ~4 months threshold

    def analyze(self, symbol: str) -> TASignal:
        """Analyze 4-hour timeframe for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")

        Returns:
            TASignal with populated wyckoff and alpha_factors fields

        Logs:
            Warning if fewer than 720 candles returned
        """
        # Step 1: Fetch OHLCV data
        client = get_ohlcv_client()
        candles = client.fetch_ohlcv(symbol, self.TIMEFRAME, limit=self.CANDLE_LIMIT)

        # Step 2: Check candle count and log warning if insufficient
        if len(candles) < self.MIN_CANDLES_WARNING:
            logger.warning(
                f"Insufficient history for {symbol} on {self.TIMEFRAME}: "
                f"got {len(candles)} candles (recommended {self.MIN_CANDLES_WARNING}+)"
            )

        # Step 3: Convert to DataFrame
        df = pd.DataFrame(candles)

        # Step 4: Calculate technical indicators
        indicators = self._calculate_indicators(df)

        # Step 5: Calculate alpha factors
        alpha_factors = self._calculate_alpha_factors(df)

        # Step 6: Detect Wyckoff patterns (requires 50+ candles for best results)
        wyckoff = detect_wyckoff(df) if len(df) >= 50 else None
        if wyckoff is None and len(df) < 50:
            logger.info(f"Wyckoff detection skipped for {symbol}: only {len(df)} candles")

        # Step 7: Determine overall trend and confidence
        direction, confidence = self._determine_trend_confluence(indicators, wyckoff)

        # Step 8: Build and return TASignal
        return self._build_ta_signal(
            symbol, df, indicators, alpha_factors, wyckoff, direction, confidence
        )

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """Calculate all technical indicators."""
        return {
            'rsi': calculate_rsi(df),
            'macd': calculate_macd(df),
            'adx': calculate_adx(df),
            'sr_levels': detect_support_resistance(df),
        }

    def _calculate_alpha_factors(self, df: pd.DataFrame) -> Optional[AlphaFactors]:
        """Calculate alpha factors and build AlphaFactors model."""
        momentum_data = None
        volume_data = None
        ma_data = None
        volatility_data = None

        if momentum := calculate_momentum_score(df):
            momentum_data = AlphaMomentumData(**momentum)

        if volume := detect_volume_anomaly(df):
            volume_data = VolumeAnomalyData(**volume)

        if ma_dev := calculate_ma_deviation(df):
            ma_data = MADeviationData(**ma_dev)

        if vol := calculate_volatility_score(df):
            volatility_data = VolatilityData(**vol)

        # Return None if no factors could be calculated
        if not any([momentum_data, volume_data, ma_data, volatility_data]):
            return None

        return AlphaFactors(
            momentum=momentum_data,
            volume_anomaly=volume_data,
            ma_deviation=ma_data,
            volatility=volatility_data
        )

    def _determine_trend_confluence(
        self,
        indicators: dict,
        wyckoff: Optional[WyckoffAnalysis]
    ) -> tuple[str, int]:
        """Determine overall trend direction and confidence from indicator confluence.

        Uses a weighted voting system:
        - RSI: overbought/oversold signals (weight: 20)
        - MACD: histogram direction (weight: 25)
        - ADX: trend strength modifier (multiplier 0.7-1.3)
        - Wyckoff: phase direction (weight: 30 for Phase E)

        Returns:
            (direction, confidence) where direction in ["bullish", "bearish", "neutral"]
            and confidence in 0-100 range
        """
        signals = []  # List of (direction, weight) tuples

        # RSI contribution
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi > 70:
                signals.append(("bearish", 20))  # Overbought
            elif rsi < 30:
                signals.append(("bullish", 20))  # Oversold
            elif rsi > 50:
                signals.append(("bullish", 10))  # Above midline
            else:
                signals.append(("bearish", 10))  # Below midline

        # MACD contribution
        macd = indicators.get('macd')
        if macd is not None and 'histogram' in macd:
            if macd['histogram'] > 0:
                signals.append(("bullish", 25))
            else:
                signals.append(("bearish", 25))

        # Wyckoff contribution (strong signal for Phase E)
        if wyckoff and wyckoff.phase != "unknown":
            if "accumulation" in wyckoff.phase:
                weight = 30 if wyckoff.phase.endswith("_e") else 15
                signals.append(("bullish", weight))
            elif "distribution" in wyckoff.phase:
                weight = 30 if wyckoff.phase.endswith("_e") else 15
                signals.append(("bearish", weight))

        # ADX trend strength modifier
        adx = indicators.get('adx')
        trend_multiplier = 1.0
        if adx is not None:
            if adx > 25:
                trend_multiplier = 1.3  # Strong trend
            elif adx < 20:
                trend_multiplier = 0.7  # Weak trend

        # Aggregate signals
        if not signals:
            return ("neutral", 50)

        bullish_weight = sum(w for d, w in signals if d == "bullish")
        bearish_weight = sum(w for d, w in signals if d == "bearish")
        total_weight = bullish_weight + bearish_weight

        if bullish_weight > bearish_weight:
            direction = "bullish"
            raw_confidence = (bullish_weight / total_weight) * 100 if total_weight > 0 else 50
        elif bearish_weight > bullish_weight:
            direction = "bearish"
            raw_confidence = (bearish_weight / total_weight) * 100 if total_weight > 0 else 50
        else:
            direction = "neutral"
            raw_confidence = 50

        # Apply trend strength modifier and clamp to 0-100
        final_confidence = int(min(max(raw_confidence * trend_multiplier, 0), 100))

        return (direction, final_confidence)

    def _build_ta_signal(
        self,
        symbol: str,
        df: pd.DataFrame,
        indicators: dict,
        alpha_factors: Optional[AlphaFactors],
        wyckoff: Optional[WyckoffAnalysis],
        direction: str,
        confidence: int
    ) -> TASignal:
        """Build TASignal from analysis outputs."""
        # Extract symbol base (BTC/USDT -> BTC)
        symbol_base = symbol.split('/')[0] if '/' in symbol else symbol

        # Map direction to strength
        strength = "strong" if confidence > 70 else "moderate" if confidence > 40 else "weak"

        # Determine EMA alignment from MACD (simplified proxy)
        macd = indicators.get('macd')
        if macd and 'macd' in macd and 'signal' in macd:
            ema_alignment = "bullish" if macd['macd'] > macd['signal'] else "bearish"
        else:
            ema_alignment = "neutral"

        # Build TrendData
        trend = TrendData(
            direction=direction if direction != "neutral" else "sideways",
            strength=strength,
            ema_alignment=ema_alignment
        )

        # Build MomentumData (using TASignal's MomentumData, not AlphaFactors)
        rsi = indicators.get('rsi')
        macd_bias = "bullish" if macd and macd.get('histogram', 0) > 0 else "bearish" if macd else "neutral"
        momentum = TAMomentumData(
            rsi=rsi,
            macd_bias=macd_bias,
            momentum_divergence=False  # Divergence detection not implemented yet
        )

        # Build KeyLevels from support/resistance
        sr = indicators.get('sr_levels', {})
        support_levels = sr.get('support', [])
        resistance_levels = sr.get('resistance', [])
        key_levels = KeyLevels(
            major_support=support_levels[0] if support_levels else None,
            major_resistance=resistance_levels[0] if resistance_levels else None
        )

        # Build PatternData (no pattern detection implemented yet)
        patterns = PatternData(
            detected=[],
            pattern_bias="neutral"
        )

        # Build OverallAssessment
        notes = self._generate_notes(indicators, wyckoff, direction, confidence)
        overall = OverallAssessment(
            bias=direction if direction != "sideways" else "neutral",
            confidence=confidence,
            notes=notes
        )

        return TASignal(
            symbol=symbol_base,
            timeframe="4h",
            trend=trend,
            momentum=momentum,
            key_levels=key_levels,
            patterns=patterns,
            overall=overall,
            wyckoff=wyckoff,
            alpha_factors=alpha_factors
        )

    def _generate_notes(
        self,
        indicators: dict,
        wyckoff: Optional[WyckoffAnalysis],
        direction: str,
        confidence: int
    ) -> str:
        """Generate analysis notes summarizing key findings."""
        notes_parts = []

        # Trend summary
        notes_parts.append(f"4H {direction} bias ({confidence}% confidence)")

        # RSI context
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi > 70:
                notes_parts.append(f"RSI overbought ({rsi:.1f})")
            elif rsi < 30:
                notes_parts.append(f"RSI oversold ({rsi:.1f})")

        # Wyckoff context
        if wyckoff and wyckoff.phase != "unknown":
            phase_readable = wyckoff.phase.replace("_", " ").title()
            notes_parts.append(f"Wyckoff: {phase_readable}")

        return ". ".join(notes_parts) + "."
