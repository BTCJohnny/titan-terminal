"""Comprehensive unit tests for Telegram Agent.

Covers: signals present, empty results, best signal selection,
entry/stop/target extraction, freshness, confluence counting, and 48h window filtering.
"""
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.backend.agents.telegram_agent import TelegramAgent, _query_signals
from src.backend.models.telegram_signal import TelegramSignal, TelegramChannelSignal


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_signal_row(
    symbol: str = "BTC",
    direction: str = "long",
    confidence_score: int = 75,
    provider: str = "CryptoAlpha",
    entry_1: float = 65000.0,
    stop_loss: float = 63000.0,
    targets: list = None,
    created_at: str = None,
) -> dict:
    """Build a complete signal row dict matching _query_signals output format."""
    if targets is None:
        targets = [68000.0, 70000.0, None, None, None]
    # Pad/trim to exactly 5 elements
    while len(targets) < 5:
        targets.append(None)

    return {
        "symbol": symbol,
        "direction": direction,
        "signal_type": "breakout",
        "timeframe": "4h",
        "entry_1": entry_1,
        "entry_2": None,
        "entry_3": None,
        "stop_loss": stop_loss,
        "target_1": targets[0],
        "target_2": targets[1],
        "target_3": targets[2],
        "target_4": targets[3],
        "target_5": targets[4],
        "confidence_score": confidence_score,
        "pattern_type": "bull_flag",
        "setup_description": "Strong setup",
        "provider": provider,
        "status": "active",
        "created_at": created_at if created_at is not None else datetime.utcnow().isoformat(),
        "pnl_percent": None,
    }


# ---------------------------------------------------------------------------
# In-memory SQLite helper for 48h filter tests
# ---------------------------------------------------------------------------

def _create_test_db() -> sqlite3.Connection:
    """Create an in-memory SQLite database with the signals table."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE signals (
            symbol TEXT,
            direction TEXT,
            signal_type TEXT,
            timeframe TEXT,
            entry_1 REAL,
            entry_2 REAL,
            entry_3 REAL,
            stop_loss REAL,
            target_1 REAL,
            target_2 REAL,
            target_3 REAL,
            target_4 REAL,
            target_5 REAL,
            confidence_score INTEGER,
            pattern_type TEXT,
            setup_description TEXT,
            provider TEXT,
            status TEXT,
            created_at TEXT,
            pnl_percent REAL
        )
    """)
    conn.commit()
    return conn


def _insert_signal(conn: sqlite3.Connection, created_at: datetime, status: str = "active") -> None:
    """Insert a test signal row into the in-memory database."""
    conn.execute("""
        INSERT INTO signals (
            symbol, direction, signal_type, timeframe,
            entry_1, entry_2, entry_3, stop_loss,
            target_1, target_2, target_3, target_4, target_5,
            confidence_score, pattern_type, setup_description,
            provider, status, created_at, pnl_percent
        ) VALUES (
            'BTC', 'long', 'breakout', '4h',
            65000.0, NULL, NULL, 63000.0,
            68000.0, 70000.0, NULL, NULL, NULL,
            75, 'bull_flag', 'Strong setup',
            'TestProvider', ?, ?, NULL
        )
    """, (status, created_at.isoformat()))
    conn.commit()


# ===========================================================================
# TEST-05 — Signals Present
# ===========================================================================

