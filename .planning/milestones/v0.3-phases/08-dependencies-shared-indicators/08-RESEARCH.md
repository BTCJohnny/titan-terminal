# Phase 8: Dependencies + Shared Indicators - Research

**Researched:** 2026-02-27
**Domain:** Technical Analysis Indicators, Python Data Science Libraries
**Confidence:** HIGH

## Summary

Phase 8 establishes the technical analysis foundation by installing required dependencies (pandas-ta, numpy, scipy) and implementing a shared indicators module at `src/backend/analysis/indicators.py`. The research confirms that pandas-ta is a mature, pure-Python alternative to TA-Lib with 150+ indicators, eliminating C dependency compilation issues. All required indicators (RSI, MACD, Bollinger Bands, ADX, OBV, VWAP, ATR) are available with TradingView-compatible default parameters. scipy's `find_peaks` function provides robust support/resistance detection using prominence and distance parameters.

The project's current Python 3.12.7, numpy 1.26.4, and pandas 2.3.0 environment is compatible with pandas-ta. The existing test infrastructure (pytest 8.4.0) and OHLCVClient provide solid foundations for unit testing with synthetic OHLCV data.

**Primary recommendation:** Install pandas-ta (latest stable), use its DataFrame extension API for indicator calculations, and implement scipy find_peaks for support/resistance detection. Test all indicators with synthetic OHLCV data before integrating into subagents.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Library Choice:**
- Use pandas-ta for all indicator calculations — do NOT use TA-Lib

**Module Location:**
- Shared indicators module at `src/backend/analysis/indicators.py`

**Indicator Parameters:**
- RSI: period 14
- MACD: fast 12, slow 26, signal 9
- Bollinger Bands: period 20, std dev 2
- ADX: period 14
- OBV: standard calculation
- VWAP: standard calculation
- ATR: period 14
- Support/Resistance: identify 3 nearest support and 3 nearest resistance levels from recent price action

**Function Signatures:**
- All functions take a pandas DataFrame with columns: timestamp, open, high, low, close, volume
- All functions return either a scalar value or a dict — no side effects
- Pure functions only

**Dependencies:**
- Add pandas-ta and numpy to requirements.txt if not already present

**Testing:**
- Full unit tests with synthetic OHLCV data
- No live API calls in tests
- Verify calculations against known values

### Claude's Discretion

- Internal helper functions organization
- Exact scipy parameters for peak detection (support/resistance)
- Error handling approach for insufficient data
- Whether to cache indicator results or compute fresh

### Deferred Ideas (OUT OF SCOPE)

None — phase scope is clearly defined

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-001 | Shared indicators module at `src/backend/analysis/indicators.py` | Module structure patterns documented; standard Python package organization |
| REQ-002 | RSI indicator (14-period default) | pandas-ta `rsi()` function with configurable length parameter |
| REQ-003 | MACD indicator (12/26/9 default) | pandas-ta `macd()` returns 3-column DataFrame (MACD, signal, histogram) |
| REQ-004 | Bollinger Bands (20-period, 2 std dev) | pandas-ta `bbands()` with length and std parameters |
| REQ-005 | ADX indicator (14-period default) | pandas-ta `adx()` with RMA mode (TradingView-compatible) |
| REQ-006 | OBV (On-Balance Volume) | pandas-ta `obv()` standard calculation |
| REQ-007 | VWAP (Volume Weighted Average Price) | pandas-ta `vwap()` requires DatetimeIndex |
| REQ-008 | ATR (Average True Range, 14-period) | pandas-ta `atr()` with RMA mode default |
| REQ-009 | Support/Resistance level detection | scipy.signal.find_peaks with prominence/distance parameters |
| REQ-010 | Use pandas-ta library for indicators | Confirmed compatible with numpy 1.26.4, pandas 2.3.0, Python 3.12.7 |
| REQ-043 | Unit tests for indicators module | pytest fixtures for synthetic OHLCV, mock patterns from test_ohlcv_client.py |
| REQ-052 | Add pandas-ta to requirements | Latest stable version (0.4.71b0 or 0.3.14b if stability preferred) |
| REQ-053 | Add numpy to requirements | Already present at 1.26.4 (compatible) |
| REQ-054 | Add scipy to requirements | Version 1.11.0+ recommended for find_peaks |
| REQ-055 | Verify pandas present | Already at 2.3.0 (compatible) |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas-ta | ^0.3.14b or 0.4.71b0 | Technical indicators | Pure Python, 150+ indicators, no C deps, TradingView-compatible |
| numpy | ^1.26.0 (already installed) | Numerical computation | Required by pandas-ta, industry standard |
| pandas | ^2.0.0 (already at 2.3.0) | DataFrame operations | Required by pandas-ta, already in use |
| scipy | ^1.11.0 | Signal processing | find_peaks for support/resistance detection |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | ^7.4.0 (already at 8.4.0) | Unit testing | Test infrastructure already established |
| pytest-asyncio | ^0.23.0 (already installed) | Async test support | If indicators need async wrappers |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pandas-ta | TA-Lib | TA-Lib requires C compilation, platform-specific binaries, harder installation. Rejected per user decision. |
| pandas-ta | Custom calculations | Reinventing wheel, edge cases, testing burden. pandas-ta is battle-tested with 150+ indicators. |
| scipy find_peaks | Custom peak detection | Complex algorithm, parameter tuning needed anyway. scipy is optimized and well-documented. |

