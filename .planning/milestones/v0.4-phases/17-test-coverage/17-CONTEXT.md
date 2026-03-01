# Phase 17: Test Coverage - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning
**Source:** User decisions (inline)

<domain>
## Phase Boundary

Comprehensive unit test coverage for all Nansen agent, Telegram agent, and database functionality added in Phases 14-16.

</domain>

<decisions>
## Implementation Decisions

### Mocking Strategy
- Tests must use mocked data — never call the real Nansen CLI or real signals.db in unit tests
- Nansen tests: mock subprocess.run() to return realistic Nansen CLI JSON responses
- Telegram tests: use an in-memory SQLite database seeded with test data — do not connect to the real signals.db

### Nansen Agent Tests
- Test each of the 5 signals independently
- Test graceful handling when CLI returns error codes (CREDITS_EXHAUSTED, RATE_LIMITED)
- Test overall signal aggregation logic (4-5 bullish, 2-3 mixed, 0-1 bearish)
- Test vault logging writes to the correct file path

### Telegram Agent Tests
- Test with signals present (multiple directions for confluence testing)
- Test with no signals (empty result)
- Test 48h window filter (insert one signal older than 48h, verify it's excluded)
- Test confluence counting logic
- Test best_signal selection by confidence_score

### Database Tests
- Test CREATE TABLE IF NOT EXISTS for onchain_snapshots and ta_snapshots
- Test insert into both snapshot tables
- Verify existing signals table is untouched

### Test Location & Conventions
- Test file location: src/backend/tests/
- Follow existing test file naming conventions (test_*.py)
- Existing relevant files: test_nansen_agent.py, test_telegram_agent.py

### Claude's Discretion
- Internal test helper organization
- Fixture structure and conftest additions
- Assertion granularity within each test case

</decisions>

<specifics>
## Specific Ideas

- Mock subprocess.run() responses should match realistic Nansen CLI JSON output format
- In-memory SQLite for Telegram tests avoids filesystem side effects
- Error code handling tests: CREDITS_EXHAUSTED, RATE_LIMITED specifically called out
- Confluence testing needs multiple signal directions in test data

</specifics>

<deferred>
## Deferred Ideas

None — scope covers all Phase 14-16 functionality

</deferred>

---

*Phase: 17-test-coverage*
*Context gathered: 2026-03-01 via user decisions*
