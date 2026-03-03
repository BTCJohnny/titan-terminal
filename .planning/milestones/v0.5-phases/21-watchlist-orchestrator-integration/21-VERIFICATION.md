---
phase: 21-watchlist-orchestrator-integration
verified: 2026-03-01T13:30:00Z
status: passed
score: 7/7 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 6/7
  gaps_closed:
    - "run_morning_batch() sort/filter logic now uses _get_field() — no AttributeError on OrchestratorOutput"
    - "test_run_morning_batch_sorts_orchestrator_output added — exercises real OrchestratorOutput through sort path"
    - "test_run_morning_batch_handles_mixed_results added — exercises mixed OrchestratorOutput + error dict"
  gaps_remaining: []
  regressions: []
---

# Phase 21: Watchlist + Orchestrator Integration — Verification Report

**Phase Goal:** Orchestrator runs the complete agent chain on a configurable, dynamically extended watchlist
**Verified:** 2026-03-01T13:30:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (Plan 04 fixed run_morning_batch sort logic)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can configure a watchlist via settings.WATCHLIST (not hardcoded) and the orchestrator reads it | VERIFIED | settings.py: WATCHLIST class attr parsed from os.getenv("WATCHLIST", "BTC,ETH,SOL,AVAX,ARB,LINK"); orchestrator.py line 83: `settings.WATCHLIST` consumed in get_merged_watchlist() |
| 2 | Symbols from Telegram signals in the last 72h are automatically merged into the watchlist with deduplication | VERIFIED | telegram_agent.py: get_recent_signal_symbols(hours=72) queries distinct UPPER(symbol); orchestrator.py line 87: dict.fromkeys(base_symbols + telegram_symbols) for order-preserving dedup |
| 3 | run_morning_batch() iterates the merged watchlist and analyzes each symbol, sorting results correctly | VERIFIED | Lines 391-420: iteration correct; sort block (lines 413-417) now uses _get_field() — no AttributeError; 2 regression tests confirm both OrchestratorOutput-only and mixed-type lists sort correctly |
| 4 | analyze_symbol() chains TA -> Nansen -> Telegram -> Risk and then calls Anthropic SDK to produce final OrchestratorOutput | VERIFIED | orchestrator.py lines 104-166: full pipeline — wyckoff, nansen, telegram, weekly/daily/4h subagents, ta_mentor.synthesize(), risk.analyze(), _build_mentor_context(), _call_mentor() returning OrchestratorOutput |
| 5 | The Mentor SDK call uses settings.MENTOR_MODEL (claude-opus-4-6) at temperature 0.2 | VERIFIED | orchestrator.py lines 262-268: self.mentor_client.messages.create(model=settings.MENTOR_MODEL, max_tokens=4000, temperature=0.2, ...) |
| 6 | OrchestratorOutput includes direction, confidence, entry zone, stop, TP1, TP2, and full reasoning text | VERIFIED | orchestrator_output.py: confidence, direction, reasoning fields present; _call_mentor() populates entry_zone, stop_loss, tp1, tp2 from RiskOutput |
| 7 | nansen.py, telegram.py, risk_levels.py, and mentor.py are deleted from agents directory | VERIFIED | Only production files remain: nansen_agent.py, telegram_agent.py, risk_agent.py — no deprecated stubs; __init__.py has no MentorCriticAgent import |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/backend/agents/orchestrator.py` | Fixed sort logic using _get_field() + no r.get() on OrchestratorOutput | VERIFIED | _get_field() at module level (lines 20-30); sort block at lines 413-417 uses _get_field() exclusively; grep for `r.get(` returns no matches in the file |
| `src/backend/tests/test_watchlist.py` | Two new regression tests with real OrchestratorOutput instances | VERIFIED | test_run_morning_batch_sorts_orchestrator_output (line 86) and test_run_morning_batch_handles_mixed_results (line 126) both present and import OrchestratorOutput directly |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `orchestrator.py` sort block | `orchestrator_output.py` | `_get_field(r, 'suggested_action')` + `_get_field(x, 'confidence', 0)` | VERIFIED | Lines 413-417: _get_field dispatches to getattr for OrchestratorOutput and .get() for error dicts — both code paths tested by regression suite |
| `test_watchlist.py` | `orchestrator_output.py` | `from src.backend.models.orchestrator_output import OrchestratorOutput` | VERIFIED | Both new test methods import OrchestratorOutput at test body level and instantiate real instances directly |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| WTCH-01 | 21-01 | User can configure watchlist via settings | SATISFIED | settings.WATCHLIST list attr + env var override verified in code and tests |
| WTCH-02 | 21-01 | Watchlist supplemented by Telegram signals (last 48-72h) | SATISFIED | get_recent_signal_symbols(hours=72) wired in get_merged_watchlist(); tested |
| WTCH-03 | 21-01 | Morning report iterates merged watchlist | SATISFIED | Sort bug fixed — _get_field() handles OrchestratorOutput and error dicts; 10/10 test_watchlist.py tests pass |
| INTG-04 | 21-02 | Orchestrator chains all agents including RiskAgent in analyze_symbol() | SATISFIED | Full 5-agent pipeline + Mentor SDK call + OrchestratorOutput with direction, reasoning, entry/stop/TPs all verified |
| INTG-05 | 21-03 | All deprecated agent files removed (clean codebase) | SATISFIED | nansen.py, telegram.py, risk_levels.py, mentor.py deleted; __init__.py clean |

**Orphaned requirements from REQUIREMENTS.md mapped to Phase 21:** None — all 5 IDs accounted for across plans 01-04.

---

### Anti-Patterns Found

None. The previously identified blocker (r.get() on OrchestratorOutput at lines 399-403) has been resolved. No new anti-patterns detected in the modified files.

---

### Human Verification Required

None — all checks are programmatically verifiable for this phase.

---

### Gap Closure Verification

**Previously reported gap (WTCH-03 / run_morning_batch sort):**

The gap was: "Lines 399-403: r.get('suggested_action') and r.get('confidence', 0) called on OrchestratorOutput — AttributeError at runtime."

**Verification of fix:**

1. `_get_field()` helper added at module level (orchestrator.py lines 20-30) — dispatches `getattr` for non-dict types and `.get()` for dicts.

2. Sort block at lines 413-417 uses `_get_field()` exclusively. Grep for `r.get(` in orchestrator.py returns zero matches.

3. Two regression tests added to test_watchlist.py:
   - `test_run_morning_batch_sorts_orchestrator_output` — uses real OrchestratorOutput instances (confidence 85 and 55), verifies descending sort and no AttributeError.
   - `test_run_morning_batch_handles_mixed_results` — uses one OrchestratorOutput (BTC, confidence 85) plus one runtime error for ETH (caught as error dict with suggested_action='Avoid'), verifies only BTC remains after the actionable filter.

4. Test run results (2026-03-01):
   - `test_watchlist.py`: 10/10 passed (8 pre-existing + 2 new regression tests)
   - `test_orchestrator.py`: 5/5 passed (no regression)
   - Total: 15/15

**Gap status: CLOSED.**

---

_Verified: 2026-03-01T13:30:00Z_
_Verifier: Claude (gsd-verifier)_
