# Architecture Research: TA Ensemble Integration

**Domain:** Multi-timeframe Technical Analysis for Crypto Trading Dashboard
**Researched:** 2026-02-27
**Confidence:** HIGH (existing codebase analysis) + MEDIUM (library ecosystem from training data)

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TA Ensemble Layer                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │WeeklySubagent│  │DailySubagent │  │ 4HSubagent   │  │ TAMentor   │  │
│  │(BaseAgent)   │  │(BaseAgent)   │  │(BaseAgent)   │  │(BaseAgent) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └─────┬──────┘  │
│         │                 │                 │                 │         │
│         └─────────────────┴─────────────────┴─────────────────┘         │
│                                     │                                    │
├─────────────────────────────────────┼────────────────────────────────────┤
│                       Analysis Layer│                                    │
├─────────────────────────────────────┼────────────────────────────────────┤
│  ┌────────────────┐  ┌──────────────▼───────┐  ┌───────────────────┐   │
│  │ indicators.py  │  │   wyckoff.py         │  │ alpha_factors.py  │   │
│  │                │  │                      │  │  (optional)       │   │
│  │ - RSI          │  │ - Phase detection    │  │ - Momentum score  │   │
│  │ - MACD         │  │ - Springs/Upthrusts  │  │ - Volume anomaly  │   │
│  │ - Bollinger    │  │ - SOS/SOW            │  │ - MA deviation    │   │
│  │ - ADX          │  │ - Volume analysis    │  │ - Volatility      │   │
│  │ - OBV          │  │                      │  │                   │   │
│  │ - VWAP         │  │                      │  │                   │   │
│  │ - ATR          │  │                      │  │                   │   │
│  │ - S/R          │  │                      │  │                   │   │
│  └────────┬───────┘  └──────────┬───────────┘  └─────────┬─────────┘   │
│           │                     │                         │             │
├───────────┴─────────────────────┴─────────────────────────┴─────────────┤
│                        Data Layer                                        │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐           │
│  │              OHLCVClient (singleton)                     │           │
│  │  - fetch_ohlcv(symbol, timeframe, limit)                │           │
│  │  - fetch_all_timeframes(symbol, limit)                  │           │
│  │  - Exponential backoff retry logic                      │           │
│  └────────────────────────┬─────────────────────────────────┘           │
│                           │                                             │
├───────────────────────────┼─────────────────────────────────────────────┤
│                           ▼                                             │
│                   Binance API (CCXT)                                    │
│                   [1w, 1d, 4h OHLCV]                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow: OHLCV → Analysis → TASignal → TAMentor

```
1. OHLCVClient.fetch_all_timeframes(symbol)
       ↓
   {"1w": [...], "1d": [...], "4h": [...]}
       ↓
   ┌───────────────────────────────────────┐
   │                                       │
   ▼                   ▼                   ▼
WeeklySubagent    DailySubagent    FourHourSubagent
   │                   │                   │
   ├─→ indicators.compute_all(candles)     │
   ├─→ wyckoff.detect_phase(candles)       │
   ├─→ alpha_factors.calculate(candles)    │
   │                   │                   │
   ▼                   ▼                   ▼
TASignal (w)      TASignal (d)      TASignal (4h)
   │                   │                   │
   └───────────────────┴───────────────────┘
                       ↓
                   TAMentor
                       │
                       ├─→ Detect confluence
                       ├─→ Detect conflicts
                       ├─→ Adjust confidence
                       ├─→ Apply hierarchy (W > D > 4H)
                       │
                       ▼
                TAMentorSignal
                (unified output)
```

## Component Responsibilities

