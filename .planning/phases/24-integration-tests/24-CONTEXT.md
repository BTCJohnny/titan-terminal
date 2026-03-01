# Phase 24: Integration Tests - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning
**Source:** User-provided context

<domain>
## Phase Boundary

End-to-end integration tests for BTC, ETH, and SOL through the full Titan Terminal pipeline. Tests verify the complete chain from API request through all agents to final response.

</domain>

<decisions>
## Implementation Decisions

### Test Architecture
- Tests hit the live FastAPI backend at localhost:8000 via GET /morning-report
- Each symbol must flow through: OHLCV fetch → TA Ensemble → Nansen Agent (CLI via subprocess, `nansen research <category> <subcommand>`) → Telegram Agent → Risk Agent → Orchestrator → API response
- Assert response matches OrchestratorOutput Pydantic model
- Response must contain valid: direction, confidence, entry_zone, stop, TP1, TP2, and reasoning fields

### Dashboard Rendering Test
- Test that the Next.js dashboard frontend correctly renders a real API response
- A mock-vs-real rendering bug exists and must be caught and fixed
- Dashboard fetches data via user-triggered button click, not on page load

### Agent Configuration
- TAMentor and Orchestrator Mentor use settings.MENTOR_MODEL (claude-opus-4-6) at temperature 0.2
- Risk Agent enforces 3 Laws: max 2% risk, min 3:1 R:R, max 5 positions
- Weekly/Daily override 4H direction — 4H is entry timing only
- Nansen subprocess only — not MCP

### Claude's Discretion
- Test framework choice (pytest markers, fixtures)
- Timeout/retry strategy for live API calls
- How to trigger and verify dashboard rendering (Playwright, Cypress, etc.)

</decisions>

<specifics>
## Specific Ideas

- GET /morning-report is the primary endpoint under test
- Nansen Agent uses CLI subprocess: `nansen research <category> <subcommand>`
- OrchestratorOutput is the Pydantic model to validate against
- Dashboard has a known mock-vs-real rendering bug to find and fix
- Button-triggered fetch, not page-load fetch

</specifics>

<deferred>
## Deferred Ideas

None — context covers phase scope

</deferred>

---

*Phase: 24-integration-tests*
*Context gathered: 2026-03-01 via user-provided context*
