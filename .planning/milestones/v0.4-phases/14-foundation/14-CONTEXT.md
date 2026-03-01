# Phase 14: Foundation - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning
**Source:** User-provided context

<domain>
## Phase Boundary

Type-safe models and database infrastructure for storing on-chain and TA snapshots. Creates NansenSignal and TelegramSignal Pydantic models, and onchain_snapshots/ta_snapshots tables in signals.db.

</domain>

<decisions>
## Implementation Decisions

### Model Location
- Models go in `src/backend/models/` alongside existing models
- NansenSignal and TelegramSignal models follow same Pydantic v2 patterns already used in project

### Database Connection
- Use existing db module at `src/backend/db/` — check how v0.3 connects before creating anything new
- Database path MUST come from settings, not hardcoded
- signals.db lives at `/Users/johnny_main/Developer/data/signals/signals.db` — external database, not inside project directory

### Table Creation
- New tables (onchain_snapshots, ta_snapshots) created with `CREATE TABLE IF NOT EXISTS` — safe to run on every startup
- Existing signals table MUST NEVER be modified

### Claude's Discretion
- Exact column names for snapshot tables (derived from model fields)
- Internal model validation logic
- Migration/init function organization

</decisions>

<specifics>
## Specific Ideas

- Check existing models in `src/backend/models/` for Pydantic v2 patterns before writing new ones
- Check existing db module at `src/backend/db/` for connection patterns
- signals.db path: `/Users/johnny_main/Developer/data/signals/signals.db`

</specifics>

<deferred>
## Deferred Ideas

None — phase scope is well-defined.

</deferred>

---

*Phase: 14-foundation*
*Context gathered: 2026-02-28 via user input*
