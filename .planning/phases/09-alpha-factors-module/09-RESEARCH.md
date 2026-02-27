# Phase 9: Alpha Factors Module - Research

**Researched:** 2026-02-27
**Domain:** Quantitative Trading Alpha Factors, Financial Feature Engineering
**Confidence:** HIGH

## Summary

Phase 9 implements alpha factors module at `src/backend/analysis/alpha_factors.py` to compute quantitative market condition factors for trading signals. Alpha factors are transformations of market data containing predictive signals designed to capture risks that drive asset returns. The four core factors—momentum score, volume anomaly, MA deviation, and volatility score—represent industry-standard quantitative signals used in systematic trading.

Research confirms established methodologies: momentum via Rate of Change (ROC) normalized to -100/+100 scale, volume anomalies detected via Z-score deviation from moving averages (2x threshold standard), MA deviation as percentage distance from 20/50/200 EMAs, and volatility normalized as ATR percentage of price for cross-asset comparison. All factors leverage existing pandas operations and the ATR function from Phase 8's indicators.py.

The project's existing pandas 2.3.0, numpy 1.26.4, and pytest 8.4.0 infrastructure provides full support. Pydantic v2's Rust-backed validation (5-50x faster) ensures type-safe factor models. The pure-function pattern from Phase 8 applies directly: each factor function takes DataFrame, returns dict, handles insufficient data gracefully.

**Primary recommendation:** Implement four standalone factor functions returning dicts with named fields, create AlphaFactors Pydantic model for validation, reuse calculate_atr from indicators.py, test with synthetic OHLCV data following Phase 8 patterns.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**File Structure:**
- Single module: `src/backend/analysis/alpha_factors.py`
- Import ATR from existing `src/backend/analysis/indicators.py` — do not reimplement

**Function Signatures:**
- All 4 functions take a pandas DataFrame with columns: timestamp, open, high, low, close, volume
- Each function returns a dict with named fields — no raw scalars

**Momentum Score:**
- Rate of change over 10 and 20 periods
- Normalised to -100/+100 scale

**Volume Anomaly:**
- Current volume vs 20-period moving average
- Returns ratio and bool flag (True if >2x average)

**MA Deviation:**
- Price deviation from 20/50/200 EMAs
- Returns deviation as percentage for each MA

**Volatility Score:**
- ATR-based normalised volatility
- 0-100 scale

### Claude's Discretion

- Internal helper functions if needed
- Pydantic model structure for AlphaFactors
- Edge case handling (insufficient data)
- Specific normalisation formulas within constraints

### Deferred Ideas (OUT OF SCOPE)

None — phase scope is well-defined

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-019 | Alpha factors module at `src/backend/analysis/alpha_factors.py` | Module structure follows Phase 8 indicators.py pattern |
| REQ-020 | Momentum score calculation | ROC formula: ((close - close_n) / close_n) * 100; normalize via tanh or min-max to -100/+100 |
| REQ-021 | Volume anomaly detection | Compare current volume to 20-period SMA; Z-score or ratio-based detection; 2x threshold standard |
| REQ-022 | MA deviation calculation | pandas.DataFrame.ewm() for EMAs; percentage deviation: ((price - EMA) / EMA) * 100 |
| REQ-023 | Volatility score calculation | Reuse calculate_atr() from indicators.py; normalize: (ATR / price) * 100; scale to 0-100 via percentile or min-max |
| REQ-024 | AlphaFactors Pydantic model | Pydantic v2 models with field validation; Optional fields for graceful degradation |
| REQ-045 | Unit tests for alpha factors | pytest fixtures with synthetic data; test edge cases (insufficient data, zero volume, extreme values) |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | 2.3.0 (already installed) | DataFrame operations, EMA calculation | Industry standard for financial time series; .ewm() for EMA, .rolling() for MA |
| numpy | 1.26.4 (already installed) | Numerical operations | Required for normalization calculations, percentile functions |
| pydantic | Latest (already installed) | Data validation | Type-safe models; v2 Rust core 5-50x faster; used by FastAPI, LangChain |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.4.0 (already installed) | Unit testing | Test infrastructure established in Phase 8 |
| typing | Standard library | Type hints | Optional, Literal types for validation |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pandas EMA | Custom exponential smoothing | pandas.ewm() is optimized, handles NaN, widely tested. No benefit to custom. |
| Dict return types | Pydantic models directly | Separation of concerns: functions compute, models validate. Easier testing. |
| Percentile normalization | Min-max scaling | Percentiles handle outliers better; min-max simpler but sensitive to extremes. Use both where appropriate. |

