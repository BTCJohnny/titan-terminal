# Roadmap: Titan Terminal

## Milestones

- ✅ **v0.1 Project Scaffold** - Phases 1-4 (shipped 2026-02-26)
- ✅ **v0.2 Data Foundation** - Phases 5-7 (shipped 2026-02-27)
- ✅ **v0.3 TA Ensemble** - Phases 8-13 (shipped 2026-02-28)
- ✅ **v0.4 Nansen Agent + Telegram Agent** - Phases 14-19 (shipped 2026-03-01)
- 🚧 **v0.5 Risk Agent + API + Dashboard** - Phases 20-24 (in progress)

## Phases

<details>
<summary>✅ v0.1 Project Scaffold (Phases 1-4) - SHIPPED 2026-02-26</summary>

- [x] Phase 1: Agent Structure (1/1 plans) - completed 2026-02-26
- [x] Phase 2: Pydantic Models (2/2 plans) - completed 2026-02-26
- [x] Phase 3: Configuration (1/1 plans) - completed 2026-02-26
- [x] Phase 4: Smoke Tests (2/2 plans) - completed 2026-02-26

See: `.planning/milestones/v0.1-ROADMAP.md`

</details>

<details>
<summary>✅ v0.2 Data Foundation (Phases 5-7) - SHIPPED 2026-02-27</summary>

- [x] Phase 5: Configuration Consolidation (1/1 plans) - completed 2026-02-27
- [x] Phase 6: OHLCV Data Client (1/1 plans) - completed 2026-02-27
- [x] Phase 7: Data Layer Testing (1/1 plans) - completed 2026-02-27

See: `.planning/milestones/v0.2-ROADMAP.md`

</details>

<details>
<summary>✅ v0.3 TA Ensemble (Phases 8-13) - SHIPPED 2026-02-28</summary>

- [x] Phase 8: Dependencies + Shared Indicators (2/2 plans) - completed 2026-02-27
- [x] Phase 9: Alpha Factors Module (2/2 plans) - completed 2026-02-27
- [x] Phase 10: Wyckoff Detection Module (3/3 plans) - completed 2026-02-27
- [x] Phase 11: WeeklySubagent + TASignal Extension (3/3 plans) - completed 2026-02-27
- [x] Phase 12: Daily + FourHour Subagents (2/2 plans) - completed 2026-02-28
- [x] Phase 13: TAMentor Implementation (2/2 plans) - completed 2026-02-28

See: `.planning/milestones/v0.3-ROADMAP.md`

</details>

<details>
<summary>✅ v0.4 Nansen Agent + Telegram Agent (Phases 14-19) - SHIPPED 2026-03-01</summary>

- [x] Phase 14: Foundation (2/2 plans) - completed 2026-02-28
- [x] Phase 15: Nansen Agent (4/4 plans) - completed 2026-03-01
- [x] Phase 16: Telegram Agent (2/2 plans) - completed 2026-03-01
- [x] Phase 17: Test Coverage (3/3 plans) - completed 2026-03-01
- [x] Phase 18: Orchestrator Integration Fixes (1/1 plan) - completed 2026-03-01
- [x] Phase 19: DB Init & Test Isolation (1/1 plan) - completed 2026-03-01

See: `.planning/milestones/v0.4-ROADMAP.md`

</details>

---

### 🚧 v0.5 Risk Agent + API + Dashboard (In Progress)

**Milestone Goal:** Complete the full stack — Risk Agent with S/R-based stops and position sizing, FastAPI endpoints for morning report and chat, and a working Next.js dashboard.

- [ ] **Phase 20: Risk Agent** - Complete RiskAgent with S/R stops, R:R enforcement, and position sizing
- [ ] **Phase 21: Watchlist + Orchestrator Integration** - Configurable watchlist, Telegram supplementation, chain RiskAgent into orchestrator
- [ ] **Phase 22: API Endpoints** - Complete /morning-report, /analyze/{symbol}, and /chat FastAPI endpoints
- [ ] **Phase 23: Dashboard** - Next.js morning report with expandable signal cards and chat sidebar
- [ ] **Phase 24: Integration Tests** - End-to-end pipeline tests on BTC, ETH, SOL

## Phase Details

### Phase 20: Risk Agent
**Goal**: Users receive actionable risk parameters (stops, targets, position size) derived from S/R levels
**Depends on**: Phase 19
**Requirements**: RISK-01, RISK-02, RISK-03, RISK-04, RISK-05, RISK-06
**Success Criteria** (what must be TRUE):
  1. User receives stop-loss zones anchored to S/R levels from TA data, not arbitrary ATR multiples
  2. User receives target zones with a displayed R:R ratio, and any setup with R:R below 3:1 is flagged or suppressed
  3. User receives a calculated position size when a portfolio value is provided as input
  4. When no portfolio value is provided, the agent returns risk zones (stop/target/R:R) without errors
  5. RiskAgent returns a valid RiskOutput Pydantic model in all code paths — no raw dicts
**Plans**: TBD

Plans:
- [ ] 20-01: Integrate RiskOutput model and implement dual-mode logic (risk zones vs. position sizing)
- [ ] 20-02: S/R-based stop and target derivation with 2% risk cap and 3:1 R:R enforcement
- [ ] 20-03: Unit tests for RiskAgent covering both modes and edge cases

### Phase 21: Watchlist + Orchestrator Integration
**Goal**: Orchestrator runs the complete agent chain on a configurable, dynamically extended watchlist
**Depends on**: Phase 20
**Requirements**: WTCH-01, WTCH-02, WTCH-03, INTG-04, INTG-05
**Success Criteria** (what must be TRUE):
  1. User can edit a watchlist in settings (not constants.py) and analysis picks it up without code changes
  2. Symbols from Telegram signals in the last 48-72h are automatically merged into the watchlist
  3. Morning report analysis iterates the merged watchlist (settings symbols + Telegram symbols)
  4. Calling analyze_symbol() chains TA → Nansen → Telegram → Risk and returns a complete OrchestratorOutput
  5. Deprecated agent stub files are gone — the repository contains only production code
