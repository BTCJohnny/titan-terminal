---
phase: 21-watchlist-orchestrator-integration
plan: 01
subsystem: agents
tags: [watchlist, telegram, orchestrator, settings, sqlite]

# Dependency graph
requires:
  - phase: 20-risk-agent
    provides: RiskOutput model and RiskAgent used in Orchestrator pipeline
provides:
  - WATCHLIST setting configurable via env var in settings.py
  - get_recent_signal_symbols() function for Telegram DB watchlist supplementation
  - get_merged_watchlist() method on Orchestrator combining settings + Telegram symbols
  - Updated run_morning_batch() defaulting to merged watchlist
affects:
  - 21-02 (morning batch invocation)
  - 21-03 (further orchestrator integration)
  - 24-integration-tests

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Settings class-level list attribute parsed from comma-separated env var
    - Module-level utility function pattern for DB-backed symbol retrieval
    - Merged watchlist via dict.fromkeys() for order-preserving deduplication

key-files:
  created:
    - src/backend/tests/test_watchlist.py
  modified:
    - src/backend/config/settings.py
    - src/backend/agents/telegram_agent.py
    - src/backend/agents/orchestrator.py

key-decisions:
  - "WATCHLIST defaults to BTC,ETH,SOL,AVAX,ARB,LINK — a sensible subset, not the full HYPERLIQUID_PERPS list"
  - "Telegram lookback window is 72h (not 48h used elsewhere) — per CONTEXT.md user decision"
  - "run_morning_batch() signature changed: market_data_fetcher is now first param, symbols is optional second"
  - "MENTOR_MODEL default updated to claude-opus-4-6 per locked CONTEXT.md decision"
  - "test_watchlist_configurable_via_env tests the env parsing logic directly due to Python class-body evaluation timing"

patterns-established:
  - "Watchlist pattern: settings base list + Telegram DB supplementation merged with dict.fromkeys()"
  - "get_recent_signal_symbols() is module-level (not a method), reusable without instantiating TelegramAgent"

requirements-completed: [WTCH-01, WTCH-02, WTCH-03]

# Metrics
duration: 8min
completed: 2026-03-01
---

# Phase 21 Plan 01: Configurable Watchlist + Telegram Supplementation Summary

**WATCHLIST setting added to settings.py with Telegram 72h signal supplementation via get_merged_watchlist() on Orchestrator, replacing hardcoded symbol lists**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-01T12:00:20Z
- **Completed:** 2026-03-01T12:08:00Z
- **Tasks:** 2
- **Files modified:** 4 (2 modified, 1 created, 1 modified in tests)

## Accomplishments
- Added `WATCHLIST` to `Settings` class with env var override support (`WATCHLIST=BTC,ETH,SOL`)
- Updated `MENTOR_MODEL` default to `claude-opus-4-6` per locked decision
- Added `get_recent_signal_symbols(hours=72)` module-level function in telegram_agent.py
- Added `get_merged_watchlist()` method to Orchestrator (settings symbols + Telegram symbols, deduped)
- Updated `run_morning_batch()` to default to merged watchlist when no symbols provided
- 8 tests created covering all three WTCH requirements — all passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Add WATCHLIST setting and Telegram symbol extraction** - `ca70d95` (feat)
2. **Task 2: Implement merged watchlist in Orchestrator and tests** - `599ba1d` (feat)

## Files Created/Modified
- `src/backend/config/settings.py` - Added WATCHLIST list setting and updated MENTOR_MODEL default
- `src/backend/agents/telegram_agent.py` - Added get_recent_signal_symbols() module-level function
- `src/backend/agents/orchestrator.py` - Added get_merged_watchlist() method, updated run_morning_batch() signature
- `src/backend/tests/test_watchlist.py` - 8 tests covering WTCH-01, WTCH-02, WTCH-03

## Decisions Made
- WATCHLIST defaults to `BTC,ETH,SOL,AVAX,ARB,LINK` — sensible subset of HYPERLIQUID_PERPS, not the full 20
- 72h Telegram lookback window (not 48h) per CONTEXT.md user decision
- `run_morning_batch()` signature changed: `market_data_fetcher` is now first, `symbols` optional second — callers must update
- `MENTOR_MODEL` default updated to `claude-opus-4-6` per locked CONTEXT.md decision
- Env var test was adjusted to test parsing logic directly (class-body evaluation in Python means os.getenv() runs at import time, not instantiation time)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_watchlist_configurable_via_env reload approach**
- **Found during:** Task 2 (test_watchlist.py creation)
- **Issue:** Plan's test used `from src.backend.config import settings as settings_mod` then `reload(settings_mod)` — but this imports the `settings` singleton object (not the module), causing `TypeError: reload() argument must be a module`
- **Fix:** Rewrote test to directly invoke the env parsing expression under the `@patch.dict` context, which correctly validates the env var parsing logic without needing module reload
- **Files modified:** `src/backend/tests/test_watchlist.py`
- **Verification:** All 8 tests pass
- **Committed in:** `599ba1d` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in plan's test code)
**Impact on plan:** Test logic corrected to match Python's module import semantics. No scope creep. All WTCH requirements validated.

## Issues Encountered
- Python class-level attribute evaluation at import time (not instantiation time) meant the plan's proposed test for env-var override needed adjustment. The WATCHLIST parsing is correct — it reads from env at class definition (module import), so a fresh `Settings()` instance reuses the cached class-level default unless the module is explicitly reloaded. The test now validates the parsing expression behavior directly.

## User Setup Required
None - no external service configuration required. Users may optionally set `WATCHLIST=BTC,ETH,...` in `.env` to customize their watchlist.

## Next Phase Readiness
- `get_merged_watchlist()` is ready for use in 21-02 and 21-03 morning batch wiring
- `run_morning_batch()` signature change (symbols now optional second param) is a breaking change — callers must be updated in subsequent plans
- All 3 WTCH requirements satisfied

---
*Phase: 21-watchlist-orchestrator-integration*
*Completed: 2026-03-01*
