# Phase 8: Dependencies + Shared Indicators - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning
**Source:** User input during plan-phase

<domain>
## Phase Boundary

Establish the technical analysis foundation with a shared indicators module that provides all required indicator calculations for downstream analysis phases.

</domain>

<decisions>
## Implementation Decisions

### Library Choice
- Use pandas-ta for all indicator calculations — do NOT use TA-Lib

### Module Location
- Shared indicators module at `src/backend/analysis/indicators.py`

### Indicator Parameters
- RSI: period 14
- MACD: fast 12, slow 26, signal 9
- Bollinger Bands: period 20, std dev 2
- ADX: period 14
- OBV: standard calculation
- VWAP: standard calculation
- ATR: period 14
- Support/Resistance: identify 3 nearest support and 3 nearest resistance levels from recent price action

### Function Signatures
- All functions take a pandas DataFrame with columns: timestamp, open, high, low, close, volume
- All functions return either a scalar value or a dict — no side effects
- Pure functions only

### Dependencies
- Add pandas-ta and numpy to requirements.txt if not already present

### Testing
- Full unit tests with synthetic OHLCV data
- No live API calls in tests
- Verify calculations against known values

### Claude's Discretion
- Internal helper functions organization
- Exact scipy parameters for peak detection (support/resistance)
- Error handling approach for insufficient data
- Whether to cache indicator results or compute fresh

</decisions>

<specifics>
## Specific Ideas

- Support/resistance detection should use scipy peak detection
- All 28 existing tests must continue to pass
- Indicators must work with any OHLCV DataFrame (exchange-agnostic)

</specifics>

<deferred>
## Deferred Ideas

None — phase scope is clearly defined

</deferred>

---

*Phase: 08-dependencies-shared-indicators*
*Context gathered: 2026-02-27 via user input*
