---
phase: 22-api-endpoints
plan: "01"
subsystem: api
tags: [fastapi, endpoints, orchestrator, schema, sqlite, testing]
dependency_graph:
  requires:
    - 21-04  # run_morning_batch sort fix and OrchestratorOutput return type
    - 21-02  # analyze_symbol returns OrchestratorOutput directly
  provides:
    - working /morning-report endpoint (real orchestrator data)
    - working /analyze/{symbol} endpoint (real orchestrator data)
    - upgraded signal_journal schema (paper-trading-ready)
  affects:
    - src/backend/api/main.py
    - src/backend/db/schema.py
    - src/backend/tests/test_api_endpoints.py
tech_stack:
  added: []
  patterns:
    - FastAPI response models mirroring OrchestratorOutput fields
    - isinstance() filtering to distinguish OrchestratorOutput vs error dicts
    - SQLite ALTER TABLE migration with try/except for existing databases
    - Dynamic module path detection for pytest namespace compatibility (_MODULE_PATH)
key_files:
  created:
    - src/backend/tests/test_api_endpoints.py
  modified:
    - src/backend/api/main.py
    - src/backend/db/schema.py
decisions:
  - No caching on /morning-report — always on-demand via run_morning_batch()
  - Top 5 results limit (valid OrchestratorOutput instances only, error dicts filtered)
  - pnl_percent not added as a separate column — outcome_pnl already serves this role with comment clarification
  - Dynamic _MODULE_PATH detection for patch paths to handle pytest vs direct-run namespace differences (backend.api.main vs src.backend.api.main)
metrics:
  duration: "~13 minutes"
  completed: "2026-03-01"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 3
  tests_added: 8
---

# Phase 22 Plan 01: API Endpoints — Real OrchestratorOutput Summary

Wired /morning-report and /analyze/{symbol} FastAPI endpoints to the real orchestrator pipeline (removing all random/simulated data), and upgraded signal_journal schema with paper-trading-ready fields (direction, entry_ideal, reasoning).

## What Was Built

### Task 1: SignalJournal Schema Upgrade

Added three new columns to `signal_journal` in `src/backend/db/schema.py`:
- `direction TEXT` — BULLISH/BEARISH/NO SIGNAL from OrchestratorOutput
- `entry_ideal REAL` — ideal entry price (from EntryZoneSimple.ideal)
- `reasoning TEXT` — full Mentor reasoning text (flat string version)

Added ALTER TABLE migration block (try/except pattern) for existing databases. Updated `record_signal()` to include all three new fields in the INSERT statement.

### Task 2: API Endpoint Rewrite

**`src/backend/api/main.py`** — Complete rewrite of endpoint logic:
- Removed all simulated/random data generation (`_clean_signal`, `_generate_narrative`, `_generate_market_context`, `_generate_whale_alerts`, `_generate_market_summary`, `_get_cached_report`)
- Removed dead response models (`Signal`, `WhaleAlert`, `MarketContext`, `MorningReportResponse` old version)
- Added `AnalyzeResponse` Pydantic model mirroring OrchestratorOutput fields
- Added new `MorningReportResponse` with `count` and `signals` list
- Added `_serialize_output()` helper converting OrchestratorOutput to response dict
- `/morning-report`: calls `orchestrator.run_morning_batch(market_data_fetcher=fetcher.fetch)`, filters OrchestratorOutput instances only, limits to top 5
- `/analyze/{symbol}`: calls `orchestrator.analyze_symbol(symbol.upper(), market_data)`, returns full AnalyzeResponse

**`src/backend/tests/test_api_endpoints.py`** — 8 new tests:
- `test_morning_report_returns_200` — status 200, count/signals/timestamp fields present
- `test_morning_report_signal_fields` — full field coverage (direction, confidence, reasoning, entry_zone, etc.)
- `test_morning_report_filters_error_dicts` — error dicts filtered from results
- `test_morning_report_max_5_results` — results capped at 5
- `test_analyze_btc_returns_200` — basic 200 check with symbol
- `test_analyze_response_includes_required_fields` — full field coverage for single symbol
- `test_analyze_symbol_uppercased` — verifies symbol.upper() called on orchestrator and fetcher
- `test_morning_report_empty_results` — empty result list handled gracefully

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Schema rewrite contained duplicate outcome tracking section**
- **Found during:** Task 1 initial edit
- **Issue:** The Edit tool inserted the paper-trading fields section between the existing outcome tracking section and the Metadata section, accidentally duplicating the outcome fields
- **Fix:** Full file rewrite with clean schema structure
- **Files modified:** src/backend/db/schema.py
- **Commit:** 663f9b3

**2. [Rule 1 - Bug] pytest module namespace difference broke @patch decorator paths**
- **Found during:** Task 2 test development
- **Issue:** pytest loads the module under `backend.api.main` namespace (with `src/` on sys.path), but patch paths used `src.backend.api.main.get_orchestrator`. This caused the real Orchestrator to run during tests instead of the mock, returning 6 real error dicts from the watchlist instead of the mocked OrchestratorOutput instances.
- **Fix:** Added `_MODULE_PATH` dynamic detection at test module import time:
  ```python
  _main_module = sys.modules.get("src.backend.api.main") or sys.modules.get("backend.api.main")
  _MODULE_PATH = _main_module.__name__
  ```
  All `patch()` calls use `f"{_MODULE_PATH}.get_orchestrator"` instead of hardcoded paths.
- **Files modified:** src/backend/tests/test_api_endpoints.py
- **Commit:** 27ea9de

## Verification Results

```
$ python -m pytest src/backend/tests/test_api_endpoints.py -x -v
8 passed in 1.36s

$ python -c "from src.backend.db.schema import init_db; init_db()"
Database initialized at .../titan.db

$ python -c "from src.backend.api.main import app; print('API imports OK')"
API imports OK

# No random.uniform/randint/choice calls in api/main.py
Has random calls: False
```

## Self-Check

- [x] `src/backend/tests/test_api_endpoints.py` — FOUND
- [x] `src/backend/api/main.py` — FOUND
- [x] `src/backend/db/schema.py` — FOUND
- [x] Commit 663f9b3 — FOUND (feat(22-01): upgrade SignalJournal schema)
- [x] Commit 27ea9de — FOUND (feat(22-01): rewrite API endpoints)

## Self-Check: PASSED
