# Titan Terminal

## What This Is

A multi-agent crypto trading dashboard that aggregates technical analysis, on-chain intelligence, and alpha signals into actionable trading opportunities. Backend in Python/FastAPI, frontend in Next.js, with specialized agents for different analysis dimensions.

## Core Value

Surface high-conviction trading setups by combining multi-timeframe technical analysis with on-chain smart money tracking — no signal without confluence.

## Requirements

### Validated

- ✓ Project structure established — existing
- ✓ Agent shell files created (orchestrator, nansen, telegram, ta_ensemble, risk_levels, mentor, wyckoff) — existing
- ✓ FastAPI backend scaffolding — existing
- ✓ Next.js frontend scaffolding — existing

### Active

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

**Current State:** Agent files exist but are empty shells. All need full implementation.

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

---
*Last updated: 2026-02-26 after initialization*
