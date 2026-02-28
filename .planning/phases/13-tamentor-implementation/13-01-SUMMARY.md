---
phase: 13-tamentor-implementation
plan: 01
subsystem: ta_ensemble
tags: [tamentor, anthropic-sdk, conflict-resolution, synthesis]
completed: 2026-02-28
duration_seconds: 105

dependencies:
  requires:
    - REQ-035
    - REQ-036
    - REQ-037
    - REQ-038
    - REQ-039
    - REQ-040
    - REQ-041
    - REQ-042
  provides:
    - TAMentor.synthesize() accepting TASignal objects
    - Direct Anthropic SDK integration
    - Explicit conflict resolution rules
  affects:
    - src/backend/agents/ta_ensemble/ta_mentor.py

tech_stack:
  added:
    - anthropic SDK direct integration (removed BaseAgent dependency)
  patterns:
    - Standalone class with direct API client
    - Pydantic model validation for input/output
    - Explicit conflict resolution via LLM prompting

key_files:
  created: []
  modified:
    - src/backend/agents/ta_ensemble/ta_mentor.py

decisions:
  - Removed BaseAgent inheritance for cleaner, more explicit implementation
  - Used settings.MENTOR_MODEL instead of settings.MODEL_NAME for model selection
  - Embedded all 4 conflict resolution rules verbatim in system prompt
  - Implemented comprehensive logging (INFO, DEBUG, ERROR levels)
  - Maintained backward compatibility with analyze() wrapper method

metrics:
  tasks_completed: 2
  tasks_planned: 2
  files_modified: 1
  commits: 1
---

# Phase 13 Plan 01: TAMentor Direct SDK Implementation Summary

**One-liner:** Reimplemented TAMentor with direct Anthropic SDK integration and explicit multi-timeframe conflict resolution rules.

## What Was Built

Replaced the BaseAgent-based TAMentor with a clean, standalone implementation that:
- Uses Anthropic SDK directly via `client.messages.create()`
- Accepts TASignal objects (not dicts) in `synthesize()` method
- Returns validated TAMentorSignal objects
- Embeds all 4 conflict resolution rules in system prompt
- Uses `settings.MENTOR_MODEL` for model configuration

## Tasks Completed

### Task 1: Reimplement TAMentor with direct Anthropic SDK
**Status:** Complete
**Commit:** a7b9b37

Replaced entire TAMentor class implementation:
- Removed BaseAgent inheritance
- Added direct Anthropic client initialization
- Changed `synthesize()` signature from dicts to TASignal objects
- Embedded all 4 conflict resolution rules verbatim in system prompt:
  1. Weekly+Daily BEARISH, 4H BULLISH → BEARISH with -20 confidence
  2. Weekly+Daily BULLISH, 4H BEARISH → BULLISH with -20 confidence
  3. Weekly conflicts Daily → neutral bias, wait action
  4. 4H for entry timing only, never overrides higher timeframes
- Implemented client.messages.create() with max_tokens=2500
- Added model_dump() serialization for TASignal objects
- Added TAMentorSignal.model_validate() for response validation
- Comprehensive error handling with re-raise pattern
- Backward compatible analyze() wrapper method

### Task 2: Add JSON parsing and response validation
**Status:** Complete (implemented in Task 1)
**Commit:** a7b9b37

All Task 2 requirements were implemented as part of Task 1:
- `_parse_json_response()` handles raw JSON and ```json blocks
- `_build_prompt()` serializes TASignal objects with model_dump()
- Logging configured at INFO, DEBUG, and ERROR levels
- System prompt instructs LLM to output ONLY valid JSON

## Deviations from Plan

None - plan executed exactly as written. Tasks 1 and 2 were naturally implemented together as a cohesive refactor.

## Verification Results

All verification tests passed:

1. **Import verification:** `from src.backend.agents.ta_ensemble import TAMentor` - PASSED
2. **Instantiation verification:** TAMentor creates client with settings.MENTOR_MODEL - PASSED (claude-sonnet-4-20250514)
3. **Method signature:** synthesize(self, weekly, daily, four_hour) - PASSED
4. **Conflict rules:** All 4 rules present in system_prompt - PASSED

## Key Technical Details

**Conflict Resolution Implementation:**
- Rules embedded in system prompt as explicit instructions
- LLM applies rules during synthesis (not hardcoded logic)
- Conflict rule text includes exact wording from requirements:
  - "4H counter-trend bounce in progress"
  - "4H pullback — potential better entry incoming"
  - "Weekly and Daily timeframes in conflict — genuine uncertainty"

**Error Handling:**
- Logs all errors at ERROR level with context
- Re-raises exceptions for caller to handle retry policy
- Validates response against TAMentorSignal schema before returning
- ValueError for invalid JSON, anthropic.APIError for API failures

**Backward Compatibility:**
- `analyze()` method converts dict inputs to TASignal if needed
- Returns dict via model_dump() for legacy callers
- Maintains same interface as BaseAgent-based version

## Testing Notes

Manual verification confirms:
- TAMentor imports without BaseAgent dependency
- Anthropic client initializes with correct API key from settings
- Model uses MENTOR_MODEL (not MODEL_NAME)
- synthesize() accepts TASignal objects
- System prompt contains all 4 conflict resolution rules verbatim

No runtime testing with live API calls (would require ANTHROPIC_API_KEY and actual TASignal data).

## Files Modified

### src/backend/agents/ta_ensemble/ta_mentor.py
- Complete rewrite (168 insertions, 103 deletions)
- Removed: BaseAgent inheritance, old system prompt
- Added: Direct Anthropic SDK integration, explicit conflict rules, Pydantic validation
- Lines: 207 (from ~142)

## Commits

| Hash    | Message                                               |
| ------- | ----------------------------------------------------- |
| a7b9b37 | feat(13-01): reimplement TAMentor with direct Anthropic SDK |

## Next Steps

Phase 13 Plan 02: Integration testing with computational subagents (WeeklySubagent, DailySubagent, FourHourSubagent).

---

## Self-Check: PASSED

Verification results:
- File exists: src/backend/agents/ta_ensemble/ta_mentor.py ✓
- Commit exists: a7b9b37 ✓
