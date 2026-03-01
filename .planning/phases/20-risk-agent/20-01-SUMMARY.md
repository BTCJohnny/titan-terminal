---
phase: 20-risk-agent
plan: 01
subsystem: api
tags: [pydantic, risk, trading, deterministic, python]

# Dependency graph
requires: []
provides:
  - "RiskOutput Pydantic model with approved/rejection_reasons/position_size_units fields"
  - "Deterministic RiskAgent pre-trade validator enforcing 3 Laws of Trading"
  - "Dual-mode risk analysis: full position sizing when account_size provided, risk zones only when omitted"
  - "Orchestrator-compatible analyze(symbol, context_dict) interface"
affects:
  - 20-02
  - 20-03
  - 21-orchestrator

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deterministic validator pattern: pure-Python domain logic with no LLM calls"
    - "S/R-derived stops and targets: stops and TPs come from structure levels, not ATR multiples"
    - "Dual-mode output: position sizing fields are Optional, populated only when account_size provided"
    - "Pydantic model as single source of truth for risk output schema"

key-files:
  created: []
  modified:
    - src/backend/models/risk_output.py
    - src/backend/agents/risk_agent.py

key-decisions:
  - "RiskAgent no longer inherits BaseAgent — deterministic validator needs no LLM calls, no anthropic dependency"
  - "law_3_positions changed from Literal[pass, check_current_positions] to Literal[pass, fail] — open_position_count is now an input so we validate directly"
  - "position_sizing and funding_filter made Optional on RiskOutput — funding data is not available to RiskAgent as pre-trade validator"
  - "Wider stop wins: when S/R stop and proposed stop differ, use the wider one (further from entry) for safety"
  - "TP1 = nearest S/R level giving >= 3:1 R:R; if none qualifies, use best available and let Law 2 flag it"
  - "Law 1 (2% risk) always passes when no account_size provided — cannot check without portfolio size"

patterns-established:
  - "Agent as validator: agents that perform deterministic logic should not inherit BaseAgent or use LLM calls"
  - "Reject explicitly: approved=False + populated rejection_reasons list, never silent pass on bad trades"

requirements-completed:
  - RISK-01
  - RISK-04
  - RISK-06

# Metrics
duration: 2min
completed: 2026-03-01
---

# Phase 20 Plan 01: Risk Agent — Deterministic Pre-Trade Validator Summary

**Pure-Python RiskAgent replacing LLM validator: enforces 3 Laws of Trading via S/R-derived stops/targets, dual-mode position sizing, and validated RiskOutput Pydantic model**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-01T11:30:27Z
- **Completed:** 2026-03-01T11:32:32Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Rewrote RiskAgent from LLM-based (Claude API calls) to pure-Python deterministic validator — eliminating API costs, latency, and non-determinism
- Updated RiskOutput Pydantic model: added approved/rejection_reasons/position_size_units fields; made position_sizing and funding_filter Optional; fixed all 3:1 and 5-position docstrings
- Implemented dual-mode logic: full position sizing (position_size_units, PositionSizing object) when account_size provided; risk zones only (None fields) when omitted
- All 3 Laws enforced explicitly: Law 1 (2% risk check), Law 2 (3:1 R:R from S/R levels), Law 3 (max 5 open positions)
- Backward-compatible orchestrator interface: analyze(symbol, context_dict) maps ta_data.key_levels, suggested_bias, open_position_count, account_size from existing context format

## Task Commits

Each task was committed atomically:

1. **Task 1: Update RiskOutput model for pre-trade validator pattern** - `c2f7241` (feat)
2. **Task 2: Rewrite RiskAgent as deterministic pre-trade validator** - `dbf6b45` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `src/backend/models/risk_output.py` - Added approved, rejection_reasons, position_size_units fields; made position_sizing and funding_filter Optional; fixed 3:1 and 5-position descriptions in ThreeLawsCheck and RiskReward
- `src/backend/agents/risk_agent.py` - Complete rewrite: removed BaseAgent inheritance and LLM calls; pure-Python deterministic validator with S/R-derived stops/targets, 3 Laws enforcement, dual-mode position sizing

## Decisions Made
- RiskAgent no longer inherits BaseAgent — no anthropic import, no API key required for instantiation
- law_3_positions Literal changed from "check_current_positions" to "pass"/"fail" — open_position_count is now an explicit input, enabling direct validation
- Wider stop rule: when S/R-derived stop and proposed stop differ, take the wider one (more conservative) for safety
- TP1/TP2 derived from S/R levels providing >= 3:1 R:R; best available level returned even if < 3:1, letting Law 2 flag the violation
- Law 1 passes by default when no account_size — cannot enforce 2% rule without knowing portfolio size

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- RiskOutput model is finalized; Plan 02 (orchestrator integration) can wire RiskAgent.analyze() into the orchestrator pipeline
- RiskAgent.analyze(symbol, context_dict) is orchestrator-compatible without any changes to orchestrator code
- All 6 edge cases verified: approved trade, Law 1 rejection, Law 2 rejection, Law 3 rejection, no account_size mode, no S/R levels

---
*Phase: 20-risk-agent*
*Completed: 2026-03-01*
