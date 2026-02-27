# Phase 11: WeeklySubagent + TASignal Extension - Research

**Researched:** 2026-02-27
**Domain:** Pydantic model extension, subagent implementation, OHLCV data fetching, technical analysis pipeline
**Confidence:** HIGH

## Summary

Phase 11 extends the existing TASignal Pydantic model with optional `wyckoff` and `alpha_factors` fields, then implements WeeklySubagent as the first fully functional subagent proving the complete analysis pipeline. The phase integrates all completed analysis modules (indicators, alpha_factors, wyckoff) with the existing OHLCVClient to produce comprehensive technical analysis signals.

All building blocks are already implemented: TASignal model exists, all analysis functions are complete and tested, OHLCVClient is production-ready, and Pydantic models for WyckoffAnalysis and AlphaFactors are available. The main work is extending the TASignal model and implementing the WeeklySubagent class that orchestrates these components.

**Primary recommendation:** Extend TASignal with two optional nested Pydantic model fields for backward compatibility. Implement WeeklySubagent.analyze() as a pure computational pipeline (no LLM calls) that chains indicator calculations, alpha factors, Wyckoff detection, and trend determination into a single TASignal output. Use mocked OHLCV data in tests to avoid live API dependencies.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**File Locations:**
- WeeklySubagent at `src/backend/agents/ta_ensemble/weekly_subagent.py`
- Extend existing TASignal Pydantic model in `src/backend/models/`
- Uses WyckoffAnalysis from `src/backend/analysis/wyckoff.py`
- Uses AlphaFactors from `src/backend/analysis/alpha_factors.py`

**TASignal Extension:**
- Add two new nested fields: `wyckoff` (WyckoffAnalysis) and `alpha_factors` (AlphaFactors)
- Both fields should be optional for backward compatibility
- Existing TASignal tests must continue to pass

**WeeklySubagent Data Fetching:**
- Takes a symbol (e.g. "BTC/USDT") as input
- Fetches 1w OHLCV data using `get_ohlcv_client()` with limit=104 (2 years of weekly candles)
- If fewer than 52 candles returned: log warning with symbol, timeframe, and actual candle count, then proceed with available data

**Analysis Pipeline:**
Runs all analysis in sequence:
1. Calculate all indicators from `src/backend/analysis/indicators.py`
2. Calculate alpha factors from `src/backend/analysis/alpha_factors.py`
3. Run `detect_wyckoff` from `src/backend/analysis/wyckoff.py`
4. Determine overall trend direction (BULLISH/BEARISH/NEUTRAL) and confidence (0-100) based on confluence of RSI, MACD, ADX, and Wyckoff phase

**Output Format:**
- Output must be a valid TASignal JSON object
- Entry point: `WeeklySubagent.analyze(symbol) -> TASignal`

**Testing:**
- Full unit tests with mocked OHLCV data
- No live API calls in tests

### Claude's Discretion

- Internal helper methods and code organization within WeeklySubagent
- Specific confidence calculation weights for indicator confluence
- Error handling patterns beyond the required warning logging
- Type hints and docstring style

### Deferred Ideas (OUT OF SCOPE)

None — Phase 11 scope is well-defined

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-025 | Add `wyckoff: Optional[WyckoffData]` to TASignal | Pydantic model extension pattern, backward compatibility through Optional fields |
| REQ-026 | Add `alpha_factors: Optional[AlphaFactors]` to TASignal | Nested Pydantic models, json_schema_extra examples update |
| REQ-027 | Backward compatible with existing tests | Optional fields default to None, existing test payloads remain valid |
| REQ-028 | WeeklySubagent full implementation | Class structure, OHLCVClient integration, pandas DataFrame conversion, analysis pipeline orchestration |
| REQ-031 | Each subagent outputs extended TASignal | Extended model with populated wyckoff and alpha_factors fields |
| REQ-032 | Use OHLCVClient from data/ohlcv_client.py | get_ohlcv_client() singleton, fetch_ohlcv() method, list[dict] to pd.DataFrame conversion |
| REQ-033 | Fetch 2 years OHLCV history | limit=104 for weekly (1w timeframe), sufficient for Wyckoff detection (100+ candles) |
| REQ-034 | Log warning if insufficient history | Python logging module, warning level, conditional check |
| REQ-046 | Unit tests for WeeklySubagent | pytest fixtures, unittest.mock for OHLCVClient, synthetic OHLCV data patterns |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.5.0+ | Model validation, nested models, optional fields | Industry standard for Python data validation, already used throughout project |
| pandas | 2.0.0+ | DataFrame operations, OHLCV data manipulation | Required by pandas-ta and analysis modules, universal data analysis library |
| pytest | Latest | Unit testing framework | Python testing standard, already used for 26+ existing tests |
| unittest.mock | Built-in | Mocking OHLCVClient for tests | Python standard library, no external deps, ideal for unit test isolation |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging | Built-in | Warning messages for insufficient data | Standard Python logging, configured project-wide |
| typing | Built-in | Type hints (Optional, Literal, etc.) | Already used consistently across codebase |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic Optional | Custom None checks | Pydantic provides validation, serialization, and JSON schema generation automatically |
| unittest.mock | pytest-mock plugin | Mock is built-in and sufficient for this phase, pytest-mock adds wrapper but no essential features needed here |
| logging module | print statements | Logging provides levels, formatting, and production-ready configurability |

