# Requirements: Titan Terminal

**Defined:** 2026-02-26
**Core Value:** Surface high-conviction trading setups by combining multi-timeframe technical analysis with on-chain smart money tracking — no signal without confluence.

## v0.1 Requirements

Requirements for Project Scaffold milestone. Each maps to roadmap phases.

### Agent Structure

- [ ] **AGNT-01**: Create nested ta_ensemble/ folder with weekly_subagent.py, daily_subagent.py, fourhour_subagent.py, ta_mentor.py
- [ ] **AGNT-02**: Create nansen_agent.py at src/backend/agents/ root
- [ ] **AGNT-03**: Create telegram_agent.py at src/backend/agents/ root
- [ ] **AGNT-04**: Create risk_agent.py at src/backend/agents/ root
- [ ] **AGNT-05**: Create orchestrator.py at src/backend/agents/ root

### Pydantic Models

- [ ] **MODL-01**: TASignal model (symbol, timeframe, direction, confidence, indicators)
- [ ] **MODL-02**: TAMentorSignal model (overall_direction, confidence, conflicts, warnings)
- [ ] **MODL-03**: NansenSignal model (5-signal framework: exchange_flows, fresh_wallets, smart_money, top_pnl, whale_activity)
- [ ] **MODL-04**: TelegramSignal model (symbol, source, timestamp, raw_text)
- [ ] **MODL-05**: RiskOutput model (position_size, stop_loss, take_profit, risk_reward_ratio)
- [ ] **MODL-06**: OrchestratorOutput model (combined signals, final recommendation)

### Configuration

- [ ] **CONF-01**: settings.py loads env vars with python-dotenv
- [ ] **CONF-02**: .env.example with ANTHROPIC_API_KEY, NANSEN_API_KEY, HYPERLIQUID_API_KEY, TELEGRAM_BOT_TOKEN, SIGNALS_DB_PATH

### Testing

- [ ] **TEST-01**: Smoke test for each TA subagent (weekly, daily, fourhour)
- [ ] **TEST-02**: Smoke test for TAMentor
- [ ] **TEST-03**: Smoke test for Nansen agent
- [ ] **TEST-04**: Smoke test for Telegram agent
- [ ] **TEST-05**: Smoke test for Risk agent
- [ ] **TEST-06**: Smoke test for Orchestrator
- [ ] **TEST-07**: All tests passing

## Future Requirements (v1.0+)

Deferred to future milestone. Tracked but not in current roadmap.

### TA Implementation

- **TA-01**: TA Ensemble with 3 timeframe subagents (Weekly, Daily, 4H)
- **TA-02**: Wyckoff phase detection (A-E, springs, upthrusts, SOS/SOW)
- **TA-03**: Technical indicators (RSI, MACD, BB, ADX, OBV, VWAP, ATR, S/R)
- **TA-04**: OHLCV alpha factors (momentum, volume anomaly, MA deviation, volatility)
- **TA-05**: TAMentor using claude-opus-4-6 with conflict resolution logic

### On-Chain

- **ONCH-01**: Nansen agent with 5-signal accumulation/distribution framework
- **ONCH-02**: Funding rate overlay from Hyperliquid perps

### Integration

- **INTG-01**: Telegram agent connected to signals.db
- **INTG-02**: Risk/Levels agent (2% max risk, 3:1 min R:R, S/R-based stops)
- **INTG-03**: Integration tests on BTC, ETH, SOL

### API & Dashboard

- **API-01**: FastAPI /morning-report endpoint (top opportunities)
- **API-02**: FastAPI /chat endpoint
- **DASH-01**: Next.js dashboard with signal cards + chat

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Copying code from titan-trading | Rewrite cleanly using as logic reference only |
| Automated trade execution | This is analysis/signals only |
| Mobile app | Web dashboard first |
| Real-time websocket streaming | Polling sufficient for v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AGNT-01 | Phase 1 | Pending |
| AGNT-02 | Phase 1 | Pending |
| AGNT-03 | Phase 1 | Pending |
| AGNT-04 | Phase 1 | Pending |
| AGNT-05 | Phase 1 | Pending |
| MODL-01 | Phase 2 | Pending |
| MODL-02 | Phase 2 | Pending |
| MODL-03 | Phase 2 | Pending |
| MODL-04 | Phase 2 | Pending |
| MODL-05 | Phase 2 | Pending |
| MODL-06 | Phase 2 | Pending |
| CONF-01 | Phase 3 | Pending |
| CONF-02 | Phase 3 | Pending |
| TEST-01 | Phase 4 | Pending |
| TEST-02 | Phase 4 | Pending |
| TEST-03 | Phase 4 | Pending |
| TEST-04 | Phase 4 | Pending |
| TEST-05 | Phase 4 | Pending |
| TEST-06 | Phase 4 | Pending |
| TEST-07 | Phase 4 | Pending |

**Coverage:**
- v0.1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-02-26*
*Last updated: 2026-02-26 after roadmap creation*