**Installation:**

```bash
# Add to requirements.txt
pandas-ta>=0.3.14b  # Pure Python TA indicators
scipy>=1.11.0       # Signal processing (find_peaks)

# numpy and pandas already present
```

**Note on pandas-ta version:** Version 0.3.14b is the last stable pip release. Version 0.4.71b0 is newer but beta. Recommend 0.3.14b for stability unless specific features needed. The library maintainer noted potential archiving by July 2026, but a fork (pandas-ta-openbb) exists for NumPy 2.0 compatibility if needed.

## Architecture Patterns

### Recommended Module Structure

```
src/backend/analysis/
├── __init__.py              # Module exports
├── indicators.py            # Core indicator functions (this phase)
├── wyckoff.py              # Phase 10 (future)
└── alpha_factors.py        # Phase 9 (future)
```

### Pattern 1: Pure Function Design

**What:** Each indicator function takes DataFrame, returns computed values (scalar or dict)

**When to use:** All indicator calculations

**Example:**

```python
import pandas as pd
import pandas_ta as ta

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
    """Calculate RSI indicator from OHLCV DataFrame.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        period: RSI period (default: 14)

    Returns:
        Most recent RSI value as float, or None if insufficient data
    """
    if len(df) < period + 1:
        return None

    # pandas-ta expects lowercase column names
    close_series = df['close']
    rsi_series = ta.rsi(close_series, length=period)

    # Return most recent non-NaN value
    return rsi_series.dropna().iloc[-1] if not rsi_series.dropna().empty else None
```

