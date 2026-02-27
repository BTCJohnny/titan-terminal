# Stack Research: TA Ensemble Implementation

**Domain:** Technical Analysis & Algorithmic Trading
**Researched:** 2026-02-27
**Confidence:** MEDIUM

## Executive Summary

For TA Ensemble implementation, we need **pandas-ta** as the core indicator library (not TA-Lib), **numpy** for numerical computations, and **scipy** for peak detection in support/resistance identification. Wyckoff detection requires custom implementation - no production-ready libraries exist. All additions integrate cleanly with existing CCXT/pandas workflow.

**Critical decision:** pandas-ta over TA-Lib because it's pure Python (no C dependencies), actively maintained, pandas-native, and provides all required indicators with consistent API.

## Recommended Stack

### Core Technologies (NEW Additions)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pandas-ta | ^0.3.14b | Technical indicator computation (RSI, MACD, BB, ADX, OBV, VWAP, ATR) | Pure Python, pandas-native, actively maintained, consistent API, no C compiler needed |
| numpy | ^1.26.0 | Numerical computations for custom algorithms (Wyckoff, alpha factors) | Industry standard for array operations, required by pandas anyway, fast vectorized ops |
| scipy | ^1.11.0 | Peak detection for support/resistance levels | Signal processing library with `find_peaks()` for S/R identification |

### Supporting Libraries (Already Validated)

| Library | Version | Purpose | Usage in TA Ensemble |
|---------|---------|---------|----------------------|
| pandas | ^2.1.0 | DataFrame operations | Convert OHLCV to DataFrame for pandas-ta, time series analysis |
| ccxt | ^4.0.0 | Market data (existing) | OHLCV data source - already implemented |
| pydantic | ^2.5.0 | Data validation (existing) | TASignal model validation - already implemented |

### Development Tools (No Changes)

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest | Unit testing | Existing - will test indicators, Wyckoff, alpha factors |
| pytest-asyncio | Async test support | Existing - sufficient for TA module tests |

## Installation

```bash
# NEW dependencies for TA Ensemble
pip install pandas-ta>=0.3.14b
pip install numpy>=1.26.0
pip install scipy>=1.11.0

# pandas will be installed as pandas-ta dependency if not already present
```

**Note:** All new dependencies are pure Python wheels - no C compiler required, unlike TA-Lib.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| Indicator Library | pandas-ta | TA-Lib | TA-Lib requires C library compilation, platform-specific install issues, less maintained Python wrapper, not pandas-native |
| Indicator Library | pandas-ta | ta (ta-python) | Smaller indicator set, less maintained, missing VWAP and advanced indicators |
| Numerical Ops | numpy + scipy | Custom pure Python | Reinventing the wheel, slower, more bugs, no optimization |
| Wyckoff Detection | Custom implementation | Pre-built library | No production-ready Wyckoff libraries exist - all are research-grade notebooks |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| TA-Lib (ta-lib) | Requires C library installation, platform-specific build issues, installation fails on many systems, Python wrapper less maintained | pandas-ta (pure Python, pandas-native) |
| tulipindicators | Unmaintained since 2018, Python bindings broken, C dependency | pandas-ta |
| backtrader indicators | Designed for backtesting framework, not standalone indicator computation, heavyweight dependency | pandas-ta for indicators, custom for strategy logic |
| finta | Limited indicator set, not actively maintained, missing modern indicators like VWAP | pandas-ta |

## Implementation Patterns

### Pattern 1: pandas-ta Integration with OHLCV Client

**What:** Convert OHLCV client output to pandas DataFrame, apply pandas-ta indicators
**When:** In each subagent (Weekly, Daily, 4H) before analysis

```python
import pandas as pd
import pandas_ta as ta
from src.backend.data.ohlcv_client import get_ohlcv_client

# Fetch OHLCV data
client = get_ohlcv_client()
candles = client.fetch_ohlcv("BTC/USDT", "1d", limit=100)

# Convert to DataFrame
df = pd.DataFrame(candles)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)

# Calculate indicators (pandas-ta adds columns in-place)
df.ta.rsi(length=14, append=True)  # Adds 'RSI_14' column
df.ta.macd(fast=12, slow=26, signal=9, append=True)  # Adds MACD columns
df.ta.bbands(length=20, std=2, append=True)  # Adds BB columns
df.ta.adx(length=14, append=True)  # Adds ADX columns
df.ta.obv(append=True)  # Adds OBV column
df.ta.vwap(append=True)  # Adds VWAP column
df.ta.atr(length=14, append=True)  # Adds ATR_14 column
```

