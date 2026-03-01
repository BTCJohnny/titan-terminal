---
phase: 20-risk-agent
plan: 03
subsystem: api
tags: [pydantic, risk, orchestrator, python, typing]

# Dependency graph
requires:
  - phase: 20-01
    provides: "RiskOutput Pydantic model and deterministic RiskAgent.analyze() interface"
provides:
  - "Orchestrator wired to RiskAgent returning typed RiskOutput (not raw dict)"
  - "Orchestrator _synthesize_results uses RiskOutput attribute access throughout"
  - "approved and rejection_reasons surfaced in final synthesis output"
  - "Orchestrator tests updated with _make_risk_output() helper and RiskOutput mocks"
affects:
  - 21-orchestrator
  - 22-api
  - 24-integration-tests

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pydantic attribute access over dict .get(): typed models eliminate runtime key errors"
    - "model_dump(mode='json') for Pydantic-to-JSON serialization in journal/logging contexts"
    - "Test helper factory pattern: _make_risk_output() centralizes valid mock creation"

key-files:
  created: []
  modified:
    - src/backend/agents/orchestrator.py
    - src/backend/tests/test_orchestrator.py

key-decisions:
  - "Orchestrator type hints updated: risk parameter is now RiskOutput, not dict — catches misuse at type-check time"
  - "approved and rejection_reasons added to synthesis output — callers now see trade approval status without digging into three_laws_check"
  - "_record_to_journal uses risk.model_dump(mode='json') — Pydantic models are not JSON-serializable by default"

patterns-established:
  - "When wiring a Pydantic model into an existing dict-based consumer, update type hints, remove all .get() calls, and use .model_dump() for serialization contexts"
  - "Test helper factories (e.g., _make_risk_output) reduce duplication and make test intent clearer than inline dicts"

requirements-completed:
  - RISK-01
  - RISK-06

# Metrics
duration: 2min
completed: 2026-03-01
---

# Phase 20 Plan 03: Orchestrator RiskOutput Integration Summary

**Orchestrator now consumes typed RiskOutput Pydantic model: all dict .get() calls replaced with attribute access, approved/rejection_reasons surfaced in synthesis, tests updated with _make_risk_output() factory**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-01T11:34:53Z
- **Completed:** 2026-03-01T11:36:34Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Replaced all `risk.get('key', {})` dict access patterns with direct `risk.attribute` Pydantic attribute access in `_synthesize_results`
- Updated `_record_to_journal` to use `risk.model_dump(mode='json')` for correct JSON serialization of Pydantic model
- Added `open_position_count` and `account_size` explicitly to `risk_context` dict for deterministic Law 3 and Law 1 enforcement
- Added `approved` and `rejection_reasons` fields to the synthesis output dict — callers no longer need to inspect `three_laws_check` manually
- Updated orchestrator tests: added `_make_risk_output()` helper and replaced raw dict mock with typed `RiskOutput` instance; both tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Update Orchestrator to consume RiskOutput model** - `8678818` (feat)
2. **Task 2: Update orchestrator tests with RiskOutput mocks** - `1d784aa` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `src/backend/agents/orchestrator.py` - Added RiskOutput import; updated risk_context with open_position_count/account_size; _synthesize_results type hint and attribute access; _record_to_journal uses model_dump(mode='json')
- `src/backend/tests/test_orchestrator.py` - Added RiskOutput imports; added _make_risk_output() helper factory; updated risk.analyze mock to return RiskOutput instance

## Decisions Made
- Orchestrator `risk` parameter type hint changed from `dict` to `RiskOutput` in both `_synthesize_results` and `_record_to_journal` — enforces correct usage at development time
- `approved` and `rejection_reasons` added to synthesis dict — these are important trade-gate fields that calling code (API, dashboard) needs without re-parsing `three_laws_check`
- Used `model_dump(mode='json')` rather than `model_dump()` to handle float/datetime serialization edge cases in the journal JSON column

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Orchestrator is fully wired to typed RiskOutput — Phase 21 (Orchestrator Integration) can consume the end-to-end pipeline
- The full import chain works: orchestrator -> risk_agent -> risk_output model
- All 2 orchestrator tests and all 29 risk agent tests pass with no regressions

## Self-Check: PASSED

- src/backend/agents/orchestrator.py: FOUND
- src/backend/tests/test_orchestrator.py: FOUND
- .planning/phases/20-risk-agent/20-03-SUMMARY.md: FOUND
- Task 1 commit 8678818: FOUND
- Task 2 commit 1d784aa: FOUND

---
*Phase: 20-risk-agent*
*Completed: 2026-03-01*