**Source:** [pandas-ta PyPI](https://pypi.org/project/pandas-ta/), [Sling Academy debugging guide](https://www.slingacademy.com/article/debugging-common-errors-when-using-pandas-ta/)

### Pattern 2: DataFrame Extension API (Alternative)

**What:** pandas-ta registers itself as DataFrame extension (`df.ta.indicator()`)

**When to use:** If computing multiple indicators at once or appending to DataFrame

**Example:**

```python
# Add indicators as new columns
df.ta.rsi(length=14, append=True)      # Adds RSI_14 column
df.ta.macd(append=True)                # Adds MACD_12_26_9, MACDh, MACDs columns
df.ta.bbands(length=20, std=2, append=True)  # Adds BBL, BBM, BBU columns
```

**Source:** [pandas-ta documentation](https://www.pandas-ta.dev/)

### Pattern 3: Support/Resistance Detection

**What:** Use scipy.signal.find_peaks on high/low price series

**When to use:** Support/resistance level identification

**Example:**

```python
from scipy.signal import find_peaks
import numpy as np

def detect_support_resistance(df: pd.DataFrame, num_levels: int = 3) -> dict:
    """Detect support and resistance levels from OHLCV DataFrame.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        num_levels: Number of support/resistance levels to return (default: 3)

    Returns:
        Dict with keys 'support' and 'resistance', each containing list of price levels
    """
    highs = df['high'].values
    lows = df['low'].values

    # Resistance: peaks in high prices
    # distance=5 means peaks must be 5+ candles apart
    # prominence=2% of mean price filters significant levels
    resistance_indices, _ = find_peaks(
        highs,
        distance=5,
        prominence=0.02 * np.mean(highs)
    )
    resistance_levels = highs[resistance_indices]

    # Support: peaks in inverted low prices (valleys)
    support_indices, _ = find_peaks(
        -lows,
        distance=5,
        prominence=0.02 * np.mean(lows)
    )
    support_levels = lows[support_indices]

    # Get closest levels to current price
    current_price = df['close'].iloc[-1]

    # Sort and filter
    resistance_sorted = sorted([r for r in resistance_levels if r > current_price])
    support_sorted = sorted([s for s in support_levels if s < current_price], reverse=True)

    return {
        'resistance': resistance_sorted[:num_levels],
        'support': support_sorted[:num_levels]
    }
```

**Source:** [scipy find_peaks docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html), [Trading Strategies Academy](https://trading-strategies.academy/archives/1067)

### Pattern 4: Error Handling for Insufficient Data

**What:** Return None or empty dict when insufficient data, log warnings

**When to use:** All indicator functions

**Example:**

```python
def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Calculate MACD indicator."""
    min_periods = slow + signal

    if len(df) < min_periods:
        print(f"Warning: Insufficient data for MACD calculation. Need {min_periods}, got {len(df)}")
        return None

    close_series = df['close']
    macd_df = ta.macd(close_series, fast=fast, slow=slow, signal=signal)

    if macd_df is None or macd_df.empty:
        return None

    # Extract most recent values
    return {
        'macd': macd_df.iloc[-1, 0],        # MACD line
        'signal': macd_df.iloc[-1, 1],      # Signal line
        'histogram': macd_df.iloc[-1, 2]    # Histogram
    }
```

### Anti-Patterns to Avoid

- **Modifying input DataFrame:** Violates pure function requirement. Use `.copy()` if needed or extract series.
- **Assuming column case:** pandas-ta expects lowercase. Always normalize or use lowercase column names.
- **Ignoring NaN handling:** Indicators produce leading NaN values. Always check for NaN before returning.
- **Hard-coding parameters:** Make all indicator parameters configurable with sensible defaults.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Technical indicators | Custom RSI/MACD/BB calculations | pandas-ta | 150+ indicators, TradingView-compatible, battle-tested, handles edge cases |
| Peak detection | Manual local maxima search | scipy.signal.find_peaks | Optimized algorithm, prominence filtering, multiple parameter options |
| Moving averages | Custom rolling window logic | pandas-ta or pandas.rolling() | Handles NaN, multiple MA types (SMA, EMA, RMA), optimized |
| Volume analysis | Custom OBV calculation | pandas-ta.obv() | Handles edge cases like gaps, zero volume |
| VWAP | Manual cumulative calculation | pandas-ta.vwap() | Handles intraday reset, requires DatetimeIndex validation |

**Key insight:** Technical analysis has numerous edge cases (gaps, halts, low volume, price spikes, insufficient history). pandas-ta has been tested across thousands of assets and timeframes. Custom implementations will miss edge cases and produce incorrect signals.

## Common Pitfalls

### Pitfall 1: Insufficient Data for Indicator Calculation

**What goes wrong:** Indicator functions return NaN or fail when DataFrame doesn't have enough rows for the lookback period.

**Why it happens:** Each indicator needs N historical candles (e.g., RSI needs 14+, MACD needs 26+). Recent listings or short timeframes may not have enough data.

**How to avoid:**
- Check `len(df) >= min_required_periods` before calculation
- Return None or empty dict with warning instead of raising exception
- Document minimum data requirements in docstrings
- Log warnings so subagents can handle gracefully

**Warning signs:**
- All indicator values are NaN
- IndexError when accessing `.iloc[-1]`
- Empty DataFrames after `.dropna()`

**Source:** [Sling Academy debugging guide](https://www.slingacademy.com/article/debugging-common-errors-when-using-pandas-ta/)

### Pitfall 2: Column Name Case Sensitivity

**What goes wrong:** pandas-ta expects lowercase column names ('close', 'high', 'low', 'open', 'volume'). If DataFrame has uppercase or mixed case, indicators fail silently or raise KeyError.

**Why it happens:** OHLCVClient returns lowercase keys, but if DataFrame is constructed elsewhere with different casing, pandas-ta won't find columns.

**How to avoid:**
- Normalize column names: `df.columns = df.columns.str.lower()`
- Document expected column format in function docstrings
- Add validation: `assert all(col in df.columns for col in ['close', 'high', 'low', 'open', 'volume'])`

**Warning signs:**
- KeyError: 'close'
- Indicator returns None despite sufficient data
- Empty results from pandas-ta functions

**Source:** [Sling Academy debugging guide](https://www.slingacademy.com/article/debugging-common-errors-when-using-pandas-ta/)

### Pitfall 3: VWAP Requires DatetimeIndex

**What goes wrong:** VWAP calculation fails if DataFrame index is not a DatetimeIndex (e.g., integer index or timestamp column not set as index).

**Why it happens:** VWAP resets daily/intraday, requiring datetime awareness. pandas-ta checks index type.

**How to avoid:**
- Convert timestamp column to datetime and set as index: `df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms'); df.set_index('timestamp', inplace=True)`
- Document VWAP's special requirement
- Provide helper function for DataFrame preparation

**Warning signs:**
- TypeError or AttributeError when calling `df.ta.vwap()`
- VWAP returns all NaN

**Source:** [pandas-ta indicators reference](https://pypi.org/project/pandas-ta/)

### Pitfall 4: scipy find_peaks Parameter Tuning

**What goes wrong:** Too many or too few support/resistance levels detected, or levels are too close together.

**Why it happens:** Default find_peaks parameters don't account for asset-specific volatility. Low-volatility assets need lower prominence; high-volatility need higher.

**How to avoid:**
- Use percentage-based prominence: `prominence=0.01 * np.mean(prices)` to `0.03 * np.mean(prices)`
- Set distance parameter based on timeframe (e.g., 5 for daily, 10 for weekly)
- Start conservative (higher prominence), tune down if needed
- Document parameter rationale in code

**Warning signs:**
- Hundreds of support/resistance levels detected
- All levels within 0.5% of current price
- No levels detected despite clear price action

**Source:** [Trading Strategies Academy](https://trading-strategies.academy/archives/1067), [scipy find_peaks docs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html)

### Pitfall 5: Indicator Result Structure Varies

**What goes wrong:** Some pandas-ta indicators return Series, others return DataFrame with multiple columns. Code breaks when assuming consistent return type.

**Why it happens:** Single-value indicators (RSI, ATR) return Series. Multi-component indicators (MACD, Bollinger Bands) return DataFrame with multiple columns.

**How to avoid:**
- Check return type: `if isinstance(result, pd.DataFrame): ...`
- Extract specific columns: `macd_df['MACD_12_26_9']`
- Standardize by converting to dict with named keys
- Document return structure for each indicator wrapper

**Warning signs:**
- AttributeError: 'DataFrame' object has no attribute 'iloc' (trying to access Series method on DataFrame)
- Wrong number of values to unpack
- Unexpected NaN when accessing column

**Source:** [pandas-ta PyPI examples](https://pypi.org/project/pandas-ta/)

## Code Examples

Verified patterns from official sources and project conventions.

### Example 1: RSI Calculation

```python
import pandas as pd
import pandas_ta as ta

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
    """Calculate RSI indicator from OHLCV DataFrame.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        period: RSI period (default: 14)

    Returns:
        Most recent RSI value (0-100), or None if insufficient data

    Min data required: period + 1 candles (15 for default period=14)
    """
    if len(df) < period + 1:
        return None

    close_series = df['close']
    rsi_series = ta.rsi(close_series, length=period)

    # Return most recent non-NaN value
    if rsi_series is None or rsi_series.dropna().empty:
        return None

    return float(rsi_series.dropna().iloc[-1])
```

### Example 2: MACD with All Components

```python
def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """Calculate MACD indicator from OHLCV DataFrame.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line period (default: 9)

    Returns:
        Dict with keys 'macd', 'signal', 'histogram', or None if insufficient data

    Min data required: slow + signal candles (35 for default parameters)
    """
    min_periods = slow + signal
    if len(df) < min_periods:
        return None

    close_series = df['close']
    macd_df = ta.macd(close_series, fast=fast, slow=slow, signal=signal)

    if macd_df is None or macd_df.empty:
        return None

    # pandas-ta returns DataFrame with columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
    last_row = macd_df.dropna().iloc[-1]

    return {
        'macd': float(last_row.iloc[0]),      # MACD line
        'signal': float(last_row.iloc[2]),    # Signal line
        'histogram': float(last_row.iloc[1])  # Histogram
    }
```

### Example 3: Bollinger Bands

```python
def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> dict:
    """Calculate Bollinger Bands from OHLCV DataFrame.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        period: BB period (default: 20)
        std: Standard deviation multiplier (default: 2.0)

    Returns:
        Dict with keys 'upper', 'middle', 'lower', or None if insufficient data

    Min data required: period candles (20 for default)
    """
    if len(df) < period:
        return None

    close_series = df['close']
    bb_df = ta.bbands(close_series, length=period, std=std)

    if bb_df is None or bb_df.empty:
        return None

    # Returns DataFrame with columns: BBL_20_2.0, BBM_20_2.0, BBU_20_2.0
    last_row = bb_df.dropna().iloc[-1]

    return {
        'upper': float(last_row.iloc[2]),   # Upper band
        'middle': float(last_row.iloc[1]),  # Middle band (SMA)
        'lower': float(last_row.iloc[0])    # Lower band
    }
```

### Example 4: Support/Resistance Detection

```python
from scipy.signal import find_peaks
import numpy as np

def detect_support_resistance(
    df: pd.DataFrame,
    num_levels: int = 3,
    distance: int = 5,
    prominence_pct: float = 0.02
) -> dict:
    """Detect support and resistance levels using scipy peak detection.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        num_levels: Number of support/resistance levels to return (default: 3)
        distance: Minimum candles between peaks (default: 5)
        prominence_pct: Prominence as % of mean price (default: 0.02 = 2%)

    Returns:
        Dict with keys 'support' (list) and 'resistance' (list),
        each containing up to num_levels price values sorted by proximity to current price
    """
    if len(df) < distance * 2:
        return {'support': [], 'resistance': []}

    highs = df['high'].values
    lows = df['low'].values
    current_price = df['close'].iloc[-1]

    # Resistance: peaks in high prices
    resistance_indices, _ = find_peaks(
        highs,
        distance=distance,
        prominence=prominence_pct * np.mean(highs)
    )
    resistance_levels = highs[resistance_indices]

    # Support: peaks in inverted low prices (valleys)
    support_indices, _ = find_peaks(
        -lows,
        distance=distance,
        prominence=prominence_pct * np.mean(lows)
    )
    support_levels = lows[support_indices]

    # Filter and sort by proximity to current price
    resistance_above = sorted([r for r in resistance_levels if r > current_price])
    support_below = sorted([s for s in support_levels if s < current_price], reverse=True)

    return {
        'resistance': resistance_above[:num_levels],
        'support': support_below[:num_levels]
    }
```

### Example 5: Single Test Function Pattern

```python
# From existing test_ohlcv_client.py pattern
import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def synthetic_ohlcv():
    """Generate synthetic OHLCV data for indicator testing."""
    np.random.seed(42)
    n = 100

    # Generate realistic price movement
    base_price = 50000.0
    returns = np.random.normal(0.001, 0.02, n)  # 0.1% drift, 2% volatility
    prices = base_price * np.exp(np.cumsum(returns))

    data = {
        'timestamp': pd.date_range(start='2024-01-01', periods=n, freq='1D'),
        'open': prices * (1 + np.random.uniform(-0.005, 0.005, n)),
        'high': prices * (1 + np.random.uniform(0.005, 0.015, n)),
        'low': prices * (1 + np.random.uniform(-0.015, -0.005, n)),
        'close': prices,
        'volume': np.random.uniform(1000, 5000, n)
    }

    return pd.DataFrame(data)

def test_calculate_rsi_returns_valid_range(synthetic_ohlcv):
    """Verify RSI returns value between 0 and 100."""
    from src.backend.analysis.indicators import calculate_rsi

    result = calculate_rsi(synthetic_ohlcv, period=14)

    assert result is not None
    assert 0 <= result <= 100
    assert isinstance(result, float)
```

**Source:** Adapted from `/Users/johnny_main/Developer/projects/titan-terminal/src/backend/tests/test_ohlcv_client.py`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TA-Lib (C library) | pandas-ta (pure Python) | 2020+ | Easier installation, no compilation, same indicators |
| Custom indicator math | Library functions | 2018+ | Reduced bugs, TradingView compatibility, maintained |
| Manual peak detection | scipy.signal.find_peaks | 2018 (scipy 1.1.0) | Robust algorithm, parameter-based filtering |
| np.nan for missing | pd.NA (nullable types) | 2020+ | Better type handling, but np.nan still standard |

**Deprecated/outdated:**
- **TA-Lib Python wrapper:** Still works but installation difficulties make it unsuitable for modern Python projects. pandas-ta has feature parity.
- **Custom RSI/MACD formulas:** No longer necessary with pandas-ta. Only implement custom indicators not in the library.

## Open Questions

1. **Exact pandas-ta version for production**
   - What we know: 0.3.14b is last stable, 0.4.71b0 is latest beta, library may be archived July 2026
   - What's unclear: Whether to use stable (older) or beta (newer features)
   - Recommendation: Start with 0.3.14b for stability. Monitor pandas-ta-openbb fork if NumPy 2.0 upgrade needed.

2. **Caching strategy for indicators**
   - What we know: User left caching to Claude's discretion
   - What's unclear: Whether subagents call indicators multiple times per analysis
   - Recommendation: Start without caching (pure functions). Add caching in Phase 11 if profiling shows performance issues.

3. **Handling zero volume candles**
   - What we know: Volume-based indicators (OBV, VWAP) need volume data
   - What's unclear: How to handle gaps, halts, or zero-volume candles
   - Recommendation: Document behavior (likely NaN for that candle), log warning. Let pandas-ta handle edge cases.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.0 |
| Config file | none — runs via `pytest src/backend/tests/` |
| Quick run command | `pytest src/backend/tests/test_indicators.py -x` |
| Full suite command | `pytest src/backend/tests/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-001 | Module imports without error | unit | `pytest src/backend/tests/test_indicators.py::test_module_import -x` | ❌ Wave 0 |
| REQ-002 | RSI returns value 0-100 for valid data | unit | `pytest src/backend/tests/test_indicators.py::test_rsi_calculation -x` | ❌ Wave 0 |
| REQ-003 | MACD returns dict with macd/signal/histogram | unit | `pytest src/backend/tests/test_indicators.py::test_macd_calculation -x` | ❌ Wave 0 |
| REQ-004 | Bollinger Bands returns upper/middle/lower | unit | `pytest src/backend/tests/test_indicators.py::test_bollinger_bands -x` | ❌ Wave 0 |
| REQ-005 | ADX returns value >=0 | unit | `pytest src/backend/tests/test_indicators.py::test_adx_calculation -x` | ❌ Wave 0 |
| REQ-006 | OBV returns numeric value | unit | `pytest src/backend/tests/test_indicators.py::test_obv_calculation -x` | ❌ Wave 0 |
| REQ-007 | VWAP returns value with DatetimeIndex | unit | `pytest src/backend/tests/test_indicators.py::test_vwap_calculation -x` | ❌ Wave 0 |
| REQ-008 | ATR returns positive value | unit | `pytest src/backend/tests/test_indicators.py::test_atr_calculation -x` | ❌ Wave 0 |
| REQ-009 | Support/resistance returns 3 levels each | unit | `pytest src/backend/tests/test_indicators.py::test_support_resistance -x` | ❌ Wave 0 |
| REQ-010 | pandas-ta import succeeds | unit | `pytest src/backend/tests/test_indicators.py::test_pandas_ta_available -x` | ❌ Wave 0 |
| REQ-043 | All indicators handle insufficient data | unit | `pytest src/backend/tests/test_indicators.py::test_insufficient_data -x` | ❌ Wave 0 |
| REQ-052 | pandas-ta installs without error | smoke | Manual: `pip install pandas-ta && python -c "import pandas_ta"` | N/A |
| REQ-053 | numpy is present | smoke | Manual: `python -c "import numpy; print(numpy.__version__)"` | ✅ (v1.26.4) |
| REQ-054 | scipy installs without error | smoke | Manual: `pip install scipy && python -c "import scipy; print(scipy.__version__)"` | ❌ Wave 0 |
| REQ-055 | pandas is present | smoke | Manual: `python -c "import pandas; print(pandas.__version__)"` | ✅ (v2.3.0) |

### Sampling Rate

- **Per task commit:** `pytest src/backend/tests/test_indicators.py -x` (fast, exits on first failure)
- **Per wave merge:** `pytest src/backend/tests/` (full suite including existing 28 tests)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `src/backend/analysis/__init__.py` — package initialization
- [ ] `src/backend/analysis/indicators.py` — indicator functions
- [ ] `src/backend/tests/test_indicators.py` — unit tests for all indicators
- [ ] `requirements.txt` — add pandas-ta>=0.3.14b and scipy>=1.11.0
- [ ] Install dependencies: `pip install -r requirements.txt`

## Sources

### Primary (HIGH confidence)

- [pandas-ta PyPI](https://pypi.org/project/pandas-ta/) - Library version, dependencies, installation
- [pandas-ta documentation](https://www.pandas-ta.dev/) - API reference, indicator parameters
- [scipy.signal.find_peaks documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html) - Official API, parameters, examples
- [Sling Academy: Debugging pandas-ta](https://www.slingacademy.com/article/debugging-common-errors-when-using-pandas-ta/) - Common pitfalls, error handling
- Project files: `src/backend/data/ohlcv_client.py`, `src/backend/tests/test_ohlcv_client.py` - Existing patterns

### Secondary (MEDIUM confidence)

- [Comparing TA-Lib to pandas-ta - Sling Academy](https://www.slingacademy.com/article/comparing-ta-lib-to-pandas-ta-which-one-to-choose/) - Library comparison
- [Trading Strategies Academy: Support/Resistance with find_peaks](https://trading-strategies.academy/archives/1067) - scipy usage for trading
- Web search: pandas-ta indicator examples, OHLCV testing patterns - Community usage patterns

### Tertiary (LOW confidence)

- pandas-ta fork status (pandas-ta-openbb) - Future compatibility concerns
- Library archival warning (July 2026) - Planning consideration only

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pandas-ta confirmed available, compatible with current environment, 150+ indicators documented
- Architecture: HIGH - Pure function pattern clear, scipy find_peaks well-documented, existing test patterns established
- Pitfalls: HIGH - Common errors documented in official debugging guide, scipy parameters tuning well-understood

**Research date:** 2026-02-27
**Valid until:** 2026-04-27 (60 days) - pandas-ta is stable, scipy is mature; both unlikely to change significantly

**Environment verified:**
- Python 3.12.7
- numpy 1.26.4 (already installed)
- pandas 2.3.0 (already installed)
- pytest 8.4.0 (already installed)
- pandas-ta: to be installed (compatible)
- scipy: to be installed (compatible)