class TestTelegramSignalsPresent:
    """Tests for TelegramAgent.analyze() when signals exist in database."""

    def test_analyze_single_long_signal(self):
        """Single long signal should produce bullish TelegramSignal with correct structure."""
        agent = TelegramAgent()
        rows = [_make_signal_row(direction="long", confidence_score=75, entry_1=65000.0)]

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=rows):
            result = agent.analyze("BTC")

        assert isinstance(result, TelegramSignal)
        assert result.symbol == "BTC"
        assert result.signals_found == 1
        assert result.overall_sentiment == "bullish"
        assert result.confluence_count == 1
        assert result.best_signal is not None
        assert result.best_signal.action == "long"
        assert result.relevant_signals[0].entry_price == 65000.0

    def test_analyze_multiple_bullish_signals(self):
        """Three long/buy signals should produce bullish sentiment with highest confidence best_signal."""
        agent = TelegramAgent()
        rows = [
            _make_signal_row(direction="long", confidence_score=70, provider="Alpha"),
            _make_signal_row(direction="buy", confidence_score=80, provider="Beta"),
            _make_signal_row(direction="long", confidence_score=90, provider="Gamma"),
        ]

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=rows):
            result = agent.analyze("BTC")

        assert result.signals_found == 3
        assert result.overall_sentiment == "bullish"
        assert result.confluence_count == 3
        assert result.best_signal is not None
        assert result.best_signal.signal_quality == 90
        assert result.best_signal.channel == "Gamma"

    def test_analyze_extracts_entry_stop_targets(self):
        """Entry price, stop loss, and take profits should be correctly extracted from row."""
        agent = TelegramAgent()
        row = _make_signal_row(
            direction="long",
            entry_1=65000.0,
            stop_loss=62000.0,
            targets=[68000.0, 70000.0, 72000.0, None, None],
        )

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=[row]):
            result = agent.analyze("BTC")

        sig = result.relevant_signals[0]
        assert sig.entry_price == 65000.0
        assert sig.stop_loss == 62000.0
        assert sig.take_profits == [68000.0, 70000.0, 72000.0]

    def test_analyze_freshness_threshold(self):
        """Signal created 6h ago should be 'fresh'; 20h ago should be 'stale'."""
        agent = TelegramAgent()
        fresh_time = (datetime.utcnow() - timedelta(hours=6)).isoformat()
        stale_time = (datetime.utcnow() - timedelta(hours=20)).isoformat()

        rows = [
            _make_signal_row(direction="long", provider="FreshProvider", created_at=fresh_time),
            _make_signal_row(direction="buy", provider="StaleProvider", created_at=stale_time),
        ]

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=rows):
            result = agent.analyze("BTC")

        # Map by channel name for reliable lookup
        by_channel = {s.channel: s for s in result.relevant_signals}
        assert by_channel["FreshProvider"].freshness == "fresh"
        assert by_channel["StaleProvider"].freshness == "stale"


# ===========================================================================
# TEST-06 — No Signals (empty results)
# ===========================================================================

class TestTelegramNoSignals:
    """Tests for TelegramAgent.analyze() when no signals are returned."""

    def test_analyze_empty_result(self):
        """Empty _query_signals result should return neutral TelegramSignal with zero counts."""
        agent = TelegramAgent()

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=[]):
            result = agent.analyze("BTC")

        assert isinstance(result, TelegramSignal)
        assert result.signals_found == 0
        assert result.active_signals == 0
        assert result.overall_sentiment == "neutral"
        assert result.confluence_count == 0
        assert result.confidence == 0
        assert result.avg_confidence == 0.0
        assert result.best_signal is None
        assert "No recent" in result.reasoning

    def test_analyze_invalid_direction_filtered(self):
        """Signal with direction='neutral' is not a valid action and should be filtered out."""
        agent = TelegramAgent()
        row = _make_signal_row(direction="neutral")

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=[row]):
            result = agent.analyze("BTC")

        # All rows were filtered — effectively zero valid signals
        assert result.signals_found == 0


# ===========================================================================
# TEST-07 — Confluence Counting
# ===========================================================================