**Installation:**

All dependencies already present in requirements.txt:
```bash
# Already installed:
pydantic>=2.5.0
pandas>=2.0.0
pandas-ta>=0.3.14b
scipy>=1.11.0
ccxt>=4.0.0
```

Testing framework (add if missing):
```bash
pytest>=7.0.0
```

## Architecture Patterns

### Recommended Project Structure

Current structure (already in place):
```
src/backend/
├── models/                    # Pydantic models
│   ├── ta_signal.py          # EXTEND: Add wyckoff, alpha_factors fields
│   ├── wyckoff.py            # Already complete
│   └── alpha_factors.py      # Already complete
├── analysis/                  # Pure functions, no state
│   ├── indicators.py         # 8 functions, all tested
│   ├── alpha_factors.py      # 4 functions, all tested
│   └── wyckoff.py            # detect_wyckoff() complete
├── data/
│   └── ohlcv_client.py       # OHLCVClient, get_ohlcv_client()
├── agents/
│   └── ta_ensemble/
│       └── weekly_subagent.py  # IMPLEMENT THIS
└── tests/
    ├── test_indicators.py    # 26 tests passing
    ├── test_alpha_factors.py # 28 tests passing
    ├── test_wyckoff.py       # 20 tests passing
    └── test_weekly_subagent.py  # CREATE THIS
```

### Pattern 1: Pydantic Model Extension with Backward Compatibility

**What:** Add optional nested model fields to existing Pydantic model without breaking existing code

**When to use:** Extending models that are already in production or have existing tests

**Example:**
```python
# Source: Pydantic 2.x documentation + project patterns
from typing import Optional
from pydantic import BaseModel, Field

# Existing nested models (already implemented)
from src.backend.models.wyckoff import WyckoffAnalysis
from src.backend.models.alpha_factors import AlphaFactors

class TASignal(BaseModel):
    """Extended with optional wyckoff and alpha_factors fields."""
    # ... existing required fields ...
    symbol: str
    timeframe: Literal["weekly", "daily", "4h"]
    trend: TrendData
    momentum: MomentumData
    key_levels: KeyLevels
    patterns: PatternData
    overall: OverallAssessment

    # NEW: Optional fields for backward compatibility
    wyckoff: Optional[WyckoffAnalysis] = Field(
        None,
        description="Wyckoff phase analysis (accumulation/distribution)"
    )
    alpha_factors: Optional[AlphaFactors] = Field(
        None,
        description="Alpha factor calculations (momentum, volume, volatility)"
    )
```

**Why this works:**
- Optional fields default to None
- Existing test payloads without these fields remain valid
- New code can populate fields, old code ignores them
- JSON serialization handles None gracefully
- Pydantic validation only runs on non-None values

### Pattern 2: Analysis Pipeline Orchestration

**What:** Chain multiple analysis functions into a single output, handling partial failures gracefully

**When to use:** When combining multiple independent analysis modules that may return None

**Example:**
```python
# Source: Project STATE.md decisions + analysis module patterns
import pandas as pd
from typing import Optional
import logging

from src.backend.analysis import (
    calculate_rsi, calculate_macd, calculate_adx,
    calculate_momentum_score, detect_volume_anomaly,
    calculate_ma_deviation, calculate_volatility_score,
    detect_wyckoff
)
from src.backend.models.alpha_factors import AlphaFactors
from src.backend.models.wyckoff import WyckoffAnalysis

logger = logging.getLogger(__name__)

def run_analysis_pipeline(df: pd.DataFrame) -> tuple:
    """
    Run full analysis pipeline, handling None returns gracefully.

    Returns:
        (wyckoff_analysis, alpha_factors, indicators_dict)
        Any component may be None if insufficient data.
    """
    # Step 1: Calculate indicators (used by multiple downstream steps)
    indicators = {
        'rsi': calculate_rsi(df),
        'macd': calculate_macd(df),
        'adx': calculate_adx(df),
    }

    # Step 2: Calculate alpha factors
    alpha_data = {}
    if momentum := calculate_momentum_score(df):
        alpha_data['momentum'] = momentum
    if volume := detect_volume_anomaly(df):
        alpha_data['volume_anomaly'] = volume
    if ma_dev := calculate_ma_deviation(df):
        alpha_data['ma_deviation'] = ma_dev
    if vol := calculate_volatility_score(df):
        alpha_data['volatility'] = vol

    alpha_factors = AlphaFactors(**alpha_data) if alpha_data else None

    # Step 3: Wyckoff detection (requires 100+ candles)
    wyckoff = detect_wyckoff(df)

    return wyckoff, alpha_factors, indicators
```

**Key principles:**
- Each analysis function returns Optional (None on insufficient data)
- Use walrus operator `:=` for concise None checks
- Build partial results even if some components fail
- Log warnings for missing components but don't crash
- Return structured data for downstream decision logic

