"""Unit tests for signals_db snapshot table creation and insert operations.

Tests use in-memory SQLite to avoid touching any real filesystem database.
"""
import sqlite3
import pytest
from unittest.mock import patch

from src.backend.db.signals_db import (
    init_snapshot_tables,
    insert_onchain_snapshot,
    insert_ta_snapshot,
)


class _NoCloseConnection:
    """Thin wrapper around a sqlite3.Connection that makes close() a no-op.

    sqlite3.Connection.close is read-only on Python 3.12+, so we cannot
    monkey-patch it directly. This wrapper delegates all attribute access
    to the underlying connection but intercepts close() so that signals_db
    functions cannot destroy the in-memory database during a test.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        object.__setattr__(self, '_conn', conn)

    # Make attribute access transparent
    def __getattr__(self, name: str):
        return getattr(object.__getattribute__(self, '_conn'), name)

    def __setattr__(self, name: str, value) -> None:
        setattr(object.__getattribute__(self, '_conn'), name, value)

    def close(self) -> None:
        """No-op: prevents signals_db from closing the test connection."""

    def real_close(self) -> None:
        """Actually close the underlying connection (called by fixture teardown)."""
        object.__getattribute__(self, '_conn').close()


@pytest.fixture
def mock_db():
    """In-memory SQLite database for testing.

    Returns a _NoCloseConnection so that signals_db functions calling
    conn.close() do not destroy the connection mid-test. The real close
    is called in fixture teardown.
    """
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    wrapper = _NoCloseConnection(conn)
    with patch('src.backend.db.signals_db.get_signals_connection', return_value=wrapper):
        yield wrapper
    wrapper.real_close()  # Actually close when fixture tears down


# ---------------------------------------------------------------------------
# TestSnapshotTableCreation  (TEST-09)
# ---------------------------------------------------------------------------

class TestSnapshotTableCreation:
    """Verify init_snapshot_tables creates both tables correctly."""

    def test_init_creates_onchain_snapshots_table(self, mock_db):
        """onchain_snapshots table should exist after init."""
        init_snapshot_tables()
        cursor = mock_db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='onchain_snapshots'"
        )
        row = cursor.fetchone()
        assert row is not None, "onchain_snapshots table was not created"

    def test_init_creates_ta_snapshots_table(self, mock_db):
        """ta_snapshots table should exist after init."""
        init_snapshot_tables()
        cursor = mock_db.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ta_snapshots'"
        )
        row = cursor.fetchone()
        assert row is not None, "ta_snapshots table was not created"

    def test_init_idempotent(self, mock_db):
        """Calling init_snapshot_tables twice should not raise any error."""
        init_snapshot_tables()
        init_snapshot_tables()  # Second call must not error (IF NOT EXISTS)

    def test_onchain_snapshots_has_expected_columns(self, mock_db):
        """onchain_snapshots should have all required columns."""
        init_snapshot_tables()
        cursor = mock_db.cursor()
        cursor.execute("PRAGMA table_info(onchain_snapshots)")
        columns = {row['name'] for row in cursor.fetchall()}
        expected_columns = {
            'id', 'symbol', 'timestamp',
            'exchange_flow_direction', 'exchange_flow_magnitude', 'exchange_flow_confidence',
            'smart_money_direction', 'smart_money_confidence',
            'whale_activity_direction', 'whale_activity_confidence',
            'top_pnl_bias', 'top_pnl_confidence',
            'fresh_wallets_level', 'fresh_wallets_trend',
            'funding_rate', 'funding_rate_available',
            'overall_bias', 'overall_confidence',
            'signal_count_bullish', 'signal_count_bearish',
            'reasoning', 'created_at',
        }
        missing = expected_columns - columns
        assert not missing, f"onchain_snapshots missing columns: {missing}"

    def test_ta_snapshots_has_expected_columns(self, mock_db):
        """ta_snapshots should have all required columns."""
        init_snapshot_tables()
        cursor = mock_db.cursor()
        cursor.execute("PRAGMA table_info(ta_snapshots)")
        columns = {row['name'] for row in cursor.fetchall()}
        expected_columns = {
            'id', 'symbol', 'timestamp',
            'weekly_direction', 'weekly_confidence', 'weekly_bias',
            'daily_direction', 'daily_confidence', 'daily_bias',
            'four_hour_direction', 'four_hour_confidence', 'four_hour_bias',
            'mentor_bias', 'mentor_confidence', 'mentor_confluence_score',
            'mentor_reasoning', 'created_at',
        }
        missing = expected_columns - columns
        assert not missing, f"ta_snapshots missing columns: {missing}"

    def test_existing_signals_table_untouched(self, mock_db):
        """init_snapshot_tables must not modify an existing signals table."""
        # Create a signals table with one row BEFORE calling init
        mock_db.execute(
            "CREATE TABLE signals (id INTEGER PRIMARY KEY, data TEXT)"
        )
        mock_db.execute("INSERT INTO signals (data) VALUES ('original')")
        mock_db.commit()

        init_snapshot_tables()

        cursor = mock_db.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM signals")
        count = cursor.fetchone()['cnt']
        assert count == 1, "signals table row count changed after init_snapshot_tables"

        cursor.execute("SELECT data FROM signals")
        row = cursor.fetchone()
        assert row['data'] == 'original', "signals table data was modified by init_snapshot_tables"


# ---------------------------------------------------------------------------
# TestSnapshotInserts  (TEST-10)
# ---------------------------------------------------------------------------

ONCHAIN_SNAPSHOT = {
    'symbol': 'BTC',
    'timestamp': '2026-03-01T10:00:00',
    'exchange_flow_direction': 'outflow',
    'exchange_flow_magnitude': 'high',
    'exchange_flow_confidence': 80,
    'smart_money_direction': 'accumulating',
    'smart_money_confidence': 75,
    'whale_activity_direction': 'accumulating',
    'whale_activity_confidence': 85,
    'top_pnl_bias': 'bullish',
    'top_pnl_confidence': 70,
    'fresh_wallets_level': 'high',
    'fresh_wallets_trend': 'increasing',
    'funding_rate': 0.0015,
    'funding_rate_available': True,
    'overall_bias': 'bullish',
    'overall_confidence': 80,
    'signal_count_bullish': 4,
    'signal_count_bearish': 1,
    'reasoning': 'Strong bullish on-chain signal',
}

TA_SNAPSHOT = {
    'symbol': 'ETH',
    'timestamp': '2026-03-01T12:00:00',
    'weekly_direction': 'bullish',
    'weekly_confidence': 75,
    'weekly_bias': 'bullish',
    'daily_direction': 'bullish',
    'daily_confidence': 65,
    'daily_bias': 'bullish',
    'four_hour_direction': 'neutral',
    'four_hour_confidence': 50,
    'four_hour_bias': 'neutral',
    'mentor_bias': 'bullish',
    'mentor_confidence': 70,
    'mentor_confluence_score': 80,
    'mentor_reasoning': 'Multi-timeframe bullish alignment',
}


class TestSnapshotInserts:
    """Verify insert functions write data and return valid IDs."""

    def test_insert_onchain_snapshot_returns_id(self, mock_db):
        """insert_onchain_snapshot should return an int > 0."""
        init_snapshot_tables()
        row_id = insert_onchain_snapshot(ONCHAIN_SNAPSHOT)
        assert isinstance(row_id, int), f"Expected int, got {type(row_id)}"
        assert row_id > 0, f"Expected positive row ID, got {row_id}"

    def test_insert_onchain_snapshot_data_persists(self, mock_db):
        """Inserted onchain snapshot values should be queryable from the table."""
        init_snapshot_tables()
        row_id = insert_onchain_snapshot(ONCHAIN_SNAPSHOT)

        cursor = mock_db.cursor()
        cursor.execute("SELECT * FROM onchain_snapshots WHERE id = ?", (row_id,))
        row = cursor.fetchone()
        assert row is not None, "Inserted row not found in onchain_snapshots"

        assert row['symbol'] == ONCHAIN_SNAPSHOT['symbol']
        assert row['timestamp'] == ONCHAIN_SNAPSHOT['timestamp']
        assert row['exchange_flow_direction'] == ONCHAIN_SNAPSHOT['exchange_flow_direction']
        assert row['exchange_flow_magnitude'] == ONCHAIN_SNAPSHOT['exchange_flow_magnitude']
        assert row['exchange_flow_confidence'] == ONCHAIN_SNAPSHOT['exchange_flow_confidence']
        assert row['smart_money_direction'] == ONCHAIN_SNAPSHOT['smart_money_direction']
        assert row['smart_money_confidence'] == ONCHAIN_SNAPSHOT['smart_money_confidence']
        assert row['whale_activity_direction'] == ONCHAIN_SNAPSHOT['whale_activity_direction']
        assert row['whale_activity_confidence'] == ONCHAIN_SNAPSHOT['whale_activity_confidence']
        assert row['top_pnl_bias'] == ONCHAIN_SNAPSHOT['top_pnl_bias']
        assert row['top_pnl_confidence'] == ONCHAIN_SNAPSHOT['top_pnl_confidence']
        assert row['fresh_wallets_level'] == ONCHAIN_SNAPSHOT['fresh_wallets_level']
        assert row['fresh_wallets_trend'] == ONCHAIN_SNAPSHOT['fresh_wallets_trend']
        assert abs(row['funding_rate'] - ONCHAIN_SNAPSHOT['funding_rate']) < 1e-9
        # funding_rate_available stored as 1 (True)
        assert row['funding_rate_available'] == 1
        assert row['overall_bias'] == ONCHAIN_SNAPSHOT['overall_bias']
        assert row['overall_confidence'] == ONCHAIN_SNAPSHOT['overall_confidence']
        assert row['signal_count_bullish'] == ONCHAIN_SNAPSHOT['signal_count_bullish']
        assert row['signal_count_bearish'] == ONCHAIN_SNAPSHOT['signal_count_bearish']
        assert row['reasoning'] == ONCHAIN_SNAPSHOT['reasoning']

    def test_insert_ta_snapshot_returns_id(self, mock_db):
        """insert_ta_snapshot should return an int > 0."""
        init_snapshot_tables()
        row_id = insert_ta_snapshot(TA_SNAPSHOT)
        assert isinstance(row_id, int), f"Expected int, got {type(row_id)}"
        assert row_id > 0, f"Expected positive row ID, got {row_id}"

    def test_insert_ta_snapshot_data_persists(self, mock_db):
        """Inserted TA snapshot values should be queryable from the table."""
        init_snapshot_tables()
        row_id = insert_ta_snapshot(TA_SNAPSHOT)

        cursor = mock_db.cursor()
        cursor.execute("SELECT * FROM ta_snapshots WHERE id = ?", (row_id,))
        row = cursor.fetchone()
        assert row is not None, "Inserted row not found in ta_snapshots"

        assert row['symbol'] == TA_SNAPSHOT['symbol']
        assert row['timestamp'] == TA_SNAPSHOT['timestamp']
        assert row['weekly_direction'] == TA_SNAPSHOT['weekly_direction']
        assert row['weekly_confidence'] == TA_SNAPSHOT['weekly_confidence']
        assert row['weekly_bias'] == TA_SNAPSHOT['weekly_bias']
        assert row['daily_direction'] == TA_SNAPSHOT['daily_direction']
        assert row['daily_confidence'] == TA_SNAPSHOT['daily_confidence']
        assert row['daily_bias'] == TA_SNAPSHOT['daily_bias']
        assert row['four_hour_direction'] == TA_SNAPSHOT['four_hour_direction']
        assert row['four_hour_confidence'] == TA_SNAPSHOT['four_hour_confidence']
        assert row['four_hour_bias'] == TA_SNAPSHOT['four_hour_bias']
        assert row['mentor_bias'] == TA_SNAPSHOT['mentor_bias']
        assert row['mentor_confidence'] == TA_SNAPSHOT['mentor_confidence']
        assert row['mentor_confluence_score'] == TA_SNAPSHOT['mentor_confluence_score']
        assert row['mentor_reasoning'] == TA_SNAPSHOT['mentor_reasoning']

    def test_insert_multiple_onchain_snapshots(self, mock_db):
        """Multiple onchain inserts should yield unique incrementing IDs and correct row count."""
        init_snapshot_tables()

        symbols = ['BTC', 'ETH', 'SOL']
        ids = []
        for symbol in symbols:
            data = dict(ONCHAIN_SNAPSHOT)
            data['symbol'] = symbol
            row_id = insert_onchain_snapshot(data)
            ids.append(row_id)

        # All IDs must be unique and positive
        assert len(set(ids)) == 3, f"Expected 3 unique IDs, got {ids}"
        assert all(i > 0 for i in ids), f"All IDs must be positive, got {ids}"
        # IDs should be strictly increasing (auto-increment)
        assert ids == sorted(ids), f"Expected ascending IDs, got {ids}"

        cursor = mock_db.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM onchain_snapshots")
        count = cursor.fetchone()['cnt']
        assert count == 3, f"Expected 3 rows, got {count}"

    def test_insert_multiple_ta_snapshots(self, mock_db):
        """Multiple TA inserts should yield unique IDs and correct row count."""
        init_snapshot_tables()

        symbols = ['BTC', 'ETH']
        ids = []
        for symbol in symbols:
            data = dict(TA_SNAPSHOT)
            data['symbol'] = symbol
            row_id = insert_ta_snapshot(data)
            ids.append(row_id)

        assert len(set(ids)) == 2, f"Expected 2 unique IDs, got {ids}"
        assert all(i > 0 for i in ids), f"All IDs must be positive, got {ids}"

        cursor = mock_db.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM ta_snapshots")
        count = cursor.fetchone()['cnt']
        assert count == 2, f"Expected 2 rows, got {count}"

    def test_insert_onchain_with_null_funding_rate(self, mock_db):
        """Insert with funding_rate=None should succeed and store NULL in the column."""
        init_snapshot_tables()
        data = dict(ONCHAIN_SNAPSHOT)
        data['funding_rate'] = None
        data['funding_rate_available'] = False

        row_id = insert_onchain_snapshot(data)
        assert row_id > 0, f"Expected positive row ID, got {row_id}"

        cursor = mock_db.cursor()
        cursor.execute("SELECT funding_rate, funding_rate_available FROM onchain_snapshots WHERE id = ?", (row_id,))
        row = cursor.fetchone()
        assert row['funding_rate'] is None, f"Expected NULL funding_rate, got {row['funding_rate']}"
        # funding_rate_available=False stores as 0
        assert row['funding_rate_available'] == 0