class TestTelegramConfluence:
    """Tests for confluence counting and overall sentiment logic."""

    def test_confluence_all_bullish(self):
        """Four long signals should yield confluence_count=4 and bullish sentiment."""
        agent = TelegramAgent()
        rows = [_make_signal_row(direction="long") for _ in range(4)]

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=rows):
            result = agent.analyze("BTC")

        assert result.confluence_count == 4
        assert result.overall_sentiment == "bullish"

    def test_confluence_all_bearish(self):
        """Three short signals should yield confluence_count=3 and bearish sentiment."""
        agent = TelegramAgent()
        rows = [_make_signal_row(direction="short") for _ in range(3)]

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=rows):
            result = agent.analyze("BTC")

        assert result.confluence_count == 3
        assert result.overall_sentiment == "bearish"

    def test_confluence_mixed_majority_bullish(self):
        """3 long + 1 short: confluence_count should be 3 (bullish majority)."""
        agent = TelegramAgent()
        rows = (
            [_make_signal_row(direction="long") for _ in range(3)]
            + [_make_signal_row(direction="short")]
        )

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=rows):
            result = agent.analyze("BTC")

        assert result.confluence_count == 3
        assert result.overall_sentiment == "bullish"

    def test_confluence_mixed_majority_bearish(self):
        """1 long + 3 short: confluence_count should be 3 (bearish majority)."""
        agent = TelegramAgent()
        rows = (
            [_make_signal_row(direction="long")]
            + [_make_signal_row(direction="short") for _ in range(3)]
        )

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=rows):
            result = agent.analyze("BTC")

        assert result.confluence_count == 3
        assert result.overall_sentiment == "bearish"

    def test_confluence_equal_split(self):
        """2 long + 2 short: mixed sentiment with confluence_count=2."""
        agent = TelegramAgent()
        rows = (
            [_make_signal_row(direction="long") for _ in range(2)]
            + [_make_signal_row(direction="short") for _ in range(2)]
        )

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=rows):
            result = agent.analyze("BTC")

        assert result.overall_sentiment == "mixed"
        assert result.confluence_count == 2

    def test_confidence_weighted_by_confluence(self):
        """Confidence is weighted by confluence ratio: avg_confidence * (confluence / total)."""
        agent = TelegramAgent()
        # 2 long (confidence 80) + 1 short (confidence 80) → 3 total, 2 agree (bullish)
        rows = (
            [_make_signal_row(direction="long", confidence_score=80) for _ in range(2)]
            + [_make_signal_row(direction="short", confidence_score=80)]
        )

        with patch("src.backend.agents.telegram_agent._query_signals", return_value=rows):
            result = agent.analyze("BTC")

        assert result.avg_confidence == 80.0
        # int(80.0 * (2/3)) = int(53.33) = 53
        assert result.confidence == 53


# ===========================================================================
# TEST-08 — 48h Window Filter (in-memory SQLite)
# ===========================================================================

class TestTelegram48hFilter:
    """Tests for _query_signals 48h window and status filtering using in-memory SQLite."""

    def test_48h_filter_includes_recent(self):
        """Signal created 1h ago should be included in _query_signals results."""
        conn = _create_test_db()
        _insert_signal(conn, created_at=datetime.utcnow() - timedelta(hours=1), status="active")

        with patch("src.backend.agents.telegram_agent.get_signals_connection", return_value=conn):
            results = _query_signals("BTC")

        assert len(results) == 1

    def test_48h_filter_excludes_old(self):
        """Signal created 72h ago should be excluded from _query_signals results."""
        conn = _create_test_db()
        _insert_signal(conn, created_at=datetime.utcnow() - timedelta(hours=72), status="active")

        with patch("src.backend.agents.telegram_agent.get_signals_connection", return_value=conn):
            results = _query_signals("BTC")

        assert len(results) == 0

    def test_48h_filter_boundary(self):
        """Signal 47h ago included; signal 49h ago excluded — boundary case."""
        conn = _create_test_db()
        _insert_signal(conn, created_at=datetime.utcnow() - timedelta(hours=47), status="active")
        _insert_signal(conn, created_at=datetime.utcnow() - timedelta(hours=49), status="active")

        with patch("src.backend.agents.telegram_agent.get_signals_connection", return_value=conn):
            results = _query_signals("BTC")

        assert len(results) == 1

    def test_48h_filter_status_filter(self):
        """Only 'active' (or 'pending') signals returned; 'closed' status filtered out."""
        conn = _create_test_db()
        _insert_signal(conn, created_at=datetime.utcnow() - timedelta(hours=1), status="active")
        _insert_signal(conn, created_at=datetime.utcnow() - timedelta(hours=1), status="closed")

        with patch("src.backend.agents.telegram_agent.get_signals_connection", return_value=conn):
            results = _query_signals("BTC")

        assert len(results) == 1
        assert results[0]["status"] == "active"
