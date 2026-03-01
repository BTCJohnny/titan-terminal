# Phase 16: Telegram Agent - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning
**Source:** User input (inline context)

<domain>
## Phase Boundary

Production-ready Telegram signal agent that queries an external SQLite database for recent signals, calculates confluence across signals, and identifies the best signal. This agent reasons over data directly — no Claude SDK calls needed.

</domain>

<decisions>
## Implementation Decisions

### Database Configuration
- Database path: `/Users/johnny_main/Developer/data/signals/signals.db` (read from settings/config — do NOT hardcode)
- Table name: `signals` (NOT telegram_signals)

### Query Parameters
- Time window: Last 48 hours
- Status filter: `status IN ('pending', 'active')`
- Ordering: `ORDER BY created_at DESC`
- Limit: 20 signals per symbol

### Key Columns (from signals table)
- `symbol`, `direction`, `signal_type`, `timeframe`
- Entry levels: `entry_1`, `entry_2`, `entry_3`
- `stop_loss`
- Target levels: `target_1` through `target_5`
- `confidence_score`, `pattern_type`, `setup_description`
- `provider`, `status`, `created_at`, `pnl_percent`

### Output Model
- Use existing `TelegramSignal` Pydantic model (built in Phase 14)
- Fields: `symbol`, `signals_found`, `active_signals` (list), `overall_sentiment`, `confluence_count`, `avg_confidence`, `best_signal`, `reasoning`, `timestamp`

### Logic
- **Confluence**: Count of signals where direction matches the majority direction
- **Best signal**: Row with highest `confidence_score`

### Claude's Discretion
- Error handling for database connection failures
- Logging implementation details
- Internal helper function organization

</decisions>

<specifics>
## Specific Ideas

- Agent file: `src/backend/agents/telegram_agent.py` — full replacement of the stub
- No Claude SDK calls — agent reads database and reasons over data directly
- Use existing Pydantic model from Phase 14 for output validation

</specifics>

<deferred>
## Deferred Ideas

None — context covers phase scope

</deferred>

---

*Phase: 16-telegram-agent*
*Context gathered: 2026-03-01 via inline user input*
