# Phase 12: Daily + FourHour Subagents - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning
**Source:** User-provided context

<domain>
## Phase Boundary

Complete the remaining two timeframe subagents (DailySubagent and FourHourSubagent) following the established WeeklySubagent pattern from Phase 11.

</domain>

<decisions>
## Implementation Decisions

### File Locations
- DailySubagent at `src/backend/agents/ta_ensemble/daily_subagent.py`
- FourHourSubagent at `src/backend/agents/ta_ensemble/four_hour_subagent.py`

### Architecture Pattern
- Both follow the exact same pattern as WeeklySubagent
- Copy the architecture, not the code

### OHLCV Fetch Parameters
- DailySubagent: fetches 1d OHLCV with limit=730 (2 years daily)
- FourHourSubagent: fetches 4h OHLCV with limit=4380 (2 years 4H)

### Insufficient History Handling
- Both log a warning if insufficient candles returned and proceed with available data
- Minimum candle threshold for warning:
  - DailySubagent: < 365 candles
  - FourHourSubagent: < 720 candles

### Output
- Both output a valid TASignal (consistent with WeeklySubagent)

### Testing
- Full unit tests with mocked OHLCV for both
- No live API calls in tests

### Claude's Discretion
- Internal implementation details (private methods, helper functions)
- Test fixture structure (as long as OHLCV is mocked)
- Log message formatting

</decisions>

<specifics>
## Specific Ideas

- Mirror WeeklySubagent's computational pipeline structure
- Use same warning log format for consistency across all three subagents
- Test fixtures should cover: normal data, insufficient data, edge cases

</specifics>

<deferred>
## Deferred Ideas

None — phase scope is well-defined

</deferred>

---

*Phase: 12-daily-fourhour-subagents*
*Context gathered: 2026-02-28 via user-provided context*