| Component | Responsibility | Current State | New Work Needed |
|-----------|----------------|---------------|-----------------|
| **OHLCVClient** | Fetch OHLCV data from Binance, handle retries | ✓ Complete | None — integration only |
| **indicators.py** | Calculate technical indicators (RSI, MACD, BB, ADX, OBV, VWAP, ATR) | ✗ Missing | NEW MODULE |
| **wyckoff.py** | Detect Wyckoff phases, springs, upthrusts, SOS/SOW | ✗ Missing | NEW MODULE |
| **alpha_factors.py** | Compute momentum, volume anomaly, MA deviation, volatility scores | ✗ Missing | NEW MODULE (optional) |
| **WeeklySubagent** | Analyze weekly timeframe, integrate OHLCVClient + analysis modules | ✓ Shell exists | ADD analysis integration |
| **DailySubagent** | Analyze daily timeframe, integrate OHLCVClient + analysis modules | ✓ Shell exists | ADD analysis integration |
| **FourHourSubagent** | Analyze 4H timeframe, integrate OHLCVClient + analysis modules | ✓ Shell exists | ADD analysis integration |
| **TAMentor** | Synthesize 3 timeframes, detect conflicts, apply hierarchy | ✓ Shell exists | ADD conflict resolution |
| **TASignal** | Pydantic model for timeframe-specific output | ✓ Complete | EXTEND with wyckoff/alpha_factors |
| **TAMentorSignal** | Pydantic model for unified synthesis | ✓ Complete | None — ready to use |

## Recommended Project Structure

### NEW Components (to create)

```
src/backend/
├── analysis/                    # NEW FOLDER
│   ├── __init__.py             # Export public API
│   ├── indicators.py           # Technical indicators module
│   ├── wyckoff.py              # Wyckoff phase detection
│   └── alpha_factors.py        # Alpha factor calculations (optional)
├── agents/
│   ├── ta_ensemble/
│   │   ├── weekly_subagent.py  # MODIFY: Add OHLCVClient + analysis integration
│   │   ├── daily_subagent.py   # MODIFY: Add OHLCVClient + analysis integration
│   │   ├── fourhour_subagent.py# MODIFY: Add OHLCVClient + analysis integration
│   │   └── ta_mentor.py        # MODIFY: Add conflict resolution logic
├── models/
│   └── ta_signal.py            # EXTEND: Add wyckoff/alpha_factors fields
├── data/
│   └── ohlcv_client.py         # ✓ Already complete
└── tests/
    ├── test_indicators.py      # NEW: Unit tests for indicators
    ├── test_wyckoff.py         # NEW: Unit tests for Wyckoff
    ├── test_alpha_factors.py   # NEW: Unit tests for alpha (optional)
    └── test_ta_subagents.py    # MODIFY: Add integration tests with mocked OHLCV
```

### Structure Rationale

- **analysis/ folder:** Pure functions for calculations, no Claude/API calls. Reusable across agents. Easily testable with mock OHLCV data.
- **Separation of concerns:** Data (OHLCVClient) → Analysis (indicators/wyckoff) → Interpretation (Subagents with Claude) → Synthesis (TAMentor)
- **Subagent shells already exist:** Leverage existing BaseAgent pattern, add data fetching + analysis module calls
- **Pydantic models ready:** TASignal/TAMentorSignal provide type-safe validation

## Architectural Patterns

### Pattern 1: Analysis Module as Pure Functions

**What:** Technical analysis modules (indicators, wyckoff) are pure functions that take OHLCV candles and return calculated values. No side effects, no API calls, no state.

**When to use:** Always for technical calculations. Enables easy testing, caching, and reusability.

**Trade-offs:**
- Pro: Testable with mock data, no API costs
- Pro: Reusable across different agents or timeframes
- Pro: Can be cached or memoized easily
- Con: Requires passing candles explicitly (not implicit state)

**Example:**
```python
# src/backend/analysis/indicators.py

import pandas as pd
from typing import Optional

def compute_rsi(candles: list[dict], period: int = 14) -> Optional[float]:
    """Compute RSI from OHLCV candles.

    Args:
        candles: List of dicts with 'close' key
        period: RSI period (default 14)

    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(candles) < period + 1:
        return None

    df = pd.DataFrame(candles)
    closes = df['close']

    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi.iloc[-1])

def compute_all(candles: list[dict]) -> dict:
    """Compute all indicators for a given set of candles.

    Returns dict with keys: rsi, macd, bb_upper, bb_lower, adx, obv, vwap, atr
    """
    return {
        'rsi': compute_rsi(candles),
        'macd': compute_macd(candles),
        'bollinger': compute_bollinger_bands(candles),
        'adx': compute_adx(candles),
        'obv': compute_obv(candles),
        'vwap': compute_vwap(candles),
        'atr': compute_atr(candles),
    }
```

