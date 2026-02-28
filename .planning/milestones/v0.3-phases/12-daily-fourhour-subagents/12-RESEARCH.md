# Phase 12: Daily + FourHour Subagents - Research

**Researched:** 2026-02-28
**Domain:** Multi-timeframe subagent implementation, code pattern replication, OHLCV fetching across timeframes
**Confidence:** HIGH

## Summary

Phase 12 completes the remaining two timeframe subagents (DailySubagent and FourHourSubagent) by directly replicating the proven WeeklySubagent pattern from Phase 11. Both subagents follow identical architecture with only three parameter differences: timeframe string, candle limit, and minimum candle threshold. The WeeklySubagent implementation provides a complete, tested template that can be adapted with minimal changes.

All required components are production-ready: TASignal model extended with wyckoff/alpha_factors fields (Phase 11), all analysis functions tested (Phases 8-10), OHLCVClient supports all timeframes (Phase 6), and comprehensive test patterns exist (Phase 11). The work is mechanical pattern replication, not new algorithm development.

**Primary recommendation:** Copy the WeeklySubagent implementation and modify three constants per subagent: TIMEFRAME ("1d" for daily, "4h" for four-hour), CANDLE_LIMIT (730 for daily, 4380 for four-hour), and MIN_CANDLES_WARNING (365 for daily, 720 for four-hour). Replicate the test structure from test_weekly_subagent.py with adjusted synthetic data fixtures. Verify consistency by running all three subagent tests together.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**File Locations:**
- DailySubagent at `src/backend/agents/ta_ensemble/daily_subagent.py`
- FourHourSubagent at `src/backend/agents/ta_ensemble/four_hour_subagent.py`

**Architecture Pattern:**
- Both follow the exact same pattern as WeeklySubagent
- Copy the architecture, not the code (adjust constants only)

**OHLCV Fetch Parameters:**
- DailySubagent: fetches 1d OHLCV with limit=730 (2 years daily)
- FourHourSubagent: fetches 4h OHLCV with limit=4380 (2 years 4H)

**Insufficient History Handling:**
- Both log a warning if insufficient candles returned and proceed with available data
- Minimum candle threshold for warning:
  - DailySubagent: < 365 candles
  - FourHourSubagent: < 720 candles

**Output:**
- Both output a valid TASignal (consistent with WeeklySubagent)

**Testing:**
- Full unit tests with mocked OHLCV for both
- No live API calls in tests

### Claude's Discretion

- Internal implementation details (private methods, helper functions)
- Test fixture structure (as long as OHLCV is mocked)
- Log message formatting

### Deferred Ideas (OUT OF SCOPE)

None — phase scope is well-defined

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-029 | DailySubagent fetches ~730 daily candles | OHLCVClient supports "1d" timeframe, limit parameter validated in Phase 6 tests |
| REQ-030 | FourHourSubagent fetches ~4380 4H candles | OHLCVClient supports "4h" timeframe, tested with variable limits |
| REQ-047 | Both produce extended TASignal | TASignal model extended in Phase 11, supports wyckoff and alpha_factors fields |
| REQ-048 | Insufficient history handling with warnings | Python logging pattern established in WeeklySubagent, tested with caplog |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.5.0+ | TASignal validation, nested models | Already used across all subagents, extended in Phase 11 |
| pandas | 2.0.0+ | DataFrame operations for OHLCV | Required by analysis modules, tested across all timeframes |
| pytest | 7.4.0+ | Unit testing framework | Standard for all backend tests (74+ tests passing) |
| unittest.mock | Built-in | OHLCVClient mocking | Used in Phase 11 tests, no dependencies |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging | Built-in | Warning messages for insufficient data | Consistent with WeeklySubagent pattern |
| typing | Built-in | Type hints (Optional, tuple, etc.) | Project-wide standard |
| numpy | 2.0.0+ | Synthetic test data generation | Used in all test fixtures for deterministic patterns |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Code duplication | Abstract base class for subagents | Pattern replication is explicit and maintainable, abstraction adds complexity for 3 simple variants |
| Shared test fixtures | Timeframe-specific fixtures | Explicit fixtures per subagent make tests easier to understand and modify |
| Dynamic timeframe mapping | Hard-coded constants | Constants are clearer, no runtime logic needed for static values |

**Installation:**

All dependencies already present in requirements.txt:
```bash
# Already installed:
pydantic>=2.5.0
pandas>=2.0.0
pandas-ta>=0.3.14b
scipy>=1.11.0
ccxt>=4.0.0
pytest>=7.4.0
pytest-asyncio>=0.23.0
```

## Architecture Patterns

### Recommended Project Structure

```
src/backend/
├── models/
│   ├── ta_signal.py            # Extended in Phase 11 (wyckoff, alpha_factors)
│   ├── wyckoff.py              # Complete (Phase 10)
│   └── alpha_factors.py        # Complete (Phase 9)
├── analysis/
│   ├── indicators.py           # 8 functions (Phase 8)
│   ├── alpha_factors.py        # 4 functions (Phase 9)
│   └── wyckoff.py              # detect_wyckoff() (Phase 10)
├── data/
│   └── ohlcv_client.py         # Supports 1w, 1d, 4h (Phase 6)
├── agents/
│   └── ta_ensemble/
│       ├── weekly_subagent.py    # ✅ Complete (Phase 11)
│       ├── daily_subagent.py     # 🔨 IMPLEMENT THIS
│       └── fourhour_subagent.py  # 🔨 IMPLEMENT THIS (note: file name is four_hour_subagent.py)
└── tests/
    ├── test_weekly_subagent.py   # ✅ 16 tests passing (Phase 11)
    ├── test_daily_subagent.py    # 🔨 CREATE THIS
    └── test_fourhour_subagent.py # 🔨 CREATE THIS
```

