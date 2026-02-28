"""Signals database operations for on-chain and TA snapshots.

Uses external signals.db database (path from settings).
Creates onchain_snapshots and ta_snapshots tables for agent output storage.
IMPORTANT: Never modifies existing signals table.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.backend.config.settings import settings


def get_signals_connection() -> sqlite3.Connection:
    """Get connection to signals.db with row factory."""
    db_path = Path(settings.SIGNALS_DB_PATH)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_snapshot_tables() -> None:
    """Initialize snapshot tables (safe to run on every startup)."""
    conn = get_signals_connection()
    cursor = conn.cursor()

    # onchain_snapshots - stores Nansen agent outputs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS onchain_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TEXT NOT NULL,

            -- Exchange flows
            exchange_flow_direction TEXT,
            exchange_flow_magnitude TEXT,
            exchange_flow_confidence INTEGER,

            -- Smart money
            smart_money_direction TEXT,
            smart_money_confidence INTEGER,

            -- Whale activity
            whale_activity_direction TEXT,
            whale_activity_confidence INTEGER,

            -- Top PnL
            top_pnl_bias TEXT,
            top_pnl_confidence INTEGER,

            -- Fresh wallets
            fresh_wallets_level TEXT,
            fresh_wallets_trend TEXT,

            -- Funding rate
            funding_rate REAL,
            funding_rate_available INTEGER,

            -- Overall
            overall_bias TEXT,
            overall_confidence INTEGER,
            signal_count_bullish INTEGER,
            signal_count_bearish INTEGER,
            reasoning TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ta_snapshots - stores TA subagent outputs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ta_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TEXT NOT NULL,

            -- Weekly TA
            weekly_direction TEXT,
            weekly_confidence INTEGER,
            weekly_bias TEXT,

            -- Daily TA
            daily_direction TEXT,
            daily_confidence INTEGER,
            daily_bias TEXT,

            -- 4H TA
            four_hour_direction TEXT,
            four_hour_confidence INTEGER,
            four_hour_bias TEXT,

            -- TAMentor overall
            mentor_bias TEXT,
            mentor_confidence INTEGER,
            mentor_confluence_score INTEGER,
            mentor_reasoning TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def insert_onchain_snapshot(snapshot_data: dict) -> int:
    """Insert on-chain snapshot and return ID."""
    conn = get_signals_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO onchain_snapshots (
            symbol, timestamp,
            exchange_flow_direction, exchange_flow_magnitude, exchange_flow_confidence,
            smart_money_direction, smart_money_confidence,
            whale_activity_direction, whale_activity_confidence,
            top_pnl_bias, top_pnl_confidence,
            fresh_wallets_level, fresh_wallets_trend,
            funding_rate, funding_rate_available,
            overall_bias, overall_confidence,
            signal_count_bullish, signal_count_bearish, reasoning
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        snapshot_data.get('symbol'),
        snapshot_data.get('timestamp', datetime.utcnow().isoformat()),
        snapshot_data.get('exchange_flow_direction'),
        snapshot_data.get('exchange_flow_magnitude'),
        snapshot_data.get('exchange_flow_confidence'),
        snapshot_data.get('smart_money_direction'),
        snapshot_data.get('smart_money_confidence'),
        snapshot_data.get('whale_activity_direction'),
        snapshot_data.get('whale_activity_confidence'),
        snapshot_data.get('top_pnl_bias'),
        snapshot_data.get('top_pnl_confidence'),
        snapshot_data.get('fresh_wallets_level'),
        snapshot_data.get('fresh_wallets_trend'),
        snapshot_data.get('funding_rate'),
        1 if snapshot_data.get('funding_rate_available', True) else 0,
        snapshot_data.get('overall_bias'),
        snapshot_data.get('overall_confidence'),
        snapshot_data.get('signal_count_bullish'),
        snapshot_data.get('signal_count_bearish'),
        snapshot_data.get('reasoning'),
    ))

    snapshot_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return snapshot_id


def insert_ta_snapshot(snapshot_data: dict) -> int:
    """Insert TA snapshot and return ID."""
    conn = get_signals_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ta_snapshots (
            symbol, timestamp,
            weekly_direction, weekly_confidence, weekly_bias,
            daily_direction, daily_confidence, daily_bias,
            four_hour_direction, four_hour_confidence, four_hour_bias,
            mentor_bias, mentor_confidence, mentor_confluence_score, mentor_reasoning
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        snapshot_data.get('symbol'),
        snapshot_data.get('timestamp', datetime.utcnow().isoformat()),
        snapshot_data.get('weekly_direction'),
        snapshot_data.get('weekly_confidence'),
        snapshot_data.get('weekly_bias'),
        snapshot_data.get('daily_direction'),
        snapshot_data.get('daily_confidence'),
        snapshot_data.get('daily_bias'),
        snapshot_data.get('four_hour_direction'),
        snapshot_data.get('four_hour_confidence'),
        snapshot_data.get('four_hour_bias'),
        snapshot_data.get('mentor_bias'),
        snapshot_data.get('mentor_confidence'),
        snapshot_data.get('mentor_confluence_score'),
        snapshot_data.get('mentor_reasoning'),
    ))

    snapshot_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return snapshot_id
