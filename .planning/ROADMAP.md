# Roadmap: Titan Terminal

## Milestones

- [x] **v0.1 Project Scaffold** - Phases 1-4 (shipped 2026-02-26)
- [x] **v0.2 Data Foundation** - Phases 5-7 (shipped 2026-02-27)
- [ ] **v0.3 TA Ensemble** - Phases 8-13 (in progress)
- [ ] **v1.0 Core Agents** - TBD
- [ ] **v1.1 API & Dashboard** - TBD

## Phases

<details>
<summary>[x] v0.1 Project Scaffold (Phases 1-4) - SHIPPED 2026-02-26</summary>

- [x] Phase 1: Agent Structure (1/1 plans) - completed 2026-02-26
- [x] Phase 2: Pydantic Models (2/2 plans) - completed 2026-02-26
- [x] Phase 3: Configuration (1/1 plans) - completed 2026-02-26
- [x] Phase 4: Smoke Tests (2/2 plans) - completed 2026-02-26

See: `.planning/milestones/v0.1-ROADMAP.md`

</details>

<details>
<summary>[x] v0.2 Data Foundation (Phases 5-7) - SHIPPED 2026-02-27</summary>

- [x] Phase 5: Configuration Consolidation (1/1 plans) - completed 2026-02-27
- [x] Phase 6: OHLCV Data Client (1/1 plans) - completed 2026-02-27
- [x] Phase 7: Data Layer Testing (1/1 plans) - completed 2026-02-27

See: `.planning/milestones/v0.2-ROADMAP.md`

</details>

### v0.3 TA Ensemble (In Progress)

**Milestone Goal:** Implement fully functional TA subagents (Weekly, Daily, 4H) with Wyckoff detection, technical indicators, and alpha factors. TAMentor synthesizes all three with conflict resolution.

- [x] **Phase 8: Dependencies + Shared Indicators** - Install pandas-ta stack, implement shared indicators module (completed 2026-02-27)
- [x] **Phase 9: Alpha Factors Module** - Momentum, volume anomaly, MA deviation, volatility calculations (completed 2026-02-27)
- [x] **Phase 10: Wyckoff Detection Module** - Phases A-E, springs, upthrusts, SOS/SOW detection (completed 2026-02-27)
- [x] **Phase 11: WeeklySubagent + TASignal Extension** - First full subagent with extended model (completed 2026-02-27)
- [x] **Phase 12: Daily + FourHour Subagents** - Parallel implementation following weekly pattern (completed 2026-02-28)
- [x] **Phase 13: TAMentor Implementation** - Synthesis with conflict resolution rules (completed 2026-02-28)

## Phase Details

### Phase 8: Dependencies + Shared Indicators
**Goal**: Establish technical analysis foundation with all required indicators available
**Depends on**: Phase 7 (OHLCV client ready)
**Requirements**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-008, REQ-009, REQ-010, REQ-043, REQ-052, REQ-053, REQ-054, REQ-055
**Success Criteria** (what must be TRUE):
  1. `import pandas_ta` works without error after installation
  2. indicators.py calculates RSI, MACD, Bollinger Bands, ADX, OBV, VWAP, ATR for any OHLCV DataFrame
  3. Support/resistance levels detected using scipy peak detection
  4. Unit tests verify indicator calculations against known values
  5. All 28 existing tests still pass
**Plans**: 2 plans

Plans:
- [x] 08-01-PLAN.md — Install pandas-ta/scipy dependencies, create analysis package, implement 7 core indicator functions (completed 2026-02-27)
- [x] 08-02-PLAN.md — Implement support/resistance detection, create comprehensive unit tests for all indicators (completed 2026-02-27)

### Phase 9: Alpha Factors Module
**Goal**: Compute alpha factors that quantify market conditions for trading signals
**Depends on**: Phase 8 (indicators available)
**Requirements**: REQ-019, REQ-020, REQ-021, REQ-022, REQ-023, REQ-024, REQ-045
**Success Criteria** (what must be TRUE):
  1. alpha_factors.py computes momentum_score from rate of change and trend strength
  2. Volume anomaly detection flags unusual volume vs moving average
  3. MA deviation calculation shows price distance from key moving averages
  4. Volatility score normalizes ATR for cross-asset comparison
  5. AlphaFactors Pydantic model validates all computed values
  6. Unit tests verify alpha factor calculations
**Plans**: 2 plans

Plans:
- [x] 09-01-PLAN.md — Implement 4 alpha factor functions + AlphaFactors Pydantic model (completed 2026-02-27)
- [x] 09-02-PLAN.md — Create comprehensive unit tests, wire module exports (completed 2026-02-27)

### Phase 10: Wyckoff Detection Module
**Goal**: Detect Wyckoff accumulation/distribution patterns for market structure analysis
**Depends on**: Phase 8 (indicators available)
**Requirements**: REQ-011, REQ-012, REQ-013, REQ-014, REQ-015, REQ-016, REQ-017, REQ-018, REQ-044
**Success Criteria** (what must be TRUE):
  1. wyckoff.py identifies current phase (A-E) from volume-price patterns
  2. Spring events detected when price shakes out below support with low volume
  3. Upthrust events detected when price fails above resistance with low volume
  4. SOS (Sign of Strength) detected on breakout with high volume
  5. SOW (Sign of Weakness) detected on breakdown with high volume
  6. WyckoffAnalysis Pydantic model captures phase, events, and confidence
  7. Unit tests verify detection with synthetic accumulation/distribution patterns