### Pattern 1: Subagent Implementation via Template Replication

**What:** Create new timeframe subagents by copying WeeklySubagent and adjusting three constants

**When to use:** When implementing parallel functionality with only parameter differences

**Example:**
```python
# Source: src/backend/agents/ta_ensemble/weekly_subagent.py (Phase 11)
# Adaptation: Change TIMEFRAME, CANDLE_LIMIT, MIN_CANDLES_WARNING

class DailySubagent:
    """Daily timeframe technical analysis subagent.

    Pure computational pipeline that:
    1. Fetches 730 daily candles (2 years) via OHLCVClient
    2. Calculates all technical indicators
    3. Computes alpha factors
    4. Detects Wyckoff patterns
    5. Synthesizes into extended TASignal
    """

    TIMEFRAME = "1d"           # Was: "1w"
    CANDLE_LIMIT = 730         # Was: 104 (52 weeks * 2 years ≈ 104, 365 days * 2 ≈ 730)
    MIN_CANDLES_WARNING = 365  # Was: 52 (1 year daily = 365 candles)

    def analyze(self, symbol: str) -> TASignal:
        """Analyze daily timeframe for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")

        Returns:
            TASignal with populated wyckoff and alpha_factors fields

        Logs:
            Warning if fewer than 365 candles returned
        """
        # Identical implementation to WeeklySubagent.analyze()
        # Constants above automatically adapt behavior
        # ...


class FourHourSubagent:
    """Four-hour timeframe technical analysis subagent.

    Pure computational pipeline that:
    1. Fetches 4380 4H candles (2 years) via OHLCVClient
    2. Calculates all technical indicators
    3. Computes alpha factors
    4. Detects Wyckoff patterns
    5. Synthesizes into extended TASignal
    """

    TIMEFRAME = "4h"            # Was: "1w"
    CANDLE_LIMIT = 4380         # Was: 104 (6 candles/day * 365 days * 2 years ≈ 4380)
    MIN_CANDLES_WARNING = 720   # Was: 52 (6 months 4H = ~720 candles, threshold for warning)

    def analyze(self, symbol: str) -> TASignal:
        """Analyze 4-hour timeframe for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")

        Returns:
            TASignal with populated wyckoff and alpha_factors fields

        Logs:
            Warning if fewer than 720 candles returned
        """
        # Identical implementation to WeeklySubagent.analyze()
        # Constants above automatically adapt behavior
        # ...
```

**Key principles:**
- Three constant changes per subagent (TIMEFRAME, CANDLE_LIMIT, MIN_CANDLES_WARNING)
- All other code identical to WeeklySubagent
- TASignal timeframe field must match: "daily" for DailySubagent, "4h" for FourHourSubagent
- Same helper method structure (_calculate_indicators, _calculate_alpha_factors, _determine_trend_confluence, _build_ta_signal)

### Pattern 2: Timeframe-Specific Test Fixtures

**What:** Create separate test fixtures for each timeframe with appropriate candle counts

**When to use:** Testing timeframe-specific subagents with realistic data volumes

**Example:**
```python
# Source: src/backend/tests/test_weekly_subagent.py (Phase 11)
# Adaptation: Change candle count and time delta

@pytest.fixture
def synthetic_daily_ohlcv_730():
    """Generate 730 daily candles (2 years) with realistic patterns."""
    np.random.seed(42)
    base_price = 50000.0
    base_time = datetime.now() - timedelta(days=730)  # Was: weeks=104

    data = []
    price = base_price

    for i in range(730):  # Was: range(104)
        change = np.random.normal(0.005, 0.03)
        price = price * (1 + change)

        volatility = price * 0.03
        high = price + abs(np.random.normal(0, volatility))
        low = price - abs(np.random.normal(0, volatility))
        open_price = low + np.random.random() * (high - low)
        volume = np.random.uniform(100000, 500000)

        timestamp = int((base_time + timedelta(days=i)).timestamp() * 1000)  # Was: weeks=i

        data.append({
            'timestamp': timestamp,
            'open': float(open_price),
            'high': float(high),
            'low': float(low),
            'close': float(price),
            'volume': float(volume)
        })

    return data


@pytest.fixture
def synthetic_daily_ohlcv_200():
    """Generate 200 daily candles (insufficient history for warning test)."""
    # Similar structure, but only 200 candles (< 365 threshold)
    # ...


@pytest.fixture
def synthetic_fourhour_ohlcv_4380():
    """Generate 4380 4-hour candles (2 years) with realistic patterns."""
    np.random.seed(42)
    base_price = 45000.0
    base_time = datetime.now() - timedelta(hours=4*4380)  # 4H intervals

    data = []
    price = base_price

    for i in range(4380):
        change = np.random.normal(0.002, 0.02)  # Lower volatility for shorter timeframe
        price = price * (1 + change)

        volatility = price * 0.015
        high = price + abs(np.random.normal(0, volatility))
        low = price - abs(np.random.normal(0, volatility))
        open_price = low + np.random.random() * (high - low)
        volume = np.random.uniform(50000, 300000)  # Lower volume for 4H

        timestamp = int((base_time + timedelta(hours=4*i)).timestamp() * 1000)

        data.append({
            'timestamp': timestamp,
            'open': float(open_price),
            'high': float(high),
            'low': float(low),
            'close': float(price),
            'volume': float(volume)
        })

    return data


@pytest.fixture
def synthetic_fourhour_ohlcv_500():
    """Generate 500 4H candles (insufficient history for warning test)."""
    # Similar structure, but only 500 candles (< 720 threshold)
    # ...
```

