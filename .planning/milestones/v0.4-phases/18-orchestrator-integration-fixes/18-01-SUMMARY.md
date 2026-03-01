---
phase: 18-orchestrator-integration-fixes
plan: 01
subsystem: orchestrator
tags: [pydantic, integration, bug-fix, nansen-agent, signals-db]
dependency_graph:
  requires: []
  provides: [orchestrator-end-to-end, nansen-snapshot-storage, signals-db-relative-import]
  affects: [orchestrator.py, nansen_agent.py, signals_db.py, test_orchestrator.py]
tech_stack:
  added: []
  patterns: [pydantic-model-dump-json, attribute-access-on-pydantic-models]
key_files:
  created: []
  modified:
    - src/backend/agents/orchestrator.py
    - src/backend/agents/nansen_agent.py
    - src/backend/db/signals_db.py
    - src/backend/tests/test_orchestrator.py
decisions:
  - Use model_dump(mode='json') instead of model_dump() for JSON serialization to handle datetime fields
  - market_data parameter in NansenAgent.analyze() is intentionally unused - agent fetches own data via CLI
metrics:
  duration: 3 min
  completed_date: "2026-03-01"
  tasks_completed: 3
  files_modified: 4
---

# Phase 18 Plan 01: Orchestrator Integration Fixes Summary

**One-liner:** Fixed all INT-01 through INT-04 integration bugs so orchestrator.analyze_symbol() runs end-to-end without AttributeError, TypeError, or missing snapshot storage.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix orchestrator Pydantic model access and serialization | f8aaa77 | src/backend/agents/orchestrator.py |
| 2 | Fix NansenAgent.analyze() signature and wire snapshot storage | 2f95ac1 | src/backend/agents/nansen_agent.py |
| 3 | Fix signals_db.py import style | 9ac1d3c | src/backend/db/signals_db.py |

## What Was Built

Fixed three root-cause integration bugs identified in the v0.4 milestone audit (INT-01 through INT-04):

**INT-01 (Pydantic dict-access):** `_synthesize_results()` was calling `.get()` on `NansenSignal` and `TelegramSignal` Pydantic model instances as if they were dicts. Fixed by switching to attribute access: `nansen.overall_signal`, `nansen_overall.bias`, `nansen_overall.confidence`, `nansen_overall.key_insights`, `telegram.confidence`, and `[s.model_dump() for s in telegram.relevant_signals]`.

**INT-01b (JSON serialization):** `_record_to_journal()` was calling `json.dumps(nansen)` and `json.dumps(telegram)` directly on Pydantic models. Fixed with `json.dumps(nansen.model_dump(mode='json'))` and `json.dumps(telegram.model_dump(mode='json'))`. Used `mode='json'` to serialize datetime fields as ISO strings.

**INT-02 (Signature mismatch):** `NansenAgent.analyze()` had signature `(self, symbol, log_to_vault=True)` but the orchestrator calls it as `self.nansen.analyze(symbol, market_data)`. Fixed by adding `market_data: dict = None` as the second parameter. Parameter is intentionally unused - NansenAgent fetches its own data via CLI/MCP.

**INT-03 (Snapshot storage never triggered):** Added `insert_onchain_snapshot()` call in `NansenAgent.analyze()` after NansenSignal construction, mapping all signal fields to the snapshot schema. Wrapped in try/except so storage failure does not block signal return.

**INT-04 (Absolute import):** `signals_db.py` used `from src.backend.config.settings import settings` (absolute). Fixed to `from ..config.settings import settings` (relative) matching all other backend modules.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] datetime serialization failure in model_dump()**
- **Found during:** Task 1 verification (running orchestrator smoke test)
- **Issue:** `json.dumps(nansen.model_dump())` raises `TypeError: Object of type datetime is not JSON serializable` because Pydantic's `model_dump()` returns Python `datetime` objects by default
- **Fix:** Changed to `model_dump(mode='json')` which serializes datetime fields to ISO strings
- **Files modified:** src/backend/agents/orchestrator.py
- **Commit:** 0167dc1

**2. [Rule 1 - Bug] Orchestrator smoke test mocking plain dicts instead of Pydantic models**
- **Found during:** Task 1 verification (running full test suite post-fix)
- **Issue:** `test_orchestrator_smoke` mocked `nansen.analyze` and `telegram.analyze` to return plain dicts, which worked before but now fails because `_synthesize_results` correctly uses attribute access on Pydantic models
- **Fix:** Updated test to create actual `NansenSignal` and `TelegramSignal` Pydantic model instances as mock return values
- **Files modified:** src/backend/tests/test_orchestrator.py
- **Commit:** 0167dc1

**Pre-existing failure noted (not fixed - out of scope):**
- `test_ta_subagents.py::TestDailySubagent::test_daily_subagent_smoke` fails with `AttributeError: DailySubagent does not have the attribute '_call_claude'` - pre-existed before this plan's changes, deferred to separate plan.

## Verification Results

```
All integration checks passed:
- NansenAgent.analyze() signature: (self, symbol, market_data=None, log_to_vault=True)
- _synthesize_results: no .get() calls on nansen or telegram
- _record_to_journal: model_dump() present

Test results: 212 passed, 1 pre-existing failure (test_ta_subagents, unrelated)
```

## Self-Check: PASSED

Files exist:
- FOUND: src/backend/agents/orchestrator.py
- FOUND: src/backend/agents/nansen_agent.py
- FOUND: src/backend/db/signals_db.py
- FOUND: src/backend/tests/test_orchestrator.py

Commits exist:
- FOUND: f8aaa77 (Task 1 - orchestrator Pydantic model access)
- FOUND: 2f95ac1 (Task 2 - NansenAgent signature + snapshot storage)
- FOUND: 9ac1d3c (Task 3 - signals_db relative import)
- FOUND: 0167dc1 (Auto-fix - model_dump mode=json + test update)
