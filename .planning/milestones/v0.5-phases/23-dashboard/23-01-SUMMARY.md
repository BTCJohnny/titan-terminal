---
phase: 23-dashboard
plan: "01"
subsystem: frontend
tags: [nextjs, typescript, dashboard, api-client, layout]
dependency_graph:
  requires: [22-02]
  provides: [types.ts, api.ts, SymbolSidebar, page-shell]
  affects: [23-02, 23-03]
tech_stack:
  added: []
  patterns: [three-column-layout, confidence-bar, direction-badge]
key_files:
  created:
    - src/frontend/src/lib/types.ts
    - src/frontend/src/components/symbol-sidebar.tsx
  modified:
    - src/frontend/src/lib/api.ts
    - src/frontend/src/app/page.tsx
decisions:
  - "Removed stale components (market-context-bar, rich-signal-card, whale-alert-panel, stats-card, signal-card) — they imported deleted api.ts types and were not referenced by any file"
  - "API_BASE updated from port 8001 to 8000 to match Phase 22 FastAPI backend"
metrics:
  duration_seconds: 136
  completed_date: "2026-03-01"
  tasks_completed: 2
  files_changed: 9
---

# Phase 23 Plan 01: Dashboard Foundation Summary

**One-liner:** Rewrote api.ts and types.ts to match Phase 22 backend contracts, built SymbolSidebar with confidence bars and direction badges, and established the three-column page shell with auto-fetch on mount.

## What Was Built

### Task 1: types.ts and api.ts rewrite

`src/frontend/src/lib/types.ts` — New file with TypeScript interfaces matching the Phase 22 FastAPI models exactly:
- `AnalyzeResponse` (all fields: direction, three_laws_check, nansen_summary, etc.)
- `MorningReportResponse` (timestamp, count, signals)
- `ChatRequest` / `ChatResponse`
- `EntryZone`, `ThreeLawsCheck`, `Direction`, `SuggestedAction` types

`src/frontend/src/lib/api.ts` — Rewritten:
- `API_BASE` updated to port 8000
- `getMorningReport()` — no query params, returns `MorningReportResponse`
- `analyzeSymbol(symbol)` — returns `AnalyzeResponse`
- `sendChat(question)` — POST body `{question}`, not `{message}`
- `checkHealth()` — unchanged logic, preserved
- Removed: `recordOutcome`, `getStats`, `getHistory`, all inline type definitions

### Task 2: SymbolSidebar and three-column page shell

`src/frontend/src/components/symbol-sidebar.tsx` — New component:
- "Run Morning Report" button at top (disabled + "Running..." when loading)
- Loading skeleton (5 grey pulse bars when isLoading and no signals)
- Signals sorted by confidence descending (copy, not mutate)
- Per-row: symbol name, direction badge (green/red/grey), confidence bar (green >=70, yellow >=50, red <50), confidence % right-aligned, suggested_action text
- Selected row highlighted bg-zinc-800; hover bg-zinc-800/50
- Empty state: "No report data. Click Run Morning Report."

`src/frontend/src/app/page.tsx` — Rewritten three-column shell:
- Header: title + backend status badge + last refresh time
- Left sidebar (280px): SymbolSidebar
- Center (flex-1): placeholder for Plan 23-02 SignalDetailPanel
- Right sidebar (320px): placeholder for Plan 23-03 ChatPanel
- `fetchReport()`: checkHealth → getMorningReport → auto-select first signal
- On mount: calls fetchReport()

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Removed stale legacy components**
- **Found during:** Task 2 build verification
- **Issue:** `market-context-bar.tsx`, `rich-signal-card.tsx`, `whale-alert-panel.tsx`, `stats-card.tsx`, `signal-card.tsx` all imported types (`Signal`, `MarketContext`, `WhaleAlert`, `Stats`) that no longer exist in api.ts. TypeScript build failed with 18 type errors across these files.
- **Fix:** Deleted all 5 files. None were imported by page.tsx or any other file in scope.
- **Files modified:** 5 files deleted
- **Commit:** d162225

## Verification Results

1. `npm run build` passes with zero TypeScript errors — confirmed
2. `types.ts` has `AnalyzeResponse` with `direction`, `three_laws_check`, `nansen_summary` — confirmed
3. `api.ts` `sendChat` sends `{question: "..."}` not `{message: "..."}` — confirmed
4. `api.ts` `getMorningReport` hits `/api/morning-report` with no query params — confirmed
5. `SymbolSidebar` shows symbols sorted by confidence descending with direction badges — confirmed
6. `page.tsx` has no imports of old components — confirmed

## Self-Check: PASSED

Files exist:
- FOUND: src/frontend/src/lib/types.ts
- FOUND: src/frontend/src/lib/api.ts
- FOUND: src/frontend/src/components/symbol-sidebar.tsx
- FOUND: src/frontend/src/app/page.tsx

Commits exist:
- FOUND: 6352c4f — feat(23-01): rewrite types.ts and api.ts
- FOUND: d162225 — feat(23-01): build SymbolSidebar and three-column page shell