**Fixture naming convention:**
- Format: `synthetic_{timeframe}_ohlcv_{count}`
- Sufficient data: Use CANDLE_LIMIT value (730 for daily, 4380 for 4H)
- Insufficient data: Use value below MIN_CANDLES_WARNING (200 < 365 for daily, 500 < 720 for 4H)

### Pattern 3: Consistent TASignal Timeframe Mapping

**What:** Map subagent class to TASignal timeframe Literal value

**When to use:** Building TASignal in _build_ta_signal() method

**Example:**
```python
# Source: TASignal model expects Literal["weekly", "daily", "4h"]
# From: src/backend/models/ta_signal.py

class WeeklySubagent:
    def _build_ta_signal(self, symbol, df, indicators, alpha_factors, wyckoff, direction, confidence) -> TASignal:
        return TASignal(
            symbol=symbol_base,
            timeframe="weekly",  # Hard-coded constant matching Literal
            # ...
        )

class DailySubagent:
    def _build_ta_signal(self, symbol, df, indicators, alpha_factors, wyckoff, direction, confidence) -> TASignal:
        return TASignal(
            symbol=symbol_base,
            timeframe="daily",  # Hard-coded constant matching Literal
            # ...
        )

class FourHourSubagent:
    def _build_ta_signal(self, symbol, df, indicators, alpha_factors, wyckoff, direction, confidence) -> TASignal:
        return TASignal(
            symbol=symbol_base,
            timeframe="4h",  # Hard-coded constant matching Literal
            # ...
        )
```

**Mapping:**
- WeeklySubagent → timeframe="weekly"
- DailySubagent → timeframe="daily"
- FourHourSubagent → timeframe="4h" (matches TIMEFRAME constant)

### Pattern 4: Test Isolation with Mocking

**What:** Use unittest.mock.patch to isolate subagent tests from OHLCVClient

**When to use:** Every subagent test to ensure no live API calls

**Example:**
```python
# Source: test_weekly_subagent.py (Phase 11)
# Replication: Same pattern for daily and fourhour tests

def test_daily_subagent_analyze(synthetic_daily_ohlcv_730):
    """Test DailySubagent with full 2 years of daily data."""
    mock_client = Mock()
    mock_client.fetch_ohlcv.return_value = synthetic_daily_ohlcv_730

    with patch('src.backend.agents.ta_ensemble.daily_subagent.get_ohlcv_client',
               return_value=mock_client):
        subagent = DailySubagent()
        result = subagent.analyze("BTC/USDT")

        # Verify mock called with correct parameters
        mock_client.fetch_ohlcv.assert_called_once_with(
            "BTC/USDT", "1d", limit=730
        )

        # Verify TASignal structure
        assert isinstance(result, TASignal)
        assert result.symbol == "BTC"
        assert result.timeframe == "daily"


def test_daily_insufficient_history_warning(synthetic_daily_ohlcv_200, caplog):
    """Verify warning logged when fewer than 365 candles returned."""
    mock_client = Mock()
    mock_client.fetch_ohlcv.return_value = synthetic_daily_ohlcv_200

    with patch('src.backend.agents.ta_ensemble.daily_subagent.get_ohlcv_client',
               return_value=mock_client):
        with caplog.at_level(logging.WARNING):
            subagent = DailySubagent()
            result = subagent.analyze("SOL/USDT")

            # Verify warning logged
            assert "Insufficient history" in caplog.text
            assert "200 candles" in caplog.text
            assert "SOL/USDT" in caplog.text

            # Verify analysis still completes
            assert isinstance(result, TASignal)
```

**Mock patch locations:**
- DailySubagent tests: `'src.backend.agents.ta_ensemble.daily_subagent.get_ohlcv_client'`
- FourHourSubagent tests: `'src.backend.agents.ta_ensemble.four_hour_subagent.get_ohlcv_client'`
- Must patch in the module where get_ohlcv_client is imported, not where it's defined

### Anti-Patterns to Avoid