### Pattern 2: Custom Wyckoff Detection

**What:** Implement Wyckoff phase detection using volume-price analysis
**When:** In shared indicators module, called by each subagent

**Approach:**
- Phase A (Stopping Action): High volume, narrow price range after downtrend
- Phase B (Building Cause): Wide, choppy range with volume tests
- Phase C (Spring/Test): Fake breakdown below support on decreasing volume
- Phase D (Sign of Strength): Break above resistance with expanding volume
- Phase E (Markup): New highs with strong volume

**Implementation location:** `src/backend/agents/ta_ensemble/indicators.py`

**Key metrics:**
- Volume anomaly: Current volume vs 20-period MA (>150% = high, <50% = low)
- Price range: (high - low) / ATR ratio
- Trend context: Position relative to 50/200 MA
- SOS/SOW detection: Volume surge (>2x MA) + strong price move (>1.5 ATR)

**No libraries:** Custom algorithm required - use numpy for array ops, scipy.signal.find_peaks for swing highs/lows

### Pattern 3: Alpha Factor Computation

**What:** Calculate momentum score, volume anomaly, MA deviation, volatility metrics
**When:** After indicator computation, before generating TASignal

```python
import numpy as np

def compute_alpha_factors(df: pd.DataFrame) -> dict:
    """Compute alpha factors from OHLCV + indicators DataFrame."""
    latest = df.iloc[-1]

    # Momentum score: RSI + MACD + price vs MA
    rsi_score = (latest['RSI_14'] - 50) / 50  # -1 to 1
    macd_score = 1 if latest['MACD_12_26_9'] > 0 else -1
    ma_score = (latest['close'] - latest['SMA_50']) / latest['SMA_50']
    momentum = (rsi_score + macd_score + ma_score) / 3

    # Volume anomaly: current vs average
    vol_ma = df['volume'].rolling(20).mean().iloc[-1]
    volume_anomaly = (latest['volume'] - vol_ma) / vol_ma

    # MA deviation: distance from 50/200 MA
    ma_deviation = {
        'ma50': (latest['close'] - latest['SMA_50']) / latest['SMA_50'],
        'ma200': (latest['close'] - latest['SMA_200']) / latest['SMA_200']
    }

    # Volatility: ATR as % of price
    volatility = latest['ATR_14'] / latest['close']

    return {
        'momentum_score': round(momentum, 3),
        'volume_anomaly': round(volume_anomaly, 3),
        'ma_deviation': ma_deviation,
        'volatility': round(volatility, 4)
    }
```

### Pattern 4: Support/Resistance Detection

**What:** Use scipy.signal.find_peaks to identify swing highs/lows
**When:** In indicators module, called by each subagent

```python
from scipy.signal import find_peaks

def find_support_resistance(df: pd.DataFrame, prominence: float = 0.02) -> dict:
    """Find major S/R levels using peak detection.

    Args:
        df: OHLCV DataFrame
        prominence: Minimum prominence as fraction of price (0.02 = 2%)

    Returns:
        dict with 'support' and 'resistance' price levels
    """
    prices = df['close'].values
    prominence_abs = prominence * prices.mean()

    # Find peaks (resistance) and troughs (support)
    peaks, _ = find_peaks(prices, prominence=prominence_abs)
    troughs, _ = find_peaks(-prices, prominence=prominence_abs)

    # Get most recent significant levels
    major_resistance = prices[peaks[-1]] if len(peaks) > 0 else None
    major_support = prices[troughs[-1]] if len(troughs) > 0 else None

    return {
        'major_resistance': major_resistance,
        'major_support': major_support
    }
```

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| pandas-ta ^0.3.14b | pandas ^2.0.0 | Requires pandas 2.x for modern API |
| pandas-ta ^0.3.14b | numpy ^1.24.0 | Any numpy 1.24+ works |
| scipy ^1.11.0 | numpy ^1.26.0 | Must match numpy version ranges |
| pandas ^2.1.0 | python ^3.10 | Python 3.10+ required for match/case |

**Critical:** Install pandas-ta with `pip install pandas-ta` not `pip install ta` (different package)