**Installation:**

```bash
# No new dependencies required
# pandas, numpy, pydantic already installed
```

## Architecture Patterns

### Recommended Module Structure

```
src/backend/analysis/
├── __init__.py              # Module exports
├── indicators.py            # Phase 8 (existing)
├── alpha_factors.py         # THIS PHASE
└── wyckoff.py              # Phase 10 (future)
```

### Pattern 1: Pure Function Design (Factor Functions)

**What:** Each alpha factor function takes DataFrame, returns dict with named fields

**When to use:** All four factor calculations

**Example:**

```python
import pandas as pd
import numpy as np
from typing import Optional

def calculate_momentum_score(df: pd.DataFrame, short_period: int = 10, long_period: int = 20) -> Optional[dict]:
    """Calculate momentum score from rate of change.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        short_period: Short ROC period (default: 10)
        long_period: Long ROC period (default: 20)

    Returns:
        Dict with keys: 'short_roc', 'long_roc', 'momentum_score' (-100 to +100)
        or None if insufficient data

    Minimum data: long_period + 1 candles (21 for default)
    """
    if len(df) < long_period + 1:
        return None

    close = df['close']

    # Rate of change: ((close - close_n) / close_n) * 100
    short_roc = ((close.iloc[-1] - close.iloc[-short_period]) / close.iloc[-short_period]) * 100
    long_roc = ((close.iloc[-1] - close.iloc[-long_period]) / close.iloc[-long_period]) * 100

    # Normalize to -100/+100 using tanh scaling
    # Combined momentum: weight short-term 60%, long-term 40%
    combined = (0.6 * short_roc + 0.4 * long_roc)
    momentum_score = np.tanh(combined / 10) * 100  # tanh normalizes, *100 scales to -100/+100

    return {
        'short_roc': float(short_roc),
        'long_roc': float(long_roc),
        'momentum_score': float(momentum_score)
    }
```

