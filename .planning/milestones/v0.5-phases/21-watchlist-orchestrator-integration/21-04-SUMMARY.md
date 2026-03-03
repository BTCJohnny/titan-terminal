---
phase: 21-watchlist-orchestrator-integration
plan: 04
subsystem: agents
tags: [orchestrator, pydantic, run_morning_batch, sort, regression-test]

# Dependency graph
requires:
  - phase: 21-watchlist-orchestrator-integration
    provides: "Plan 02 changed analyze_symbol() to return OrchestratorOutput; Plan 01 added run_morning_batch() with dict-style sort"
provides:
  - "_get_field() module-level helper for type-safe field extraction from OrchestratorOutput or error dict"
  - "Fixed run_morning_batch() sort/filter logic — no AttributeError on OrchestratorOutput"
  - "Two regression tests covering OrchestratorOutput-only and mixed-type result lists"
affects: [22-fastapi-endpoints, 24-integration-tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_get_field(item, field, default) helper: dispatches getattr vs .get() based on isinstance(item, dict)"
    - "Mixed-type result list pattern: append OrchestratorOutput on success, error dict on exception"

key-files:
  created: []
  modified:
    - src/backend/agents/orchestrator.py
    - src/backend/tests/test_watchlist.py

key-decisions:
  - "_get_field() placed at module level (not class method) — pure utility with no self dependency"
  - "Error dict path in run_morning_batch() preserved unchanged — both types now handled by _get_field()"

patterns-established:
  - "_get_field pattern: always use when iterating mixed OrchestratorOutput/dict results"

requirements-completed: [WTCH-01, WTCH-02, WTCH-03, INTG-04, INTG-05]

# Metrics
duration: 8min
completed: 2026-03-01
---

# Phase 21 Plan 04: run_morning_batch Sort Fix Summary

**Type-safe _get_field() helper fixes AttributeError crash when OrchestratorOutput instances (Pydantic) hit dict-style .get() calls in run_morning_batch() sort/filter block, with two regression tests covering OrchestratorOutput-only and mixed result lists**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-01T12:39:56Z
- **Completed:** 2026-03-01T12:48:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added module-level `_get_field(item, field, default)` helper that dispatches attribute access for OrchestratorOutput (Pydantic BaseModel) or `.get()` for error dicts
- Replaced three `.get()` calls in `run_morning_batch()` lines 413-417 with `_get_field()` calls — eliminates the AttributeError production blocker
- Added `test_run_morning_batch_sorts_orchestrator_output` — verifies descending confidence sort with real OrchestratorOutput instances without raising AttributeError
- Added `test_run_morning_batch_handles_mixed_results` — verifies mixed list (OrchestratorOutput + error dict) filters Avoid correctly and returns only actionable results
- All 10 test_watchlist.py tests pass; all 5 test_orchestrator.py tests pass (no regression)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix run_morning_batch() sort logic for mixed result types** - `416f623` (fix)
2. **Task 2: Add test for run_morning_batch with real OrchestratorOutput** - `f3cdb87` (test)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `src/backend/agents/orchestrator.py` - Added `_get_field()` helper at module level; replaced `.get()` calls in sort block with `_get_field()` calls
- `src/backend/tests/test_watchlist.py` - Added `test_run_morning_batch_sorts_orchestrator_output` and `test_run_morning_batch_handles_mixed_results` to `TestMergedWatchlist` class

## Decisions Made
- `_get_field()` placed at module level (not as a static method on Orchestrator) — pure utility function, no class dependency, cleaner import if needed elsewhere
- Error dict path in the `except` branch of `run_morning_batch()` left unchanged — the fix is in the sort/filter consumer, not the producer

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- run_morning_batch() is now production-safe for OrchestratorOutput return values from Plan 02
- WTCH-03 production blocker resolved — morning batch can sort mixed result lists without crashing
- Phase 22 (FastAPI Endpoints) can call run_morning_batch() safely via /morning-report endpoint
- Phase 24 (Integration Tests) can exercise run_morning_batch() end-to-end

## Self-Check: PASSED

- FOUND: src/backend/agents/orchestrator.py
- FOUND: src/backend/tests/test_watchlist.py
- FOUND: .planning/phases/21-watchlist-orchestrator-integration/21-04-SUMMARY.md
- FOUND commit: 416f623 (Task 1)
- FOUND commit: f3cdb87 (Task 2)

---
*Phase: 21-watchlist-orchestrator-integration*
*Completed: 2026-03-01*
