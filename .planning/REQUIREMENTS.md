# Requirements: Titan Terminal

**Defined:** 2026-03-01
**Core Value:** Surface high-conviction trading setups by combining multi-timeframe technical analysis with on-chain smart money tracking — no signal without confluence.

## v0.5 Requirements

Requirements for v0.5 Risk Agent + API + Dashboard. Each maps to roadmap phases.

### Risk Agent

- [x] **RISK-01**: RiskAgent uses RiskOutput Pydantic model instead of returning raw dicts
- [ ] **RISK-02**: User receives stop-loss zones derived from S/R levels in TA data
- [ ] **RISK-03**: User receives target zones with R:R ratio (minimum 3:1 enforced)
- [x] **RISK-04**: User receives position size when portfolio value is provided
- [ ] **RISK-05**: Risk agent enforces 2% max risk per trade
- [x] **RISK-06**: Risk agent returns risk zones (stop/target/R:R) when no portfolio value given

### Watchlist

- [ ] **WTCH-01**: User can configure a watchlist via settings (not just hardcoded constants)
- [ ] **WTCH-02**: Watchlist is supplemented by symbols from Telegram signals (last 48-72h)
- [ ] **WTCH-03**: Morning report iterates the merged watchlist (config + Telegram)

### API

- [ ] **API-01**: /morning-report endpoint returns top 3-5 opportunities ranked by confluence score
- [ ] **API-02**: /morning-report runs analysis on-demand (not cached/scheduled)
- [ ] **API-03**: /morning-report response includes TA, on-chain, Telegram, and risk data per symbol
- [ ] **API-04**: /chat endpoint accepts natural language query and returns signal Q&A
- [ ] **API-05**: /chat uses Anthropic SDK to generate natural language summaries from pipeline data
- [ ] **API-06**: /analyze/{symbol} runs full pipeline (TA + Nansen + Telegram + Risk) for a single symbol

### Dashboard

- [ ] **DASH-01**: Next.js landing page shows morning report with ranked opportunity cards
- [ ] **DASH-02**: Signal cards are expandable to show TA, on-chain, Telegram, and risk details
- [ ] **DASH-03**: Chat sidebar accepts questions and displays signal Q&A responses
- [ ] **DASH-04**: Dashboard fetches data from /morning-report endpoint on load
- [ ] **DASH-05**: Dashboard displays confluence score and directional bias per symbol

### Integration & Cleanup

- [ ] **INTG-01**: End-to-end integration test for BTC (TA → Nansen → Telegram → Risk → Output)
- [ ] **INTG-02**: End-to-end integration test for ETH (full pipeline)
- [ ] **INTG-03**: End-to-end integration test for SOL (full pipeline)
- [ ] **INTG-04**: Orchestrator chains all agents including RiskAgent in analyze_symbol()
- [ ] **INTG-05**: All deprecated agent files removed (clean codebase)

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
| RISK-02 | Phase 20 | Pending |
| RISK-03 | Phase 20 | Pending |
| RISK-04 | Phase 20 | Complete |
| RISK-05 | Phase 20 | Pending |
| RISK-06 | Phase 20 | Complete |
| WTCH-01 | Phase 21 | Pending |
| WTCH-02 | Phase 21 | Pending |
| WTCH-03 | Phase 21 | Pending |
| API-01 | Phase 22 | Pending |
| API-02 | Phase 22 | Pending |
| API-03 | Phase 22 | Pending |
| API-04 | Phase 22 | Pending |
| API-05 | Phase 22 | Pending |
| API-06 | Phase 22 | Pending |
| DASH-01 | Phase 23 | Pending |
| DASH-02 | Phase 23 | Pending |
| DASH-03 | Phase 23 | Pending |
| DASH-04 | Phase 23 | Pending |
| DASH-05 | Phase 23 | Pending |
| INTG-01 | Phase 24 | Pending |
| INTG-02 | Phase 24 | Pending |
| INTG-03 | Phase 24 | Pending |
| INTG-04 | Phase 21 | Pending |
| INTG-05 | Phase 21 | Pending |

**Coverage:**
- v0.5 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-01*
*Last updated: 2026-03-01 after v0.5 roadmap creation — traceability complete*
