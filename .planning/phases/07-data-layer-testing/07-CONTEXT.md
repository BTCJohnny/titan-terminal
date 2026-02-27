# Phase 7: Data Layer Testing - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning
**Source:** User-provided context

<domain>
## Phase Boundary

Unit tests for `src/backend/data/ohlcv_client.py`. Comprehensive test coverage for the OHLCV client with mocked CCXT exchanges.

</domain>

<decisions>
## Implementation Decisions

### Test Location
- Test file: `src/backend/tests/test_ohlcv_client.py`

### Mocking Strategy
- All CCXT exchange calls MUST be mocked — no live API hits in tests

### Test Coverage Requirements
- Successful fetch returns correct dict structure (timestamp, open, high, low, close, volume)
- All 3 timeframes: 1w, 1d, 4h
- All 3 symbols: BTC/USDT, ETH/USDT, SOL/USDT
- Invalid symbol raises ValueError
- Invalid timeframe raises ValueError
- Rate limit error triggers exponential backoff retry
- `fetch_all_timeframes` returns data for all 3 timeframes

### Regression Safety
- All 11 existing smoke tests must still pass after adding new tests

### Claude's Discretion
- Test fixture design and organization
- Specific mock return values
- Test naming conventions (following project patterns)

</decisions>

<specifics>
## Specific Ideas

- Dict structure must include: timestamp, open, high, low, close, volume
- Timeframes to test: 1w, 1d, 4h
- Symbols to test: BTC/USDT, ETH/USDT, SOL/USDT
- Exponential backoff retry behavior for rate limits

</specifics>

<deferred>
## Deferred Ideas

None — context covers phase scope

</deferred>

---

*Phase: 07-data-layer-testing*
*Context gathered: 2026-02-27 via user input*
