# Titan Terminal

## What This Is

A multi-agent crypto trading dashboard that aggregates technical analysis, on-chain intelligence, and alpha signals into actionable trading opportunities. Backend in Python/FastAPI with 9 specialized agents, frontend in Next.js, type-safe Pydantic output models, comprehensive test coverage, and production-ready data infrastructure.

## Core Value

Surface high-conviction trading setups by combining multi-timeframe technical analysis with on-chain smart money tracking — no signal without confluence.

## Current State

**Shipped:** v0.3 TA Ensemble (2026-02-28)

**Codebase:** 9,860 Python LOC across 9 agents, 10 Pydantic models, 158 tests (11 smoke + 147 unit).

**What's Working:**
- 3 pure computational subagents (WeeklySubagent, DailySubagent, FourHourSubagent) with weighted confluence scoring
- Shared indicators module (RSI, MACD, Bollinger Bands, ADX, OBV, VWAP, ATR, S/R)
- Wyckoff pattern detection (Phase A-E, springs, upthrusts, SOS/SOW)
- Alpha factors (momentum score, volume anomaly, MA deviation, volatility)
- TAMentor with direct Anthropic SDK and 4 conflict resolution rules
- Extended TASignal model with optional wyckoff and alpha_factors fields
- OHLCV client with CCXT/Binance for BTC/ETH/SOL on 1w/1d/4h timeframes

**Agent Architecture:**
- `ta_ensemble/` — WeeklySubagent, DailySubagent, FourHourSubagent, TAMentor
- Root agents — NansenAgent, TelegramAgent, RiskAgent, Orchestrator (shells)

**Test Status:** 158/158 tests passing (1 pre-existing smoke test failure, unrelated)

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
- ✓ Shared indicators module (RSI, MACD, BB, ADX, OBV, VWAP, ATR, S/R) — v0.3
- ✓ Wyckoff detection module (phases A-E, springs, upthrusts, SOS/SOW) — v0.3
- ✓ Alpha factors computation (momentum, volume anomaly, MA deviation, volatility) — v0.3
- ✓ Extended TASignal model with wyckoff and alpha_factors — v0.3
- ✓ WeeklySubagent implementation with full analysis — v0.3
- ✓ DailySubagent implementation with full analysis — v0.3
- ✓ FourHourSubagent implementation with full analysis — v0.3
- ✓ TAMentor using Anthropic SDK with MENTOR_MODEL — v0.3
- ✓ TAMentor conflict resolution (Weekly/Daily > 4H, -20 penalty, NO SIGNAL on W/D conflict) — v0.3
- ✓ Unit tests for indicators module — v0.3
- ✓ Unit tests for Wyckoff detection — v0.3
- ✓ Unit tests for subagents with mocked OHLCV — v0.3
- ✓ Unit tests for TAMentor with mocked responses — v0.3

### Active (v1.0+)

- [ ] Nansen agent with 5-signal accumulation/distribution framework
- [ ] Funding rate overlay from Hyperliquid perps
- [ ] Telegram agent connected to signals.db
- [ ] Risk/Levels agent (2% max risk, 3:1 min R:R, S/R-based stops)
- [ ] Integration tests on BTC, ETH, SOL
- [ ] FastAPI /morning-report endpoint (top opportunities)
- [ ] FastAPI /chat endpoint
- [ ] Next.js dashboard with signal cards + chat
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
- Agents: `src/backend/agents/` — 8 agent files exist
- Analysis: `src/backend/analysis/` — indicators, wyckoff, alpha_factors modules
- Data: `src/backend/data/` — OHLCV client for market data
- Models: `src/backend/models/` — Pydantic models for all signals

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
| Higher timeframe wins direction | Structural trends override short-term noise | ✓ Implemented in TAMentor v0.3 |
| S/R levels from TA drive stops/targets | Technical levels more meaningful than arbitrary ATR multiples | ✓ Implemented in indicators v0.3 |
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
| pandas-ta over TA-Lib (v0.3) | Pure Python, no C dependencies, easier installation | ✓ Good |
| Pure computational subagents (v0.3) | Deterministic analysis, no LLM calls for indicators | ✓ Good |
| Weighted confluence scoring (v0.3) | RSI (20), MACD (25), ADX (multiplier), Wyckoff (15-30) for robust signals | ✓ Good |
| Direct Anthropic SDK for TAMentor (v0.3) | Cleaner implementation, explicit conflict rules in prompt | ✓ Good |

---
*Last updated: 2026-02-28 after v0.3 milestone*
