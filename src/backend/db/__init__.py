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

__all__ = [
    'init_db',
    'get_connection',
    'record_signal',
    'update_outcome',
    'get_similar_patterns',
    'get_pattern_stats',
    'get_recent_signals',
]