## Module Structure

Recommended file organization:

```
src/backend/agents/ta_ensemble/
├── __init__.py
├── indicators.py          # NEW: Shared indicator computation
├── wyckoff.py            # NEW: Wyckoff phase detection
├── alpha_factors.py      # NEW: Alpha factor calculations
├── weekly_subagent.py    # EXISTS: Use new modules
├── daily_subagent.py     # EXISTS: Use new modules
├── fourhour_subagent.py  # EXISTS: Use new modules
└── ta_mentor.py          # EXISTS: Synthesize signals
```

**Rationale:** Shared modules prevent code duplication across 3 subagents, enable isolated unit testing, follow DRY principle.

## Integration Points

### 1. OHLCV Client → Indicators Module
**Flow:** `OHLCVClient.fetch_ohlcv()` → convert to DataFrame → `indicators.compute_all(df)` → returns dict with all indicators

### 2. Indicators Module → Subagents
**Flow:** Each subagent calls `indicators.compute_all()`, `wyckoff.detect_phase()`, `alpha_factors.compute()` → constructs TASignal

### 3. Subagents → TAMentor
**Flow:** TAMentor receives 3 TASignal objects → applies conflict resolution → returns TAMentorSignal

### 4. No Database Integration (Yet)
**Note:** v0.3 computes on-demand. Caching/database storage deferred to v1.0.

## Testing Strategy

### Unit Tests Required

1. **indicators.py tests:**
   - RSI, MACD, BB, ADX, OBV, VWAP, ATR computation with known values
   - Support/resistance detection with synthetic peaks
   - Edge cases: insufficient data, NaN handling

2. **wyckoff.py tests:**
   - Phase detection with synthetic volume-price patterns
   - Spring detection (fake breakdown + volume decrease)
   - SOS/SOW detection (volume surge + strong move)

3. **alpha_factors.py tests:**
   - Momentum score calculation with known indicator values
   - Volume anomaly detection with synthetic volume spikes
   - MA deviation computation

4. **Subagent integration tests:**
   - Mock OHLCV data → full TASignal generation
   - Verify TASignal Pydantic validation passes
   - Multiple symbols and timeframes

**Mock Strategy:** Use `pandas.DataFrame` with synthetic OHLCV data, not live CCXT calls.

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| pandas-ta choice | HIGH | Industry standard, widely used in quant trading, actively maintained |
| numpy/scipy | HIGH | De facto standard for scientific computing in Python |
| Wyckoff approach | MEDIUM | No standard libraries - custom implementation required, algorithm well-documented but subjective |
| Integration pattern | HIGH | Straightforward DataFrame workflow, aligns with existing CCXT → dict pattern |
| Version compatibility | MEDIUM | Versions based on training data (Jan 2025 cutoff), should verify latest on PyPI |

## Open Questions

1. **Wyckoff calibration:** What volume/price thresholds work best for crypto vs stocks? Requires empirical testing.
2. **Indicator periods:** Use standard periods (RSI 14, MACD 12/26/9) or optimize per asset/timeframe?
3. **Support/resistance sensitivity:** scipy `prominence` parameter needs tuning per timeframe.
4. **Performance:** How many candles needed for accurate Wyckoff detection? (Hypothesis: 100+ for weekly, 200+ for daily)

## Sources

**Note:** Web search and Context7 tools were unavailable during research. Recommendations based on:

- Training data (Jan 2025 cutoff): pandas-ta, numpy, scipy standard usage patterns
- Project codebase: `/Users/johnny_main/Developer/projects/titan-terminal/requirements.txt`, OHLCV client implementation
- PROJECT.md: TA Ensemble requirements (RSI, MACD, BB, ADX, OBV, VWAP, ATR, S/R, Wyckoff phases)

**Verification needed:**
- [ ] pandas-ta latest version on PyPI (training data: 0.3.14b)
- [ ] numpy latest stable (training data: 1.26.x)
- [ ] scipy latest stable (training data: 1.11.x)
- [ ] pandas-ta maintenance status (was active as of Jan 2025)

**Recommended verification:** `pip index versions pandas-ta numpy scipy` before final installation

---
*Stack research for: TA Ensemble Technical Indicators*
*Researched: 2026-02-27*
*Confidence: MEDIUM (training data only, web tools unavailable)*