**Plans**: TBD

Plans:
- [ ] 21-01: Configurable watchlist in settings with Telegram signal supplementation logic
- [ ] 21-02: Chain RiskAgent into Orchestrator analyze_symbol() flow
- [ ] 21-03: Remove deprecated files and verify clean import graph

### Phase 22: API Endpoints
**Goal**: FastAPI exposes working endpoints for morning report, single-symbol analysis, and chat
**Depends on**: Phase 21
**Requirements**: API-01, API-02, API-03, API-04, API-05, API-06
**Success Criteria** (what must be TRUE):
  1. GET /morning-report returns a ranked list of 3-5 opportunities each containing TA, on-chain, Telegram, and risk data
  2. Every /morning-report call triggers fresh on-demand analysis — no stale cached response is served
  3. GET /analyze/{symbol} runs the full pipeline for one symbol and returns complete signal data
  4. POST /chat accepts a natural language question and returns a coherent natural language answer grounded in live signal data
  5. /chat uses the Anthropic SDK to generate responses — not hardcoded templates
**Plans**: TBD

Plans:
- [ ] 22-01: /morning-report endpoint (on-demand analysis, ranked by confluence, full signal payload)
- [ ] 22-02: /analyze/{symbol} endpoint (single-symbol full pipeline)
- [ ] 22-03: /chat endpoint (Anthropic SDK natural language Q&A over pipeline data)

### Phase 23: Dashboard
**Goal**: Next.js dashboard renders morning report and supports conversational signal Q&A
**Depends on**: Phase 22
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05
**Success Criteria** (what must be TRUE):
  1. Dashboard landing page loads and displays ranked opportunity cards fetched from /morning-report
  2. Each card shows the symbol's confluence score and directional bias (BULLISH / BEARISH / NO SIGNAL)
  3. User can expand a signal card to see full TA, on-chain, Telegram, and risk details for that symbol
  4. User can type a question in the chat sidebar and receive a signal Q&A response from /chat
**Plans**: TBD

Plans:
- [ ] 23-01: Landing page with ranked signal cards (fetch from /morning-report on load, confluence + bias visible)
- [ ] 23-02: Expandable card detail panels (TA, on-chain, Telegram, risk sections)
- [ ] 23-03: Chat sidebar wired to /chat endpoint

### Phase 24: Integration Tests
**Goal**: Full pipeline verified on BTC, ETH, and SOL with live data — no crashes, complete output
**Depends on**: Phase 21
**Requirements**: INTG-01, INTG-02, INTG-03
**Success Criteria** (what must be TRUE):
  1. BTC integration test runs TA → Nansen → Telegram → Risk and produces a complete OrchestratorOutput without errors
  2. ETH integration test runs the same full pipeline and produces a complete OrchestratorOutput without errors
  3. SOL integration test runs the same full pipeline and produces a complete OrchestratorOutput without errors
**Plans**: TBD

Plans:
- [ ] 24-01: Integration tests for BTC, ETH, and SOL (full pipeline, real data, asserts on output shape)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Agent Structure | v0.1 | 1/1 | Complete | 2026-02-26 |
| 2. Pydantic Models | v0.1 | 2/2 | Complete | 2026-02-26 |
| 3. Configuration | v0.1 | 1/1 | Complete | 2026-02-26 |
| 4. Smoke Tests | v0.1 | 2/2 | Complete | 2026-02-26 |
| 5. Configuration Consolidation | v0.2 | 1/1 | Complete | 2026-02-27 |
| 6. OHLCV Data Client | v0.2 | 1/1 | Complete | 2026-02-27 |
| 7. Data Layer Testing | v0.2 | 1/1 | Complete | 2026-02-27 |
| 8. Dependencies + Shared Indicators | v0.3 | 2/2 | Complete | 2026-02-27 |
| 9. Alpha Factors Module | v0.3 | 2/2 | Complete | 2026-02-27 |
| 10. Wyckoff Detection Module | v0.3 | 3/3 | Complete | 2026-02-27 |
| 11. WeeklySubagent + TASignal Extension | v0.3 | 3/3 | Complete | 2026-02-27 |
| 12. Daily + FourHour Subagents | v0.3 | 2/2 | Complete | 2026-02-28 |
| 13. TAMentor Implementation | v0.3 | 2/2 | Complete | 2026-02-28 |
| 14. Foundation | v0.4 | 2/2 | Complete | 2026-02-28 |
| 15. Nansen Agent | v0.4 | 4/4 | Complete | 2026-03-01 |
| 16. Telegram Agent | v0.4 | 2/2 | Complete | 2026-03-01 |
| 17. Test Coverage | v0.4 | 3/3 | Complete | 2026-03-01 |
| 18. Orchestrator Integration Fixes | v0.4 | 1/1 | Complete | 2026-03-01 |
| 19. DB Init & Test Isolation | v0.4 | 1/1 | Complete | 2026-03-01 |
| 20. Risk Agent | v0.5 | 0/3 | Not started | - |
| 21. Watchlist + Orchestrator Integration | v0.5 | 0/3 | Not started | - |
| 22. API Endpoints | v0.5 | 0/3 | Not started | - |
| 23. Dashboard | v0.5 | 0/3 | Not started | - |
| 24. Integration Tests | v0.5 | 0/1 | Not started | - |

---

*Roadmap updated: 2026-03-01 after v0.5 milestone roadmap creation*
