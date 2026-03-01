# Phase 22: API Endpoints - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning
**Source:** User input during plan-phase

<domain>
## Phase Boundary

FastAPI exposes working endpoints for morning report, single-symbol analysis, and chat. Also establishes the SQLite SignalJournal schema for future paper trading.

</domain>

<decisions>
## Implementation Decisions

### Endpoints
- GET /morning-report — runs orchestrator.run_morning_batch() on the merged watchlist, returns top 3-5 opportunities ranked by confidence. Response includes full OrchestratorOutput per symbol including reasoning text.
- GET /analyze/{symbol} — runs orchestrator.analyze_symbol() for a single symbol, returns full OrchestratorOutput.
- POST /chat — accepts {"question": "..."}, uses Anthropic SDK (settings.MODEL_NAME, not MENTOR_MODEL) to answer in plain English using live signal data as context.

### SignalJournal SQLite Schema
- Design now to support future paper trading engine
- Required fields: signal_id, symbol, timestamp, direction, confidence, suggested_action, entry_low, entry_high, entry_ideal, stop_loss, tp1, tp2, risk_reward, reasoning (full text), outcome (nullable — filled later), outcome_timestamp (nullable), pnl_percent (nullable), batch_id
- Never drop or migrate this table later — get the schema right now

### Architecture
- No authentication needed — single-user tool
- No caching — all analysis is on-demand
- All endpoints must return valid JSON

### Claude's Discretion
- FastAPI app structure (router organization, lifespan events)
- Error handling patterns for endpoint failures
- Response model schemas (Pydantic)
- How to pipe OrchestratorOutput into chat context

</decisions>

<specifics>
## Specific Ideas

- Use settings.MODEL_NAME for chat endpoint (not MENTOR_MODEL)
- OrchestratorOutput is the core return type — endpoints serialize it
- SignalJournal records every signal for future paper trading backtesting

</specifics>

<deferred>
## Deferred Ideas

- Paper trading engine (uses SignalJournal but built in a future phase)
- Authentication / multi-user support
- Caching layer

</deferred>

---

*Phase: 22-api-endpoints*
*Context gathered: 2026-03-01 via user input*
