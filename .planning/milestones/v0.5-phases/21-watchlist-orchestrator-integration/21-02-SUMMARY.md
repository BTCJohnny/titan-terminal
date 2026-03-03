---
phase: 21-watchlist-orchestrator-integration
plan: 02
subsystem: agents
tags: [orchestrator, anthropic-sdk, mentor, obsidian-vault, signal-synthesis]

# Dependency graph
requires:
  - phase: 21-01
    provides: MENTOR_MODEL setting (claude-opus-4-6), NANSEN_VAULT_PATH for Obsidian routing
  - phase: 20-risk-agent
    provides: RiskOutput model with entry_zone/stop_loss/take_profits/three_laws_check
provides:
  - Orchestrator with direct Anthropic SDK Mentor call replacing MentorCriticAgent
  - OrchestratorOutput with direction (BULLISH/BEARISH/NO SIGNAL) and reasoning fields
  - Obsidian vault logging for high-conviction signals (confidence > 75)
  - analyze_symbol() returns OrchestratorOutput (not raw dict)
affects:
  - 22-api-endpoints
  - 23-dashboard
  - 24-integration-tests

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Mentor as SDK call: Orchestrator makes direct anthropic.Anthropic().messages.create() call instead of delegating to a MentorCriticAgent subclass"
    - "Single SDK synthesis: All agent outputs combined into one Anthropic call that returns structured JSON"
    - "Confidence gate logging: if confidence > 75 then log to Obsidian vault"

key-files:
  created: []
  modified:
    - src/backend/agents/orchestrator.py
    - src/backend/models/orchestrator_output.py
    - src/backend/tests/test_orchestrator.py

key-decisions:
  - "analyze_symbol() now returns OrchestratorOutput directly (not raw dict) — run_morning_batch updated to handle both OrchestratorOutput and error dicts"
  - "direction field added as proper OrchestratorOutput model field (Literal BULLISH/BEARISH/NO SIGNAL) — @property direction removed to avoid conflict"
  - "Obsidian vault path derived from NANSEN_VAULT_PATH parent.parent / agents / orchestrator / session-notes.md"
  - "Mentor SDK call uses temperature=0.2 and max_tokens=4000 for deterministic synthesis output"

patterns-established:
  - "Mentor system prompt weights: Wyckoff 30%, Nansen 25%, TA 25%, Telegram 10%, Risk 10%"
  - "Risk agent rejection (approved=false) overrides Mentor — must set suggested_action to Avoid"
  - "JSON fallback chain: parse direct JSON -> regex extract -> structured fallback with NO SIGNAL/confidence 0"

requirements-completed: [INTG-04]

# Metrics
duration: 15min
completed: 2026-03-01
---

# Phase 21 Plan 02: Mentor SDK Synthesis Summary

**Direct Anthropic SDK Mentor call replaces MentorCriticAgent — synthesizes all 5 agent outputs into OrchestratorOutput with BULLISH/BEARISH/NO SIGNAL direction, full reasoning text, and Obsidian vault logging for confidence > 75 signals**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-01T12:10:00Z
- **Completed:** 2026-03-01T12:25:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Rewrote orchestrator synthesis pipeline to use direct `anthropic.Anthropic().messages.create()` call with `settings.MENTOR_MODEL` (claude-opus-4-6) at temperature 0.2
- Added `direction` and `reasoning` fields to `OrchestratorOutput`; `analyze_symbol()` now returns typed `OrchestratorOutput` instead of raw dict
- Implemented `_log_to_obsidian()` — signals with confidence > 75 appended to `agents/orchestrator/session-notes.md` in the Obsidian vault
- All 5 new orchestrator tests pass (Mentor SDK mock, model/temperature validation, Obsidian logging threshold)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add reasoning field to OrchestratorOutput and rewrite orchestrator synthesis** - `9edede8` (feat)
2. **Task 2: Update orchestrator tests for Mentor SDK pattern** - `34a427b` (test)

**Plan metadata:** `(pending docs commit)` (docs: complete plan)

## Files Created/Modified

- `src/backend/agents/orchestrator.py` - Removed MentorCriticAgent; added mentor_client, _build_mentor_context, _call_mentor, _log_to_obsidian, _record_to_journal_v2; analyze_symbol returns OrchestratorOutput
- `src/backend/models/orchestrator_output.py` - Added direction (Literal field) and reasoning (Optional[str]) to OrchestratorOutput; removed @property direction
- `src/backend/tests/test_orchestrator.py` - Rewrote tests: 4 new tests covering Mentor SDK pattern, model/temperature, Obsidian logging threshold (high and low confidence)

## Decisions Made

- `analyze_symbol()` returns `OrchestratorOutput` directly rather than raw dict — `run_morning_batch()` updated with a helper to read `.confidence` from OrchestratorOutput instances and `.get('confidence')` from error dicts
- `direction` added as a proper Pydantic field (`Literal["BULLISH", "BEARISH", "NO SIGNAL"]`) instead of a `@property` to avoid Pydantic conflict and to be serializable via `model_dump()`
- Obsidian vault path: `Path(settings.NANSEN_VAULT_PATH).parent.parent / "agents" / "orchestrator" / "session-notes.md"` — consistent with existing vault structure
- Kept `is_actionable` property (non-conflicting, useful for calling code)

## Deviations from Plan

None — plan executed exactly as written. The `run_morning_batch()` method required a minor adaptation (helper functions `get_confidence` and `get_action`) since it now handles `OrchestratorOutput` instances instead of raw dicts, but this was inherent in the plan's requirement that `analyze_symbol()` return `OrchestratorOutput`.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required beyond what was set up in Phase 21 Plan 01 (MENTOR_MODEL env var, NANSEN_VAULT_PATH).

## Next Phase Readiness

- Orchestrator synthesis pipeline complete with Mentor SDK call — centrepiece of v0.5 is operational
- Phase 21 Plan 03 can proceed: wire the updated orchestrator into the morning batch runner / watchlist scan
- Phase 22 (API endpoints) can consume OrchestratorOutput directly — direction and reasoning fields now available
- Phase 23 (Dashboard) can display direction/reasoning from OrchestratorOutput

---
*Phase: 21-watchlist-orchestrator-integration*
*Completed: 2026-03-01*
