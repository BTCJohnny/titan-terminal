# Titan Terminal

## What This Is

A multi-agent crypto trading dashboard that aggregates technical analysis, on-chain intelligence, and alpha signals into actionable trading opportunities. Backend in Python/FastAPI with 9 specialized agents, frontend in Next.js, type-safe Pydantic output models, comprehensive test coverage, and production-ready data infrastructure.

## Core Value

Surface high-conviction trading setups by combining multi-timeframe technical analysis with on-chain smart money tracking — no signal without confluence.

## Current Milestone: v0.3 TA Ensemble

**Goal:** Implement fully functional TA subagents (Weekly, Daily, 4H) with Wyckoff detection, technical indicators, and alpha factors — plus TAMentor synthesis with conflict resolution.

**Target features:**
- WeeklySubagent, DailySubagent, FourHourSubagent producing extended TASignal
- Shared indicators module (RSI, MACD, Bollinger Bands, ADX, OBV, VWAP, ATR, S/R)
- Wyckoff phase detection (A-E, springs, upthrusts, SOS/SOW, volume-price)
- Alpha factors (momentum score, volume anomaly, MA deviation, volatility)
- TAMentor using claude-opus with conflict resolution rules
- Extended TASignal model with wyckoff and alpha_factors
- Full unit tests with mocked OHLCV data

## Current State

**Shipped:** v0.2 Data Foundation (2026-02-27)

**Codebase:** 4,901 Python LOC across 9 agents, 6 Pydantic models, 28 tests (11 smoke + 17 unit).

**Agent Architecture:**
- `ta_ensemble/` — WeeklySubagent, DailySubagent, FourHourSubagent, TAMentor
- Root agents — NansenAgent, TelegramAgent, RiskAgent, Orchestrator

**Data Infrastructure:**
- `data/ohlcv_client.py` — CCXT/Binance OHLCV client with exponential backoff retry
- Supports BTC/USDT, ETH/USDT, SOL/USDT on 1w, 1d, 4h timeframes
- `config/constants.py` — Trading constants (risk limits, symbols, scheduling)
- `config/settings.py` — Single source of truth for environment variables

**Test Status:** 28/28 tests passing (0.85s)

**Tech Debt:**
- Agents return dict (Pydantic integration via model_validate in tests)
- Deprecated agent files kept for rollback
- OHLCVClient not yet integrated into production code (planned for v1.0)
- market_data.py deprecated but still in use (migration pending)

## Requirements

### Validated

- ✓ Project structure established — existing
- ✓ Agent shell files created — existing
- ✓ FastAPI backend scaffolding — existing
- ✓ Next.js frontend scaffolding — existing
- ✓ Nested ta_ensemble/ folder with 4 subagent files — v0.1
- ✓ Root-level agents (nansen_agent, telegram_agent, risk_agent, orchestrator) — v0.1
- ✓ TASignal, TAMentorSignal, NansenSignal Pydantic models — v0.1
- ✓ TelegramSignal, RiskOutput, OrchestratorOutput Pydantic models — v0.1
- ✓ Settings module with python-dotenv — v0.1
- ✓ .env.example with all required keys — v0.1
- ✓ Smoke tests for all agents returning valid Pydantic output — v0.1
- ✓ All 11 smoke tests passing — v0.1
- ✓ Settings class single source of truth for environment variables — v0.2
- ✓ Trading constants (risk limits, symbol lists) in config/constants.py — v0.2
- ✓ Old Config class deleted entirely — v0.2
- ✓ All 5 files importing old Config migrated to Settings/constants — v0.2
- ✓ OHLCV client using CCXT + Binance (1w, 1d, 4h candles) — v0.2
- ✓ OHLCV client with exponential backoff retry for rate limits — v0.2
- ✓ market_data.py deprecated with backup notice — v0.2
- ✓ Unit tests for OHLCV client with mocked exchange — v0.2
- ✓ Unit tests for rate limit retry behavior — v0.2
- ✓ All 11 original smoke tests still pass — v0.2

### Active

- [ ] Shared indicators module (RSI, MACD, BB, ADX, OBV, VWAP, ATR, S/R)
- [ ] Wyckoff detection module (phases A-E, springs, upthrusts, SOS/SOW)
- [ ] Alpha factors computation (momentum, volume anomaly, MA deviation, volatility)
- [ ] Extended TASignal model with wyckoff and alpha_factors
- [ ] WeeklySubagent implementation with full analysis
- [ ] DailySubagent implementation with full analysis
- [ ] FourHourSubagent implementation with full analysis
- [ ] TAMentor using Anthropic SDK with MENTOR_MODEL
- [ ] TAMentor conflict resolution (Weekly/Daily > 4H, -20 penalty, NO SIGNAL on W/D conflict)
- [ ] Unit tests for indicators module
- [ ] Unit tests for Wyckoff detection
- [ ] Unit tests for subagents with mocked OHLCV
- [ ] Unit tests for TAMentor with mocked responses

### Future (v1.0+)

