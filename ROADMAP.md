# Titan Terminal — Roadmap

## Current Status
Milestone v0.1 (Project Scaffold) ✓ Complete
- Agent stubs, Pydantic models, config, 11/11 smoke tests passing
- Structure: src/backend/agents/ + src/frontend/

---

## Milestone v0.2 — Data Layer
- Binance OHLCV client via CCXT (src/backend/data/ohlcv_client.py)
- Timeframes: 1w, 1d, 4h — fetched natively, no resampling
- Symbols: BTC, ETH, SOL minimum
- Unit tests for all timeframes

---

## Milestone v0.3 — TA Ensemble
- WeeklySubagent, DailySubagent, FourHourSubagent
  - Wyckoff: phases A-E, springs, upthrusts, SOS/SOW, volume-price
  - Indicators: RSI, MACD, Bollinger Bands, ADX, OBV, VWAP, ATR, S/R levels
  - Alpha factors: momentum, volume anomaly, MA deviation, volatility score
- TAMentor (Opus) — reads all 3, reasons independently
  - Weekly/Daily bearish + 4H bullish → BEARISH, confidence -20
  - Weekly/Daily bullish + 4H bearish → BULLISH, confidence -20
  - Weekly vs Daily conflict → NO SIGNAL
  - 4H = entry timing only, never overrides direction
- Output: TAMentorSignal (direction, confidence, conflicts, warnings)
- Claude Agent SDK for subagent orchestration

---

## Milestone v0.4 — Nansen + Telegram Agents
- Nansen Agent: live Nansen MCP only
  - 5-signal framework: exchange flows, fresh wallets, smart money,
    top PnL wallets, whale activity
  - Funding rate check via Hyperliquid perps
  - Vault logging to agents/nansen/signal-combinations.md from day one
- Telegram Agent: reads signals.db at
  /Users/johnny_main/Developer/data/signals/signals.db
  - Clean rewrite (reference: titan-trading signals_fetcher.py, do not copy)

---

## Milestone v0.5 — Risk Agent + Orchestrator
- Risk Agent: 3 Laws enforced
  - Max 2% risk per trade
  - Min 3:1 R:R
  - Max 5 open positions
  - Output: entry zone, stop, TP1, TP2
- Orchestrator: combines all agent signals
  - Two Mentor calls: one inside TA Ensemble (TA only),
    one at final signal level
  - Output: OrchestratorOutput with final recommendation

---

## Milestone v0.6 — Integration + API
- End-to-end integration test: BTC, ETH, SOL
- FastAPI endpoints:
  - GET /morning-report — full signal for a symbol
  - POST /chat — conversational interface
- SQLite SignalJournal — logs every signal with timestamp and outcome

---

## Milestone v0.7 — Dashboard (MVP)
- Next.js frontend (src/frontend/)
- Morning report cards per symbol
- Key levels display (entry, stop, TP1, TP2)
- Signal confidence indicators
- Chat interface connected to /chat endpoint
- Dark mode

---

## Phase 2 — Polish (after dashboard is live)
- Multi-timeframe heatmap across watchlist
- Auto-refresh every 15 min + manual refresh button
- Keyboard shortcuts
- Export signal journal to CSV

---

## Phase 3 — Nice-to-Have
- Backtesting view against SignalJournal history
- Performance tracking: signal accuracy over time ★
- Alert system: push notification when high-confidence signal fires ★
- Watchlist management in dashboard ★

---

## ★ Suggested Features Worth Considering

**Signal accuracy tracking**
Every signal gets logged with outcome (did price move as expected?).
Over time TAMentor's confidence scores get calibrated against real results.
This is the self-learning loop — makes the system smarter the longer it runs.

**Watchlist beyond BTC/ETH/SOL**
The architecture already supports any symbol. A simple watchlist config
lets you scan 10-20 tokens in one morning report without code changes.

**Conflict log**
When TAMentor fires a NO SIGNAL due to Weekly vs Daily disagreement,
log it separately. Reviewing these over time reveals recurring patterns
worth adding to the conflict resolution rules.

**Push alerts**
When Orchestrator produces a high-confidence signal (>80%), send a
Telegram or email notification. Means you don't have to check the
dashboard — the dashboard comes to you.