### Pattern 3: OHLCV Data Conversion

**What:** Convert OHLCVClient list[dict] output to pandas DataFrame for analysis functions

**When to use:** Any time fetching data from OHLCVClient for use with indicators/alpha/wyckoff modules

**Example:**
```python
# Source: Project analysis modules expect pd.DataFrame with lowercase columns
import pandas as pd
from src.backend.data.ohlcv_client import get_ohlcv_client

def fetch_and_convert_ohlcv(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """
    Fetch OHLCV data and convert to DataFrame format expected by analysis modules.

    Analysis modules expect lowercase column names:
    [timestamp, open, high, low, close, volume]
    """
    client = get_ohlcv_client()
    candles = client.fetch_ohlcv(symbol, timeframe, limit=limit)

    # OHLCVClient already returns dicts with lowercase keys
    df = pd.DataFrame(candles)

    # Verify expected columns present
    required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required):
        raise ValueError(f"Missing required columns. Got: {df.columns.tolist()}")

    return df
```

### Pattern 4: Trend Determination by Indicator Confluence

**What:** Combine multiple indicator signals to determine overall trend direction and confidence

**When to use:** When synthesizing multiple technical indicators into a single actionable signal

**Example:**
```python
# Source: User requirements + technical analysis best practices
def determine_trend_with_confidence(
    rsi: Optional[float],
    macd: Optional[dict],
    adx: Optional[float],
    wyckoff_phase: Optional[str]
) -> tuple[str, int]:
    """
    Determine trend direction and confidence from indicator confluence.

    Returns:
        (direction, confidence) where direction in ["BULLISH", "BEARISH", "NEUTRAL"]
        and confidence in 0-100 range.
    """
    signals = []

    # RSI: >70 overbought (bearish), <30 oversold (bullish), 30-70 neutral
    if rsi is not None:
        if rsi > 70:
            signals.append(("BEARISH", 60))
        elif rsi < 30:
            signals.append(("BULLISH", 60))
        else:
            signals.append(("NEUTRAL", 40))

    # MACD: histogram positive = bullish, negative = bearish
    if macd is not None:
        if macd['histogram'] > 0:
            signals.append(("BULLISH", 70))
        else:
            signals.append(("BEARISH", 70))

    # ADX: >25 = strong trend (boost confidence), <20 = weak trend
    trend_strength = 1.0
    if adx is not None:
        if adx > 25:
            trend_strength = 1.3
        elif adx < 20:
            trend_strength = 0.7

    # Wyckoff: Phase E = strong directional signal
    if wyckoff_phase:
        if "accumulation_e" in wyckoff_phase:
            signals.append(("BULLISH", 80))
        elif "distribution_e" in wyckoff_phase:
            signals.append(("BEARISH", 80))

    # Aggregate: majority vote on direction, average confidence
    if not signals:
        return ("NEUTRAL", 50)

    bullish_count = sum(1 for d, _ in signals if d == "BULLISH")
    bearish_count = sum(1 for d, _ in signals if d == "BEARISH")

    if bullish_count > bearish_count:
        direction = "BULLISH"
        avg_confidence = sum(c for d, c in signals if d == "BULLISH") / bullish_count
    elif bearish_count > bullish_count:
        direction = "BEARISH"
        avg_confidence = sum(c for d, c in signals if d == "BEARISH") / bearish_count
    else:
        direction = "NEUTRAL"
        avg_confidence = 50

    # Apply trend strength multiplier
    final_confidence = int(min(avg_confidence * trend_strength, 100))

    return (direction, final_confidence)
```

### Anti-Patterns to Avoid

- **Calling analysis functions with raw lists:** All analysis functions expect pd.DataFrame, not list[dict]. Always convert OHLCV data first.
- **Treating None as error:** Analysis functions return None for insufficient data. This is normal, not an exception. Check for None and handle gracefully.
- **Mutating shared DataFrames:** Some analysis functions (calculate_vwap) create copies. Never rely on in-place mutations.
- **Ignoring logging:** The requirement explicitly states "log warning if insufficient history". Don't silently proceed without logging.
- **Over-engineering confidence:** User has discretion on confidence calculation. Start simple (weighted average), iterate if needed. Don't prematurely optimize.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pydantic model validation | Manual isinstance checks, custom validators | Pydantic field validators, model_validator | Pydantic handles edge cases (nested models, None, type coercion) that manual validation misses |
| DataFrame column validation | Manual column name checks | pandas column assertions in tests | Analysis functions already handle missing columns gracefully with try/except |
| OHLCV data fetching | Custom CCXT wrapper | get_ohlcv_client() singleton | Already implemented with retry logic, rate limiting, exponential backoff |
| Test mocking | Custom mock classes | unittest.mock.Mock, patch decorator | Standard library, pytest-compatible, handles method call verification |
| Indicator calculations | Custom RSI/MACD implementations | pandas-ta functions via analysis modules | Already tested (26 tests), handles edge cases, production-ready |

