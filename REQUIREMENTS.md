# Titan Terminal - REQUIREMENTS.md

## Functional Requirements
1. Daily 8:30 AM local batch run → ranked list of 8–20 high-liquidity tokens (Hyperliquid perps + popular Nansen AI tokens with high market cap / low slippage).
2. For each token: Accumulation Score OR Distribution Score (0–100), Wyckoff phase, suggested action (Long Spot / Long HL / Short HL / Avoid), clean levels (entry zone, stop, TP1, TP2, RR), confidence.
3. Multi-timeframe: Weekly (macro), Daily (signal), 4H (confirmation).
4. Self-learning: Every signal saved to SQLite SignalJournal; orchestrator references past outcomes automatically.
5. Persistent chat: "analyze XYZ", "how’s the market?", "mark SOL as win +18%" etc.
6. One-click deep dive report from dashboard.
7. All powered by my paid Claude subscription (Opus 4.6 main + separate cheap Opus 4.6 mentor).

## Non-Functional
- Minimalist dark UI (Next.js + shadcn).
- Smart cost control (light scan → deep dive).
- Keep all existing titan-trading Python playbooks/Nansen/Telegram SQLite logic.
- Local only for now (FastAPI backend + Next.js frontend).
