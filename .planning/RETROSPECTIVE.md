# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v0.4 — Nansen Agent + Telegram Agent

**Shipped:** 2026-03-01
**Phases:** 6 | **Plans:** 13 | **Sessions:** ~4

### What Was Built
- NansenAgent with 5-signal on-chain framework (exchange flows, smart money, whales, top PnL, fresh wallets) via Nansen CLI subprocess
- Signal aggregation: 4-5 bullish = ACCUMULATION, 0-1 = DISTRIBUTION, contrarian funding rate overlay
- Obsidian vault logging for every Nansen analysis to signal-combinations.md
- TelegramAgent with signals.db integration, 48h query window, confluence counting, best signal identification
- NansenSignal and TelegramSignal Pydantic models with full type safety
- Database infrastructure: onchain_snapshots and ta_snapshots tables with startup initialization
- End-to-end orchestrator integration (Pydantic attribute access, model_dump serialization, snapshot storage)
- 57 new tests (28 Nansen + 16 Telegram + 13 DB)

### What Worked
- Milestone audit (gsd-audit-milestone) caught 3 integration gaps before completion — Phases 18 & 19 closed 2 of 3
- Pure computational agent pattern (no LLM) for TelegramAgent — fast, deterministic, easily testable
- Nansen CLI subprocess approach eliminated dependency on Claude Code MCP runtime
- Gap closure phases (18, 19) effectively addressed cross-module integration issues
- Comprehensive unit tests with mocked subprocess/DB enabled confident refactoring

### What Was Inefficient
- Initial Nansen MCP approach had to be replaced with CLI subprocess (Phase 15-04 was a mid-course correction)
- 8 requirements missing from SUMMARY frontmatter — documentation hygiene could be better
- `insert_ta_snapshot` built but never wired to any agent (premature infrastructure)
- Phase 18 and 19 were retroactively created after audit — could have been caught during initial planning

### Patterns Established
- CLI subprocess pattern for external tool integration (more portable than MCP dependency)
- Module-level attribute override pattern for configurable paths (vault_logger.VAULT_PATH)
- Startup hook pattern: chain init functions in FastAPI startup event
- Patch-at-import-site testing pattern for subprocess-based agents
- Gap closure phases for integration issues discovered during audit

### Key Lessons
1. Milestone audits before completion are essential — integration gaps between agents are invisible until tested end-to-end
2. CLI subprocess calls are more robust than MCP for production agents — no runtime dependency on Claude Code
3. Database infrastructure should be wired to agents immediately, not created as "forward-looking" dead code
4. Gap closure phases (18, 19) are a natural part of multi-agent milestone development — plan for them

### Cost Observations
- Model mix: 85% sonnet, 10% haiku, 5% opus (for audit)
- Sessions: ~4 (2 days elapsed)
- Notable: Gap closure phases (18, 19) were fast single-plan phases — tight scope from audit findings

---

## Milestone: v0.3 — TA Ensemble

**Shipped:** 2026-02-28
**Phases:** 6 | **Plans:** 14 | **Sessions:** ~6

### What Was Built
- Shared indicators module (RSI, MACD, Bollinger Bands, ADX, OBV, VWAP, ATR, S/R) using pandas-ta
- Wyckoff pattern detection (Phase A-E, Spring, Upthrust, SOS, SOW) with confidence scoring
- Alpha factors computation (momentum, volume anomaly, MA deviation, volatility)
- Extended TASignal model with optional wyckoff and alpha_factors fields
- 3 pure computational subagents (WeeklySubagent, DailySubagent, FourHourSubagent) with weighted confluence
- TAMentor reimplemented with direct Anthropic SDK and 4 explicit conflict resolution rules
- 107 new tests added (158 total)

### What Worked
- pandas-ta over TA-Lib decision eliminated C dependency headaches
- Pure computational pipeline for subagents — deterministic, fast, testable
- Weighted confluence scoring provides transparent signal derivation
- Direct Anthropic SDK in TAMentor — cleaner than BaseAgent inheritance
- Comprehensive test fixtures enabled reliable mocked testing
- Milestone audit (gsd-audit-milestone) verified 55/55 requirements before completion

### What Was Inefficient
- OHLCVClient integration required during subagent implementation (discovered dependency late)
- Some indicators (Bollinger Bands, OBV, VWAP) implemented but not consumed by subagent logic
- Pre-existing smoke test failure (test_daily_subagent_smoke) still unfixed

### Patterns Established
- Pure computational pipeline pattern: fetch → compute → synthesize (no LLM for indicators)
- Weighted confluence voting: RSI (20), MACD (25), ADX (multiplier), Wyckoff (15-30)
- Graceful degradation: return None on insufficient data, log warnings
- Import aliases for name collisions (TAMomentumData vs AlphaMomentumData)
- Event deduplication by candle_index for Wyckoff detection

### Key Lessons
1. Pure Python TA libraries (pandas-ta) are viable alternatives to C-based TA-Lib for most use cases
2. Computational pipelines are easier to test and debug than LLM-based analysis
3. Wyckoff detection needs threshold tuning per asset — configurable parameters essential
4. Conflict resolution rules embedded in prompts are more maintainable than hardcoded logic

