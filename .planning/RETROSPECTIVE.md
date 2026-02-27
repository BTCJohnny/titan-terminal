# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

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

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v0.1 | 11 | Smoke only | 6 Pydantic models |
| v0.2 | 28 | Smoke + Unit | OHLCVClient, retry decorator |

### Top Lessons (Verified Across Milestones)

1. Small, focused plans (1-3 tasks) enable fast, single-session execution
2. Phase verification (gsd-verifier, gsd-audit) catches integration issues early
3. Tech debt is acceptable when documented — consolidate in dedicated milestones

---

*Last updated: 2026-02-27 after v0.2 completion*