- **Creating unique implementations:** Don't rewrite analysis logic per subagent. The only differences should be TIMEFRAME, CANDLE_LIMIT, and MIN_CANDLES_WARNING constants.
- **Inconsistent timeframe strings:** OHLCVClient uses "1d"/"4h", TASignal uses "daily"/"4h". Don't mix them up.
- **Shared test fixtures across timeframes:** Create separate fixtures per timeframe for clarity and maintenance.
- **Different confidence calculation logic:** Keep _determine_trend_confluence() identical across all three subagents for consistent signal quality.
- **Skipping insufficient data tests:** Both subagents must log warnings for insufficient history. Test this explicitly.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Subagent architecture | Custom implementation | Copy WeeklySubagent pattern | Proven in Phase 11, tested, consistent with project patterns |
| OHLCV data fetching | Custom CCXT calls | get_ohlcv_client() with timeframe parameter | Already supports 1d and 4h, tested in Phase 6 |
| Test data generation | Manual OHLCV arrays | np.random with seed for deterministic patterns | Used in all existing test fixtures (indicators, alpha, wyckoff, weekly) |
| Mock setup | Custom mock classes | unittest.mock.Mock and patch decorator | Standard library, proven in test_weekly_subagent.py |
| Indicator calculations | New implementations | Existing analysis module functions | Already tested with 26 indicator tests, 28 alpha tests, 20 wyckoff tests |

**Key insight:** Phase 12 is pattern replication, not innovation. WeeklySubagent provides a complete, tested template. The value is in consistency, not creativity.

## Common Pitfalls

### Pitfall 1: File Naming Inconsistency

**What goes wrong:** File named `fourhour_subagent.py` but user context specifies `four_hour_subagent.py`

**Why it happens:** Natural to use compact naming like "fourhour" instead of "four_hour"

**How to avoid:**
- Check user context: file location is `src/backend/agents/ta_ensemble/four_hour_subagent.py` (underscore between "four" and "hour")
- Match existing pattern: daily_subagent.py already exists, use same convention
- Class name: `FourHourSubagent` (CamelCase, no underscore)

**Warning signs:**
- Import errors: `ModuleNotFoundError: No module named 'four_hour_subagent'`
- File not found errors in tests

### Pitfall 2: Incorrect Candle Limit Calculations

**What goes wrong:** Using wrong math for CANDLE_LIMIT (e.g., 365*2 = 730 for daily is correct, but 4*365*2 = 2920 for 4H would be wrong)

**Why it happens:** Confusion about candles per day for 4H timeframe

**How to avoid:**
```python
# DAILY: 1 candle per day
# 2 years = 365 days/year * 2 years ≈ 730 candles
CANDLE_LIMIT = 730  # ✅ Correct

# 4-HOUR: 24 hours/day ÷ 4 hours/candle = 6 candles per day
# 2 years = 6 candles/day * 365 days/year * 2 years = 4380 candles
CANDLE_LIMIT = 4380  # ✅ Correct

# WRONG calculations:
# 4H: 4 * 365 * 2 = 2920  # ❌ Wrong (multiplying by 4 instead of dividing)
# 4H: 730 * 6 = 4380  # ✅ Correct, but less clear than direct calculation
```

**Warning signs:**
- Tests fetching wrong number of candles
- Insufficient history warnings when they shouldn't trigger
- OHLCVClient rate limits hit unexpectedly (requesting too many candles)

### Pitfall 3: Timeframe String Mismatch

**What goes wrong:** Using "1d" in TASignal timeframe field instead of "daily"

**Why it happens:** OHLCVClient uses "1d", easy to copy that into TASignal

**How to avoid:**
```python
# WRONG:
return TASignal(
    symbol=symbol,
    timeframe="1d",  # ❌ TASignal expects "daily", not "1d"
    # ...
)

# RIGHT:
class DailySubagent:
    TIMEFRAME = "1d"  # For OHLCVClient

    def _build_ta_signal(self, ...) -> TASignal:
        return TASignal(
            symbol=symbol,
            timeframe="daily",  # ✅ TASignal Literal value
            # ...
        )

# FourHourSubagent is simpler (both use "4h"):
class FourHourSubagent:
    TIMEFRAME = "4h"  # For OHLCVClient

    def _build_ta_signal(self, ...) -> TASignal:
        return TASignal(
            symbol=symbol,
            timeframe="4h",  # ✅ Same string works for both
            # ...
        )
```

**Warning signs:**
- Pydantic ValidationError: "Input should be 'weekly', 'daily' or '4h'"
- Test failures on TASignal instantiation

### Pitfall 4: Insufficient Data Threshold Confusion

**What goes wrong:** Using wrong MIN_CANDLES_WARNING threshold (e.g., 365 for 4H instead of 720)

**Why it happens:** Copy-paste error or unclear logic for what "insufficient" means per timeframe

**How to avoid:**
```python
# Rule: MIN_CANDLES_WARNING should be roughly "minimum useful history"
# For technical analysis, generally need at least 6-12 months of data

# DAILY: 1 year = 365 days
MIN_CANDLES_WARNING = 365  # ✅ 1 year daily

# 4-HOUR: 6 months = 180 days * 6 candles/day = 1080, but user specified 720
# User logic: Wyckoff needs 50+ candles (lowered from 100 in Phase 11)
# 720 candles / 6 candles per day = 120 days ≈ 4 months
MIN_CANDLES_WARNING = 720  # ✅ Per user specification (about 4 months)

# WRONG:
# 4H: MIN_CANDLES_WARNING = 365  # ❌ That's only 60 days of 4H data
# Daily: MIN_CANDLES_WARNING = 180  # ❌ User specified 365
```