**Plans**: 3 plans

Plans:
- [ ] 10-01-PLAN.md — Create WyckoffEvent and WyckoffAnalysis Pydantic models
- [ ] 10-02-PLAN.md — Implement detection functions (spring, upthrust, SOS, SOW) and phase classification
- [ ] 10-03-PLAN.md — Create comprehensive unit tests, wire module exports

### Phase 11: WeeklySubagent + TASignal Extension
**Goal**: First fully functional subagent proving the complete analysis pipeline
**Depends on**: Phase 9, Phase 10 (alpha factors and Wyckoff ready)
**Requirements**: REQ-025, REQ-026, REQ-027, REQ-028, REQ-031, REQ-032, REQ-033, REQ-034, REQ-046
**Success Criteria** (what must be TRUE):
  1. TASignal model extended with optional wyckoff and alpha_factors fields
  2. Existing TASignal tests pass (backward compatibility)
  3. WeeklySubagent fetches 2 years of weekly OHLCV via OHLCVClient
  4. WeeklySubagent produces extended TASignal with populated wyckoff and alpha_factors
  5. Warning logged if insufficient history available
  6. Unit tests verify WeeklySubagent output with mocked OHLCV
**Plans**: 3 plans

Plans:
- [ ] 11-01-PLAN.md — Extend TASignal model with optional wyckoff and alpha_factors fields
- [ ] 11-02-PLAN.md — Implement WeeklySubagent as pure computational pipeline
- [ ] 11-03-PLAN.md — Create comprehensive unit tests with mocked OHLCV data

### Phase 12: Daily + FourHour Subagents
**Goal**: Complete all three timeframe subagents using proven weekly pattern
**Depends on**: Phase 11 (weekly pattern established)
**Requirements**: REQ-029, REQ-030, REQ-047, REQ-048
**Success Criteria** (what must be TRUE):
  1. DailySubagent fetches ~730 daily candles and produces extended TASignal
  2. FourHourSubagent fetches ~4380 4H candles and produces extended TASignal
  3. Both subagents handle insufficient history gracefully with warnings
  4. Unit tests verify both subagents with mocked OHLCV
  5. All three subagents produce consistent TASignal structure
**Plans**: 2 plans

Plans:
- [ ] 12-01-PLAN.md — DailySubagent implementation + comprehensive test suite
- [ ] 12-02-PLAN.md — FourHourSubagent implementation + comprehensive test suite

### Phase 13: TAMentor Implementation
**Goal**: Synthesize all timeframe signals with intelligent conflict resolution
**Depends on**: Phase 12 (all subagents operational)
**Requirements**: REQ-035, REQ-036, REQ-037, REQ-038, REQ-039, REQ-040, REQ-041, REQ-042, REQ-049, REQ-050, REQ-051
**Success Criteria** (what must be TRUE):
  1. TAMentor calls Anthropic SDK directly with MENTOR_MODEL from settings
  2. TAMentor outputs valid TAMentorSignal Pydantic model
  3. When 4H contradicts Weekly/Daily direction, confidence penalized by 20 points
  4. When Weekly and Daily conflict, TAMentor returns NO SIGNAL
  5. 4H used for entry timing only, never overrides direction
  6. Conflict warnings surfaced in synthesis_notes field
  7. Unit tests cover all 3 conflict scenarios with mocked Claude responses
  8. All 28 original tests plus new tests pass (target 50+ total)
**Plans**: 2 plans

Plans:
- [ ] 13-01-PLAN.md — Reimplement TAMentor with direct Anthropic SDK and conflict resolution rules
- [ ] 13-02-PLAN.md — Comprehensive test suite covering all conflict scenarios

### v1.0 Core Agents (Planned)

Phases TBD - run `/gsd:new-milestone` to define

### v1.1 API & Dashboard (Planned)

Phases TBD - run `/gsd:new-milestone` to define

## Progress

**Execution Order:** Phases execute in numeric order: 8 -> 9 -> 10 -> 11 -> 12 -> 13

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Agent Structure | v0.1 | 1/1 | Complete | 2026-02-26 |
| 2. Pydantic Models | v0.1 | 2/2 | Complete | 2026-02-26 |
| 3. Configuration | v0.1 | 1/1 | Complete | 2026-02-26 |
| 4. Smoke Tests | v0.1 | 2/2 | Complete | 2026-02-26 |
| 5. Configuration Consolidation | v0.2 | 1/1 | Complete | 2026-02-27 |
| 6. OHLCV Data Client | v0.2 | 1/1 | Complete | 2026-02-27 |
| 7. Data Layer Testing | v0.2 | 1/1 | Complete | 2026-02-27 |
| 8. Dependencies + Shared Indicators | v0.3 | 2/2 | Complete | 2026-02-27 |
| 9. Alpha Factors Module | v0.3 | 2/2 | Complete | 2026-02-27 |
| 10. Wyckoff Detection Module | 3/3 | Complete    | 2026-02-27 | - |
| 11. WeeklySubagent + TASignal Extension | 3/3 | Complete    | 2026-02-27 | - |
| 12. Daily + FourHour Subagents | 2/2 | Complete    | 2026-02-28 | - |
| 13. TAMentor Implementation | 2/2 | Complete   | 2026-02-28 | - |

---
*Roadmap updated: 2026-02-28 for Phase 12 planning*