### Pattern 2: Subagent Orchestration (Data → Analysis → LLM)

**What:** Subagents fetch OHLCV data, compute indicators, then ask Claude to interpret the results. Claude doesn't compute — it analyzes pre-calculated values.

**When to use:** When you want LLM to provide contextual interpretation but not perform calculations (LLMs are bad at math).

**Trade-offs:**
- Pro: Offload computation to reliable, tested functions
- Pro: LLM focuses on interpretation (its strength)
- Pro: Reduces token usage (no raw OHLCV in prompts)
- Con: More code to maintain (analysis modules + agent logic)

**Example:**
```python
# src/backend/agents/ta_ensemble/weekly_subagent.py

from ...data.ohlcv_client import get_ohlcv_client
from ...analysis import indicators, wyckoff

class WeeklySubagent(BaseAgent):

    def analyze(self, symbol: str, context: dict) -> dict:
        # 1. Fetch data
        client = get_ohlcv_client()
        candles = client.fetch_ohlcv(f"{symbol}/USDT", "1w", limit=100)

        # 2. Compute indicators
        ind = indicators.compute_all(candles)
        wyck = wyckoff.detect_phase(candles)

        # 3. Build prompt with computed values
        prompt = f"""Analyze weekly timeframe for {symbol}.

CURRENT PRICE: {candles[-1]['close']}

TECHNICAL INDICATORS:
- RSI (14): {ind['rsi']:.2f}
- MACD: {ind['macd']}
- Bollinger Bands: {ind['bollinger']}
- ADX: {ind['adx']:.2f}

WYCKOFF ANALYSIS:
- Current Phase: {wyck['phase']}
- Signs of Strength/Weakness: {wyck['sos_sow']}
- Spring/Upthrust: {wyck['spring_upthrust']}

Provide weekly TA assessment as JSON..."""

        # 4. Call Claude for interpretation
        response = self._call_claude(prompt)
        return self._parse_json_response(response)
```

### Pattern 3: TAMentor Conflict Resolution with Hierarchy

**What:** TAMentor applies explicit rules for resolving timeframe conflicts. Higher timeframes (Weekly, Daily) override lower timeframes (4H). Conflicts penalize confidence.

**When to use:** Multi-timeframe synthesis where not all timeframes agree. Prevents paralysis by establishing clear hierarchy.

**Trade-offs:**
- Pro: Deterministic conflict resolution
- Pro: Respects market structure (HTF > LTF)
- Pro: Penalizes low-conviction signals
- Con: May miss valid counter-trend opportunities

**Example:**
```python
# src/backend/agents/ta_ensemble/ta_mentor.py

def synthesize(self, weekly: dict, daily: dict, fourhour: dict) -> dict:
    # Extract biases
    w_bias = weekly['overall']['bias']
    d_bias = daily['overall']['bias']
    fh_bias = fourhour['overall']['bias']

    # Detect conflicts
    conflicts = []
    conflict_penalty = 0

    # Rule 1: Weekly vs Daily conflict = NO SIGNAL (genuine uncertainty)
    if w_bias != d_bias and w_bias != "neutral" and d_bias != "neutral":
        conflicts.append({
            "type": "trend",
            "description": f"Weekly {w_bias} conflicts with Daily {d_bias}",
            "severity": "high"
        })
        conflict_penalty = 100  # Fatal — no signal

    # Rule 2: Weekly/Daily vs 4H conflict = penalize ~20 points
    elif (w_bias == d_bias) and (fh_bias != w_bias) and (fh_bias != "neutral"):
        conflicts.append({
            "type": "trend",
            "description": f"4H {fh_bias} conflicts with higher timeframes {w_bias}",
            "severity": "medium"
        })
        conflict_penalty = 20

    # Rule 3: Higher timeframe wins direction
    if w_bias != "neutral":
        unified_bias = w_bias
    elif d_bias != "neutral":
        unified_bias = d_bias
    else:
        unified_bias = fh_bias

    # Calculate confidence with penalty
    base_confidence = weekly['overall']['confidence']
    final_confidence = max(0, base_confidence - conflict_penalty)

    # Build unified signal
    return {
        "symbol": weekly['symbol'],
        "timeframe_alignment": {
            "weekly_bias": w_bias,
            "daily_bias": d_bias,
            "fourhour_bias": fh_bias,
            "alignment_score": calculate_alignment_score(w_bias, d_bias, fh_bias),
            "confluence": determine_confluence(w_bias, d_bias, fh_bias)
        },
        "conflicts_detected": conflicts,
        "unified_signal": {
            "bias": unified_bias if final_confidence > 0 else "neutral",
            "confidence": final_confidence,
            "recommended_action": "wait" if final_confidence == 0 else determine_action(unified_bias)
        }
    }
```