### Cost Observations
- Model mix: 90% sonnet, 10% haiku (for quick research)
- Sessions: ~6 (3 days elapsed)
- Notable: 14-plan milestone executed smoothly with consistent 2-3 plans per phase

---

## Milestone: v0.2 — Data Foundation

**Shipped:** 2026-02-27
**Phases:** 3 | **Plans:** 3 | **Sessions:** ~3

### What Was Built
- Consolidated configuration (Settings class sole source of truth, constants.py for static values)
- Production-ready OHLCV client with CCXT/Binance integration
- Exponential backoff retry logic (1s, 2s, 4s + jitter) for rate limiting
- Comprehensive unit test suite (17 new tests covering data layer)

### What Worked
- Config consolidation was clean — complete deletion of old Config class, no compatibility shims
- Milestone audit (gsd-audit-milestone) provided confidence before completion
- Single-plan phases kept execution focused and fast
- Mocked exchange tests provide reliable CI without API dependencies

### What Was Inefficient
- OHLCVClient created but not integrated into production code (deferred to v1.0)
- market_data.py deprecated but still in use — migration incomplete
- Human verification for live API testing still pending

### Patterns Established
- Singleton pattern for data clients (get_ohlcv_client)
- Retry decorator pattern for external API calls
- Clear separation: Settings for env vars, constants.py for static values
- Exchange-level mocking strategy for CCXT tests

### Key Lessons
1. Config consolidation should happen early — parallel systems create cognitive overhead
2. Deprecation with DeprecationWarning is safer than immediate deletion for data layer code
3. Comprehensive unit tests with mocks enable confident refactoring

### Cost Observations
- Model mix: 95% sonnet, 5% haiku (quick tasks)
- Sessions: ~3 (1 day elapsed)
- Notable: Single-plan phases execute in under 3 minutes each

---

## Milestone: v0.1 — Project Scaffold

**Shipped:** 2026-02-26
**Phases:** 4 | **Plans:** 6 | **Sessions:** ~5

### What Was Built
- Multi-timeframe TA ensemble (weekly/daily/4h subagents + TAMentor synthesizer)
- 6 type-safe Pydantic models (TASignal, TAMentorSignal, NansenSignal, TelegramSignal, RiskOutput, OrchestratorOutput)
- Centralized settings module with python-dotenv
- Complete smoke test suite (11 tests, 100% pass rate)

### What Worked
- Phased approach: structure → models → config → tests
- Small, focused plans (1-3 tasks each) kept context manageable
- Pydantic validation in tests bridged the dict→model gap elegantly
- gsd-verifier caught wiring issues early (VERIFICATION.md for each phase)

### What Was Inefficient
- Two config systems created (old Config + new Settings) — migration deferred
- 10 TODO comments accumulated instead of integrating Pydantic models in agents
- Deprecated files kept for rollback safety — adds clutter

### Patterns Established
- Multi-timeframe TA pattern: separate subagents per timeframe, TAMentor synthesizes
- Nested Pydantic models for complex signal structures
- Confidence scoring as 0-100 integers across all models
- `*_agent.py` naming convention for root-level agents

### Key Lessons
1. Scaffold milestones can accept tech debt as intentional deferral — TODOs are fine when documented
2. Smoke tests validating Pydantic models provide confidence even when agents return dicts
3. Phase verification (gsd-verifier) catches integration gaps before they compound

### Cost Observations
- Model mix: 100% sonnet (scaffold work)
- Sessions: ~5 (2 days elapsed)
- Notable: Fast iteration — each phase completed in single session

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v0.1 | 5 | 4 | First milestone — established GSD workflow |
| v0.2 | 3 | 3 | Config consolidation, data layer foundation |
| v0.3 | 6 | 6 | Full TA pipeline, computational subagents, conflict resolution |
| v0.4 | 4 | 6 | On-chain + Telegram agents, gap closure phases, E2E integration |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v0.1 | 11 | Smoke only | 6 Pydantic models |
| v0.2 | 28 | Smoke + Unit | OHLCVClient, retry decorator |
| v0.3 | 158 | Comprehensive | indicators, wyckoff, alpha_factors, 3 subagents, TAMentor |
| v0.4 | 213 | Comprehensive | NansenAgent, TelegramAgent, signals_db, vault_logger |

### LOC Progression

| Milestone | Python LOC | Delta | Tests Added |
|-----------|------------|-------|-------------|
| v0.1 | 4,458 | - | 11 |
| v0.2 | 4,901 | +443 | 17 |
| v0.3 | 9,860 | +4,959 | 130 |
| v0.4 | 12,838 | +2,978 | 55 |

### Top Lessons (Verified Across Milestones)

1. Small, focused plans (1-3 tasks) enable fast, single-session execution
2. Phase verification (gsd-verifier, gsd-audit) catches integration issues early
3. Tech debt is acceptable when documented — consolidate in dedicated milestones
4. Pure computational pipelines are easier to test than LLM-based analysis
5. Milestone audits before completion catch requirements gaps early
6. Gap closure phases are a natural part of multi-agent development — plan for them
7. CLI subprocess calls are more robust than MCP for production agent integration

---

*Last updated: 2026-03-01 after v0.4 completion*
