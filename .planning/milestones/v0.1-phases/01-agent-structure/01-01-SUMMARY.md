---
phase: 01-agent-structure
plan: 01
subsystem: agents
tags: [multi-agent, technical-analysis, timeframe-analysis, agent-architecture]

# Dependency graph
requires:
  - phase: 00-initial
    provides: Basic project structure and agent base class
provides:
  - Multi-timeframe TA analysis structure (weekly, daily, 4h subagents)
  - TAMentor for synthesizing multi-timeframe signals with confluence detection
  - Standardized *_agent.py naming convention for root agents
  - Deprecated old agent files with safe rollback capability
affects: [02-models, orchestration, signal-generation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Multi-timeframe TA subagent pattern
    - TAMentor synthesis with confluence/conflict detection
    - Standardized *_agent.py naming convention

key-files:
  created:
    - src/backend/agents/ta_ensemble/__init__.py
    - src/backend/agents/ta_ensemble/weekly_subagent.py
    - src/backend/agents/ta_ensemble/daily_subagent.py
    - src/backend/agents/ta_ensemble/fourhour_subagent.py
    - src/backend/agents/ta_ensemble/ta_mentor.py
    - src/backend/agents/nansen_agent.py
    - src/backend/agents/telegram_agent.py
    - src/backend/agents/risk_agent.py
  modified:
    - src/backend/agents/__init__.py
    - src/backend/agents/orchestrator.py
    - src/backend/agents/nansen.py (deprecated)
    - src/backend/agents/telegram.py (deprecated)
    - src/backend/agents/risk_levels.py (deprecated)
    - src/backend/agents/ta_ensemble.py (deprecated)
    - src/backend/agents/mentor.py (deprecated)

key-decisions:
  - "Keep old agent files with deprecation notices for safe rollback during v0.1"
  - "TAMentor synthesizes 3 timeframes (weekly > daily > 4h precedence) with confluence scoring"
  - "Each subagent returns dict stubs (Pydantic integration deferred to Phase 2)"

patterns-established:
  - "Multi-timeframe TA pattern: separate subagents per timeframe, TAMentor synthesizes"
  - "Confluence detection: alignment score, conflict detection, confidence adjustment"
  - "*_agent.py naming convention for root-level agents"

requirements-completed: [AGNT-01, AGNT-02, AGNT-03, AGNT-04, AGNT-05]

# Metrics
duration: 5min
completed: 2026-02-26
---

# Phase 01 Plan 01: Agent Structure Summary

**Multi-timeframe TA ensemble with weekly/daily/4h subagents and TAMentor synthesizer, plus standardized *_agent.py naming convention**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-26T16:05:40Z
- **Completed:** 2026-02-26T16:10:32Z
- **Tasks:** 2
- **Files modified:** 17 (8 created, 9 modified)

## Accomplishments
- Created ta_ensemble/ package with 3 timeframe-specific subagents (weekly, daily, 4h)
- Built TAMentor to synthesize multi-timeframe signals with confluence detection
- Refactored root-level agents to follow *_agent.py naming convention
- Updated orchestrator to run multi-timeframe TA pipeline
- All agents importable without errors, ready for Phase 2 Pydantic integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Create nested ta_ensemble/ folder with subagent stubs** - `7a9954e` (feat)
2. **Task 2: Refactor root-level agents to match naming convention** - `6e702a4` (refactor)

## Files Created/Modified

**Created:**
- `src/backend/agents/ta_ensemble/__init__.py` - Package exports for TA subagents
- `src/backend/agents/ta_ensemble/weekly_subagent.py` - Weekly timeframe TA analysis (macro trend)
- `src/backend/agents/ta_ensemble/daily_subagent.py` - Daily timeframe TA analysis (swing setups)
- `src/backend/agents/ta_ensemble/fourhour_subagent.py` - 4H timeframe TA analysis (entry timing)
- `src/backend/agents/ta_ensemble/ta_mentor.py` - Multi-timeframe synthesis with confluence detection
- `src/backend/agents/nansen_agent.py` - On-chain analysis agent (renamed from nansen.py)
- `src/backend/agents/telegram_agent.py` - Telegram signal scanning (renamed from telegram.py)
- `src/backend/agents/risk_agent.py` - Risk/levels calculation (renamed from risk_levels.py)

**Modified:**
- `src/backend/agents/__init__.py` - Updated exports for new agent structure
- `src/backend/agents/orchestrator.py` - Uses multi-timeframe TA pipeline
- `src/backend/agents/nansen.py` - Added deprecation notice
- `src/backend/agents/telegram.py` - Added deprecation notice
- `src/backend/agents/risk_levels.py` - Added deprecation notice
- `src/backend/agents/ta_ensemble.py` - Added deprecation notice
- `src/backend/agents/mentor.py` - Added deprecation notice

## Decisions Made

1. **Keep old files with deprecation notices** - Safe rollback during v0.1 development. Will remove in v1.0.
2. **TAMentor synthesis approach** - Weekly > daily > 4h precedence. Confluence scoring based on alignment. Confidence adjusted for conflicts.
3. **Dict stubs for now** - All agents return dict with TODO comments for Phase 2 Pydantic integration.
4. **Orchestrator TA flow** - Run 3 subagents sequentially, then synthesize with TAMentor (parallelization deferred to optimization phase).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated agents/__init__.py and orchestrator.py during Task 1**
- **Found during:** Task 1 (ta_ensemble package creation)
- **Issue:** ta_ensemble/__init__.py created but root __init__.py still importing TAEnsembleAgent from .ta_ensemble (now a package, not file), causing import failure
- **Fix:** Updated agents/__init__.py to import new ta_ensemble classes; temporarily stubbed orchestrator.py to unblock Task 1 verification, then fully updated in Task 2
- **Files modified:** src/backend/agents/__init__.py, src/backend/agents/orchestrator.py
- **Verification:** Import test passes: `from src.backend.agents.ta_ensemble import WeeklySubagent, DailySubagent, FourHourSubagent, TAMentor`
- **Committed in:** 7a9954e (Task 1 commit), 6e702a4 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking import issue)
**Impact on plan:** Auto-fix required to complete Task 1 verification. Plan anticipated orchestrator updates in Task 2, but partial update needed in Task 1 to unblock imports. No scope creep.

## Issues Encountered

None - all tasks executed as planned with one expected blocking import issue auto-fixed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Phase 2 (Pydantic Models):**
- All agent stubs return dict with clear TODO comments marking Pydantic integration points
- TAMentor synthesize() method signature ready for Pydantic model inputs/outputs
- Multi-timeframe pipeline established in orchestrator
- Import structure verified and working

**Blockers:** None

## Self-Check: PASSED

**Files verified:**
- All 8 created files exist
- All 9 modified files exist

**Commits verified:**
- 7a9954e: Task 1 commit exists
- 6e702a4: Task 2 commit exists

---
*Phase: 01-agent-structure*
*Completed: 2026-02-26*