**Warning signs:**
- Tests expecting warnings don't trigger them
- Warnings triggering on valid data (threshold too high)

### Pitfall 5: Copy-Paste Errors in Test Assertions

**What goes wrong:** Tests for DailySubagent still assert timeframe="weekly" due to copy-paste from test_weekly_subagent.py

**Why it happens:** Mechanical copying without adjusting assertions

**How to avoid:**
```python
# WRONG (in test_daily_subagent.py):
def test_daily_subagent_returns_ta_signal(synthetic_daily_ohlcv_730):
    # ...
    result = subagent.analyze("BTC/USDT")
    assert result.timeframe == "weekly"  # ❌ Copy-paste error

# RIGHT:
def test_daily_subagent_returns_ta_signal(synthetic_daily_ohlcv_730):
    # ...
    result = subagent.analyze("BTC/USDT")
    assert result.timeframe == "daily"  # ✅ Correct for DailySubagent

# For FourHourSubagent:
def test_fourhour_subagent_returns_ta_signal(synthetic_fourhour_ohlcv_4380):
    # ...
    result = subagent.analyze("BTC/USDT")
    assert result.timeframe == "4h"  # ✅ Correct for FourHourSubagent
```

**Checklist when copying test file:**
- [ ] Update fixture names (weekly → daily or fourhour)
- [ ] Update timeframe assertions ("weekly" → "daily" or "4h")
- [ ] Update candle count assertions (104 → 730 or 4380)
- [ ] Update warning threshold assertions (52 → 365 or 720)
- [ ] Update patch paths (weekly_subagent → daily_subagent or four_hour_subagent)

**Warning signs:**
- Test failures with "AssertionError: weekly != daily"
- Mock not being called (wrong patch path)

### Pitfall 6: Wyckoff Detection Threshold

**What goes wrong:** Changing the 50-candle threshold for Wyckoff detection per timeframe

**Why it happens:** Assumption that shorter timeframes need different thresholds

**How to avoid:**
```python
# In WeeklySubagent (Phase 11):
wyckoff = detect_wyckoff(df) if len(df) >= 50 else None

# Keep SAME threshold for all subagents:
# DailySubagent:
wyckoff = detect_wyckoff(df) if len(df) >= 50 else None  # ✅ Same 50

# FourHourSubagent:
wyckoff = detect_wyckoff(df) if len(df) >= 50 else None  # ✅ Same 50

# WRONG:
# wyckoff = detect_wyckoff(df) if len(df) >= 100 else None  # ❌ Different threshold
```

**Reasoning:**
- User lowered threshold from 100 to 50 in Phase 11 for "better symbol coverage"
- This threshold is about Wyckoff algorithm requirements, not timeframe-specific
- Consistent threshold = consistent behavior across all three subagents

**Warning signs:**
- Different wyckoff detection rates across timeframes
- Tests failing due to unexpected None wyckoff results

## Code Examples

Verified patterns from WeeklySubagent (Phase 11) adapted for Phase 12:

### Example 1: DailySubagent Implementation

```python
# File: src/backend/agents/ta_ensemble/daily_subagent.py
# Source: WeeklySubagent from Phase 11, adapted for daily timeframe

"""Daily Timeframe TA Subagent - Pure computational analysis pipeline.

This subagent fetches 2 years of daily OHLCV data and produces comprehensive
technical analysis including indicators, alpha factors, and Wyckoff detection.
No LLM calls are made - all analysis is deterministic computation.
"""
import logging
from typing import Optional

import pandas as pd

from src.backend.data.ohlcv_client import get_ohlcv_client
from src.backend.models.ta_signal import (
    TASignal, TrendData, MomentumData as TAMomentumData,
    KeyLevels, PatternData, OverallAssessment
)
from src.backend.models.wyckoff import WyckoffAnalysis
from src.backend.models.alpha_factors import (
    AlphaFactors,
    MomentumData as AlphaMomentumData,
    VolumeAnomalyData,
    MADeviationData,
    VolatilityData
)
from src.backend.analysis import (
    calculate_rsi, calculate_macd, calculate_adx,
    detect_support_resistance,
    calculate_momentum_score, detect_volume_anomaly,
    calculate_ma_deviation, calculate_volatility_score,
    detect_wyckoff
)

logger = logging.getLogger(__name__)


class DailySubagent:
    """Daily timeframe technical analysis subagent.

    Pure computational pipeline that:
    1. Fetches 730 daily candles (2 years) via OHLCVClient
    2. Calculates all technical indicators
    3. Computes alpha factors
    4. Detects Wyckoff patterns
    5. Synthesizes into extended TASignal
    """

    TIMEFRAME = "1d"
    CANDLE_LIMIT = 730  # 2 years of daily candles
    MIN_CANDLES_WARNING = 365  # Warn if less than 1 year

    def analyze(self, symbol: str) -> TASignal:
        """Analyze daily timeframe for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")

        Returns:
            TASignal with populated wyckoff and alpha_factors fields

        Logs:
            Warning if fewer than 365 candles returned
        """
        # Implementation identical to WeeklySubagent
        # (see WeeklySubagent for full implementation details)
        # ...

        # Only difference: timeframe field in _build_ta_signal returns "daily"
        return self._build_ta_signal(
            symbol, df, indicators, alpha_factors, wyckoff, direction, confidence
        )

    # All helper methods identical to WeeklySubagent:
    # _calculate_indicators()
    # _calculate_alpha_factors()
    # _determine_trend_confluence()
    # _build_ta_signal()  # Returns timeframe="daily"
    # _generate_notes()
```

