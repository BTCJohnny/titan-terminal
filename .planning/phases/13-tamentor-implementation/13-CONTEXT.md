# Phase 13: TAMentor Implementation - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning
**Source:** User input during plan-phase

<domain>
## Phase Boundary

TAMentor synthesizes three TASignal objects (weekly, daily, four_hour) into a single trading decision via Anthropic SDK.

</domain>

<decisions>
## Implementation Decisions

### Location
- TAMentor at `src/backend/agents/ta_ensemble/ta_mentor.py`

### Architecture
- Receives three TASignal objects: weekly, daily, four_hour
- Makes single Anthropic SDK call using `settings.MENTOR_MODEL`
- Do NOT average scores — TAMentor reasons independently via LLM

### Conflict Resolution Rules (must be in LLM prompt)
1. Weekly/Daily bearish + 4H bullish → output BEARISH, confidence -20, warning "4H counter-trend bounce in progress"
2. Weekly/Daily bullish + 4H bearish → output BULLISH, confidence -20, warning "4H pullback — potential better entry incoming"
3. Weekly vs Daily conflict → output NO_SIGNAL
4. 4H is entry timing only, never overrides Weekly or Daily direction

### Output Model
- Must be valid TAMentorSignal Pydantic model matching `src/backend/models/`
- Fields: direction, confidence, conflicts, warnings, reasoning, key_levels

### LLM Prompt Requirements
- Must include all three TASignal JSON objects
- Must include conflict resolution rules explicitly

### Testing
- Unit tests must mock the Anthropic SDK call
- No live API calls in tests

### Claude's Discretion
- Prompt engineering specifics for the TAMentor system prompt
- JSON serialization approach for TASignal objects
- Error handling for SDK failures
- Logging strategy

</decisions>

<specifics>
## Specific Ideas

- The conflict resolution rules are explicit and must be enforced in the prompt
- TAMentor does NOT average or mathematically combine signals — it reasons via Claude
- The 4H timeframe is for entry timing only, never directional override

</specifics>

<deferred>
## Deferred Ideas

None — phase scope is well-defined.

</deferred>

---

*Phase: 13-tamentor-implementation*
*Context gathered: 2026-02-28 via user input*
