# Requirements: Titan Terminal

**Defined:** 2026-02-28
**Core Value:** Surface high-conviction trading setups by combining multi-timeframe technical analysis with on-chain smart money tracking — no signal without confluence.

## v0.4 Requirements

Requirements for milestone v0.4: Nansen Agent + Telegram Agent.

### Nansen Agent

- [x] **NANS-01**: Agent fetches exchange flow direction (inflow/outflow/neutral) with magnitude via Nansen MCP
- [x] **NANS-02**: Agent fetches smart money activity (accumulating/distributing/neutral) with confidence via Nansen MCP
- [x] **NANS-03**: Agent fetches whale activity direction with magnitude via Nansen MCP
- [x] **NANS-04**: Agent fetches top PnL wallets direction with notable count via Nansen MCP
- [x] **NANS-05**: Agent fetches fresh wallet activity level with interpretation via Nansen MCP
- [x] **NANS-06**: Agent fetches funding rate from Hyperliquid perps endpoint (marks unavailable if not in MCP)
- [x] **NANS-07**: Agent aggregates 5 signals into overall bullish/bearish/neutral with confidence 0-100
- [x] **NANS-08**: Agent outputs valid NansenSignal Pydantic model
- [x] **NANS-09**: Agent logs every analysis to Obsidian vault (signal-combinations.md with date/symbol/signals/outcome)
- [x] **NANS-10**: Agent handles missing MCP data gracefully (neutral confidence 0, log warning, continue)

### Telegram Agent

- [ ] **TELE-01**: Agent queries `signals` table in signals.db (not telegram_signals)
- [ ] **TELE-02**: Agent filters signals from last 48 hours with status pending/active
- [ ] **TELE-03**: Agent extracts entry_1/2/3, stop_loss, target_1-5 from signals
- [ ] **TELE-04**: Agent calculates confluence_count (number of signals agreeing on direction)
- [ ] **TELE-05**: Agent identifies best_signal (highest confidence_score)
- [ ] **TELE-06**: Agent outputs valid TelegramSignal Pydantic model

### Models

- [x] **MODL-01**: NansenSignal Pydantic model with all specified fields (symbol, exchange_flow, smart_money, whale_activity, top_pnl_wallets, fresh_wallets, funding_rate, overall_signal, confidence, signal_count_bullish, signal_count_bearish, reasoning, timestamp)
- [x] **MODL-02**: TelegramSignal Pydantic model with all specified fields (symbol, signals_found, active_signals, overall_sentiment, confluence_count, avg_confidence, best_signal, reasoning, timestamp)

### Database

- [x] **DB-01**: Create `onchain_snapshots` table in signals.db with all Nansen signal fields
- [x] **DB-02**: Create `ta_snapshots` table in signals.db with weekly/daily/4h direction/confidence fields
- [x] **DB-03**: Snapshot tables are append-only — never modify existing signals table
- [x] **DB-04**: Database path loaded from settings/config, not hardcoded

### Tests

- [ ] **TEST-01**: Unit tests for each of the 5 Nansen signals (exchange flow, smart money, whales, top PnL, fresh wallets)
- [ ] **TEST-02**: Unit tests for Nansen overall signal aggregation logic
- [ ] **TEST-03**: Unit tests for Nansen vault logging (appends to signal-combinations.md)
- [ ] **TEST-04**: Unit tests for Nansen graceful handling when MCP returns no data
- [ ] **TEST-05**: Unit tests for Telegram agent with signals present
- [ ] **TEST-06**: Unit tests for Telegram agent with no signals (empty result)
- [ ] **TEST-07**: Unit tests for Telegram confluence counting logic
- [ ] **TEST-08**: Unit tests for Telegram 48h window filter
- [ ] **TEST-09**: Unit tests for new DB table creation (onchain_snapshots, ta_snapshots)
- [ ] **TEST-10**: Unit tests for insert operations into both snapshot tables

## Future Requirements

### v1.0+ Pending

- Risk/Levels agent (2% max risk, 3:1 min R:R, S/R-based stops)
- Integration tests on BTC, ETH, SOL
- FastAPI /morning-report endpoint (top opportunities)
- FastAPI /chat endpoint
- Next.js dashboard with signal cards + chat
- Complete market_data.py migration

## Out of Scope

| Feature | Reason |
|---------|--------|
| Copying Titan Trading code | Rewrite cleanly — reference only |
| Simulated/fallback data for Nansen | Must use live MCP tools only |
| Claude knowledge fallback for on-chain | No signal without real data |
| Automated trade execution | Analysis/signals only |
| Mobile app | Web dashboard first |
| Real-time websocket streaming | Polling sufficient for v1 |
| Modifying existing signals table | Snapshot tables are append-only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| NANS-01 | Phase 15 | Complete |
| NANS-02 | Phase 15 | Complete |
| NANS-03 | Phase 15 | Complete |
| NANS-04 | Phase 15 | Complete |
| NANS-05 | Phase 15 | Complete |
| NANS-06 | Phase 15 | Complete |
| NANS-07 | Phase 15 | Complete |
| NANS-08 | Phase 15 | Complete |
| NANS-09 | Phase 15 | Complete |
| NANS-10 | Phase 15 | Complete |
| TELE-01 | Phase 16 | Pending |
| TELE-02 | Phase 16 | Pending |
| TELE-03 | Phase 16 | Pending |
| TELE-04 | Phase 16 | Pending |
| TELE-05 | Phase 16 | Pending |
| TELE-06 | Phase 16 | Pending |
| MODL-01 | Phase 14 | Complete |
| MODL-02 | Phase 14 | Complete |
| DB-01 | Phase 14 | Complete |
| DB-02 | Phase 14 | Complete |
| DB-03 | Phase 14 | Complete |
| DB-04 | Phase 14 | Complete |
| TEST-01 | Phase 17 | Pending |
| TEST-02 | Phase 17 | Pending |
| TEST-03 | Phase 17 | Pending |
| TEST-04 | Phase 17 | Pending |
| TEST-05 | Phase 17 | Pending |
| TEST-06 | Phase 17 | Pending |
| TEST-07 | Phase 17 | Pending |
| TEST-08 | Phase 17 | Pending |
| TEST-09 | Phase 17 | Pending |
| TEST-10 | Phase 17 | Pending |

**Coverage:**
- v0.4 requirements: 32 total
- Mapped to phases: 32 (100% coverage)
- Unmapped: 0

**Phase breakdown:**
- Phase 14 (Foundation): 6 requirements
- Phase 15 (Nansen Agent): 10 requirements
- Phase 16 (Telegram Agent): 6 requirements
- Phase 17 (Test Coverage): 10 requirements

---
*Requirements defined: 2026-02-28*
*Last updated: 2026-02-28 after v0.4 roadmap creation*
