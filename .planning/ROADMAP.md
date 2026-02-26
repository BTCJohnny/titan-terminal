# Roadmap: Titan Terminal

## Overview

Milestone v0.1 (Project Scaffold) establishes the foundational agent architecture with nested folder structures, Pydantic models for type-safe agent outputs, environment configuration, and smoke tests to verify every component returns valid data. This creates the clean scaffolding needed for full agent implementations in v1.0.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Agent Structure** - Create nested ta_ensemble/ folder and root-level agent files
- [ ] **Phase 2: Pydantic Models** - Define output models for all agent types
- [ ] **Phase 3: Configuration** - Set up environment config with python-dotenv
- [ ] **Phase 4: Smoke Tests** - Verify all agent stubs return valid Pydantic models

## Phase Details

### Phase 1: Agent Structure
**Goal**: Developer has complete agent folder structure matching architectural design
**Depends on**: Nothing (first phase)
**Requirements**: AGNT-01, AGNT-02, AGNT-03, AGNT-04, AGNT-05
**Success Criteria** (what must be TRUE):
  1. ta_ensemble/ folder exists with weekly_subagent.py, daily_subagent.py, fourhour_subagent.py, ta_mentor.py
  2. nansen_agent.py, telegram_agent.py, risk_agent.py, orchestrator.py exist at src/backend/agents/ root
  3. All agent files contain stub functions that can be imported without errors
**Plans:** 1 plan

Plans:
- [x] 01-01-PLAN.md — Create ta_ensemble/ folder structure and refactor root-level agents

### Phase 2: Pydantic Models
**Goal**: All agents have type-safe output models defined
**Depends on**: Phase 1
**Requirements**: MODL-01, MODL-02, MODL-03, MODL-04, MODL-05, MODL-06
**Success Criteria** (what must be TRUE):
  1. TASignal model exists with symbol, timeframe, direction, confidence, indicators fields
  2. TAMentorSignal model exists with overall_direction, confidence, conflicts, warnings fields
  3. NansenSignal model exists with 5-signal framework fields (exchange_flows, fresh_wallets, smart_money, top_pnl, whale_activity)
  4. TelegramSignal, RiskOutput, OrchestratorOutput models exist with appropriate fields
  5. All models can be instantiated and serialized to JSON without errors
**Plans:** 2 plans

Plans:
- [ ] 02-01-PLAN.md — Core signal models (TASignal, TAMentorSignal, NansenSignal)
- [ ] 02-02-PLAN.md — Integration models (TelegramSignal, RiskOutput, OrchestratorOutput)

### Phase 3: Configuration
**Goal**: Environment variables loaded from .env with all required keys documented
**Depends on**: Phase 2
**Requirements**: CONF-01, CONF-02
**Success Criteria** (what must be TRUE):
  1. settings.py loads environment variables using python-dotenv
  2. .env.example exists with all required keys (ANTHROPIC_API_KEY, NANSEN_API_KEY, HYPERLIQUID_API_KEY, TELEGRAM_BOT_TOKEN, SIGNALS_DB_PATH)
  3. Developer can import settings and access config values without errors
**Plans:** 1 plan

Plans:
- [ ] 03-01-PLAN.md — Create settings.py module and update .env.example with all required keys

### Phase 4: Smoke Tests
**Goal**: Every agent stub verified to return valid Pydantic output
**Depends on**: Phase 3
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07
**Success Criteria** (what must be TRUE):
  1. Each TA subagent (weekly, daily, fourhour) has smoke test that verifies it returns valid TASignal
  2. TAMentor has smoke test that verifies it returns valid TAMentorSignal
  3. Nansen, Telegram, Risk, Orchestrator agents have smoke tests verifying valid output models
  4. All tests passing (pytest runs without failures)
  5. Developer can run `pytest` and see green pass indicators for all agent stubs
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Agent Structure | 1/1 | ✓ Complete | 2026-02-26 |
| 2. Pydantic Models | 0/2 | Planned | - |
| 3. Configuration | 0/1 | Planned | - |
| 4. Smoke Tests | 0/TBD | Not started | - |