## Data Flow Details

### 1. OHLCV Data Fetching

```
Subagent.analyze(symbol, context)
    ↓
get_ohlcv_client().fetch_ohlcv(symbol + "/USDT", timeframe, limit=100)
    ↓
[retry_with_backoff decorator]
    ↓
ccxt.binance.fetch_ohlcv()
    ↓
Convert from array format to dict format
    ↓
Return: [{'timestamp': int, 'open': float, 'high': float, 'low': float, 'close': float, 'volume': float}, ...]
```

**Key decisions:**
- Use `get_ohlcv_client()` singleton to reuse CCXT exchange instance
- Fetch 100 candles by default (provides sufficient history for indicators)
- Weekly: 100 candles = ~2 years
- Daily: 100 candles = ~3 months
- 4H: 100 candles = ~16 days

### 2. Indicator Calculation

```
indicators.compute_all(candles)
    ↓
Convert candles to pandas DataFrame
    ↓
Compute each indicator using pandas vectorized operations
    ↓
Return: {'rsi': float, 'macd': dict, 'bollinger': dict, ...}
```

**Implementation approach:**
- Use pandas for vectorized calculations (fast, standard library)
- Return None for indicators with insufficient data
- Each indicator is independent function (testable in isolation)
- `compute_all()` convenience wrapper for subagents

### 3. Wyckoff Phase Detection

```
wyckoff.detect_phase(candles)
    ↓
Analyze volume-price relationship
    ↓
Identify accumulation/distribution phases (A-E)
    ↓
Detect springs, upthrusts, SOS, SOW
    ↓
Return: {'phase': str, 'spring_upthrust': str, 'sos_sow': str, 'confidence': int}
```

**Wyckoff detection logic:**
- Phase A: Stopping action (volume climax)
- Phase B: Building cause (range development)
- Phase C: Spring/Upthrust (test of supply/demand)
- Phase D: Signs of Strength/Weakness (trend emergence)
- Phase E: Markup/Markdown (trend continuation)

### 4. Subagent TASignal Generation

```
Subagent.analyze()
    ↓
1. Fetch OHLCV (OHLCVClient)
    ↓
2. Compute indicators (indicators.compute_all)
    ↓
3. Detect Wyckoff (wyckoff.detect_phase)
    ↓
4. Build prompt with computed values + current price
    ↓
5. Call Claude for interpretation (_call_claude)
    ↓
6. Parse JSON response to dict
    ↓
7. Validate with Pydantic TASignal.model_validate()
    ↓
Return: TASignal (Pydantic model)
```

### 5. TAMentor Synthesis