- [ ] TA Ensemble with 3 timeframe subagents (Weekly, Daily, 4H)
- [ ] Wyckoff phase detection (A-E, springs, upthrusts, SOS/SOW)
- [ ] Technical indicators (RSI, MACD, BB, ADX, OBV, VWAP, ATR, S/R)
- [ ] OHLCV alpha factors (momentum, volume anomaly, MA deviation, volatility)
- [ ] TAMentor using claude-opus-4-6 with conflict resolution logic
- [ ] Nansen agent with 5-signal accumulation/distribution framework
- [ ] Funding rate overlay from Hyperliquid perps
- [ ] Telegram agent connected to signals.db
- [ ] Risk/Levels agent (2% max risk, 3:1 min R:R, S/R-based stops)
- [ ] Integration tests on BTC, ETH, SOL
- [ ] FastAPI /morning-report endpoint (top opportunities)
- [ ] FastAPI /chat endpoint
- [ ] Next.js dashboard with signal cards + chat
- [ ] OHLCVClient integration into production agents
- [ ] Complete market_data.py migration

### Out of Scope

- Copying code from titan-trading — rewrite cleanly using as logic reference only
- Automated trade execution — this is analysis/signals only
- Mobile app — web dashboard first
- Real-time websocket streaming — polling sufficient for v1

## Context

**Reference Repository:** `/Users/johnny_main/Developer/projects/titan-trading` — use for logic reference only, never copy code directly.

**Signals Database:** `/Users/johnny_main/Developer/data/signals/signals.db` — alpha leads from Telegram channels requiring on-chain validation.

**Architecture:**
- Backend: `src/backend/` — Python/FastAPI
- Frontend: `src/frontend/` — Next.js
- Agents: `src/backend/agents/` — 8 agent files exist as shells
- Data: `src/backend/data/` — OHLCV client for market data

**Current State:** Agent files exist but are empty shells. All need full implementation. Data layer is production-ready with OHLCV client.

**TAMentor Conflict Resolution:**
- Higher timeframe wins direction (Weekly/Daily override 4H)
- Conflicts penalize confidence by ~20 points
- Weekly vs Daily conflict = no signal (genuine uncertainty)
- Warnings surface conflict context ("4H counter-trend bounce", "4H pullback — potential better entry")

**Nansen 5-Signal Framework:**
| # | Signal | Bullish (Accumulation) | Bearish (Distribution) |
|---|--------|------------------------|------------------------|
| 1 | Exchange Flows | Outflows | Inflows |
| 2 | Fresh Wallets | New buyers entering | Absent or selling |
| 3 | Smart Money | Buying or holding | Selling or reducing |
| 4 | Top PnL Traders | Net positive activity | Net negative activity |
| 5 | Whale Activity | Accumulating | Distributing |

Scoring: 4-5 bullish → ACCUMULATION, 2-3 → MIXED, 0-1 → DISTRIBUTION

**Funding Rate Overlay (Hyperliquid):**
- Above +0.01% → Crowded longs → bearish contrarian signal
- Below -0.01% → Crowded shorts → bullish contrarian signal

**Watchlist:** Dynamic from Telegram signals and Nansen alerts.

## Constraints

- **JSON Output**: Every agent must output valid JSON
- **No Code Copying**: Titan Trading code is reference only — rewrite cleanly
- **Testing**: Tests required for every agent
- **Parallel Development**: Titan Trading stays live — build Terminal in parallel
- **Risk Rules**: Max 2% portfolio risk per trade, minimum 3:1 reward-to-risk ratio

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Higher timeframe wins direction | Structural trends override short-term noise | — Pending |
| S/R levels from TA drive stops/targets | Technical levels more meaningful than arbitrary ATR multiples | — Pending |
| Dynamic watchlist | System discovers opportunities vs fixed list maintenance | — Pending |
| Morning report = top opportunities only | Focus on highest conviction, not information overload | — Pending |
| Multi-timeframe TA pattern (v0.1) | Separate subagents per timeframe, TAMentor synthesizes with confluence scoring | ✓ Good |
| Nested Pydantic models (v0.1) | Better type safety and validation for hierarchical data | ✓ Good |
| Confidence 0-100 integers (v0.1) | Consistent confidence representation makes signal comparison easier | ✓ Good |
| Keep deprecated files for rollback (v0.1) | Safe migration path during scaffold phase | ⚠️ Revisit in v1.0 |
| Settings class for env vars, constants.py for static (v0.2) | Clear separation of environment vs static configuration | ✓ Good |
| CCXT/Binance public API for OHLCV (v0.2) | No authentication needed, robust retry logic for rate limits | ✓ Good |
| Exponential backoff retry (1s, 2s, 4s + jitter) (v0.2) | Handles Binance rate limits gracefully without manual intervention | ✓ Good |
| Deprecate market_data.py (v0.2) | New OHLCV client superior, gradual migration path | ✓ Good |

---
*Last updated: 2026-02-27 after v0.3 milestone started*
