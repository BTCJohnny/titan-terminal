# Phase 9: Alpha Factors Module - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning
**Source:** User input during plan-phase

<domain>
## Phase Boundary

Implement alpha factors module at `src/backend/analysis/alpha_factors.py` that computes quantitative market condition factors for trading signals. Uses existing indicators from Phase 8.

</domain>

<decisions>
## Implementation Decisions

### File Structure
- Single module: `src/backend/analysis/alpha_factors.py`
- Import ATR from existing `src/backend/analysis/indicators.py` — do not reimplement

### Function Signatures
- All 4 functions take a pandas DataFrame with columns: timestamp, open, high, low, close, volume
- Each function returns a dict with named fields — no raw scalars

### Momentum Score
- Rate of change over 10 and 20 periods
- Normalised to -100/+100 scale

### Volume Anomaly
- Current volume vs 20-period moving average
- Returns ratio and bool flag (True if >2x average)

### MA Deviation
- Price deviation from 20/50/200 EMAs
- Returns deviation as percentage for each MA

### Volatility Score
- ATR-based normalised volatility
- 0-100 scale

### Claude's Discretion
- Internal helper functions if needed
- Pydantic model structure for AlphaFactors
- Edge case handling (insufficient data)
- Specific normalisation formulas within constraints

</decisions>

<specifics>
## Specific Ideas

- Reuse ATR calculation from indicators.py
- Synthetic data for unit tests
- Full test coverage for all 4 factor functions

</specifics>

<deferred>
## Deferred Ideas

None — phase scope is well-defined

</deferred>

---

*Phase: 09-alpha-factors-module*
*Context gathered: 2026-02-27 via user input*