```
TAMentor.synthesize(weekly, daily, fourhour)
    ↓
1. Extract biases from each timeframe
    ↓
2. Detect conflicts (W vs D = fatal, HTF vs 4H = penalty)
    ↓
3. Apply hierarchy (W > D > 4H)
    ↓
4. Adjust confidence (base - conflict_penalty)
    ↓
5. Build synthesis prompt with conflict context
    ↓
6. Call Claude (uses MENTOR_MODEL, likely opus)
    ↓
7. Parse JSON response
    ↓
8. Validate with Pydantic TAMentorSignal.model_validate()
    ↓
Return: TAMentorSignal (Pydantic model)
```

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **OHLCVClient ↔ Subagents** | Direct function call via singleton | Subagents call `get_ohlcv_client().fetch_ohlcv()` |
| **Analysis modules ↔ Subagents** | Pure function calls | Subagents import `indicators`, `wyckoff` and call functions |
| **Subagents ↔ BaseAgent** | Inheritance | Subagents inherit `_call_claude()`, `_parse_json_response()` |
| **Subagents ↔ TAMentor** | Dict passing | TAMentor receives dicts from 3 subagents via `context` |
| **Claude API ↔ Agents** | Anthropic SDK via BaseAgent | All agents use `self._call_claude()` from BaseAgent |
| **Pydantic models ↔ Agents** | Validation layer | Agents return dicts, tests validate with `TASignal.model_validate()` |

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Binance API (via CCXT)** | Public API, no auth | Uses CCXT's built-in rate limiting + custom retry decorator |
| **Anthropic Claude API** | SDK via BaseAgent | Uses `settings.MODEL_NAME` for subagents, `settings.MENTOR_MODEL` for TAMentor |

### New Integration Required

**1. OHLCVClient into Subagents:**
```python
from ...data.ohlcv_client import get_ohlcv_client

def analyze(self, symbol: str, context: dict) -> dict:
    client = get_ohlcv_client()
    candles = client.fetch_ohlcv(f"{symbol}/USDT", "1w", limit=100)
    # ... rest of analysis
```

**2. Analysis modules into Subagents:**
```python
from ...analysis import indicators, wyckoff

def analyze(self, symbol: str, context: dict) -> dict:
    # After fetching candles
    ind = indicators.compute_all(candles)
    wyck = wyckoff.detect_phase(candles)
    # ... use in prompt
```

**3. Extended TASignal model:**
```python
# src/backend/models/ta_signal.py

class WyckoffData(BaseModel):
    """Wyckoff phase analysis."""
    phase: Literal["A", "B", "C", "D", "E", "unknown"]
    spring_upthrust: Optional[str] = None
    sos_sow: Optional[str] = None  # Signs of Strength/Weakness
    confidence: int = Field(..., ge=0, le=100)

class AlphaFactors(BaseModel):
    """Alpha factor scores."""
    momentum_score: Optional[float] = None
    volume_anomaly: Optional[float] = None
    ma_deviation: Optional[float] = None
    volatility_score: Optional[float] = None

class TASignal(BaseModel):
    # ... existing fields
    wyckoff: Optional[WyckoffData] = None  # NEW
    alpha_factors: Optional[AlphaFactors] = None  # NEW
```

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-100 requests/day** | Current architecture is perfect. OHLCVClient singleton, no caching needed. |
| **100-1000 requests/day** | Add caching layer for OHLCV data (Redis or in-memory with TTL). Cache key: `symbol:timeframe:timestamp_bucket`. |
| **1000+ requests/day** | Move indicator calculations to background jobs (Celery). Cache TASignal outputs. Rate limit user requests. |

### Scaling Priorities

**1. First bottleneck: Claude API costs**
- **What breaks:** High request volume = high Claude API costs
- **Fix:** Cache TASignal outputs for 4H (cache TTL = 4 hours), Daily (cache TTL = 24 hours), Weekly (cache TTL = 7 days)
- **Implementation:** Redis with TTL, cache key format: `ta_signal:{symbol}:{timeframe}:{date}`

