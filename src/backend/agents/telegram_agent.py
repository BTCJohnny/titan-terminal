"""Telegram Alpha Agent - Scans Telegram signals from SQLite.

Production implementation that queries signals.db for external signals.
No Claude SDK calls - pure computational analysis.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from ..db.signals_db import get_signals_connection
from ..models import TelegramSignal, TelegramChannelSignal

logger = logging.getLogger(__name__)


def _query_signals(symbol: str, hours: int = 48, limit: int = 20) -> list[dict]:
    """Query signals table for recent signals.

    Args:
        symbol: Trading symbol to query (e.g., 'BTC', 'ETH')
        hours: Time window in hours (default 48)
        limit: Maximum number of signals to return (default 20)

    Returns:
        List of signal dicts with all columns from signals table
    """
    try:
        conn = get_signals_connection()
        cursor = conn.cursor()

        # Query signals table with status and time filters
        cursor.execute("""
            SELECT
                symbol, direction, signal_type, timeframe,
                entry_1, entry_2, entry_3, stop_loss,
                target_1, target_2, target_3, target_4, target_5,
                confidence_score, pattern_type, setup_description,
                provider, status, created_at, pnl_percent
            FROM signals
            WHERE symbol LIKE ?
            AND status IN ('pending', 'active')
            AND datetime(created_at) > datetime('now', '-48 hours')
            ORDER BY created_at DESC
            LIMIT ?
        """, (f"%{symbol}%", limit))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"Found {len(results)} signals for {symbol} in last {hours}h")
        return results

    except Exception as e:
        logger.warning(f"Database query failed for {symbol}: {e}")
        return []


class TelegramAgent:
    """Telegram signal scanning agent.

    Pure computational agent - no Claude SDK calls.
    Queries signals.db and returns TelegramSignal model.
    """

    def __init__(self):
        """Initialize TelegramAgent."""
        self.name = "Telegram Alpha"
        logger.info(f"Initialized {self.name} agent")

    def analyze(self, symbol: str) -> TelegramSignal:
        """Analyze Telegram signals for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTC')

        Returns:
            TelegramSignal with aggregated analysis
        """
        # Query database for recent signals
        signal_rows = _query_signals(symbol, hours=48, limit=20)

        # Handle empty results
        if not signal_rows:
            return TelegramSignal(
                symbol=symbol,
                signals_found=0,
                active_signals=0,
                relevant_signals=[],
                overall_sentiment="neutral",
                confluence_count=0,
                confidence=0,
                avg_confidence=0.0,
                best_signal=None,
                reasoning=f"No recent Telegram signals found for {symbol}",
                timestamp=datetime.utcnow(),
                notes=""
            )

        # Build TelegramChannelSignal list from database rows
        channel_signals = []
        for row in signal_rows:
            # Map direction to action
            direction = row.get('direction', '').lower()
            if direction in ['long', 'buy']:
                action = 'long' if direction == 'long' else 'buy'
            elif direction in ['short', 'sell']:
                action = 'short' if direction == 'short' else 'sell'
            else:
                # Skip invalid directions
                continue

            # Extract entry price from first non-null entry
            entry_price = row.get('entry_1') or row.get('entry_2') or row.get('entry_3')

            # Extract stop loss
            stop_loss = row.get('stop_loss')

            # Build take profits list from targets (filter nulls)
            take_profits = [
                t for t in [
                    row.get('target_1'),
                    row.get('target_2'),
                    row.get('target_3'),
                    row.get('target_4'),
                    row.get('target_5')
                ] if t is not None
            ]

            # Map confidence_score to signal_quality
            signal_quality = int(row.get('confidence_score', 0))

            # Determine freshness (fresh if within 12 hours)
            created_at_str = row.get('created_at', '')
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                hours_old = (datetime.utcnow() - created_at).total_seconds() / 3600
                freshness = "fresh" if hours_old <= 12 else "stale"
                timestamp = created_at
            except:
                freshness = "stale"
                timestamp = None

            # Build channel signal
            channel_signal = TelegramChannelSignal(
                channel=row.get('provider', 'Unknown'),
                action=action,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profits=take_profits,
                signal_quality=signal_quality,
                freshness=freshness,
                timestamp=timestamp,
                raw_text=row.get('setup_description'),
                notes=""
            )
            channel_signals.append(channel_signal)

        # Calculate confluence
        bullish_count = sum(1 for s in channel_signals if s.action in ['long', 'buy'])
        bearish_count = sum(1 for s in channel_signals if s.action in ['short', 'sell'])
        confluence_count = max(bullish_count, bearish_count)

        # Determine overall sentiment
        if bullish_count > bearish_count:
            overall_sentiment = "bullish"
        elif bearish_count > bullish_count:
            overall_sentiment = "bearish"
        elif bullish_count == bearish_count and bullish_count > 0:
            overall_sentiment = "mixed"
        else:
            overall_sentiment = "neutral"

        # Calculate confidence
        total_signals = len(channel_signals)
        avg_confidence = sum(s.signal_quality for s in channel_signals) / total_signals if total_signals > 0 else 0.0

        # Weighted confidence based on confluence
        if total_signals > 0:
            confidence = int(avg_confidence * (confluence_count / total_signals))
        else:
            confidence = 0

        # Find best signal (highest signal_quality)
        best_signal = max(channel_signals, key=lambda s: s.signal_quality) if channel_signals else None

        # Build reasoning string
        direction_word = "bullish" if bullish_count > bearish_count else "bearish"
        if best_signal:
            reasoning = (
                f"{total_signals} signals found. "
                f"{confluence_count} signals agree on {direction_word}. "
                f"Best signal from {best_signal.channel} with {best_signal.signal_quality}% confidence."
            )
        else:
            reasoning = f"{total_signals} signals found but none with valid direction."

        # Return TelegramSignal
        return TelegramSignal(
            symbol=symbol,
            signals_found=total_signals,
            active_signals=total_signals,  # All queried signals are active (status filter)
            relevant_signals=channel_signals,
            overall_sentiment=overall_sentiment,
            confluence_count=confluence_count,
            confidence=confidence,
            avg_confidence=avg_confidence,
            best_signal=best_signal,
            reasoning=reasoning,
            timestamp=datetime.utcnow(),
            notes=""
        )
