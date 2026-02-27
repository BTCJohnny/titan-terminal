# Phase 6: OHLCV Data Client - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning
**Source:** User-provided context

<domain>
## Phase Boundary

Production-ready OHLCV client using CCXT with Binance for multi-timeframe candle data.

</domain>

<decisions>
## Implementation Decisions

### Data Source
- Use public Binance API via CCXT — no API key needed for OHLCV data

### File Location
- Client location: `src/backend/data/ohlcv_client.py`

### Timeframes
- Fetch 1w, 1d, 4h candles natively — no resampling required

### Symbols
- Minimum supported: BTC/USDT, ETH/USDT, SOL/USDT

### Error Handling
- Rate limit errors: exponential backoff retry

### Testing
- Tests must mock the CCXT exchange — no live API calls in tests

### Deprecation
- `src/backend/tools/market_data.py` gets a deprecation notice added but is NOT deleted

### Claude's Discretion
- Internal code organization within ohlcv_client.py
- Specific retry parameters (base delay, max retries, jitter)
- Helper function structure
- Type hints and Pydantic model design for responses

</decisions>

<specifics>
## Specific Ideas

- Use CCXT's `fetch_ohlcv()` method for candle retrieval
- Standard OHLCV format: [timestamp, open, high, low, close, volume]

</specifics>

<deferred>
## Deferred Ideas

- Additional symbols beyond the minimum three
- Historical data caching/persistence
- WebSocket streaming for real-time updates

</deferred>

---

*Phase: 06-ohlcv-data-client*
*Context gathered: 2026-02-27 via user input*