**2. Second bottleneck: OHLCV API rate limits**
- **What breaks:** Binance rate limits (1200 requests/minute for public API)
- **Fix:** Already handled by `retry_with_backoff` decorator. For high volume, add caching layer (Redis).
- **Implementation:** Cache OHLCV responses with 5-minute TTL (OHLCV doesn't change retroactively)

**3. Third bottleneck: Indicator calculation CPU time**
- **What breaks:** pandas operations on large datasets (100+ candles) can take 50-100ms
- **Fix:** Pre-calculate indicators in background job, store in cache
- **Implementation:** Celery task that refreshes indicator cache every 4H/Daily/Weekly

## Anti-Patterns

### Anti-Pattern 1: LLM Computing Indicators

**What people do:** Pass raw OHLCV data to Claude and ask it to calculate RSI, MACD, etc.

**Why it's wrong:**
- LLMs are terrible at arithmetic (will hallucinate RSI values)
- Wastes tokens (OHLCV data is large)
- Non-deterministic (same input = different RSI each time)
- Expensive (compute + API costs)

**Do this instead:** Use analysis modules to compute indicators, pass computed values to Claude for interpretation.

```python
# BAD
prompt = f"Here's OHLCV data: {candles}. Calculate RSI and analyze."

# GOOD
rsi = indicators.compute_rsi(candles)
prompt = f"RSI is {rsi:.2f}. Analyze the momentum situation."
```

### Anti-Pattern 2: Fetching OHLCV Inside Analysis Modules

**What people do:** Put `get_ohlcv_client().fetch_ohlcv()` inside `indicators.py` functions.

**Why it's wrong:**
- Couples analysis logic to data fetching (hard to test)
- Can't reuse indicators with different data sources
- Makes mocking difficult in tests

**Do this instead:** Analysis modules are pure functions. Subagents fetch data, pass to analysis.

```python
# BAD (in indicators.py)
def compute_rsi(symbol: str, timeframe: str) -> float:
    candles = get_ohlcv_client().fetch_ohlcv(symbol, timeframe)
    # compute RSI

# GOOD (in indicators.py)
def compute_rsi(candles: list[dict], period: int = 14) -> float:
    # compute RSI from provided candles
```

### Anti-Pattern 3: Skipping Pydantic Validation

**What people do:** Return raw dicts from agents, skip `TASignal.model_validate()` validation.

**Why it's wrong:**
- No type safety (typos cause runtime errors)
- No validation (confidence > 100 goes undetected)
- No documentation (dict shape is implicit)

**Do this instead:** Validate all agent outputs with Pydantic models (at least in tests).

```python
# In tests
def test_weekly_subagent_output():
    result = agent.analyze("BTC", context)
    # This validates structure and types
    signal = TASignal.model_validate(result)
    assert 0 <= signal.overall.confidence <= 100
```

### Anti-Pattern 4: Stateful Analysis Modules

**What people do:** Store indicator values in class attributes, maintain state across calls.

**Why it's wrong:**
- Race conditions in concurrent environments
- Hard to test (need to reset state between tests)
- Confusing behavior (same function call = different results)

**Do this instead:** Pure functions that take candles and return values. No state.

```python
# BAD
class Indicators:
    def __init__(self):
        self.rsi_cache = {}

    def compute_rsi(self, candles):
        # Uses and updates self.rsi_cache

# GOOD
def compute_rsi(candles: list[dict], period: int = 14) -> float:
    # Pure function, no state
```

## Suggested Build Order (Dependency-Aware)

### Phase 1: Analysis Foundation (No Dependencies)

**Build these first — no external dependencies except pandas:**

1. **`src/backend/analysis/__init__.py`** — Empty package init
2. **`src/backend/analysis/indicators.py`** — Pure functions for RSI, MACD, BB, ADX, OBV, VWAP, ATR, S/R
3. **`tests/test_indicators.py`** — Unit tests with mock OHLCV data

**Why first:** Analysis modules have no dependencies on existing code. Can be built and tested in isolation. Provides foundation for subagents.

**Deliverable:** Working, tested indicator library ready to import.

---

### Phase 2: Wyckoff Detection (Depends on Phase 1 indicators)

**Build after indicators are complete:**

4. **`src/backend/analysis/wyckoff.py`** — Phase detection using indicator values + volume-price analysis
5. **`tests/test_wyckoff.py`** — Unit tests with mock OHLCV + expected phase outputs

**Why second:** Wyckoff detection may use indicator values (e.g., volume moving averages). Better to have indicators ready.

**Deliverable:** Wyckoff phase detection ready to import.

---

### Phase 3: Extended TASignal Model (Depends on Phase 2 for data shape)

**Build after analysis modules define their output structure:**

6. **`src/backend/models/ta_signal.py`** — Extend with `WyckoffData` and `AlphaFactors` nested models

**Why third:** Need to know what Wyckoff detection returns before defining Pydantic model shape.

**Deliverable:** Extended TASignal model with wyckoff/alpha_factors fields.

---

### Phase 4: Subagent Integration (Depends on Phases 1, 2, 3)

**Build after analysis modules + models are ready:**

7. **`src/backend/agents/ta_ensemble/weekly_subagent.py`** — Integrate OHLCVClient + indicators + wyckoff
8. **`src/backend/agents/ta_ensemble/daily_subagent.py`** — Same integration pattern
9. **`src/backend/agents/ta_ensemble/fourhour_subagent.py`** — Same integration pattern
10. **`tests/test_ta_subagents.py`** — Update with mocked OHLCVClient, verify TASignal output

**Why fourth:** Requires completed analysis modules, OHLCVClient (already exists), and extended TASignal model.

**Deliverable:** Three working subagents producing extended TASignal outputs.

---

### Phase 5: TAMentor Synthesis (Depends on Phase 4)

**Build after subagents produce valid TASignal outputs:**

11. **`src/backend/agents/ta_ensemble/ta_mentor.py`** — Add conflict resolution logic, hierarchy rules
12. **`tests/test_ta_mentor.py`** — Update with mocked subagent outputs, verify conflict detection

**Why fifth:** Requires working subagents to synthesize. Can test with mocked subagent outputs.

**Deliverable:** TAMentor with conflict resolution, ready to synthesize real signals.

---

### Phase 6: Alpha Factors (Optional — Can Be Parallel or Deferred)

**Build in parallel with Phase 4 or defer to v0.4:**

13. **`src/backend/analysis/alpha_factors.py`** — Momentum score, volume anomaly, MA deviation, volatility
14. **`tests/test_alpha_factors.py`** — Unit tests

**Why optional:** Not critical for MVP. Can be added later without breaking existing code.

**Deliverable:** Alpha factor calculations available to enhance TASignal.

---

## Dependency Graph

```
Phase 1: indicators.py
           ↓
Phase 2: wyckoff.py (uses indicators)
           ↓
Phase 3: Extended TASignal model (defines wyckoff/alpha schema)
           ↓
Phase 4: Subagents (use indicators + wyckoff + OHLCVClient → TASignal)
           ↓
Phase 5: TAMentor (synthesizes subagent TASignals → TAMentorSignal)
           ↓
Phase 6: alpha_factors.py (optional enhancement)
```

**Critical path:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5

**Parallel work:** Phase 6 (alpha factors) can be built anytime after Phase 1.

---

## Key Architectural Decisions

### 1. Pure Functions for Analysis (Not Classes)

**Decision:** `indicators.py` and `wyckoff.py` expose pure functions, not classes.

**Rationale:**
- No state = easier to test
- Functional style common in data analysis (pandas, numpy)
- Avoids boilerplate (no `__init__`, no `self`)

**Example:**
```python
# indicators.py
def compute_rsi(candles: list[dict], period: int = 14) -> Optional[float]:
    # Pure function
```

### 2. Subagents Call Claude for Interpretation, Not Calculation

**Decision:** Indicators/Wyckoff are computed in Python. Claude receives computed values and interprets them.

**Rationale:**
- LLMs bad at math
- Deterministic calculations
- Lower token usage
- Cacheable computation

**Prompt format:**
```
TECHNICAL INDICATORS:
- RSI (14): 65.3
- MACD: {'signal': 'bullish', 'histogram': 120.5}

Interpret these indicators in context of weekly trend...
```

### 3. TASignal Extension vs New Model

**Decision:** Extend existing `TASignal` model with optional `wyckoff` and `alpha_factors` fields.

**Rationale:**
- Backward compatible (existing tests still pass)
- Single source of truth for TA output
- Optional fields allow gradual rollout

**Implementation:**
```python
class TASignal(BaseModel):
    # Existing fields
    symbol: str
    timeframe: Literal["weekly", "daily", "4h"]
    trend: TrendData
    # ... etc

    # NEW optional fields
    wyckoff: Optional[WyckoffData] = None
    alpha_factors: Optional[AlphaFactors] = None
```

### 4. TAMentor Conflict Resolution Rules

**Decision:** Explicit, deterministic rules for conflict resolution.

**Rules:**
1. Weekly vs Daily conflict → NO SIGNAL (confidence = 0)
2. HTF vs 4H conflict → Penalize -20 confidence
3. Higher timeframe wins direction (W > D > 4H)

**Rationale:**
- Predictable behavior
- Respects market structure
- Prevents low-conviction signals

---

## Testing Strategy

### Unit Tests (Isolated Components)

**indicators.py:**
```python
# tests/test_indicators.py
def test_compute_rsi_with_mock_candles():
    candles = [
        {'close': 100}, {'close': 102}, {'close': 101}, # ...
    ]
    rsi = indicators.compute_rsi(candles, period=14)
    assert 0 <= rsi <= 100
    assert isinstance(rsi, float)
```

**wyckoff.py:**
```python
# tests/test_wyckoff.py
def test_detect_phase_accumulation():
    # Mock OHLCV with accumulation pattern
    candles = create_accumulation_pattern()
    result = wyckoff.detect_phase(candles)
    assert result['phase'] in ['A', 'B', 'C', 'D', 'E']
```

### Integration Tests (Subagents with Mocked OHLCV)

**Subagents:**
```python
# tests/test_ta_subagents.py
@patch('src.backend.data.ohlcv_client.OHLCVClient.fetch_ohlcv')
def test_weekly_subagent_with_mocked_data(mock_fetch):
    mock_fetch.return_value = create_mock_weekly_candles()

    agent = WeeklySubagent()
    result = agent.analyze("BTC", {})

    # Validate Pydantic model
    signal = TASignal.model_validate(result)
    assert signal.timeframe == "weekly"
    assert signal.wyckoff is not None
```

**TAMentor:**
```python
# tests/test_ta_mentor.py
def test_conflict_detection():
    weekly = {'overall': {'bias': 'bullish', 'confidence': 80}}
    daily = {'overall': {'bias': 'bearish', 'confidence': 75}}
    fourhour = {'overall': {'bias': 'neutral', 'confidence': 50}}

    mentor = TAMentor()
    result = mentor.synthesize(weekly, daily, fourhour)

    # Weekly vs Daily conflict → NO SIGNAL
    signal = TAMentorSignal.model_validate(result)
    assert len(signal.conflicts_detected) > 0
    assert signal.unified_signal.confidence == 0  # Fatal conflict
```

---

## Sources

**Existing Codebase Analysis (HIGH CONFIDENCE):**
- `/Users/johnny_main/Developer/projects/titan-terminal/src/backend/agents/base.py` — BaseAgent pattern
- `/Users/johnny_main/Developer/projects/titan-terminal/src/backend/data/ohlcv_client.py` — OHLCVClient implementation
- `/Users/johnny_main/Developer/projects/titan-terminal/src/backend/models/ta_signal.py` — TASignal model structure
- `/Users/johnny_main/Developer/projects/titan-terminal/src/backend/models/ta_mentor_signal.py` — TAMentorSignal model structure
- `/Users/johnny_main/Developer/projects/titan-terminal/src/backend/agents/ta_ensemble/` — Existing subagent shells
- `/Users/johnny_main/Developer/projects/titan-terminal/.planning/PROJECT.md` — Project context and requirements

**Technical Analysis Implementation Patterns (MEDIUM CONFIDENCE — Training Data):**
- pandas library for vectorized indicator calculations (industry standard)
- Pure function approach for analysis modules (common pattern in data science)
- Separation of calculation vs interpretation (established ML/AI pattern)
- Multi-timeframe hierarchy (W > D > 4H) (standard in technical analysis)
- Wyckoff method phases A-E (established trading methodology)

**Library Ecosystem (LOW CONFIDENCE — Training Data, No Current Verification):**
- pandas-ta: Popular TA library, may have changed since training cutoff
- TA-Lib: C library with Python bindings, stable but complex setup
- NumPy/pandas: Core dependencies, well-established

**NOTE:** Could not verify current state of TA libraries due to search tool restrictions. Recommendations based on training data knowledge of pandas-ta and TA-Lib. Suggest manual verification of library versions/APIs during implementation.

---

**Architecture research for: Titan Terminal TA Ensemble Integration**
**Researched: 2026-02-27**
