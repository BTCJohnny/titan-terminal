# Titan Terminal

## What This Is

A full-stack crypto trading dashboard that surfaces high-conviction setups by combining multi-timeframe TA, on-chain smart money tracking, and Telegram signal intelligence. Backend: Python/FastAPI with 8 specialized agents and deterministic risk management. Frontend: Next.js dashboard with morning report, expandable signal detail, and conversational chat. Verified end-to-end on BTC/ETH/SOL.

## Core Value

Surface high-conviction trading setups by combining multi-timeframe technical analysis with on-chain smart money tracking — no signal without confluence.

## Current State

**Shipped:** v0.5 Risk Agent + API + Dashboard (2026-03-03)

**Codebase:** 14,653 Python LOC + 1,374 TypeScript LOC across 8 agents, 10 Pydantic models, full FastAPI backend, Next.js dashboard.

**What's Working:**
- Full agent pipeline: OHLCV → TA (3 subagents) → Nansen (5-signal) → Telegram → Risk (3 Laws) → Mentor synthesis
- Deterministic RiskAgent: S/R-derived stops/targets, 3:1 R:R enforcement, 2% risk cap, dual-mode position sizing
- Configurable watchlist with Telegram 72h signal supplementation
- FastAPI: /morning-report (on-demand ranked opportunities), /analyze/{symbol} (full pipeline), /chat (Anthropic SDK Q&A)
- Next.js dashboard: three-column layout with SymbolSidebar, SignalDetailPanel, NansenSignalCards, ChatPanel
- Integration tests: BTC/ETH/SOL verified end-to-end via live backend
- Obsidian vault logging for high-confidence signals

**Agent Architecture:**
- `ta_ensemble/` — WeeklySubagent, DailySubagent, FourHourSubagent, TAMentor
- Root agents — NansenAgent, TelegramAgent, RiskAgent (deterministic), Orchestrator

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
- ✓ NansenAgent with 5-signal framework (exchange flows, smart money, whales, top PnL, fresh wallets) — v0.4
- ✓ Funding rate overlay from Hyperliquid perps — v0.4
- ✓ Telegram agent connected to signals.db with 48h query window — v0.4
- ✓ NansenSignal Pydantic model with all MODL-01 fields — v0.4
- ✓ TelegramSignal Pydantic model with all MODL-02 fields — v0.4
- ✓ onchain_snapshots and ta_snapshots tables in signals.db — v0.4
- ✓ Database path from settings, not hardcoded — v0.4
- ✓ Obsidian vault logging for Nansen analysis — v0.4
- ✓ Graceful handling of missing MCP data — v0.4
- ✓ Unit tests for Nansen agent (28 tests) — v0.4
- ✓ Unit tests for Telegram agent (16 tests) — v0.4
- ✓ Unit tests for DB snapshot operations (13 tests) — v0.4
- ✓ End-to-end orchestrator integration — v0.4

- ✓ Risk/Levels agent with dual mode (risk zones + position sizing) — v0.5
- ✓ Configurable watchlist (settings + Telegram signal supplements) — v0.5
- ✓ Integration tests on BTC, ETH, SOL (full pipeline end-to-end) — v0.5
- ✓ FastAPI /morning-report endpoint (on-demand analysis, ranked) — v0.5
- ✓ FastAPI /chat endpoint (signal Q&A via Anthropic SDK) — v0.5
- ✓ Next.js morning report dashboard with expandable signal cards — v0.5
- ✓ market_data.py removed (migration complete) — v0.5

### Active

(To be defined in next milestone — run `/gsd:new-milestone`)

### Out of Scope

- Copying code from titan-trading — rewrite cleanly using as logic reference only
- Automated trade execution — this is analysis/signals only
- Mobile app — web dashboard first
- Real-time websocket streaming — polling sufficient for v1
- Modifying existing signals table — snapshot tables are append-only
- OAuth/user authentication — single-user tool, no auth needed

## Context

**Reference Repository:** `/Users/johnny_main/Developer/projects/titan-trading` — use for logic reference only, never copy code directly.