**Key insight:** Phase 11 is integration work, not new algorithms. Every component already exists and is tested. The value is in orchestration, not reimplementation.

## Common Pitfalls

### Pitfall 1: Breaking Backward Compatibility with Required Fields

**What goes wrong:** Adding wyckoff/alpha_factors as required fields breaks all existing TASignal usage and tests

**Why it happens:** Natural instinct is to make fields required since WeeklySubagent will always populate them

**How to avoid:**
- Use `Optional[WyckoffAnalysis]` and `Optional[AlphaFactors]`
- Default to `None` with `Field(None, description=...)`
- Run existing tests after model changes to verify no breaks

**Warning signs:**
- Test failures in test_ta_signal.py (if exists)
- ValidationError exceptions when parsing old JSON payloads
- Other agents (DailySubagent, FourHourSubagent) failing

### Pitfall 2: Forgetting pd.DataFrame Conversion

**What goes wrong:** Passing OHLCVClient list[dict] directly to analysis functions causes KeyError or AttributeError

**Why it happens:** OHLCVClient returns list[dict], but all analysis functions expect pd.DataFrame with column access

**How to avoid:**
```python
# WRONG:
candles = client.fetch_ohlcv(symbol, "1w", limit=104)
rsi = calculate_rsi(candles)  # Fails: list has no 'close' attribute

# RIGHT:
candles = client.fetch_ohlcv(symbol, "1w", limit=104)
df = pd.DataFrame(candles)
rsi = calculate_rsi(df)  # Works: df['close'] exists
```

**Warning signs:**
- `TypeError: 'list' object is not subscriptable`
- `KeyError: 'close'`
- `AttributeError: 'list' object has no attribute 'iloc'`

### Pitfall 3: Insufficient Data Handling

**What goes wrong:** Not checking for None returns from analysis functions causes NoneType errors downstream

**Why it happens:** Analysis functions return None when data is insufficient, but code assumes they always succeed

**How to avoid:**
```python
# WRONG:
wyckoff = detect_wyckoff(df)
phase = wyckoff.phase  # Crashes if wyckoff is None

# RIGHT:
wyckoff = detect_wyckoff(df) if len(df) >= 100 else None
if wyckoff:
    phase = wyckoff.phase
else:
    logger.warning(f"Wyckoff detection skipped: only {len(df)} candles")
    phase = "unknown"
```

**Warning signs:**
- `AttributeError: 'NoneType' object has no attribute 'phase'`
- Tests failing with None-related errors
- Production crashes on symbols with limited history

### Pitfall 4: Logging vs Printing

**What goes wrong:** Using print() instead of logging.warning() for insufficient data warnings

**Why it happens:** print() is simpler for quick debugging, but requirement explicitly says "log warning"

**How to avoid:**
```python
import logging
logger = logging.getLogger(__name__)

# WRONG:
if len(candles) < 52:
    print(f"Warning: only {len(candles)} candles")

# RIGHT:
if len(candles) < 52:
    logger.warning(
        f"Insufficient history for {symbol} on {timeframe}: "
        f"got {len(candles)} candles, recommended 52+"
    )
```

**Warning signs:**
- Code review feedback about using print
- Production logs missing expected warnings
- Difficulty filtering logs by severity

### Pitfall 5: Test Isolation - Using Live API Calls

**What goes wrong:** Tests call real OHLCVClient.fetch_ohlcv(), making tests slow, flaky, and dependent on network

**Why it happens:** Easier to use real client than mock it

**How to avoid:**
```python
# Use unittest.mock to replace OHLCVClient in tests
from unittest.mock import patch, Mock

def test_weekly_subagent_analyze(synthetic_ohlcv_104):
    """Test WeeklySubagent with mocked OHLCV data."""
    mock_client = Mock()
    mock_client.fetch_ohlcv.return_value = synthetic_ohlcv_104.to_dict('records')

    with patch('src.backend.data.ohlcv_client.get_ohlcv_client', return_value=mock_client):
        subagent = WeeklySubagent()
        result = subagent.analyze("BTC/USDT")

        # Verify mock was called correctly
        mock_client.fetch_ohlcv.assert_called_once_with("BTC/USDT", "1w", limit=104)

        # Verify result structure
        assert result.symbol == "BTC/USDT"
        assert result.wyckoff is not None
```

**Warning signs:**
- Tests taking >5 seconds to run
- Intermittent test failures (network issues)
- Tests failing when offline
- Rate limit errors in test runs

### Pitfall 6: Mapping TASignal Structure to Raw Indicators

**What goes wrong:** WeeklySubagent must output TASignal with existing structure (trend, momentum, key_levels, patterns, overall) but user decisions don't specify how to map raw indicators to these nested models

**Why it happens:** TASignal expects TrendData, MomentumData, KeyLevels, PatternData, OverallAssessment nested models, but analysis functions return raw floats/dicts

