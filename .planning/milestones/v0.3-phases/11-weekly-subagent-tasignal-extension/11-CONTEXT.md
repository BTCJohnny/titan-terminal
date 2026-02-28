# Phase 11: WeeklySubagent + TASignal Extension - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning
**Source:** User input

<domain>
## Phase Boundary

First fully functional subagent proving the complete analysis pipeline. Extends TASignal model with Wyckoff and alpha factor fields, implements WeeklySubagent that fetches weekly OHLCV data and produces comprehensive technical analysis signals.

</domain>

<decisions>
## Implementation Decisions

### File Locations
- WeeklySubagent at `src/backend/agents/ta_ensemble/weekly_subagent.py`
- Extend existing TASignal Pydantic model in `src/backend/models/`
- Uses WyckoffAnalysis from `src/backend/analysis/wyckoff.py`
- Uses AlphaFactors from `src/backend/analysis/alpha_factors.py`

### TASignal Extension
- Add two new nested fields: `wyckoff` (WyckoffAnalysis) and `alpha_factors` (AlphaFactors)
- Both fields should be optional for backward compatibility
- Existing TASignal tests must continue to pass

### WeeklySubagent Data Fetching
- Takes a symbol (e.g. "BTC/USDT") as input
- Fetches 1w OHLCV data using `get_ohlcv_client()` with limit=104 (2 years of weekly candles)
- If fewer than 52 candles returned: log warning with symbol, timeframe, and actual candle count, then proceed with available data

### Analysis Pipeline
Runs all analysis in sequence:
1. Calculate all indicators from `src/backend/analysis/indicators.py`
2. Calculate alpha factors from `src/backend/analysis/alpha_factors.py`
3. Run `detect_wyckoff` from `src/backend/analysis/wyckoff.py`
4. Determine overall trend direction (BULLISH/BEARISH/NEUTRAL) and confidence (0-100) based on confluence of RSI, MACD, ADX, and Wyckoff phase

### Output Format
- Output must be a valid TASignal JSON object
- Entry point: `WeeklySubagent.analyze(symbol) -> TASignal`

### Testing
- Full unit tests with mocked OHLCV data
- No live API calls in tests

### Claude's Discretion
- Internal helper methods and code organization within WeeklySubagent
- Specific confidence calculation weights for indicator confluence
- Error handling patterns beyond the required warning logging
- Type hints and docstring style

</decisions>

<specifics>
## Specific Ideas

- Symbol format: "BTC/USDT" style
- OHLCV limit: 104 candles (2 years weekly)
- Minimum history threshold: 52 candles before warning
- Trend directions: BULLISH, BEARISH, NEUTRAL
- Confidence range: 0-100

</specifics>

<deferred>
## Deferred Ideas

None — Phase 11 scope is well-defined

</deferred>

---

*Phase: 11-weekly-subagent-tasignal-extension*
*Context gathered: 2026-02-27 via user input*