**Source:** Adapted from [Rate of Change formula](https://python.stockindicators.dev/indicators/Roc/), [WorldQuant 101 Alphas](https://docs.dolphindb.com/en/Tutorials/wq101alpha.html)

### Pattern 2: Volume Anomaly Detection

**What:** Compare current volume to moving average, flag anomalies

**When to use:** Volume anomaly factor calculation

**Example:**

```python
def detect_volume_anomaly(df: pd.DataFrame, ma_period: int = 20, threshold: float = 2.0) -> Optional[dict]:
    """Detect volume anomalies vs moving average.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        ma_period: MA period for baseline (default: 20)
        threshold: Anomaly threshold multiplier (default: 2.0 = 200%)

    Returns:
        Dict with keys: 'current_volume', 'avg_volume', 'volume_ratio', 'is_anomaly' (bool)
        or None if insufficient data

    Minimum data: ma_period candles (20 for default)
    """
    if len(df) < ma_period:
        return None

    volume = df['volume']
    current_volume = volume.iloc[-1]
    avg_volume = volume.rolling(window=ma_period).mean().iloc[-1]

    if avg_volume == 0:
        return None  # Cannot calculate ratio

    volume_ratio = current_volume / avg_volume
    is_anomaly = volume_ratio > threshold

    return {
        'current_volume': float(current_volume),
        'avg_volume': float(avg_volume),
        'volume_ratio': float(volume_ratio),
        'is_anomaly': bool(is_anomaly)
    }
```

**Source:** Based on [Volume anomaly detection methodology](https://www.tradingview.com/script/M7YYuUEP-Volume-Anomaly-Detector/), [Stock market anomaly detection](https://slicematrix.github.io/stock_market_anomalies.html)

### Pattern 3: MA Deviation Calculation

**What:** Calculate percentage distance from key EMAs

**When to use:** MA deviation factor calculation

**Example:**

```python
def calculate_ma_deviation(df: pd.DataFrame) -> Optional[dict]:
    """Calculate price deviation from 20/50/200 EMAs as percentage.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]

    Returns:
        Dict with keys: 'deviation_20', 'deviation_50', 'deviation_200' (percentage)
        or None if insufficient data

    Minimum data: 200 candles for all EMAs
    """
    if len(df) < 200:
        return None

    close = df['close']
    current_price = close.iloc[-1]

    # Calculate EMAs using pandas ewm (exponential weighted moving average)
    ema_20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema_50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ema_200 = close.ewm(span=200, adjust=False).mean().iloc[-1]

    # Percentage deviation: ((price - EMA) / EMA) * 100
    deviation_20 = ((current_price - ema_20) / ema_20) * 100
    deviation_50 = ((current_price - ema_50) / ema_50) * 100
    deviation_200 = ((current_price - ema_200) / ema_200) * 100

    return {
        'deviation_20': float(deviation_20),
        'deviation_50': float(deviation_50),
        'deviation_200': float(deviation_200)
    }
```

**Source:** [Distance from Moving Average indicator](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/distance-from-moving-average), [pandas.DataFrame.ewm](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html)

### Pattern 4: Volatility Score Normalization

**What:** Normalize ATR as percentage of price for cross-asset comparison

**When to use:** Volatility score factor calculation

**Example:**

```python
from src.backend.analysis.indicators import calculate_atr

def calculate_volatility_score(df: pd.DataFrame, atr_period: int = 14) -> Optional[dict]:
    """Calculate normalized volatility score for cross-asset comparison.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        atr_period: ATR period (default: 14)

    Returns:
        Dict with keys: 'atr', 'atr_percent', 'volatility_score' (0-100)
        or None if insufficient data

    Minimum data: atr_period + 1 candles (15 for default)
    """
    atr = calculate_atr(df, period=atr_period)

    if atr is None:
        return None

    current_price = df['close'].iloc[-1]

    if current_price == 0:
        return None

    # Normalize ATR as percentage of price
    atr_percent = (atr / current_price) * 100

    # Scale to 0-100 using percentile-based approach
    # Rule of thumb: 1% ATR = low volatility, 5%+ = high volatility
    # Linear scale: 0% = 0, 5% = 100
    volatility_score = min(atr_percent * 20, 100.0)  # 5% ATR maps to 100

    return {
        'atr': float(atr),
        'atr_percent': float(atr_percent),
        'volatility_score': float(volatility_score)
    }
```

**Source:** [Normalized ATR methodology](https://www.macroption.com/normalized-atr/), [ATR Normalized guide](https://help.trendspider.com/kb/indicators/atr-normalized)

### Pattern 5: Pydantic Model Validation

**What:** Type-safe validation for computed alpha factors

**When to use:** Validating factor calculation outputs

**Example:**

```python
from pydantic import BaseModel, Field
from typing import Optional

class MomentumData(BaseModel):
    """Momentum score components."""
    short_roc: float = Field(..., description="10-period rate of change (%)")
    long_roc: float = Field(..., description="20-period rate of change (%)")
    momentum_score: float = Field(..., ge=-100, le=100, description="Normalized momentum score")

class VolumeAnomalyData(BaseModel):
    """Volume anomaly detection results."""
    current_volume: float = Field(..., gt=0, description="Current candle volume")
    avg_volume: float = Field(..., gt=0, description="20-period average volume")
    volume_ratio: float = Field(..., gt=0, description="Current/average ratio")
    is_anomaly: bool = Field(..., description="True if volume > 2x average")

class MADeviationData(BaseModel):
    """Moving average deviation percentages."""
    deviation_20: float = Field(..., description="Deviation from 20 EMA (%)")
    deviation_50: float = Field(..., description="Deviation from 50 EMA (%)")
    deviation_200: float = Field(..., description="Deviation from 200 EMA (%)")

class VolatilityData(BaseModel):
    """Volatility score components."""
    atr: float = Field(..., gt=0, description="Average True Range")
    atr_percent: float = Field(..., gt=0, description="ATR as % of price")
    volatility_score: float = Field(..., ge=0, le=100, description="Normalized volatility (0-100)")

class AlphaFactors(BaseModel):
    """Complete alpha factors for a trading signal."""
    momentum: Optional[MomentumData] = Field(None, description="Momentum score data")
    volume_anomaly: Optional[VolumeAnomalyData] = Field(None, description="Volume anomaly data")
    ma_deviation: Optional[MADeviationData] = Field(None, description="MA deviation data")
    volatility: Optional[VolatilityData] = Field(None, description="Volatility score data")
```

**Source:** [Pydantic models documentation](https://docs.pydantic.dev/latest/concepts/models/), [Pydantic 2026 guide](https://devtoolbox.dedyn.io/blog/pydantic-complete-guide)

### Anti-Patterns to Avoid

- **Reimplementing ATR:** Use existing calculate_atr from indicators.py. Don't duplicate code.
- **Returning raw scalars:** Always return dict with named fields. Improves readability and future extensibility.
- **Ignoring zero division:** Check for zero price/volume before division. Return None gracefully.
- **Hardcoded normalization constants:** Document rationale for scaling factors (e.g., tanh divisor, volatility scale).
- **Mixing calculation and validation:** Keep factor functions pure (calculate only). Use Pydantic models for validation separately.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ATR calculation | Custom true range logic | calculate_atr from indicators.py | Already implemented and tested in Phase 8 |
| EMA calculation | Custom exponential smoothing | pandas.DataFrame.ewm() | Optimized, handles NaN, widely tested |
| Moving averages | Manual rolling sum | pandas.DataFrame.rolling().mean() | Built-in, efficient, consistent API |
| Normalization functions | Custom min-max/z-score | numpy.percentile, numpy.tanh | Optimized, numerically stable |
| Data validation | Manual type checking | Pydantic models | Type inference, automatic validation, better error messages |

**Key insight:** Alpha factors require robust numerical handling (zero division, NaN propagation, extreme values). pandas and numpy have battle-tested edge case handling. Pydantic ensures type safety without manual validation boilerplate. Custom implementations will miss edge cases and create maintenance burden.

## Common Pitfalls

### Pitfall 1: Insufficient Data for Long-Period Calculations

**What goes wrong:** MA deviation requires 200 candles for 200 EMA. New assets or short timeframes fail silently.

**Why it happens:** Alpha factors often need longer lookbacks than indicators. 200-period EMA needs 200 candles minimum.

**How to avoid:**
- Check minimum data requirements per function (10, 20, 200 candles)
- Return None with clear documentation when insufficient
- Log warnings at subagent level (not in pure functions)
- Document minimum data in docstrings

**Warning signs:**
- All MA deviations return None
- Only short-period factors populate
- IndexError on .iloc[-200]

### Pitfall 2: Zero Division in Normalization

**What goes wrong:** Volatility score divides ATR by price. Zero price causes ZeroDivisionError. Volume ratio divides by average volume—zero average fails.

**Why it happens:** Edge cases in data: gaps, halts, erroneous zero prices, newly listed assets.

**How to avoid:**
- Check denominator != 0 before division
- Return None if zero encountered (uncomputable)
- Document edge case behavior in docstrings
- Unit tests for zero price/volume scenarios

**Warning signs:**
- ZeroDivisionError in production logs
- Factor functions crash instead of returning None
- NaN or inf in computed values

### Pitfall 3: Momentum Score Normalization Out of Range

**What goes wrong:** Extreme price moves cause momentum score to exceed -100/+100 range despite normalization attempt.

**Why it happens:** Linear normalization (multiplying by constant) doesn't bound output. Tanh bounds but parameters need tuning.

**How to avoid:**
- Use tanh for bounded output: `np.tanh(value / scale) * 100`
- Tune scale parameter (divisor) based on typical ROC values (10-20 works for most assets)
- Add clipping as safety: `np.clip(score, -100, 100)`
- Test with extreme synthetic data (100% price move)

**Warning signs:**
- momentum_score = 150 or -200 (outside bounds)
- Validation errors from Pydantic Field(ge=-100, le=100)
- Inconsistent behavior across assets

**Source:** [Volatility-Adjusted Momentum Score normalization](https://www.tradingview.com/script/P71BL3mF-Volatility-Adjusted-Momentum-Score-VAMS-QuantAlgo/)

### Pitfall 4: Volume Anomaly False Positives

**What goes wrong:** Low-volume assets trigger anomalies constantly. High-volume spikes during news/events flagged as anomalies even when expected.

**Why it happens:** Fixed 2x threshold doesn't adapt to asset characteristics. Thin markets have natural volatility in volume.

**How to avoid:**
- Document that 2x threshold is baseline, may need tuning per asset
- Consider rolling std dev for adaptive thresholds (future enhancement)
- Return ratio in dict so consumers can apply custom thresholds
- Test with both low-volume and high-volume synthetic data

**Warning signs:**
- 80%+ of candles flagged as anomalies (threshold too low)
- No anomalies detected during obvious volume spikes (threshold too high)
- Different assets need different thresholds (expected—document it)

**Source:** [Volume anomaly detection methods](https://slicematrix.github.io/stock_market_anomalies.html)

### Pitfall 5: EMA Calculation Assumptions

**What goes wrong:** pandas ewm() with adjust=True vs adjust=False produces different values. Code assumes one, gets another.

**Why it happens:** adjust=True normalizes weights (EWMA), adjust=False uses recursive formula (EMA). TradingView uses adjust=False.

**How to avoid:**
- Always use adjust=False for TradingView-compatible EMA
- Document EMA calculation method in docstring
- Test against known EMA values (TradingView comparison)
- Be consistent across all factor functions

**Warning signs:**
- EMA values don't match TradingView/external sources
- Deviation percentages seem off
- Inconsistent results across timeframes

**Source:** [pandas.DataFrame.ewm documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html), [EMA calculation guide](https://www.statology.org/exponential-moving-average-pandas/)

## Code Examples

Verified patterns from official sources and project conventions.

### Example 1: Complete Momentum Score Implementation

```python
import pandas as pd
import numpy as np
from typing import Optional

def calculate_momentum_score(
    df: pd.DataFrame,
    short_period: int = 10,
    long_period: int = 20
) -> Optional[dict]:
    """Calculate momentum score from rate of change.

    Combines short-term and long-term rate of change (ROC) into a single
    momentum score normalized to -100/+100 scale using tanh function.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        short_period: Short ROC period (default: 10)
        long_period: Long ROC period (default: 20)

    Returns:
        Dict with keys:
            - short_roc: 10-period rate of change (%)
            - long_roc: 20-period rate of change (%)
            - momentum_score: Normalized score (-100 to +100)
        Returns None if insufficient data

    Minimum data: long_period + 1 candles (21 for default)

    Normalization: Uses tanh to bound output, scales to -100/+100.
    Positive scores indicate upward momentum, negative indicate downward.
    """
    if len(df) < long_period + 1:
        return None

    close = df['close']

    # Rate of change: ((close - close_n) / close_n) * 100
    short_roc = ((close.iloc[-1] - close.iloc[-short_period]) / close.iloc[-short_period]) * 100
    long_roc = ((close.iloc[-1] - close.iloc[-long_period]) / close.iloc[-long_period]) * 100

    # Combined momentum: weight short-term 60%, long-term 40%
    combined = (0.6 * short_roc + 0.4 * long_roc)

    # Normalize using tanh (bounds to -1/+1), then scale to -100/+100
    # Divisor 10 means ±10% ROC maps to ±0.76 (±76 after scaling)
    momentum_score = np.tanh(combined / 10) * 100

    # Safety clipping (tanh should bound, but handle numerical edge cases)
    momentum_score = np.clip(momentum_score, -100, 100)

    return {
        'short_roc': float(short_roc),
        'long_roc': float(long_roc),
        'momentum_score': float(momentum_score)
    }
```

### Example 2: Volume Anomaly Detection with Edge Cases

```python
def detect_volume_anomaly(
    df: pd.DataFrame,
    ma_period: int = 20,
    threshold: float = 2.0
) -> Optional[dict]:
    """Detect volume anomalies vs moving average.

    Compares current volume to rolling average and flags anomalies
    when volume exceeds threshold multiplier (default: 2x).

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        ma_period: MA period for baseline (default: 20)
        threshold: Anomaly threshold multiplier (default: 2.0 = 200%)

    Returns:
        Dict with keys:
            - current_volume: Current candle volume
            - avg_volume: 20-period average volume
            - volume_ratio: current_volume / avg_volume
            - is_anomaly: True if volume_ratio > threshold
        Returns None if insufficient data or zero average volume

    Minimum data: ma_period candles (20 for default)

    Note: Threshold may need tuning per asset. Low-volume assets
    naturally have higher variance. Use ratio for custom thresholds.
    """
    if len(df) < ma_period:
        return None

    volume = df['volume']
    current_volume = volume.iloc[-1]
    avg_volume = volume.rolling(window=ma_period).mean().iloc[-1]

    # Edge case: zero average volume (halts, new listings, gaps)
    if avg_volume == 0 or pd.isna(avg_volume):
        return None

    volume_ratio = current_volume / avg_volume
    is_anomaly = volume_ratio > threshold

    return {
        'current_volume': float(current_volume),
        'avg_volume': float(avg_volume),
        'volume_ratio': float(volume_ratio),
        'is_anomaly': bool(is_anomaly)
    }
```

### Example 3: MA Deviation with Graceful Degradation

```python
def calculate_ma_deviation(df: pd.DataFrame) -> Optional[dict]:
    """Calculate price deviation from 20/50/200 EMAs as percentage.

    Measures how far current price is from key moving averages.
    Positive deviation = price above MA (bullish position).
    Negative deviation = price below MA (bearish position).

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]

    Returns:
        Dict with keys:
            - deviation_20: Deviation from 20 EMA (%)
            - deviation_50: Deviation from 50 EMA (%)
            - deviation_200: Deviation from 200 EMA (%)
        Returns None if insufficient data (< 200 candles)

    Minimum data: 200 candles for 200 EMA

    Formula: ((price - EMA) / EMA) * 100
    Uses adjust=False for TradingView-compatible EMA calculation.
    """
    if len(df) < 200:
        return None

    close = df['close']
    current_price = close.iloc[-1]

    # Calculate EMAs using pandas ewm (exponential weighted moving average)
    # adjust=False for TradingView-compatible calculation
    ema_20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
    ema_50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ema_200 = close.ewm(span=200, adjust=False).mean().iloc[-1]

    # Edge case: zero EMA (shouldn't happen with valid price data)
    if ema_20 == 0 or ema_50 == 0 or ema_200 == 0:
        return None

    # Percentage deviation: ((price - EMA) / EMA) * 100
    deviation_20 = ((current_price - ema_20) / ema_20) * 100
    deviation_50 = ((current_price - ema_50) / ema_50) * 100
    deviation_200 = ((current_price - ema_200) / ema_200) * 100

    return {
        'deviation_20': float(deviation_20),
        'deviation_50': float(deviation_50),
        'deviation_200': float(deviation_200)
    }
```

### Example 4: Volatility Score with ATR Reuse

```python
from src.backend.analysis.indicators import calculate_atr

def calculate_volatility_score(
    df: pd.DataFrame,
    atr_period: int = 14
) -> Optional[dict]:
    """Calculate normalized volatility score for cross-asset comparison.

    Normalizes ATR as percentage of price, then scales to 0-100.
    Allows comparing volatility across assets with different price levels.

    Args:
        df: DataFrame with columns [timestamp, open, high, low, close, volume]
        atr_period: ATR period (default: 14)

    Returns:
        Dict with keys:
            - atr: Average True Range (absolute)
            - atr_percent: ATR as percentage of price
            - volatility_score: Normalized score (0-100)
        Returns None if insufficient data or zero price

    Minimum data: atr_period + 1 candles (15 for default)

    Scaling: 0% ATR = 0, 5% ATR = 100. Linear interpolation.
    5% chosen as high volatility threshold for most assets.
    Bitcoin often 3-7% daily, stocks typically 1-3% daily.
    """
    # Reuse existing ATR calculation from indicators.py
    atr = calculate_atr(df, period=atr_period)

    if atr is None:
        return None

    current_price = df['close'].iloc[-1]

    # Edge case: zero price (shouldn't happen with valid data)
    if current_price == 0:
        return None

    # Normalize ATR as percentage of price
    atr_percent = (atr / current_price) * 100

    # Scale to 0-100 using linear mapping
    # 0% ATR = 0, 5% ATR = 100, cap at 100
    # Formula: atr_percent * 20 (since 5 * 20 = 100)
    volatility_score = min(atr_percent * 20, 100.0)

    return {
        'atr': float(atr),
        'atr_percent': float(atr_percent),
        'volatility_score': float(volatility_score)
    }
```

### Example 5: Test Pattern with Synthetic Data

```python
# From existing test_indicators.py pattern
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

@pytest.fixture
def synthetic_ohlcv():
    """Generate synthetic OHLCV data for alpha factor testing (100 candles)."""
    np.random.seed(42)
    base_price = 100.0
    timestamps = [int((datetime.now() - timedelta(days=100-i)).timestamp() * 1000) for i in range(100)]

    # Generate realistic price movement with trend and volatility
    prices = [base_price]
    for _ in range(99):
        change = np.random.normal(0.001, 0.02)  # 0.1% drift, 2% volatility
        prices.append(prices[-1] * (1 + change))

    data = []
    for i, timestamp in enumerate(timestamps):
        close = prices[i]
        volatility = close * 0.02
        high = close + abs(np.random.normal(0, volatility))
        low = close - abs(np.random.normal(0, volatility))
        open_price = low + np.random.random() * (high - low)
        volume = np.random.uniform(1000, 10000)

        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    return pd.DataFrame(data)

def test_momentum_score_returns_dict_in_range(synthetic_ohlcv):
    """Verify momentum score returns dict with values in -100/+100 range."""
    from src.backend.analysis.alpha_factors import calculate_momentum_score

    result = calculate_momentum_score(synthetic_ohlcv)

    assert result is not None
    assert isinstance(result, dict)
    assert set(result.keys()) == {'short_roc', 'long_roc', 'momentum_score'}
    assert -100 <= result['momentum_score'] <= 100
    assert isinstance(result['momentum_score'], float)

def test_volume_anomaly_insufficient_data_returns_none():
    """Verify volume anomaly returns None for insufficient data."""
    from src.backend.analysis.alpha_factors import detect_volume_anomaly

    # Only 10 candles, need 20
    small_df = pd.DataFrame({
        'timestamp': range(10),
        'open': [100] * 10,
        'high': [101] * 10,
        'low': [99] * 10,
        'close': [100] * 10,
        'volume': [1000] * 10
    })

    result = detect_volume_anomaly(small_df)

    assert result is None
```

**Source:** Adapted from `/Users/johnny_main/Developer/projects/titan-terminal/src/backend/tests/test_indicators.py`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom alpha factor formulas | Standardized factor libraries (WorldQuant 101 Alphas) | 2016+ | Industry-standard factors, reproducible research |
| Fixed normalization ranges | Adaptive percentile-based scaling | 2020+ | Better handling of outliers, cross-asset robustness |
| Separate validation code | Pydantic models | 2023+ (Pydantic v2) | Type-safe, automatic validation, 5-50x faster |
| Manual EMA calculation | pandas.DataFrame.ewm() | 2015+ | Optimized, handles NaN, TradingView-compatible |

**Deprecated/outdated:**
- **Custom ROC implementations:** pandas has efficient diff() and pct_change() methods. No need for manual calculation.
- **Z-score only for anomalies:** Ratio-based thresholds more interpretable for traders. Z-score still useful but not sole method.
- **Fixed volatility thresholds:** Cross-asset comparison requires percentage-based normalization. Absolute ATR insufficient.

## Open Questions

1. **Optimal momentum normalization parameters**
   - What we know: tanh with divisor 10 works for typical assets; min-max clipping as safety
   - What's unclear: Whether single normalization works across all crypto (BTC, ETH, SOL) or needs per-asset tuning
   - Recommendation: Start with tanh(combined/10) * 100. Monitor momentum_score distribution in production. Tune divisor if >10% of scores hit ±100 bounds.

2. **Volume anomaly threshold sensitivity**
   - What we know: 2x threshold is industry standard baseline; thin markets more volatile
   - What's unclear: Whether BTC/ETH/SOL need different thresholds
   - Recommendation: Implement 2x default, expose threshold parameter for tuning. Document that threshold may need adjustment per asset in future phases.

3. **Volatility score scaling factor**
   - What we know: 5% ATR as "high volatility" works for stocks; crypto often 3-7% daily
   - What's unclear: Whether linear 20x multiplier (5% → 100) is appropriate for crypto
   - Recommendation: Use 20x multiplier initially. If BTC regularly hits 100 score, adjust to 30x (3.33% → 100). Document scaling rationale.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.0 |
| Config file | none — runs via `pytest src/backend/tests/` |
| Quick run command | `pytest src/backend/tests/test_alpha_factors.py -x` |
| Full suite command | `pytest src/backend/tests/` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-019 | Module imports without error | unit | `pytest src/backend/tests/test_alpha_factors.py::test_module_import -x` | ❌ Wave 0 |
| REQ-020 | Momentum score returns dict with -100/+100 range | unit | `pytest src/backend/tests/test_alpha_factors.py::test_momentum_score -x` | ❌ Wave 0 |
| REQ-021 | Volume anomaly detects 2x threshold correctly | unit | `pytest src/backend/tests/test_alpha_factors.py::test_volume_anomaly -x` | ❌ Wave 0 |
| REQ-022 | MA deviation returns percentage for 20/50/200 EMAs | unit | `pytest src/backend/tests/test_alpha_factors.py::test_ma_deviation -x` | ❌ Wave 0 |
| REQ-023 | Volatility score returns 0-100 range | unit | `pytest src/backend/tests/test_alpha_factors.py::test_volatility_score -x` | ❌ Wave 0 |
| REQ-024 | AlphaFactors model validates all fields | unit | `pytest src/backend/tests/test_alpha_factors.py::test_alpha_factors_model -x` | ❌ Wave 0 |
| REQ-045 | All factors handle insufficient data (return None) | unit | `pytest src/backend/tests/test_alpha_factors.py::test_insufficient_data -x` | ❌ Wave 0 |
| REQ-045 | Zero division edge cases handled | unit | `pytest src/backend/tests/test_alpha_factors.py::test_zero_division -x` | ❌ Wave 0 |
| REQ-045 | Extreme price moves don't break normalization | unit | `pytest src/backend/tests/test_alpha_factors.py::test_extreme_values -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest src/backend/tests/test_alpha_factors.py -x` (fast, exits on first failure)
- **Per wave merge:** `pytest src/backend/tests/` (full suite including existing 28 tests + Phase 8 indicators)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `src/backend/analysis/alpha_factors.py` — four factor functions + helper functions
- [ ] `src/backend/models/signals.py` — add AlphaFactors Pydantic model (or new file if preferred)
- [ ] `src/backend/tests/test_alpha_factors.py` — comprehensive unit tests with synthetic data
- [ ] `src/backend/analysis/__init__.py` — update exports to include alpha factor functions

## Sources

### Primary (HIGH confidence)

- [pandas.DataFrame.ewm documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html) - EMA calculation method
- [Normalized ATR: Two Ways of Expressing ATR as Percentage](https://www.macroption.com/normalized-atr/) - Volatility normalization methodology
- [Distance From Moving Average | ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-indicators/distance-from-moving-average) - MA deviation indicator
- [Rate of Change (ROC) | Stock Indicators for Python](https://python.stockindicators.dev/indicators/Roc/) - ROC formula and implementation
- [Pydantic models documentation](https://docs.pydantic.dev/latest/concepts/models/) - Model validation patterns
- Project files: `src/backend/analysis/indicators.py`, `src/backend/tests/test_indicators.py` - Existing patterns

### Secondary (MEDIUM confidence)

- [WorldQuant 101 Alphas](https://docs.dolphindb.com/en/Tutorials/wq101alpha.html) - Industry-standard alpha factor formulas
- [Understanding Alpha Factors — Foundation of Quantitative Trading](https://pyquantlab.medium.com/understanding-alpha-factors-the-foundation-of-quantitative-trading-strategies-9b5604e7581c) - Alpha factor methodology
- [Volume Anomaly Detector — TradingView](https://www.tradingview.com/script/M7YYuUEP-Volume-Anomaly-Detector/) - Volume anomaly detection approach
- [Stock Market Volume Anomaly Detection](https://slicematrix.github.io/stock_market_anomalies.html) - Statistical methods for anomalies
- [Volatility-Adjusted Momentum Score](https://www.tradingview.com/script/P71BL3mF-Volatility-Adjusted-Momentum-Score-VAMS-QuantAlgo/) - Momentum normalization techniques
- [pandas 3.0 missing data handling](https://pandas.pydata.org/docs/user_guide/missing_data.html) - NaN handling best practices (2026)

### Tertiary (LOW confidence)

- General web search results on momentum indicators - Community practices
- Trading forum discussions on thresholds - Anecdotal threshold recommendations

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pandas/numpy already installed and compatible; Pydantic v2 confirmed in use
- Architecture: HIGH - Pure function pattern established in Phase 8; Pydantic model patterns clear; ATR reuse straightforward
- Pitfalls: HIGH - Edge cases (zero division, insufficient data, normalization bounds) well-documented; pandas NaN handling robust

**Research date:** 2026-02-27
**Valid until:** 2026-04-27 (60 days) - Alpha factor methodologies are stable; pandas/numpy APIs mature

**Environment verified:**
- Python 3.12.7
- pandas 2.3.0 (compatible)
- numpy 1.26.4 (compatible)
- pytest 8.4.0 (compatible)
- pydantic latest (v2 Rust-backed, 5-50x faster)

**Key findings:**
1. All four alpha factors have established quantitative finance methodologies
2. pandas ewm() and rolling() provide all needed calculation primitives
3. Reusing calculate_atr from Phase 8 eliminates code duplication
4. Pydantic v2 provides fast, type-safe validation for computed factors
5. Pure function pattern from Phase 8 applies directly to alpha factors
6. Test infrastructure (pytest, synthetic OHLCV fixtures) ready to use