**How to avoid:**
```python
# Map raw indicators to TASignal nested models
from src.backend.models.ta_signal import (
    TASignal, TrendData, MomentumData, KeyLevels,
    PatternData, OverallAssessment
)

# Example mapping logic (Claude's discretion):
def build_ta_signal(
    symbol: str,
    df: pd.DataFrame,
    indicators: dict,
    wyckoff: Optional[WyckoffAnalysis],
    alpha_factors: Optional[AlphaFactors]
) -> TASignal:
    """Build TASignal from raw analysis outputs."""

    # Determine trend from indicators
    direction, confidence = determine_trend_with_confidence(
        indicators.get('rsi'),
        indicators.get('macd'),
        indicators.get('adx'),
        wyckoff.phase if wyckoff else None
    )

    # Map to TrendData structure
    trend = TrendData(
        direction=direction.lower(),  # "BULLISH" -> "bullish"
        strength="strong" if confidence > 70 else "moderate" if confidence > 40 else "weak",
        ema_alignment="bullish" if direction == "BULLISH" else "bearish" if direction == "BEARISH" else "neutral"
    )

    # Build other nested models similarly...
    return TASignal(
        symbol=symbol,
        timeframe="weekly",
        trend=trend,
        momentum=momentum,
        key_levels=key_levels,
        patterns=patterns,
        overall=overall,
        wyckoff=wyckoff,  # NEW
        alpha_factors=alpha_factors  # NEW
    )
```

**Warning signs:**
- Pydantic validation errors about missing fields
- Type errors (passing float where Literal["bullish"] expected)
- Confusion about how to populate PatternData.detected list

## Code Examples

Verified patterns from official sources and existing project code:

### Example 1: Extending TASignal Model

```python
# File: src/backend/models/ta_signal.py
# Source: Existing ta_signal.py + Pydantic 2.x Optional fields pattern

from typing import Literal, Optional
from pydantic import BaseModel, Field

from src.backend.models.wyckoff import WyckoffAnalysis
from src.backend.models.alpha_factors import AlphaFactors

# ... existing nested models (TrendData, MomentumData, etc.) ...

class TASignal(BaseModel):
    """
    Technical Analysis signal for a specific timeframe.

    Output structure for weekly, daily, and 4-hour TA subagents.
    Extended with optional Wyckoff and alpha factor analysis.
    """
    # Existing required fields
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC')")
    timeframe: Literal["weekly", "daily", "4h"] = Field(
        ..., description="Timeframe for this analysis"
    )
    trend: TrendData
    momentum: MomentumData
    key_levels: KeyLevels
    patterns: PatternData
    overall: OverallAssessment

    # NEW: Optional fields for extended analysis
    wyckoff: Optional[WyckoffAnalysis] = Field(
        None,
        description="Wyckoff accumulation/distribution phase analysis"
    )
    alpha_factors: Optional[AlphaFactors] = Field(
        None,
        description="Alpha factor calculations (momentum, volume, volatility)"
    )

    # Update json_schema_extra to include example with new fields
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTC",
                    "timeframe": "weekly",
                    "trend": {
                        "direction": "bullish",
                        "strength": "strong",
                        "ema_alignment": "bullish"
                    },
                    "momentum": {
                        "rsi": 65.0,
                        "macd_bias": "bullish",
                        "momentum_divergence": False
                    },
                    "key_levels": {
                        "major_support": 60000.0,
                        "major_resistance": 70000.0
                    },
                    "patterns": {
                        "detected": ["ascending_triangle"],
                        "pattern_bias": "bullish"
                    },
                    "overall": {
                        "bias": "bullish",
                        "confidence": 75,
                        "notes": "Strong weekly uptrend with bullish EMA alignment"
                    },
                    "wyckoff": {
                        "phase": "accumulation_e",
                        "phase_confidence": 80,
                        "events": [],
                        "volume_confirms": True,
                        "analysis_notes": "Markup phase with volume confirmation"
                    },
                    "alpha_factors": {
                        "momentum": {
                            "short_roc": 5.2,
                            "long_roc": 3.8,
                            "momentum_score": 45.6
                        },
                        "volatility": {
                            "atr": 150.5,
                            "atr_percent": 2.3,
                            "volatility_score": 46.0
                        }
                    }
                }
            ]
        }
    }
```

### Example 2: WeeklySubagent Implementation Structure

