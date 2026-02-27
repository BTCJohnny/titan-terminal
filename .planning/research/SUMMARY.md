# Research Summary: TA Ensemble Stack Additions

**Domain:** Technical Analysis Implementation - TA Ensemble
**Researched:** 2026-02-27
**Overall confidence:** MEDIUM

## Executive Summary

Research focused on stack additions for TA Ensemble (WeeklySubagent, DailySubagent, FourHourSubagent, TAMentor) implementation. The project already has validated OHLCV data infrastructure (CCXT/Binance), Pydantic models, and testing framework - no changes needed there.

**Three new dependencies required:**
1. **pandas-ta** (^0.3.14b) - All technical indicators (RSI, MACD, BB, ADX, OBV, VWAP, ATR)
2. **numpy** (^1.26.0) - Numerical computations for custom algorithms
3. **scipy** (^1.11.0) - Peak detection for support/resistance levels

**Critical finding:** pandas-ta over TA-Lib because it's pure Python (no C dependencies), actively maintained, and pandas-native. TA-Lib has notorious platform-specific installation issues that would block development.

**Wyckoff detection:** No production-ready libraries exist. Requires custom implementation using volume-price relationship analysis with numpy array operations and scipy peak detection.

**Alpha factors:** Custom implementation - straightforward calculations using computed indicators (momentum score, volume anomaly, MA deviation, volatility).

## Key Findings

**Stack:** pandas-ta + numpy + scipy (3 pure Python additions, no C compilation needed)

**Architecture:** Shared modules pattern - `indicators.py`, `wyckoff.py`, `alpha_factors.py` used by all 3 subagents to prevent duplication

**Critical decision rationale:** Avoid TA-Lib due to C library dependency causing cross-platform installation failures - pandas-ta provides identical functionality with zero installation issues

## Implications for Roadmap

Based on research, v0.3 TA Ensemble phases should be:

1. **Phase 1: Shared Indicators Module**
   - Addresses: All 8 required indicators (RSI, MACD, BB, ADX, OBV, VWAP, ATR, S/R)
   - Why first: Foundational - all 3 subagents depend on this
   - Complexity: Low - pandas-ta provides all indicators with 1-line calls
   - Testing: Straightforward unit tests with synthetic OHLCV data

2. **Phase 2: Alpha Factors Module**
   - Addresses: Momentum score, volume anomaly, MA deviation, volatility
   - Why second: Depends on indicators from Phase 1, independent of Wyckoff
   - Complexity: Low - simple calculations using indicator outputs
   - Testing: Easy to verify with known inputs

3. **Phase 3: Wyckoff Detection Module**
   - Addresses: Phases A-E, springs, upthrusts, SOS/SOW
   - Why third: Most complex, requires calibration, optional for basic TA
   - Complexity: Medium-High - custom algorithm, subjective thresholds
   - Testing: Requires synthetic volume-price patterns
   - **Research flag:** Likely needs additional research during implementation for threshold tuning

4. **Phase 4: WeeklySubagent Implementation**
   - Addresses: Full weekly analysis with extended TASignal
   - Why fourth: Proves out the full stack with shared modules
   - Complexity: Medium - integration of all modules
   - Testing: End-to-end with mocked OHLCV

5. **Phase 5: DailySubagent & FourHourSubagent**
   - Addresses: Daily and 4H analysis (parallel implementation)
   - Why fifth: Copy pattern from WeeklySubagent
   - Complexity: Low - code reuse from Phase 4
   - Testing: Same pattern as weekly

6. **Phase 6: TAMentor Conflict Resolution**
   - Addresses: Synthesis with conflict rules (W/D > 4H, -20 penalty, no signal on W/D conflict)
   - Why last: Requires all 3 subagents operational
   - Complexity: Medium - conflict logic + Claude API integration
   - Testing: Mock Claude responses, test conflict scenarios

**Phase ordering rationale:**
- Bottom-up approach: Foundation (indicators) → building blocks (alpha, Wyckoff) → consumers (subagents) → synthesis (mentor)
- Enables incremental testing: Each phase independently testable
- Parallelize Phase 5: Daily and 4H subagents can be implemented simultaneously once weekly proves pattern

