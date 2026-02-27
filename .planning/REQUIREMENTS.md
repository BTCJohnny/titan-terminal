# Requirements: Titan Terminal

**Defined:** 2026-02-27
**Core Value:** Surface high-conviction trading setups by combining multi-timeframe technical analysis with on-chain smart money tracking — no signal without confluence.

## v0.2 Requirements

Requirements for Data Foundation milestone. Each maps to roadmap phases.

### Configuration

- [x] **CFG-01**: Settings class is the single source of truth for environment variables
- [x] **CFG-02**: Trading constants (risk limits, symbol lists) live in config/constants.py
- [x] **CFG-03**: Old Config class is deleted entirely
- [x] **CFG-04**: All 5 files importing old Config updated to use Settings/constants

### Data Layer

- [x] **DATA-01**: OHLCV client exists at src/backend/data/ohlcv_client.py
- [x] **DATA-02**: Client uses CCXT library with Binance exchange
- [x] **DATA-03**: Client fetches 1w, 1d, 4h candle timeframes
- [x] **DATA-04**: Client supports BTC/USDT, ETH/USDT, SOL/USDT symbols
- [x] **DATA-05**: Client handles Binance rate limits with exponential backoff retry
- [x] **DATA-06**: market_data.py deprecated with backup notice

### Testing

- [ ] **TEST-01**: Unit tests for OHLCV client (mocked exchange calls)
- [ ] **TEST-02**: Unit tests for rate limit retry behavior
- [ ] **TEST-03**: Existing 11 smoke tests still pass after config changes

## Future Requirements

### v1.0 Core Agents

- **TA-01**: Full TA Ensemble implementation (Weekly, Daily, 4H subagents)
- **TA-02**: Wyckoff phase detection (A-E, springs, upthrusts, SOS/SOW)
- **TA-03**: Technical indicators (RSI, MACD, BB, ADX, OBV, VWAP, ATR, S/R)
- **NAN-01**: Nansen 5-signal accumulation/distribution framework
- **RISK-01**: Risk/Levels agent (2% max risk, 3:1 min R:R, S/R-based stops)
- **INT-01**: Integration tests on BTC, ETH, SOL

### v1.1 API & Dashboard

- **API-01**: FastAPI /morning-report endpoint
- **API-02**: FastAPI /chat endpoint
- **DASH-01**: Next.js dashboard with signal cards + chat

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time websocket streaming | Polling sufficient for v1 |
| Automated trade execution | Analysis/signals only |
| Mobile app | Web dashboard first |
| OAuth/social login | API key auth sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CFG-01 | Phase 5 | Complete |
| CFG-02 | Phase 5 | Complete |
| CFG-03 | Phase 5 | Complete |
| CFG-04 | Phase 5 | Complete |
| DATA-01 | Phase 6 | Complete |
| DATA-02 | Phase 6 | Complete |
| DATA-03 | Phase 6 | Complete |
| DATA-04 | Phase 6 | Complete |
| DATA-05 | Phase 6 | Complete |
| DATA-06 | Phase 6 | Complete |
| TEST-01 | Phase 7 | Pending |
| TEST-02 | Phase 7 | Pending |
| TEST-03 | Phase 7 | Pending |

**Coverage:**
- v0.2 requirements: 13 total
- Mapped to phases: 13
- Unmapped: 0

---
*Requirements defined: 2026-02-27*
*Last updated: 2026-02-27 after roadmap creation*
