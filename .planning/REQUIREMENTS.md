# Requirements: Titan Terminal

**Defined:** 2026-03-01
**Core Value:** Surface high-conviction trading setups by combining multi-timeframe technical analysis with on-chain smart money tracking — no signal without confluence.

## v0.5 Requirements

Requirements for v0.5 Risk Agent + API + Dashboard. Each maps to roadmap phases.

### Risk Agent

- [x] **RISK-01**: RiskAgent uses RiskOutput Pydantic model instead of returning raw dicts
- [x] **RISK-02**: User receives stop-loss zones derived from S/R levels in TA data
- [x] **RISK-03**: User receives target zones with R:R ratio (minimum 3:1 enforced)
- [x] **RISK-04**: User receives position size when portfolio value is provided
- [x] **RISK-05**: Risk agent enforces 2% max risk per trade
- [x] **RISK-06**: Risk agent returns risk zones (stop/target/R:R) when no portfolio value given

### Watchlist

- [x] **WTCH-01**: User can configure a watchlist via settings (not just hardcoded constants)
- [x] **WTCH-02**: Watchlist is supplemented by symbols from Telegram signals (last 48-72h)
- [x] **WTCH-03**: Morning report iterates the merged watchlist (config + Telegram)

### API

- [x] **API-01**: /morning-report endpoint returns top 3-5 opportunities ranked by confluence score
- [x] **API-02**: /morning-report runs analysis on-demand (not cached/scheduled)
- [x] **API-03**: /morning-report response includes TA, on-chain, Telegram, and risk data per symbol
- [x] **API-04**: /chat endpoint accepts natural language query and returns signal Q&A
- [x] **API-05**: /chat uses Anthropic SDK to generate natural language summaries from pipeline data
- [x] **API-06**: /analyze/{symbol} runs full pipeline (TA + Nansen + Telegram + Risk) for a single symbol

### Dashboard

- [x] **DASH-01**: Next.js landing page shows morning report with ranked opportunity cards
- [x] **DASH-02**: Signal cards are expandable to show TA, on-chain, Telegram, and risk details
- [x] **DASH-03**: Chat sidebar accepts questions and displays signal Q&A responses
- [x] **DASH-04**: Dashboard fetches data from /morning-report endpoint on user action (Run Morning Report button)
- [x] **DASH-05**: Dashboard displays confluence score and directional bias per symbol

### Integration & Cleanup

- [x] **INTG-01**: End-to-end integration test for BTC (TA → Nansen → Telegram → Risk → Output)
- [x] **INTG-02**: End-to-end integration test for ETH (full pipeline)
- [x] **INTG-03**: End-to-end integration test for SOL (full pipeline)
- [x] **INTG-04**: Orchestrator chains all agents including RiskAgent in analyze_symbol()
- [x] **INTG-05**: All deprecated agent files removed (clean codebase)

## Future Requirements

### Scheduling & Caching

- **SCHED-01**: Morning report runs on cron (e.g., 8:30am) with cached results
- **SCHED-02**: Dashboard shows cached report with "last updated" timestamp
- **SCHED-03**: User can trigger manual refresh from dashboard

### Advanced Chat

- **CHAT-01**: Chat supports portfolio questions ("What's my exposure?")
- **CHAT-02**: Chat supports trade journaling ("I entered ETH long at $3,200")
- **CHAT-03**: Chat provides market context beyond individual signals

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time websocket streaming | Polling/on-demand sufficient for v0.5 |
| Automated trade execution | Analysis/signals only — user executes |
| Mobile app | Web dashboard first |
| OAuth/user authentication | Single-user tool, no auth needed |
| Trade history tracking | Defer to future — focus on signal generation |
| Dark mode / theme switching | Ship functional first, polish later |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| RISK-01 | Phase 20 | Complete |
| RISK-02 | Phase 20 | Complete |
| RISK-03 | Phase 20 | Complete |
| RISK-04 | Phase 20 | Complete |
| RISK-05 | Phase 20 | Complete |
| RISK-06 | Phase 20 | Complete |
| WTCH-01 | Phase 21 | Complete |
| WTCH-02 | Phase 21 | Complete |
| WTCH-03 | Phase 21 | Complete |
| API-01 | Phase 22 | Complete |
| API-02 | Phase 22 | Complete |
| API-03 | Phase 22 | Complete |
| API-04 | Phase 22 | Complete |
| API-05 | Phase 22 | Complete |
| API-06 | Phase 22 | Complete |
| DASH-01 | Phase 23 | Complete |
| DASH-02 | Phase 23 | Complete |
| DASH-03 | Phase 23 | Complete |
| DASH-04 | Phase 23 | Complete |
| DASH-05 | Phase 23 | Complete |
| INTG-01 | Phase 24 | Complete |
| INTG-02 | Phase 24 | Complete |
| INTG-03 | Phase 24 | Complete |
| INTG-04 | Phase 21 | Complete |
| INTG-05 | Phase 21 | Complete |

**Coverage:**
- v0.5 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-01*
*Last updated: 2026-03-01 after v0.5 roadmap creation — traceability complete*
