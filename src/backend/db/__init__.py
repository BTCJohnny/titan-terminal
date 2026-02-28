"""Database module for Titan Terminal."""
from .schema import (
    init_db,
    get_connection,
    record_signal,
    update_outcome,
    get_similar_patterns,
    get_pattern_stats,
    get_recent_signals,
)
from .signals_db import (
    get_signals_connection,
    init_snapshot_tables,
    insert_onchain_snapshot,
    insert_ta_snapshot,
)

__all__ = [
    'init_db',
    'get_connection',
    'record_signal',
    'update_outcome',
    'get_similar_patterns',
    'get_pattern_stats',
    'get_recent_signals',
    'get_signals_connection',
    'init_snapshot_tables',
    'insert_onchain_snapshot',
    'insert_ta_snapshot',
]
