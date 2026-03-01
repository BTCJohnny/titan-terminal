# Phase 21: Watchlist + Orchestrator Integration - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning
**Source:** User context (inline)

<domain>
## Phase Boundary

Phase 21 delivers the Orchestrator's second Mentor call and a configurable, dynamically extended watchlist. After all agents have run, the Orchestrator synthesises their outputs into a final trading signal via a direct Anthropic SDK call. The watchlist is moved from hardcoded constants to settings, with automatic Telegram signal supplementation.

</domain>

<decisions>
## Implementation Decisions

### Mentor Call (Centrepiece of v0.5)
- After all agents run (TA Ensemble, Nansen, Telegram, Risk), the Orchestrator makes a direct Anthropic SDK call using `settings.MENTOR_MODEL` (`claude-opus-4-6`), temperature 0.2
- This call reads all agent outputs and produces the final `OrchestratorOutput` Pydantic model
- `OrchestratorOutput` fields: direction, confidence, entry zone, stop, TP1, TP2, and full reasoning text
- Reasoning text must be captured in full — do not summarise or truncate
- Reasoning text stored in the signal journal for future dashboard display

### High-Conviction Signal Logging
- Signals with confidence > 75 must be logged in plain English to the Obsidian vault at `agents/orchestrator/session-notes.md`

### Configurable Watchlist
- Watchlist must be configurable via settings (not hardcoded in `constants.py`)
- Symbols from Telegram signals in the last 48–72h are automatically merged into the watchlist
- The orchestrator iterates the merged list when running the morning report

### Deprecated File Cleanup
- Deprecated agent stub files should be removed — production code only

### Claude's Discretion
- Prompt engineering for the Mentor call (system prompt, user prompt structure)
- Signal journal storage format and schema
- Obsidian note formatting
- Telegram signal merge deduplication strategy
- Settings key naming conventions for watchlist

</decisions>

<specifics>
## Specific Ideas

- Model: `claude-opus-4-6` via `settings.MENTOR_MODEL`
- Temperature: 0.2
- Confidence threshold for Obsidian logging: > 75
- Telegram signal lookback window: 48–72h
- Obsidian path: `agents/orchestrator/session-notes.md`

</specifics>

<deferred>
## Deferred Ideas

- Dashboard display of reasoning text (future phase)
- Signal journal querying/filtering (future phase)

</deferred>

---

*Phase: 21-watchlist-orchestrator-integration*
*Context gathered: 2026-03-01 via user inline context*
