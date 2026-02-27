# Roadmap: Titan Terminal

## Milestones

- **v0.1 Project Scaffold** - Phases 1-4 (shipped 2026-02-26)
- **v0.2 Data Foundation** - Phases 5-7 (in progress)
- **v1.0 Core Agents** - TBD
- **v1.1 API & Dashboard** - TBD

## Phases

<details>
<summary>v0.1 Project Scaffold (Phases 1-4) - SHIPPED 2026-02-26</summary>

### Phase 1: Agent Structure
**Goal**: Multi-agent architecture with proper nesting and separation of concerns
**Plans**: 1 plan

Plans:
- [x] 01-01: Create nested ta_ensemble/ folder with 4 subagent files and root-level agents

### Phase 2: Pydantic Models
**Goal**: Type-safe output models for all agent signals
**Plans**: 2 plans

Plans:
- [x] 02-01: TASignal, TAMentorSignal, NansenSignal models
- [x] 02-02: TelegramSignal, RiskOutput, OrchestratorOutput models

### Phase 3: Configuration
**Goal**: Centralized environment configuration with python-dotenv
**Plans**: 1 plan

Plans:
- [x] 03-01: Settings module with .env.example

### Phase 4: Smoke Tests
**Goal**: Verify all agents return valid Pydantic output
**Plans**: 2 plans

Plans:
- [x] 04-01: Smoke tests for TA subagents and TAMentor
- [x] 04-02: Smoke tests for Nansen, Telegram, Risk, Orchestrator agents

</details>

### v0.2 Data Foundation (In Progress)

**Milestone Goal:** Establish clean data infrastructure with CCXT/Binance OHLCV client and consolidated configuration.

- [x] **Phase 5: Configuration Consolidation** - Unify config systems into Settings as single source of truth
- [ ] **Phase 6: OHLCV Data Client** - Clean market data fetching with CCXT + Binance
- [ ] **Phase 7: Data Layer Testing** - Full unit test coverage for data infrastructure

## Phase Details

### Phase 5: Configuration Consolidation
**Goal**: Settings class becomes the single source of truth for all configuration
**Depends on**: Phase 4 (v0.1 complete)
**Requirements**: CFG-01, CFG-02, CFG-03, CFG-04
**Success Criteria** (what must be TRUE):
  1. Settings class handles all environment variables
  2. Trading constants (risk limits, symbols) accessible from config/constants.py
  3. Old Config class deleted with no references remaining
  4. All agent imports use Settings/constants with no import errors
  5. All 11 smoke tests pass after config migration
**Plans**: 1 plan

Plans:
- [x] 05-01-PLAN.md — Extend Settings, create constants.py, migrate imports, delete Config class

### Phase 6: OHLCV Data Client
**Goal**: Production-ready OHLCV client with CCXT + Binance for multi-timeframe candles
**Depends on**: Phase 5 (needs consolidated config for API keys)
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06
**Success Criteria** (what must be TRUE):
  1. ohlcv_client.py exists and initializes CCXT Binance exchange
  2. Client fetches 1w, 1d, 4h candles for BTC/USDT, ETH/USDT, SOL/USDT
  3. Rate limit errors trigger exponential backoff retry automatically
  4. market_data.py deprecated with clear backup/migration notice
**Plans**: 1 plan

Plans:
- [ ] 06-01-PLAN.md — Create OHLCV client with CCXT Binance, add deprecation to market_data.py

### Phase 7: Data Layer Testing
**Goal**: Comprehensive unit test coverage for OHLCV client with mocked exchanges
**Depends on**: Phase 6 (needs OHLCV client implementation)
**Requirements**: TEST-01, TEST-02, TEST-03
**Success Criteria** (what must be TRUE):
  1. Unit tests verify OHLCV client returns correct candle data structure
  2. Unit tests verify rate limit retry behavior with exponential backoff
  3. All 11 existing smoke tests still pass after data layer additions
**Plans**: 1 plan

Plans:
- [ ] 07-01-PLAN.md — Unit tests for OHLCV client with mocked exchange calls

## Progress

**Execution Order:**
Phases execute in numeric order: 5 -> 6 -> 7

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Agent Structure | v0.1 | 1/1 | Complete | 2026-02-26 |
| 2. Pydantic Models | v0.1 | 2/2 | Complete | 2026-02-26 |
| 3. Configuration | v0.1 | 1/1 | Complete | 2026-02-26 |
| 4. Smoke Tests | v0.1 | 2/2 | Complete | 2026-02-26 |
| 5. Configuration Consolidation | v0.2 | 1/1 | Complete | 2026-02-27 |
| 6. OHLCV Data Client | v0.2 | 0/1 | Planning complete | - |
| 7. Data Layer Testing | v0.2 | 0/1 | Planning complete | - |
