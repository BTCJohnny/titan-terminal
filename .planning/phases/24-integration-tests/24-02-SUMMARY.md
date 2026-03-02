---
phase: 24-integration-tests
plan: 02
subsystem: ui
tags: [nextjs, react, dashboard, null-handling, mock-api, rendering]

# Dependency graph
requires:
  - phase: 24-integration-tests
    provides: "24-01 integration tests: pipeline verified end-to-end, all 6 tests green"
  - phase: 22-fastapi-backend
    provides: "/api/morning-report, /api/morning-report-mock endpoints"
  - phase: 23-dashboard
    provides: "Next.js dashboard components: SignalDetailPanel, NansenSignalCards, SymbolSidebar, ChatPanel"
provides:
  - "Fixed mock endpoint with 3 diverse signal types covering null field rendering paths"
  - "NansenSignalCards fallback UI when nansen_summary is null or empty"
  - "Confirmed mock and real API response shapes are identical (18 fields)"
affects:
  - 24-integration-tests

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Mock endpoint includes Avoid signal with null entry_zone/stop/tp/rr to exercise null rendering path"
    - "NansenSignalCards shows 'No on-chain data available' fallback instead of rendering null"

key-files:
  created: []
  modified:
    - src/backend/api/main.py
    - src/frontend/src/components/nansen-signal-cards.tsx

key-decisions:
  - "NansenSignalCards returns a fallback UI element (not null/nothing) when nansen_summary is null or empty — real API returns [] for symbols with no Nansen data, so fallback must be visible to user"
  - "Mock endpoint restored with BTC Avoid signal (null entry_zone, empty nansen_summary) alongside ETH/LINK bullish signals to cover all rendering branches"

patterns-established:
  - "Mock endpoint should include at least one Avoid signal with null trade fields to test null-rendering paths in dashboard components"

requirements-completed: [INTG-01, INTG-02, INTG-03]

# Metrics
duration: 25min
completed: 2026-03-02
---

# Phase 24 Plan 02: Dashboard Mock-vs-Real Rendering Summary

**Fixed mock-vs-real rendering mismatches: NansenSignalCards null fallback, mock endpoint restored with BTC Avoid signal, frontend build clean — awaiting human browser verification**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-02T10:15:22Z
- **Completed:** 2026-03-02T10:40:00Z (Task 1 complete; Task 2 awaiting human verify)
- **Tasks:** 1 of 2 complete (Task 2 is checkpoint:human-verify)
- **Files modified:** 2

## Accomplishments

- Compared mock vs real API response field shapes — identical 18 fields confirmed
- Restored BTC Avoid signal in mock endpoint (null entry_zone, null stop/tp/rr, empty nansen_summary) to exercise null-field rendering paths
- Fixed NansenSignalCards: replaced `return null` with a "No on-chain data available" fallback message for null/empty nansen_summary
- Confirmed all frontend components already handle null direction, entry_zone, stop_loss, tp1, tp2, risk_reward, three_laws_check, reasoning, ta_summary gracefully via optional chaining and conditional rendering
- Frontend Next.js build passes with zero TypeScript errors

## Task Commits

1. **Task 1: Compare mock vs real API response and fix rendering mismatches** - `3c34a2e` (fix)

## Files Created/Modified

- `src/backend/api/main.py` — Restored BTC Avoid signal in mock endpoint with null trade fields and empty nansen_summary; mock now has 3 diverse signals (ETH bullish, LINK bullish, BTC bearish/Avoid)
- `src/frontend/src/components/nansen-signal-cards.tsx` — Changed null/empty branch from `return null` to show "No on-chain data available for this signal." fallback UI

## Decisions Made

- NansenSignalCards shows "No on-chain data available" fallback instead of rendering nothing — real BTC response returns `nansen_summary: []` (no Nansen API key for BTC), so the fallback is needed for the user to see something in the UI rather than a blank section
- Mock endpoint BTC signal kept as Avoid (null entry_zone) specifically to test null-field rendering path in SignalDetailPanel and NansenSignalCards

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added NansenSignalCards fallback for empty nansen_summary**
- **Found during:** Task 1 (mock-vs-real comparison)
- **Issue:** Real API returns `nansen_summary: []` for BTC (no Nansen API key). NansenSignalCards returned `null` (no UI) for empty arrays — user sees a blank space with no explanation
- **Fix:** Added fallback `<div>` with "No on-chain data available for this signal." text for null/empty nansen_summary
- **Files modified:** `src/frontend/src/components/nansen-signal-cards.tsx`
- **Verification:** Frontend build passes; plan explicitly states "Nansen cards render for signals with on-chain data, show fallback for empty data"
- **Committed in:** `3c34a2e` (Task 1 commit)

**2. [Rule 1 - Bug] Restored BTC Avoid signal to mock endpoint**
- **Found during:** Task 1 (mock-vs-real comparison)
- **Issue:** Unstaged changes in main.py had removed BTC (bearish/Avoid with null entry_zone) and SOL from mock, replacing with LINK. This left mock with only 2 bullish signals and no null-field test coverage
- **Fix:** Kept LINK replacement, added BTC back with `entry_zone=None, stop_loss=None, tp1=None, tp2=None, risk_reward=None, nansen_summary=[]`
- **Files modified:** `src/backend/api/main.py`
- **Verification:** Mock now exercises null rendering path; frontend build passes
- **Committed in:** `3c34a2e` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 Rule 2 missing critical, 1 Rule 1 bug)
**Impact on plan:** Both fixes essential for correctness. Null fallback was the primary rendering gap; mock restoration ensures offline UI testing covers null rendering paths.

## Issues Encountered

- Unstaged `main.py` changes from prior session had removed BTC/SOL Avoid signals from mock endpoint, leaving only bullish signals. This obscured null-field rendering paths. Restored during Task 1 audit.
- Backend running on port 8001 (not 8000) per Phase 24-01 note about port conflict with another project's webhook receiver.

## Next Phase Readiness

- Task 1 complete and committed — mock and real API shapes verified identical
- Frontend build clean, all null-field paths handled
- Task 2 (human browser verification) is the remaining step — requires manual inspection in browser at http://localhost:3000

## Self-Check: PASSED

- FOUND: `src/backend/api/main.py` (modified with BTC Avoid signal)
- FOUND: `src/frontend/src/components/nansen-signal-cards.tsx` (modified with null fallback)
- FOUND: commit `3c34a2e` (Task 1 — fix mock-vs-real rendering mismatches)

---
*Phase: 24-integration-tests*
*Completed: 2026-03-02 (Task 1 complete; awaiting Task 2 human verify)*