```python
# File: src/backend/agents/ta_ensemble/weekly_subagent.py
# Source: Project patterns + user requirements

import logging
import pandas as pd
from typing import Optional

from src.backend.data.ohlcv_client import get_ohlcv_client
from src.backend.models.ta_signal import TASignal, TrendData, MomentumData, KeyLevels, PatternData, OverallAssessment
from src.backend.models.wyckoff import WyckoffAnalysis
from src.backend.models.alpha_factors import AlphaFactors
from src.backend.analysis import (
    calculate_rsi, calculate_macd, calculate_adx,
    detect_support_resistance,
    calculate_momentum_score, detect_volume_anomaly,
    calculate_ma_deviation, calculate_volatility_score,
    detect_wyckoff
)

logger = logging.getLogger(__name__)


class WeeklySubagent:
    """
    Weekly timeframe technical analysis subagent.

    Fetches 2 years of weekly OHLCV data and produces comprehensive
    technical analysis including indicators, alpha factors, and Wyckoff
    pattern detection.
    """

    TIMEFRAME = "1w"
    CANDLE_LIMIT = 104  # 2 years of weekly candles
    MIN_CANDLES_WARNING = 52  # Warn if less than 1 year

    def analyze(self, symbol: str) -> TASignal:
        """
        Analyze weekly timeframe for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")

        Returns:
            TASignal with populated wyckoff and alpha_factors fields

        Logs:
            Warning if fewer than 52 candles returned
        """
        # Step 1: Fetch OHLCV data
        client = get_ohlcv_client()
        candles = client.fetch_ohlcv(symbol, self.TIMEFRAME, limit=self.CANDLE_LIMIT)

        # Step 2: Check candle count and log warning if insufficient
        if len(candles) < self.MIN_CANDLES_WARNING:
            logger.warning(
                f"Insufficient history for {symbol} on {self.TIMEFRAME}: "
                f"got {len(candles)} candles (recommended {self.MIN_CANDLES_WARNING}+)"
            )

        # Step 3: Convert to DataFrame
        df = pd.DataFrame(candles)

        # Step 4: Calculate indicators
        indicators = self._calculate_indicators(df)

        # Step 5: Calculate alpha factors
        alpha_factors = self._calculate_alpha_factors(df)

        # Step 6: Detect Wyckoff patterns
        wyckoff = detect_wyckoff(df) if len(df) >= 100 else None
        if wyckoff is None and len(df) < 100:
            logger.info(f"Wyckoff detection skipped for {symbol}: only {len(df)} candles (need 100+)")

        # Step 7: Determine overall trend and confidence
        direction, confidence = self._determine_trend_confluence(
            indicators, wyckoff
        )

        # Step 8: Build TASignal
        return self._build_ta_signal(
            symbol, df, indicators, alpha_factors, wyckoff, direction, confidence
        )

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """Calculate all technical indicators."""
        return {
            'rsi': calculate_rsi(df),
            'macd': calculate_macd(df),
            'adx': calculate_adx(df),
            'sr_levels': detect_support_resistance(df),
        }

    def _calculate_alpha_factors(self, df: pd.DataFrame) -> Optional[AlphaFactors]:
        """Calculate alpha factors and build AlphaFactors model."""
        alpha_data = {}

        if momentum := calculate_momentum_score(df):
            from src.backend.models.alpha_factors import MomentumData
            alpha_data['momentum'] = MomentumData(**momentum)

        if volume := detect_volume_anomaly(df):
            from src.backend.models.alpha_factors import VolumeAnomalyData
            alpha_data['volume_anomaly'] = VolumeAnomalyData(**volume)

        if ma_dev := calculate_ma_deviation(df):
            from src.backend.models.alpha_factors import MADeviationData
            alpha_data['ma_deviation'] = MADeviationData(**ma_dev)

        if vol := calculate_volatility_score(df):
            from src.backend.models.alpha_factors import VolatilityData
            alpha_data['volatility'] = VolatilityData(**vol)

        return AlphaFactors(**alpha_data) if alpha_data else None

    def _determine_trend_confluence(
        self,
        indicators: dict,
        wyckoff: Optional[WyckoffAnalysis]
    ) -> tuple[str, int]:
        """
        Determine overall trend direction and confidence from indicator confluence.

        Returns:
            (direction, confidence) where direction in ["bullish", "bearish", "neutral"]
        """
        # Implementation per Pattern 4 above
        # (Claude's discretion on specific weights)
        pass

    def _build_ta_signal(
        self,
        symbol: str,
        df: pd.DataFrame,
        indicators: dict,
        alpha_factors: Optional[AlphaFactors],
        wyckoff: Optional[WyckoffAnalysis],
        direction: str,
        confidence: int
    ) -> TASignal:
        """Build TASignal from analysis outputs."""
        # Map indicators to nested Pydantic models
        # (Claude's discretion on exact mapping logic)
        pass
```

### Example 3: Test Structure with Mocked OHLCV

