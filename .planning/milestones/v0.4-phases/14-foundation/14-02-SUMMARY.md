---
phase: 14-foundation
plan: 02
subsystem: database
tags: [signals-db, snapshots, onchain-data, ta-data, persistence]
dependency_graph:
  requires:
    - settings.SIGNALS_DB_PATH
  provides:
    - onchain_snapshots table
    - ta_snapshots table
    - signals_db module
  affects:
    - Nansen agent (future output storage)
    - Telegram agent (future snapshot retrieval)
tech_stack:
  added:
    - sqlite3 (onchain_snapshots table)
    - sqlite3 (ta_snapshots table)
  patterns:
    - External database via settings path
    - Idempotent table creation (CREATE IF NOT EXISTS)
    - Row factory for dict-like results
key_files:
  created:
    - src/backend/db/signals_db.py
  modified:
    - src/backend/config/settings.py
    - src/backend/db/__init__.py
decisions:
  - External signals.db path with fallback default
  - Separate module for signals.db (vs extending schema.py)
  - Integer storage for boolean flags (funding_rate_available)
metrics:
  duration: 105s
  tasks_completed: 3
  files_created: 1
  files_modified: 2
  commits: 3
  completed_date: 2026-02-28
---

# Phase 14 Plan 02: Database Infrastructure for Agent Snapshots Summary

**One-liner:** Created signals_db module with onchain_snapshots and ta_snapshots tables for persistent Nansen and TA agent output storage using external signals.db

## Execution Report

**Status:** Complete
**Duration:** 105 seconds (1.75 minutes)
**Tasks:** 3/3 completed
**Verification:** All verification steps passed

## Tasks Completed

### Task 1: Update settings with correct signals.db path
**Commit:** 5c03dd6
**Files:** src/backend/config/settings.py

Updated SIGNALS_DB_PATH default from `data/signals.db` to `/Users/johnny_main/Developer/data/signals/signals.db` to point to external database location while maintaining env var override capability.

### Task 2: Create signals_db module with snapshot tables
**Commit:** 35cb1a0
**Files:** src/backend/db/signals_db.py

Created new signals_db module with:
- `get_signals_connection()`: Connection factory with row factory
- `init_snapshot_tables()`: Idempotent table creation for onchain_snapshots and ta_snapshots
- `insert_onchain_snapshot()`: Insert Nansen agent output (exchange flows, smart money, whale activity, top PnL, fresh wallets, funding rate, overall bias)
- `insert_ta_snapshot()`: Insert TA subagent output (weekly/daily/4H direction, confidence, bias, TAMentor confluence)

### Task 3: Update db module exports
**Commit:** a42a123
**Files:** src/backend/db/__init__.py

Added signals_db function exports to db module __init__.py, maintaining all existing schema.py exports.

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All verification steps passed:

1. Settings verification: `settings.SIGNALS_DB_PATH` correctly configured
2. Module imports: All signals_db functions import successfully
3. Table creation: `init_snapshot_tables()` executed successfully
4. Database inspection: Both tables exist with correct schemas
5. Existing signals table: Unchanged and intact

**Database state:**
- Tables: bot_controls, onchain_snapshots, signals, ta_snapshots
- onchain_snapshots: 19 columns (all Nansen signal fields)
- ta_snapshots: 14 columns (weekly/daily/4H + TAMentor fields)

## Key Decisions

1. **External database path:** Used absolute path `/Users/johnny_main/Developer/data/signals/signals.db` as default, with SIGNALS_DB_PATH env var override for flexibility
2. **Separate module:** Created signals_db.py instead of extending schema.py to maintain clear separation between titan.db (local) and signals.db (external)
3. **Integer booleans:** Stored `funding_rate_available` as INTEGER (1/0) for SQLite compatibility

## Success Criteria Verification

- [x] onchain_snapshots table exists in signals.db with all Nansen fields
- [x] ta_snapshots table exists in signals.db with weekly/daily/4h fields
- [x] Database path comes from settings.SIGNALS_DB_PATH
- [x] Tables created with CREATE TABLE IF NOT EXISTS (idempotent)
- [x] insert_onchain_snapshot and insert_ta_snapshot functions work
- [x] Existing signals table is untouched

## Impact

**Enables:**
- Nansen agent can persist on-chain analysis snapshots
- Telegram agent can retrieve historical snapshots for context
- Future analytics on agent output quality and confluence patterns

**Ready for:**
- Phase 14 Plan 03: Nansen agent implementation
- Phase 15: Telegram agent with snapshot retrieval

## Self-Check

Verifying created files and commits exist:

**Files created:**
- src/backend/db/signals_db.py: EXISTS

**Files modified:**
- src/backend/config/settings.py: EXISTS
- src/backend/db/__init__.py: EXISTS

**Commits:**
- 5c03dd6: EXISTS (chore: update SIGNALS_DB_PATH)
- 35cb1a0: EXISTS (feat: create signals_db module)
- a42a123: EXISTS (feat: export signals_db functions)

## Self-Check: PASSED
