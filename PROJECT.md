# Titan Terminal - PROJECT.md

## 1. Project Vision (The "Holy Shit" Product)
Build a clean, minimalist, browser-based trading terminal that I (a busy non-professional trader) open every morning at 8:30 AM local time and instantly see:
- A ranked list of 8–20 high-liquidity tokens worth investigating.
- Each token shows clear **Accumulation Score** OR **Distribution Score** (0–100).
- Suggested action: Long Spot / Long Hyperliquid / Short Hyperliquid / Avoid.
- Pre-calculated clean trading levels (entry zone, stop, TP1, TP2, RR ratio).
- One-click "Deep Dive" that opens the full agent report.
- Multi-timeframe heatmap (Weekly macro view + Daily signal + 4H confirmation).
- Persistent sidebar chat where I can type "analyze SOL" or "how's the market?".

I am NOT a good trader — I want the system to do 95% of the work so I only do the final human check and click the buttons myself on Hyperliquid.

## 2. Core Requirements
- **Scanning Universe**: Hyperliquid perpetuals + popular/active Nansen AI tokens that show real activity and have high market cap / liquidity (avoid low-float tokens that cause slippage).
- **Equal focus on Accumulation AND Distribution** (not just long bias).
- **Dedicated Wyckoff Agent** — identifies classic Wyckoff phases (A–E), springs, upthrusts, SOS/SOW, volume-price relationships on Daily/Weekly/4H.
- **Multi-timeframe logic**: Weekly for macro view, Daily for primary signal, 4H for confirmation/timing.
- **Self-Learning Loop**: Every signal is automatically saved to SQLite "SignalJournal" table. Orchestrator reviews past similar cases before new decisions ("this pattern worked 4/5 times when funding was negative"). I can reply in chat "SOL call was +18%, mark as win" and it learns.
- **Morning Batch**: Automatically runs at 8:30 AM local (or on dashboard load) and refreshes every 15 min.
- **General Chat**: Always available for ad-hoc analysis ("analyze this token", "market overview", etc.).

## 3. Multi-Agent Architecture (Mixture-of-Experts)
- **Nansen On-Chain Agent**: Whale flows, smart-money accumulation/distribution, inflows/outflows, perp activity.
- **Telegram Alpha Agent**: Uses existing SQLite + chat-header monitoring (keep exactly as in titan-trading).
- **Wyckoff Specialist Agent**: Full Wyckoff method on the three timeframes.
- **TA Ensemble Agent**: Numeric indicators + pattern recognition (keep existing playbooks from titan-trading).
- **Risk/Levels Agent**: Applies my 3 Laws, calculates clean levels, funding-rate filter, max 2% risk.
- **Orchestrator (main brain)**: Reads all outputs, applies 3 Laws, produces final ranked list.
- **Mentor Critic**: Separate cheap Opus 4.6 call for second opinion on every final signal.

All agents are specialized, have fixed system prompts, and use tools (Nansen API, TA libs, SQLite, etc.).

## 4. Model Usage (Must Respect My Subscription)
- **Main Orchestrator + all agents**: Use my paid Claude subscription (Opus 4.6) via official ANTHROPIC_API_KEY in .env.
- **Mentor Critic**: Separate Opus 4.6 call (keeps costs minimal — it only reviews finals).
- Use Claude Agent SDK (or LangGraph) for orchestration so everything stays clean and uses my real subscription.

## 5. Tech Stack (Keep What I Already Love)
- Backend: Python (keep all existing playbooks, Nansen code, Telegram SQLite logic from titan-trading repo).
- Agents runtime: Claude Agent SDK (pip install claude-agent-sdk) + my ANTHROPIC_API_KEY.
- Frontend: Next.js 15 App Router + Tailwind + shadcn/ui (minimalist dark institutional look, fast, keyboard friendly).
- Database: SQLite (add SignalJournal table for self-learning).
- Dashboard: Clean cards, heatmap, levels table, persistent chat.
- Deployment for now: Local (npm run dev for frontend + uvicorn/FastAPI for backend).

## 6. Non-Functional
- Minimalist, useful, no bloat.
- Smart API tiering (light scan → deep dive only on top candidates) to control costs.
- Atomic, testable code (GSD style).
- Full self-learning from day 1.
- No auto-trading — signals + levels only. I click on Hyperliquid.

## 7. Phase 0 (MVP — what we build first)
1. Multi-agent core in Python using Claude Agent SDK.
2. SQLite SignalJournal + self-learning logic.
3. Daily batch script that produces JSON output.
4. Simple FastAPI backend exposing /morning-report and /chat endpoints.
5. Next.js dashboard that consumes the API (clean cards + chat).

Later phases (heatmaps, more polish) come after.

## Success Criteria
When I open http://localhost:3000 at 8:30 AM I go "holy shit — these are the exact tokens I should be looking at, with clean levels, and the system has already learned from my past trades."