```python
# File: src/backend/tests/test_weekly_subagent.py
# Source: Existing test patterns + unittest.mock

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, Mock
from datetime import datetime, timedelta

from src.backend.agents.ta_ensemble.weekly_subagent import WeeklySubagent
from src.backend.models.ta_signal import TASignal


@pytest.fixture
def synthetic_weekly_ohlcv_104():
    """Generate 104 weekly candles (2 years) with realistic patterns."""
    np.random.seed(42)
    base_price = 50000.0
    timestamps = [
        int((datetime.now() - timedelta(weeks=104-i)).timestamp() * 1000)
        for i in range(104)
    ]

    prices = [base_price]
    for _ in range(103):
        change = np.random.normal(0.005, 0.03)  # 0.5% drift, 3% volatility
        prices.append(prices[-1] * (1 + change))

    data = []
    for i, timestamp in enumerate(timestamps):
        close = prices[i]
        volatility = close * 0.03
        high = close + abs(np.random.normal(0, volatility))
        low = close - abs(np.random.normal(0, volatility))
        open_price = low + np.random.random() * (high - low)
        volume = np.random.uniform(100000, 500000)

        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    return data  # Return list[dict] (OHLCVClient format)


@pytest.fixture
def synthetic_weekly_ohlcv_30():
    """Generate 30 weekly candles (insufficient history)."""
    # Similar to above but only 30 candles
    pass


def test_weekly_subagent_full_analysis(synthetic_weekly_ohlcv_104):
    """Test WeeklySubagent with full 2 years of data."""
    mock_client = Mock()
    mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_104

    with patch('src.backend.data.ohlcv_client.get_ohlcv_client', return_value=mock_client):
        subagent = WeeklySubagent()
        result = subagent.analyze("BTC/USDT")

        # Verify mock called correctly
        mock_client.fetch_ohlcv.assert_called_once_with("BTC/USDT", "1w", limit=104)

        # Verify TASignal structure
        assert isinstance(result, TASignal)
        assert result.symbol == "BTC/USDT"
        assert result.timeframe == "weekly"

        # Verify extended fields populated
        assert result.wyckoff is not None
        assert result.alpha_factors is not None

        # Verify confidence in valid range
        assert 0 <= result.overall.confidence <= 100


def test_weekly_subagent_insufficient_history_warning(synthetic_weekly_ohlcv_30, caplog):
    """Test warning logged when fewer than 52 candles returned."""
    mock_client = Mock()
    mock_client.fetch_ohlcv.return_value = synthetic_weekly_ohlcv_30

    with patch('src.backend.data.ohlcv_client.get_ohlcv_client', return_value=mock_client):
        subagent = WeeklySubagent()
        result = subagent.analyze("SOL/USDT")

        # Verify warning logged
        assert "Insufficient history" in caplog.text
        assert "30 candles" in caplog.text

        # Verify analysis still completes (proceeds with available data)
        assert isinstance(result, TASignal)
        assert result.symbol == "SOL/USDT"


def test_weekly_subagent_backward_compatibility():
    """Test that TASignal with None wyckoff/alpha_factors is valid."""
    # Create TASignal without new fields
    signal = TASignal(
        symbol="BTC",
        timeframe="weekly",
        trend={"direction": "bullish", "strength": "strong", "ema_alignment": "bullish"},
        momentum={"rsi": 65.0, "macd_bias": "bullish", "momentum_divergence": False},
        key_levels={"major_support": 60000.0, "major_resistance": 70000.0},
        patterns={"detected": [], "pattern_bias": "neutral"},
        overall={"bias": "bullish", "confidence": 75, "notes": "Test"}
        # wyckoff and alpha_factors omitted (default to None)
    )

    # Should validate successfully
    assert signal.wyckoff is None
    assert signal.alpha_factors is None

    # Should serialize without errors
    json_str = signal.model_dump_json()
    assert "wyckoff" in json_str  # Field present in JSON
    assert "null" in json_str or "None" not in json_str  # But value is null
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LLM-based TA subagents with prompts | Pure computational pipeline with Pydantic validation | Phase 11 (current) | Deterministic outputs, no API costs, faster execution, testable with mocks |
| Manual indicator calculations | pandas-ta library functions | Phase 8 | Pure Python (no TA-Lib), battle-tested, consistent with TradingView |
| Dict-based analysis outputs | Pydantic models with validation | Phases 8-10 | Type safety, automatic JSON schema, validation at boundaries |
| Separate helper functions | Analysis module exports | Phase 10 | Clean imports, __all__ for IDE autocomplete |

**Deprecated/outdated:**
- **BaseAgent with Claude calls for TA subagents:** Phase 11 shifts to pure computation. Old WeeklySubagent (90 lines, agent-based) will be replaced with new WeeklySubagent (computational pipeline).
- **Manual JSON parsing:** Pydantic models handle this automatically now.

## Open Questions

1. **Pattern Detection Implementation**
   - What we know: TASignal has PatternData.detected list[str] field
   - What's unclear: No pattern detection functions exist in analysis modules yet
   - Recommendation: For Phase 11, populate with empty list or placeholder "none". Pattern detection can be added in future phase without breaking TASignal structure.

2. **Timeframe Literal Mapping**
   - What we know: OHLCVClient uses "1w", TASignal expects "weekly"
   - What's unclear: Should WeeklySubagent do string mapping or extend Literal?
   - Recommendation: Hard-code timeframe="weekly" in WeeklySubagent._build_ta_signal(). This is subagent-specific constant, not derived from data.

3. **EMA Alignment Calculation**
   - What we know: TrendData requires ema_alignment field
   - What's unclear: No EMA calculation function in indicators.py (only RSI, MACD, ADX, etc.)
   - Recommendation: Calculate in WeeklySubagent using pandas EMA, or populate with derived value from other indicators. EMAs are simple: df['close'].ewm(span=20).mean()

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.0.0+ |
| Config file | None — pytest auto-discovers tests/ directory |
| Quick run command | `pytest src/backend/tests/test_weekly_subagent.py -v` |
| Full suite command | `pytest src/backend/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REQ-025 | TASignal accepts optional wyckoff field | unit | `pytest src/backend/tests/test_ta_signal.py::test_wyckoff_field_optional -x` | ❌ Wave 0 |
| REQ-026 | TASignal accepts optional alpha_factors field | unit | `pytest src/backend/tests/test_ta_signal.py::test_alpha_factors_field_optional -x` | ❌ Wave 0 |
| REQ-027 | Existing TASignal tests pass without new fields | unit | `pytest src/backend/tests/test_ta_signal.py -x` | ❌ Wave 0 |
| REQ-028 | WeeklySubagent.analyze() returns valid TASignal | unit | `pytest src/backend/tests/test_weekly_subagent.py::test_analyze_full_pipeline -x` | ❌ Wave 0 |
| REQ-031 | TASignal includes populated wyckoff and alpha_factors | unit | `pytest src/backend/tests/test_weekly_subagent.py::test_extended_fields_populated -x` | ❌ Wave 0 |
| REQ-032 | WeeklySubagent uses get_ohlcv_client() | unit | `pytest src/backend/tests/test_weekly_subagent.py::test_ohlcv_client_called -x` | ❌ Wave 0 |
| REQ-033 | Fetches 104 candles (2 years weekly) | unit | `pytest src/backend/tests/test_weekly_subagent.py::test_fetch_limit_104 -x` | ❌ Wave 0 |
| REQ-034 | Logs warning if < 52 candles | unit | `pytest src/backend/tests/test_weekly_subagent.py::test_insufficient_history_warning -x` | ❌ Wave 0 |
| REQ-046 | Unit tests with mocked OHLCV | unit | `pytest src/backend/tests/test_weekly_subagent.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest src/backend/tests/test_weekly_subagent.py -x` (fast subset)
- **Per wave merge:** `pytest src/backend/tests/ -v` (full suite, includes regression check)
- **Phase gate:** Full suite green + coverage report before /gsd:verify-work

