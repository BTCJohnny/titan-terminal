"""SQLite database schema for Titan Terminal."""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "titan.db"


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database with all tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # SignalJournal - core self-learning table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_journal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            timeframe TEXT NOT NULL,

            -- Scores
            accumulation_score INTEGER,
            distribution_score INTEGER,
            confidence INTEGER NOT NULL,

            -- Wyckoff analysis
            wyckoff_phase TEXT,
            wyckoff_notes TEXT,

            -- Action and levels
            suggested_action TEXT NOT NULL,
            entry_zone_low REAL,
            entry_zone_high REAL,
            stop_loss REAL,
            tp1 REAL,
            tp2 REAL,
            risk_reward REAL,

            -- Agent contributions (JSON)
            nansen_data TEXT,
            telegram_data TEXT,
            wyckoff_data TEXT,
            ta_data TEXT,
            risk_data TEXT,
            mentor_critique TEXT,

            -- Paper-trading-ready fields
            direction TEXT,  -- BULLISH/BEARISH/NO SIGNAL (from OrchestratorOutput.direction)
            entry_ideal REAL,  -- ideal entry price (midpoint of entry_zone)
            reasoning TEXT,  -- full Mentor reasoning text (flat text version)

            -- Outcome tracking (self-learning)
            outcome TEXT,  -- 'win', 'loss', 'breakeven', 'skipped'
            outcome_pnl REAL,  -- outcome PnL as percentage (pnl_percent for paper trading)
            outcome_notes TEXT,
            outcome_timestamp TEXT,

            -- Metadata
            batch_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration: add columns for existing databases
    # (SQLite does not support ALTER TABLE IF NOT EXISTS — use try/except)
    for col_def in [
        "ALTER TABLE signal_journal ADD COLUMN direction TEXT",
        "ALTER TABLE signal_journal ADD COLUMN entry_ideal REAL",
        "ALTER TABLE signal_journal ADD COLUMN reasoning TEXT",
    ]:
        try:
            cursor.execute(col_def)
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Past patterns cache for self-learning
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pattern_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            symbol TEXT,
            conditions TEXT NOT NULL,  -- JSON of matching conditions
            outcome_win_count INTEGER DEFAULT 0,
            outcome_loss_count INTEGER DEFAULT 0,
            avg_pnl REAL DEFAULT 0,
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Chat history for persistent conversations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,  -- 'user' or 'assistant'
            content TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Telegram signals (from titan-trading)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telegram_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL,
            message_id INTEGER,
            content TEXT NOT NULL,
            parsed_symbol TEXT,
            parsed_action TEXT,
            parsed_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")


def record_signal(signal_data: dict) -> int:
    """Record a new signal to the journal."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO signal_journal (
            symbol, timestamp, timeframe,
            accumulation_score, distribution_score, confidence,
            wyckoff_phase, wyckoff_notes,
            suggested_action, entry_zone_low, entry_zone_high,
            stop_loss, tp1, tp2, risk_reward,
            nansen_data, telegram_data, wyckoff_data, ta_data, risk_data,
            mentor_critique, direction, entry_ideal, reasoning, batch_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signal_data.get('symbol'),
        signal_data.get('timestamp', datetime.now().isoformat()),
        signal_data.get('timeframe', 'D'),
        signal_data.get('accumulation_score'),
        signal_data.get('distribution_score'),
        signal_data.get('confidence', 50),
        signal_data.get('wyckoff_phase'),
        signal_data.get('wyckoff_notes'),
        signal_data.get('suggested_action'),
        signal_data.get('entry_zone_low'),
        signal_data.get('entry_zone_high'),
        signal_data.get('stop_loss'),
        signal_data.get('tp1'),
        signal_data.get('tp2'),
        signal_data.get('risk_reward'),
        signal_data.get('nansen_data'),
        signal_data.get('telegram_data'),
        signal_data.get('wyckoff_data'),
        signal_data.get('ta_data'),
        signal_data.get('risk_data'),
        signal_data.get('mentor_critique'),
        signal_data.get('direction'),
        signal_data.get('entry_ideal'),
        signal_data.get('reasoning'),
        signal_data.get('batch_id'),
    ))

    signal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return signal_id


def update_outcome(signal_id: int, outcome: str, pnl: float = None, notes: str = None):
    """Update signal outcome for self-learning."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE signal_journal
        SET outcome = ?, outcome_pnl = ?, outcome_notes = ?, outcome_timestamp = ?
        WHERE id = ?
    """, (outcome, pnl, notes, datetime.now().isoformat(), signal_id))

    conn.commit()
    conn.close()


def get_similar_patterns(symbol: str = None, wyckoff_phase: str = None, limit: int = 10) -> list:
    """Get past similar signals for self-learning context."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM signal_journal WHERE outcome IS NOT NULL"
    params = []

    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)
    if wyckoff_phase:
        query += " AND wyckoff_phase = ?"
        params.append(wyckoff_phase)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_pattern_stats(pattern_type: str, conditions: dict) -> dict:
    """Get win/loss stats for a pattern type."""
    conn = get_connection()
    cursor = conn.cursor()

    # Simplified pattern matching
    cursor.execute("""
        SELECT * FROM pattern_memory
        WHERE pattern_type = ?
    """, (pattern_type,))

    row = cursor.fetchone()
    conn.close()

    if row:
        total = row['outcome_win_count'] + row['outcome_loss_count']
        win_rate = row['outcome_win_count'] / total if total > 0 else 0
        return {
            'pattern_type': pattern_type,
            'win_count': row['outcome_win_count'],
            'loss_count': row['outcome_loss_count'],
            'win_rate': win_rate,
            'avg_pnl': row['avg_pnl']
        }
    return None


def get_recent_signals(limit: int = 20) -> list:
    """Get recent signals from journal."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM signal_journal
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


if __name__ == "__main__":
    init_db()