**Research flags for phases:**
- Phase 1-2: Unlikely to need additional research (standard indicator calculations)
- Phase 3: **High probability** needs deeper research for Wyckoff threshold calibration
- Phase 4-6: Standard patterns, unlikely to need research

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack (pandas-ta) | HIGH | Industry standard, well-documented, proven in production trading systems |
| Stack (numpy/scipy) | HIGH | De facto standard for scientific computing, widely used |
| Integration pattern | HIGH | Straightforward DataFrame workflow, aligns with existing OHLCV client |
| Wyckoff approach | MEDIUM | No standard library - custom required, algorithm well-documented but thresholds subjective |
| Version numbers | MEDIUM | Based on training data (Jan 2025), should verify on PyPI before installation |

**Confidence limited by:** Web search and Context7 tools unavailable during research - could not verify latest versions or check for newer alternatives released after Jan 2025 cutoff.

## Gaps to Address

### Immediate Gaps (Before Implementation)
1. **Verify versions:** Run `pip index versions pandas-ta numpy scipy` to confirm latest stable versions
2. **Check pandas-ta maintenance:** Verify GitHub shows recent commits (was active as of Jan 2025)
3. **pandas dependency:** Confirm pandas is in requirements.txt (needed by pandas-ta)

### Phase-Specific Gaps (Resolve During Implementation)
1. **Phase 3 - Wyckoff thresholds:**
   - What volume multiple indicates "high volume"? (Research: 1.5x MA? 2x MA?)
   - What ATR ratio defines "narrow range"? (Research: <0.5? <0.7?)
   - How many candles needed for accurate phase detection? (Hypothesis: 100+ weekly, 200+ daily)
   - Need empirical testing with historical crypto data

2. **Phase 3 - Support/Resistance sensitivity:**
   - scipy `find_peaks()` prominence parameter needs tuning per timeframe
   - Weekly: Higher prominence (more significant levels)
   - 4H: Lower prominence (more granular levels)
   - Requires testing across BTC/ETH/SOL

3. **Phase 4-5 - Indicator periods:**
   - Use standard (RSI 14, MACD 12/26/9) or optimize per timeframe?
   - Recommendation: Start with standards, add optimization in v1.0

### Topics NOT Needing Phase-Specific Research
- Technical indicator calculations: pandas-ta handles, well-documented
- Alpha factor formulas: Straightforward math, no unknowns
- TAMentor conflict logic: Rules clearly defined in PROJECT.md
- Pydantic model extensions: Standard pattern, already used in project

## Verification Checklist

Before starting implementation:
- [ ] Run `pip install pandas-ta numpy scipy` in test environment - confirm no errors
- [ ] Verify pandas-ta imports: `import pandas_ta as ta` works
- [ ] Check pandas version: Should be ^2.0.0 (required by pandas-ta)
- [ ] Confirm scipy.signal.find_peaks available
- [ ] Review pandas-ta docs: https://github.com/twopirllc/pandas-ta (if web tools become available)

## Anti-Patterns Identified

**DO NOT:**
1. Install TA-Lib - platform-specific C library causes installation failures
2. Copy indicator code from titan-trading reference repo - use pandas-ta instead
3. Implement all indicators from scratch - reinventing the wheel, use pandas-ta
4. Use backtrader for indicators - heavyweight backtesting framework, overkill
5. Cache indicator results in Phase 1 - premature optimization, add in v1.0

**DO:**
1. Use pandas-ta for all standard indicators
2. Convert OHLCV dict to DataFrame immediately (enables pandas-ta API)
3. Create shared modules (indicators, wyckoff, alpha_factors) to avoid duplication
4. Test with synthetic DataFrame data, not live CCXT calls
5. Start with standard indicator periods, optimize later

## Success Criteria

Research complete when:
- [x] Stack additions identified with versions
- [x] pandas-ta vs TA-Lib decision made with rationale
- [x] Wyckoff approach documented (custom implementation required)
- [x] Alpha factors approach documented (custom calculations)
- [x] Integration patterns provided with code examples
- [x] Phase structure recommended with ordering rationale
- [x] Research gaps identified for Phase 3 (Wyckoff calibration)
- [x] Anti-patterns documented
- [x] Confidence levels assigned honestly

**Quality:** Comprehensive coverage of all NEW capabilities needed, clear integration points with existing stack, actionable implementation patterns with code examples.

---
*Research summary for v0.3 TA Ensemble stack additions*
*Researched: 2026-02-27*
*Confidence: MEDIUM (training data only, web verification tools unavailable)*