**Signals Database:** `/Users/johnny_main/Developer/data/signals/signals.db` — alpha leads from Telegram channels requiring on-chain validation.

**Architecture:**
- Backend: `src/backend/` — Python/FastAPI
- Frontend: `src/frontend/` — Next.js
- Agents: `src/backend/agents/` — 8 production agents (no stubs)
- Analysis: `src/backend/analysis/` — indicators, wyckoff, alpha_factors modules
- Data: `src/backend/data/` — OHLCV client for market data
- Models: `src/backend/models/` — Pydantic models for all signals
- Database: `src/backend/db/` — signals_db module for snapshot + journal storage
- API: `src/backend/api/main.py` — FastAPI with /morning-report, /analyze/{symbol}, /chat

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
| Dynamic watchlist | System discovers opportunities vs fixed list maintenance | ✓ Implemented in v0.5 (settings + Telegram 72h supplement) |
| Morning report = top opportunities only | Focus on highest conviction, not information overload | ✓ Implemented in v0.5 (ranked by confluence score) |
| Multi-timeframe TA pattern (v0.1) | Separate subagents per timeframe, TAMentor synthesizes with confluence scoring | ✓ Good |
| Nested Pydantic models (v0.1) | Better type safety and validation for hierarchical data | ✓ Good |
| Confidence 0-100 integers (v0.1) | Consistent confidence representation makes signal comparison easier | ✓ Good |
| Keep deprecated files for rollback (v0.1) | Safe migration path during scaffold phase | ✓ Resolved in v0.5 — deprecated stubs deleted |
| Settings class for env vars, constants.py for static (v0.2) | Clear separation of environment vs static configuration | ✓ Good |
| CCXT/Binance public API for OHLCV (v0.2) | No authentication needed, robust retry logic for rate limits | ✓ Good |
| Exponential backoff retry (1s, 2s, 4s + jitter) (v0.2) | Handles Binance rate limits gracefully without manual intervention | ✓ Good |
| Deprecate market_data.py (v0.2) | New OHLCV client superior, gradual migration path | ✓ Good |
| pandas-ta over TA-Lib (v0.3) | Pure Python, no C dependencies, easier installation | ✓ Good |
| Pure computational subagents (v0.3) | Deterministic analysis, no LLM calls for indicators | ✓ Good |
| Weighted confluence scoring (v0.3) | RSI (20), MACD (25), ADX (multiplier), Wyckoff (15-30) for robust signals | ✓ Good |
| Direct Anthropic SDK for TAMentor (v0.3) | Cleaner implementation, explicit conflict rules in prompt | ✓ Good |
| Nansen CLI subprocess over MCP (v0.4) | Production-ready without Claude Code dependency, graceful error handling | ✓ Good |
| Pure computational TelegramAgent (v0.4) | No LLM calls, direct DB query + confluence logic, deterministic | ✓ Good |
| Separate snapshot tables (v0.4) | Append-only snapshots preserve history without modifying signals table | ✓ Good |
| Module-level vault path override (v0.4) | Import vault_logger as module, override VAULT_PATH attribute — keeps vault_logger.py untouched | ✓ Good |
| model_dump(mode='json') for serialization (v0.4) | Handles datetime fields cleanly for Pydantic JSON serialization | ✓ Good |
| Deterministic RiskAgent (no LLM) (v0.5) | Pure-Python validator: no API costs, no latency, no non-determinism | ✓ Good |
| Wider stop wins rule (v0.5) | When S/R stop and proposed stop differ, use more conservative (further from entry) | ✓ Good |
| Direct Anthropic SDK for Mentor synthesis (v0.5) | Replaces MentorCriticAgent stub with explicit SDK call at temperature=0.2 | ✓ Good |
| On-demand /morning-report (v0.5) | No caching — always fresh analysis per request | ✓ Good — may revisit with scheduling |
| Three-column dashboard layout (v0.5) | SymbolSidebar / SignalDetailPanel / ChatPanel for clear information hierarchy | ✓ Good |

---
*Last updated: 2026-03-03 after v0.5 milestone*