### Wave 0 Gaps

- [ ] `src/backend/tests/test_ta_signal.py` — test backward compatibility (REQ-025, REQ-026, REQ-027)
- [ ] `src/backend/tests/test_weekly_subagent.py` — test full WeeklySubagent pipeline (REQ-028, REQ-031, REQ-032, REQ-033, REQ-034, REQ-046)
- [ ] Test fixtures: `synthetic_weekly_ohlcv_104`, `synthetic_weekly_ohlcv_30` for mocking
- [ ] Mock patches: `@patch('src.backend.data.ohlcv_client.get_ohlcv_client')`

## Sources

### Primary (HIGH confidence)

- **Existing codebase inspection:**
  - `src/backend/models/ta_signal.py` — Current TASignal structure, Pydantic patterns
  - `src/backend/models/wyckoff.py` — WyckoffAnalysis model (62 lines, complete)
  - `src/backend/models/alpha_factors.py` — AlphaFactors model (105 lines, complete)
  - `src/backend/analysis/indicators.py` — 8 indicator functions, all tested (280 lines)
  - `src/backend/analysis/alpha_factors.py` — 4 alpha factor functions (227 lines)
  - `src/backend/analysis/wyckoff.py` — detect_wyckoff() implementation (507 lines)
  - `src/backend/data/ohlcv_client.py` — OHLCVClient, get_ohlcv_client() singleton (213 lines)
  - `src/backend/tests/test_indicators.py` — 26 passing tests, fixture patterns
  - `src/backend/tests/test_wyckoff.py` — 20 passing tests, mock patterns
  - `.planning/STATE.md` — Accumulated decisions from Phases 8-10
  - `requirements.txt` — Confirmed pydantic>=2.5.0, pandas-ta>=0.3.14b

- **Pydantic documentation:**
  - Optional fields pattern: https://docs.pydantic.dev/latest/api/types/#pydantic.types.Optional
  - Nested models: https://docs.pydantic.dev/latest/concepts/models/#nested-models
  - Field() with default None: Standard Pydantic 2.x pattern

- **Python standard library:**
  - logging module: https://docs.python.org/3/library/logging.html
  - unittest.mock: https://docs.python.org/3/library/unittest.mock.html
  - typing.Optional: https://docs.python.org/3/library/typing.html#typing.Optional

### Secondary (MEDIUM confidence)

- **pytest documentation:**
  - Fixtures: https://docs.pytest.org/en/stable/fixture.html
  - Mocking with unittest.mock: https://docs.pytest.org/en/stable/how-to/monkeypatch.html
  - Verified against existing test files in project

### Tertiary (LOW confidence)

None — all findings verified with primary sources or existing code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use and requirements.txt, versions confirmed
- Architecture: HIGH - All components exist, patterns verified in codebase, user decisions explicit
- Pitfalls: MEDIUM-HIGH - Based on common Pydantic/pandas patterns and project test conventions, some inference on specific edge cases

**Research date:** 2026-02-27
**Valid until:** ~60 days (stable stack, no fast-moving dependencies)

**Notes:**
- Phase 11 is primarily integration work, not new algorithms
- Every component (models, analysis functions, client) already exists and is tested
- Main complexity is orchestration and ensuring backward compatibility
- Test isolation critical given 74+ existing tests that must continue passing