### Example 2: FourHourSubagent Implementation

```python
# File: src/backend/agents/ta_ensemble/four_hour_subagent.py
# Source: WeeklySubagent from Phase 11, adapted for 4-hour timeframe

"""Four-Hour Timeframe TA Subagent - Pure computational analysis pipeline.

This subagent fetches 2 years of 4-hour OHLCV data and produces comprehensive
technical analysis including indicators, alpha factors, and Wyckoff detection.
No LLM calls are made - all analysis is deterministic computation.
"""
import logging
from typing import Optional

import pandas as pd

from src.backend.data.ohlcv_client import get_ohlcv_client
from src.backend.models.ta_signal import (
    TASignal, TrendData, MomentumData as TAMomentumData,
    KeyLevels, PatternData, OverallAssessment
)
from src.backend.models.wyckoff import WyckoffAnalysis
from src.backend.models.alpha_factors import (
    AlphaFactors,
    MomentumData as AlphaMomentumData,
    VolumeAnomalyData,
    MADeviationData,
    VolatilityData
)
from src.backend.analysis import (
    calculate_rsi, calculate_macd, calculate_adx,
    detect_support_resistance,
    calculate_momentum_score, detect_volume_anomaly,
    calculate_ma_deviation, calculate_volatility_score,
    detect_wyckoff
)

logger = logging.getLogger(__name__)


class FourHourSubagent:
    """Four-hour timeframe technical analysis subagent.

    Pure computational pipeline that:
    1. Fetches 4380 4-hour candles (2 years) via OHLCVClient
    2. Calculates all technical indicators
    3. Computes alpha factors
    4. Detects Wyckoff patterns
    5. Synthesizes into extended TASignal
    """

    TIMEFRAME = "4h"
    CANDLE_LIMIT = 4380  # 2 years of 4-hour candles (6 per day * 365 * 2)
    MIN_CANDLES_WARNING = 720  # Warn if less than ~4 months

    def analyze(self, symbol: str) -> TASignal:
        """Analyze 4-hour timeframe for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")

        Returns:
            TASignal with populated wyckoff and alpha_factors fields

        Logs:
            Warning if fewer than 720 candles returned
        """
        # Implementation identical to WeeklySubagent
        # (see WeeklySubagent for full implementation details)
        # ...

        # Only difference: timeframe field in _build_ta_signal returns "4h"
        return self._build_ta_signal(
            symbol, df, indicators, alpha_factors, wyckoff, direction, confidence
        )

    # All helper methods identical to WeeklySubagent:
    # _calculate_indicators()
    # _calculate_alpha_factors()
    # _determine_trend_confluence()
    # _build_ta_signal()  # Returns timeframe="4h"
    # _generate_notes()
```

### Example 3: Test Structure for DailySubagent

```python
# File: src/backend/tests/test_daily_subagent.py
# Source: test_weekly_subagent.py from Phase 11, adapted for daily

"""Unit tests for DailySubagent.

Tests verify:
- OHLCV data fetching via mocked OHLCVClient
- Indicator calculation pipeline
- Alpha factor computation
- Wyckoff detection integration
- TASignal output structure
- Warning logging for insufficient data
- No live API calls (all mocked)
"""
import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import logging

from src.backend.agents.ta_ensemble.daily_subagent import DailySubagent
from src.backend.models.ta_signal import TASignal


@pytest.fixture
def synthetic_daily_ohlcv_730():
    """Generate 730 daily candles (2 years) with realistic patterns."""
    np.random.seed(42)
    base_price = 50000.0
    base_time = datetime.now() - timedelta(days=730)

    data = []
    price = base_price

    for i in range(730):
        change = np.random.normal(0.005, 0.03)
        price = price * (1 + change)

        volatility = price * 0.03
        high = price + abs(np.random.normal(0, volatility))
        low = price - abs(np.random.normal(0, volatility))
        open_price = low + np.random.random() * (high - low)
        volume = np.random.uniform(100000, 500000)

        timestamp = int((base_time + timedelta(days=i)).timestamp() * 1000)

        data.append({
            'timestamp': timestamp,
            'open': float(open_price),
            'high': float(high),
            'low': float(low),
            'close': float(price),
            'volume': float(volume)
        })

    return data


@pytest.fixture
def synthetic_daily_ohlcv_200():
    """Generate 200 daily candles (insufficient history for warning test)."""
    # Similar structure, only 200 candles
    # ...


class TestDailySubagentStructure:
    """Test DailySubagent class structure and constants."""

    def test_subagent_has_required_constants(self):
        """Verify DailySubagent has required class constants."""
        subagent = DailySubagent()
        assert subagent.TIMEFRAME == "1d"
        assert subagent.CANDLE_LIMIT == 730
        assert subagent.MIN_CANDLES_WARNING == 365


class TestDailySubagentAnalyze:
    """Test DailySubagent.analyze() method."""

    def test_analyze_returns_ta_signal(self, synthetic_daily_ohlcv_730):
        """Verify analyze() returns valid TASignal instance."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_daily_ohlcv_730

        with patch('src.backend.agents.ta_ensemble.daily_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = DailySubagent()
            result = subagent.analyze("BTC/USDT")

            assert isinstance(result, TASignal)
            assert result.symbol == "BTC"
            assert result.timeframe == "daily"  # ✅ Not "weekly"

    def test_analyze_calls_ohlcv_client_correctly(self, synthetic_daily_ohlcv_730):
        """Verify analyze() calls OHLCVClient with correct parameters."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_daily_ohlcv_730

        with patch('src.backend.agents.ta_ensemble.daily_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = DailySubagent()
            subagent.analyze("ETH/USDT")

            mock_client.fetch_ohlcv.assert_called_once_with(
                "ETH/USDT", "1d", limit=730  # ✅ Not "1w", limit=104
            )


class TestDailySubagentLogging:
    """Test warning logging for insufficient history."""

    def test_warning_logged_for_insufficient_candles(self, synthetic_daily_ohlcv_200, caplog):
        """Verify warning logged when fewer than 365 candles returned."""
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_daily_ohlcv_200

        with patch('src.backend.agents.ta_ensemble.daily_subagent.get_ohlcv_client',
                   return_value=mock_client):
            with caplog.at_level(logging.WARNING):
                subagent = DailySubagent()
                result = subagent.analyze("SOL/USDT")

                # Verify warning was logged
                assert "Insufficient history" in caplog.text
                assert "200 candles" in caplog.text  # ✅ Not "30 candles"
                assert "SOL/USDT" in caplog.text

                # Verify analysis still completes
                assert isinstance(result, TASignal)
                assert result.symbol == "SOL"


# Additional test classes:
# - TestDailySubagentExtendedFields (verify wyckoff, alpha_factors populated)
# - TestDailySubagentNoLiveAPICalls (verify mocking works)
```

