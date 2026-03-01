# Roadmap: Titan Terminal

## Milestones

- ✅ **v0.1 Project Scaffold** - Phases 1-4 (shipped 2026-02-26)
- ✅ **v0.2 Data Foundation** - Phases 5-7 (shipped 2026-02-27)
- ✅ **v0.3 TA Ensemble** - Phases 8-13 (shipped 2026-02-28)
- 🚧 **v0.4 Nansen Agent + Telegram Agent** - Phases 14-17 (in progress)

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

### 🚧 v0.4 Nansen Agent + Telegram Agent (In Progress)

**Milestone Goal:** Build two production-ready agents: Nansen on-chain agent using live Nansen MCP tools with 5-signal framework and vault logging, and Telegram signal agent reading from live signals database with 48h query window.

- [x] **Phase 14: Foundation** - Pydantic models and database schema for on-chain and TA snapshots (completed 2026-02-28)
- [x] **Phase 15: Nansen Agent** - 5-signal on-chain framework with MCP integration and Obsidian vault logging (completed 2026-02-28)
- [ ] **Phase 16: Telegram Agent** - signals.db integration with 48h confluence tracking
- [ ] **Phase 17: Test Coverage** - Comprehensive unit tests for both agents

## Phase Details

### Phase 14: Foundation
**Goal**: Type-safe models and database infrastructure for storing on-chain and TA snapshots
**Depends on**: Phase 13 (v0.3 complete)
**Requirements**: MODL-01, MODL-02, DB-01, DB-02, DB-03, DB-04
**Success Criteria** (what must be TRUE):
  1. NansenSignal Pydantic model exists with all 5-signal fields plus funding rate and confidence
  2. TelegramSignal Pydantic model exists with confluence counting and best signal tracking
  3. onchain_snapshots table created in signals.db with Nansen signal fields
  4. ta_snapshots table created in signals.db with weekly/daily/4h direction and confidence
  5. Database path loads from settings/config, not hardcoded paths
**Plans**: 2 plans

Plans:
- [ ] 14-01-PLAN.md - Extend Pydantic models (NansenSignal, TelegramSignal)
- [ ] 14-02-PLAN.md - Database infrastructure (onchain_snapshots, ta_snapshots tables)

### Phase 15: Nansen Agent
**Goal**: Production-ready on-chain agent that fetches 5 Nansen signals via MCP, aggregates into bullish/bearish/neutral with confidence, and logs every analysis to Obsidian vault
**Depends on**: Phase 14
**Requirements**: NANS-01, NANS-02, NANS-03, NANS-04, NANS-05, NANS-06, NANS-07, NANS-08, NANS-09, NANS-10
**Success Criteria** (what must be TRUE):
  1. Agent fetches all 5 Nansen signals (exchange flows, smart money, whales, top PnL, fresh wallets) via Nansen MCP tools
  2. Agent fetches funding rate from Hyperliquid perps endpoint, marks unavailable if not in MCP
  3. Agent aggregates signals into overall bullish/bearish/neutral with confidence 0-100 (4-5 bullish = ACCUMULATION, 0-1 = DISTRIBUTION)
  4. Agent outputs valid NansenSignal Pydantic model matching MODL-01 schema
  5. Every analysis logs to /Users/johnny_main/Developer/obsidian-vault/obsidian-vault/agents/nansen/signal-combinations.md with date, symbol, signals, outcome
  6. Agent handles missing MCP data gracefully (neutral with confidence 0, logs warning, continues)
**Plans**: 4 plans

Plans:
- [x] 15-01-PLAN.md - MCP integration layer (exchange flows, smart money, whales, top PnL, fresh wallets, funding rate)
- [x] 15-02-PLAN.md - Signal aggregation and NansenAgent core implementation
- [x] 15-03-PLAN.md - Obsidian vault logging integration
- [ ] 15-04-PLAN.md - Gap closure: Wire live MCP tool invocations (token address mapping + callback mechanism)

### Phase 16: Telegram Agent
**Goal**: Production-ready Telegram signal agent that queries signals.db for last 48h, calculates confluence across signals, and identifies best signal
**Depends on**: Phase 14
**Requirements**: TELE-01, TELE-02, TELE-03, TELE-04, TELE-05, TELE-06
**Success Criteria** (what must be TRUE):
  1. Agent queries signals table in signals.db (not telegram_signals table)
  2. Agent filters signals from last 48 hours with status pending or active
  3. Agent extracts all entry levels (entry_1/2/3), stop_loss, and targets (target_1 through target_5)
  4. Agent calculates confluence_count (number of signals agreeing on direction)
  5. Agent identifies best_signal by highest confidence_score
  6. Agent outputs valid TelegramSignal Pydantic model matching MODL-02 schema
**Plans**: TBD

Plans:
- [ ] 16-01: TBD

### Phase 17: Test Coverage
**Goal**: Comprehensive unit test coverage for all Nansen and Telegram agent functionality
**Depends on**: Phase 15, Phase 16
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07, TEST-08, TEST-09, TEST-10
**Success Criteria** (what must be TRUE):
  1. Each of the 5 Nansen signals has individual unit tests with mocked MCP responses
  2. Nansen overall signal aggregation logic has unit tests covering all scoring scenarios (4-5 bullish, 2-3 mixed, 0-1 bearish)
  3. Nansen vault logging has unit tests confirming appends to signal-combinations.md
  4. Nansen graceful handling has unit tests for missing MCP data (neutral confidence 0)
  5. Telegram agent has unit tests with signals present in database
  6. Telegram agent has unit tests for empty result (no signals found)
  7. Telegram confluence counting logic has unit tests
  8. Telegram 48h window filter has unit tests
  9. Database table creation has unit tests for onchain_snapshots and ta_snapshots
  10. Database insert operations have unit tests for both snapshot tables
**Plans**: TBD

Plans:
- [ ] 17-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → ... → 13 → 14 → 15 → 16 → 17

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
| 14. Foundation | 2/2 | Complete    | 2026-02-28 | - |
| 15. Nansen Agent | 4/4 | Complete    | 2026-03-01 | - |
| 16. Telegram Agent | v0.4 | 0/? | Not started | - |
| 17. Test Coverage | v0.4 | 0/? | Not started | - |

---
*Roadmap updated: 2026-02-28 after v0.4 roadmap creation*
