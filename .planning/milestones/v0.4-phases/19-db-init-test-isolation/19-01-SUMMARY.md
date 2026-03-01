---
phase: 19-db-init-test-isolation
plan: 01
subsystem: database, testing
tags: [sqlite, fastapi, startup, vault-logger, pytest, mocking]

# Dependency graph
requires:
  - phase: 15-nansen-agent
    provides: NansenAgent with vault_logger and insert_onchain_snapshot integration
  - phase: 18-orchestrator-integration-fixes
    provides: Working orchestrator + nansen_agent analyze() integration
provides:
  - init_snapshot_tables() called at FastAPI startup — onchain_snapshots and ta_snapshots tables created on fresh DB
  - NANSEN_VAULT_PATH configurable via env var in Settings class
  - nansen_agent.py reads vault path from settings, overrides vault_logger.VAULT_PATH at module load
  - All analyze()-calling tests mock insert_onchain_snapshot — no real signals.db writes during test runs
affects: [20-any-future-nansen-phase, any-test-phase touching nansen_agent]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Startup hook pattern: add new init functions to FastAPI startup event in sequence after init_db()
    - Settings pattern: all path-based config lives in Settings class with os.getenv default
    - Module-level override pattern: import vault_logger as module, override VAULT_PATH/SIGNAL_LOG_FILE attributes after import
    - Outermost-decorator-is-last-param: @patch decorators applied bottom-to-top, passed as params left-to-right

key-files:
  created: []
  modified:
    - src/backend/api/main.py
    - src/backend/config/settings.py
    - src/backend/agents/nansen_agent.py
    - src/backend/tests/test_nansen_agent.py

key-decisions:
  - "Module-level vault_logger override in nansen_agent.py: import vault_logger as module, set VAULT_PATH and SIGNAL_LOG_FILE attributes — keeps vault_logger.py untouched"
  - "NANSEN_VAULT_PATH added to Settings class with same hardcoded default as vault_logger.py — overridable via env var"

patterns-established:
  - "Startup init sequence: init_db() then init_snapshot_tables() — safe to call on every startup"
  - "Test isolation: all analyze() tests must mock insert_onchain_snapshot to prevent real DB writes"

requirements-completed: [DB-01, DB-02]

# Metrics
duration: 5min
completed: 2026-03-01
---

# Phase 19 Plan 01: DB Init & Test Isolation Summary

**FastAPI startup now calls init_snapshot_tables(), VAULT_PATH loaded from NANSEN_VAULT_PATH env var in settings, and all analyze() tests mock insert_onchain_snapshot for full DB isolation**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-01T00:00:00Z
- **Completed:** 2026-03-01T00:05:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Wired `init_snapshot_tables()` into FastAPI startup event so `onchain_snapshots` and `ta_snapshots` tables are created on any fresh database
- Added `NANSEN_VAULT_PATH` to the `Settings` class with env var override support, replacing the hardcoded path in `vault_logger.py`
- `nansen_agent.py` now overrides `vault_logger.VAULT_PATH` and `vault_logger.SIGNAL_LOG_FILE` at module load from `settings.NANSEN_VAULT_PATH`
- Added `@patch('src.backend.agents.nansen_agent.insert_onchain_snapshot')` to all 3 `analyze()`-calling tests — no test touches real `signals.db`

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire init_snapshot_tables() at startup and move VAULT_PATH to settings** - `5034339` (feat)
2. **Task 2: Mock insert_onchain_snapshot in Nansen agent test file** - `7492ecb` (test)

## Files Created/Modified
- `src/backend/api/main.py` - Added `init_snapshot_tables` import and call in startup event
- `src/backend/config/settings.py` - Added `NANSEN_VAULT_PATH` setting with env var default
- `src/backend/agents/nansen_agent.py` - Import settings, expose `VAULT_PATH`, override vault_logger module attributes
- `src/backend/tests/test_nansen_agent.py` - Added `insert_onchain_snapshot` mock to 3 analyze()-calling tests

## Decisions Made
- Module-level override approach for vault_logger: `import vault_logger as vault_logger_mod`, then set `vault_logger_mod.VAULT_PATH` and `vault_logger_mod.SIGNAL_LOG_FILE` from settings — this keeps `vault_logger.py` untouched while making the path configurable
- `NANSEN_VAULT_PATH` default matches the existing hardcoded path in `vault_logger.py` to preserve backward compatibility

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. Set `NANSEN_VAULT_PATH` env var to override the vault path (optional).

## Next Phase Readiness
- DB initialization gap (DB-01, DB-02) fully closed
- Nansen agent tests are fully isolated from production databases
- Phase 19 plan 01 complete — no outstanding blockers

## Self-Check: PASSED

All files verified present. Both task commits verified in git log.

---
*Phase: 19-db-init-test-isolation*
*Completed: 2026-03-01*