### Example 4: Test Structure for FourHourSubagent

```python
# File: src/backend/tests/test_fourhour_subagent.py
# Source: test_weekly_subagent.py from Phase 11, adapted for 4-hour

@pytest.fixture
def synthetic_fourhour_ohlcv_4380():
    """Generate 4380 4-hour candles (2 years) with realistic patterns."""
    np.random.seed(42)
    base_price = 45000.0
    base_time = datetime.now() - timedelta(hours=4*4380)

    data = []
    price = base_price

    for i in range(4380):
        change = np.random.normal(0.002, 0.02)
        price = price * (1 + change)

        volatility = price * 0.015
        high = price + abs(np.random.normal(0, volatility))
        low = price - abs(np.random.normal(0, volatility))
        open_price = low + np.random.random() * (high - low)
        volume = np.random.uniform(50000, 300000)

        timestamp = int((base_time + timedelta(hours=4*i)).timestamp() * 1000)

        data.append({
            'timestamp': timestamp,
            'open': float(open_price),
            'high': float(high),
            'low': float(low),
            'close': float(price),
            'volume': float(volume)
        })

    return data


class TestFourHourSubagentStructure:
    def test_subagent_has_required_constants(self):
        subagent = FourHourSubagent()
        assert subagent.TIMEFRAME == "4h"
        assert subagent.CANDLE_LIMIT == 4380
        assert subagent.MIN_CANDLES_WARNING == 720


class TestFourHourSubagentAnalyze:
    def test_analyze_returns_ta_signal(self, synthetic_fourhour_ohlcv_4380):
        mock_client = Mock()
        mock_client.fetch_ohlcv.return_value = synthetic_fourhour_ohlcv_4380

        with patch('src.backend.agents.ta_ensemble.four_hour_subagent.get_ohlcv_client',
                   return_value=mock_client):
            subagent = FourHourSubagent()
            result = subagent.analyze("BTC/USDT")

            assert isinstance(result, TASignal)
            assert result.symbol == "BTC"
            assert result.timeframe == "4h"  # ✅ Matches both TIMEFRAME and Literal
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LLM-based TA subagents with prompts | Pure computational pipeline | Phase 11 (WeeklySubagent) | Deterministic, no API costs, testable |
| Separate implementations per timeframe | Template replication pattern | Phase 12 (current) | Consistency across all three subagents |
| Dict-based outputs | Pydantic TASignal model | Phase 11 | Type safety, validation |
| Manual OHLCV formatting | OHLCVClient + pandas DataFrame | Phases 6-11 | Clean separation, retry logic, rate limiting |

**Deprecated/outdated:**
- **Old LLM-based DailySubagent and FourHourSubagent:** Files exist at ta_ensemble/daily_subagent.py (102 lines, agent-based) and ta_ensemble/fourhour_subagent.py (103 lines, agent-based). These will be completely replaced with computational implementations following the WeeklySubagent pattern.

## Open Questions

1. **File Naming Clarification**
   - What we know: User context says "four_hour_subagent.py" (with underscore)
   - What's unclear: Existing file is "fourhour_subagent.py" (no underscore)
   - Recommendation: Follow user context exactly: use `four_hour_subagent.py`. The user explicitly specified this in CONTEXT.md decisions. If existing file needs renaming, that should be done as part of replacement.

2. **Symbol Extraction Pattern**
   - What we know: WeeklySubagent extracts symbol base with `symbol.split('/')[0]`
   - What's unclear: Is this the standard pattern or should we use a helper function?
   - Recommendation: Keep same pattern across all subagents for consistency. If refactoring needed, do it in a separate phase for all three at once.

3. **Test Fixture Volatility**
   - What we know: Weekly uses 3% volatility, daily could use same or different
   - What's unclear: Should shorter timeframes use lower volatility to reflect reality?
   - Recommendation: Use slightly lower volatility for 4H (1.5-2%) to reflect shorter timeframe noise, but keep daily same as weekly (3%) since both are swing/position timeframes.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.4.0+ |
| Config file | None — pytest auto-discovers tests/ directory |
| Quick run command | `PYTHONPATH=/Users/johnny_main/Developer/projects/titan-terminal pytest src/backend/tests/test_daily_subagent.py src/backend/tests/test_fourhour_subagent.py -v` |
| Full suite command | `PYTHONPATH=/Users/johnny_main/Developer/projects/titan-terminal pytest src/backend/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-029 | DailySubagent fetches 730 daily candles | unit | `PYTHONPATH=. pytest src/backend/tests/test_daily_subagent.py::test_analyze_calls_ohlcv_client_correctly -x` | ❌ Wave 0 |
| REQ-030 | FourHourSubagent fetches 4380 4H candles | unit | `PYTHONPATH=. pytest src/backend/tests/test_fourhour_subagent.py::test_analyze_calls_ohlcv_client_correctly -x` | ❌ Wave 0 |
| REQ-047 | Both produce extended TASignal | unit | `PYTHONPATH=. pytest src/backend/tests/test_daily_subagent.py::test_extended_fields_populated src/backend/tests/test_fourhour_subagent.py::test_extended_fields_populated -x` | ❌ Wave 0 |
| REQ-048 | Insufficient history warnings | unit | `PYTHONPATH=. pytest src/backend/tests/test_daily_subagent.py::test_warning_logged_for_insufficient_candles src/backend/tests/test_fourhour_subagent.py::test_warning_logged_for_insufficient_candles -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** Quick test of modified subagent only
- **Per wave merge:** All three subagent tests together (weekly, daily, fourhour)
- **Phase gate:** Full suite including regression (all 74+ existing tests + new tests)

### Wave 0 Gaps

- [ ] `src/backend/tests/test_daily_subagent.py` — full test suite for DailySubagent (mirror test_weekly_subagent.py)
- [ ] `src/backend/tests/test_fourhour_subagent.py` — full test suite for FourHourSubagent (mirror test_weekly_subagent.py)
- [ ] Test fixtures: `synthetic_daily_ohlcv_730`, `synthetic_daily_ohlcv_200`, `synthetic_fourhour_ohlcv_4380`, `synthetic_fourhour_ohlcv_500`
- [ ] Mock patches for both subagents targeting correct import paths

## Sources

### Primary (HIGH confidence)

- **Existing codebase inspection:**
  - `src/backend/agents/ta_ensemble/weekly_subagent.py` — Complete implementation (317 lines, Phase 11)
  - `src/backend/tests/test_weekly_subagent.py` — Complete test suite (338 lines, 16 tests passing, Phase 11)
  - `src/backend/models/ta_signal.py` — Extended TASignal model with wyckoff/alpha_factors (Phase 11)
  - `src/backend/data/ohlcv_client.py` — OHLCVClient supports 1w, 1d, 4h timeframes (Phase 6)
  - `src/backend/analysis/` — All analysis modules complete and tested (Phases 8-10)
  - `.planning/STATE.md` — Decisions from Phases 8-11
  - `.planning/phases/12-daily-fourhour-subagents/12-CONTEXT.md` — User decisions for this phase

- **User-provided context:**
  - Phase 12 CONTEXT.md explicitly defines file locations, candle limits, warning thresholds
  - Roadmap confirms all dependencies complete (Phases 8-11)

- **Python standard library:**
  - logging module: https://docs.python.org/3/library/logging.html
  - unittest.mock: https://docs.python.org/3/library/unittest.mock.html
  - datetime.timedelta: https://docs.python.org/3/library/datetime.html

### Secondary (MEDIUM confidence)

- **Pattern extrapolation:**
  - 4H candle count calculation: 6 candles/day * 365 days * 2 years = 4380 (verified math)
  - Test fixture structure: Based on proven weekly fixture pattern, adapted for different timeframes

### Tertiary (LOW confidence)

None — all findings verified with primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All dependencies in use since Phase 6, no new libraries
- Architecture: HIGH - Complete template exists (WeeklySubagent), pattern replication well-understood
- Pitfalls: HIGH - All common errors documented from Phase 11 experience, applied to Phase 12 context

**Research date:** 2026-02-28
**Valid until:** ~60 days (stable stack, proven patterns, no dependencies on external updates)

**Notes:**
- Phase 12 is pure pattern replication from Phase 11
- WeeklySubagent (317 lines) provides complete implementation template
- Only changes: 3 constants per subagent (TIMEFRAME, CANDLE_LIMIT, MIN_CANDLES_WARNING)
- Test coverage mirrors Phase 11: 16 tests per subagent expected
- Critical: File naming must match user context exactly (four_hour_subagent.py, not fourhour_subagent.py)
