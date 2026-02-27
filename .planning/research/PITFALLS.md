# Domain Pitfalls: Technical Analysis Implementation

**Domain:** Technical Indicator Computation & Wyckoff Detection with LLM Synthesis
**Researched:** 2026-02-27
**Confidence:** MEDIUM (training data + codebase analysis, no external verification)

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: TA-Lib Installation Hell
**What goes wrong:** Choose TA-Lib, spend days fighting platform-specific C library compilation errors, blocks development

**Why it happens:** TA-Lib appears in many tutorials and seems like the "standard" - but requires compiling C code which fails on macOS ARM, Windows without Visual Studio, Linux without build tools

**Consequences:**
- Days lost to installation debugging
- Different behavior across dev machines
- CI/CD pipeline failures
- Blocked PRs waiting for dependencies

**Prevention:**
- Use pandas-ta (pure Python, no C dependencies)
- Zero compilation needed, pip install works everywhere
- Identical indicator outputs to TA-Lib

**Detection:** If you see "error: command 'gcc' failed" or "Microsoft Visual C++ required" during install → wrong library

---

### Pitfall 2: Look-Ahead Bias in Indicators
**What goes wrong:** Use future data in indicator calculations, creating "magical" backtest results that fail in production

**Why it happens:** pandas default behavior uses entire DataFrame, including future rows, when calculating indicators without proper iloc slicing

**Consequences:**
- Backtest shows 90% win rate
- Production shows 40% win rate
- False confidence in strategy
- Lost capital from bad signals

**Prevention:**
```python
# WRONG: Uses future data
df['rsi'] = df.ta.rsi(length=14)
signal = df[df['close'] > df['rsi'].shift(1)]  # shift() creates look-ahead

# CORRECT: Only use past data
for i in range(14, len(df)):
    current_df = df.iloc[:i+1]  # Only data up to current candle
    rsi_value = current_df.ta.rsi(length=14).iloc[-1]
```

**Better approach:** Calculate indicators on entire DataFrame ONCE, then use `.iloc[-1]` for latest value in production (no look-ahead since you only have past data in real-time)

**Detection:** If backtest results are "too good" → check for look-ahead bias

---

### Pitfall 3: Insufficient Data for Indicator Warmup
**What goes wrong:** Calculate MACD(12,26,9) with only 30 candles → first 26 values are NaN, only 4 valid signals

**Why it happens:** Indicators need "warmup period" - MACD needs 26+ candles, Bollinger Bands need 20+, but code doesn't fetch enough history

**Consequences:**
- NaN errors crash agents
- Missing signals on first runs
- Inconsistent behavior (works after running a while, fails on fresh start)

**Prevention:**
```python
# Calculate required lookback
lookback_needed = max(
    200,  # 200 MA is longest standard indicator
    26 + 9,  # MACD slow + signal
    20,  # Bollinger Bands
    14  # RSI/ADX
)

# Fetch extra for safety
candles = client.fetch_ohlcv(symbol, timeframe, limit=lookback_needed + 50)
```

**Rule of thumb:** Fetch 250+ candles for any indicator calculations (covers 200 MA + buffer)

**Detection:** Check for NaN in indicator columns: `df.isna().sum()` before using values

---

### Pitfall 4: Timezone Inconsistency in OHLCV Data
**What goes wrong:** CCXT returns UTC timestamps, but pandas interprets as local time → indicators calculated on wrong candle boundaries

**Why it happens:** CCXT timestamps are Unix milliseconds (UTC), pandas `to_datetime()` defaults to local timezone

**Consequences:**
- 4H candle closes don't align with exchange
- Indicator signals delayed by hours
- Backtests don't match live behavior

**Prevention:**
```python
# WRONG: Local timezone
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# CORRECT: Explicit UTC
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
df.set_index('timestamp', inplace=True)
```

**Detection:** Compare DataFrame index timezone with exchange data - should both be UTC

---

### Pitfall 5: Wyckoff False Positives
**What goes wrong:** Detect "spring" pattern on every small dip, flood system with false signals

**Why it happens:** Wyckoff patterns are subjective - without proper thresholds, every price action matches some phase

**Consequences:**
- 50+ "spring" detections per week
- Signal fatigue (traders ignore)
- Execution costs from overtrading
- Missed real opportunities (lost in noise)

**Prevention:**
- Require MULTIPLE confirmations (volume + price + trend context)
- Use strict thresholds: volume >2x MA, price move >1.5 ATR, support test within 2%
- Limit detections: Max 1 phase per symbol per week on weekly timeframe
- Add confidence scoring: Low confidence if only 1-2 criteria met

**Detection:** If Wyckoff module returns >5 detections per day → thresholds too loose

---

### Pitfall 6: Multi-Timeframe Alignment Errors

**What goes wrong:**
Weekly candle closes Sunday 23:59 UTC, daily closes every day 23:59 UTC, 4H closes every 4 hours. Fetching "current" data from all three timeframes at Tuesday 10:00 UTC produces misaligned analysis: weekly shows last week's close, daily shows yesterday's close, 4H shows 2 hours ago. TAMentor synthesizes analysis from different time windows, treating them as concurrent.

**Why it happens:**
OHLCV APIs return closed candles only. The current (incomplete) candle isn't included unless explicitly requested. Developers assume "latest data" from all timeframes represents "now", but latest weekly candle may be up to 7 days old.

**Consequences:**
- TAMentor sees "weekly bullish, daily bearish, 4H bullish" frequently (misaligned timeframes)
- Weekly bias changes on Monday but daily/4H don't reflect it
- Backtesting shows different results depending on what day of week analysis runs
- "Current" analysis references price levels not touched in days

**Prevention:**
```python
# Document staleness explicitly
def fetch_aligned_data(symbol: str) -> dict:
    """Fetch multi-timeframe data with staleness awareness.

    NOTE: Weekly data may be up to 7 days stale.
          Daily data may be up to 24 hours stale.
          4H data may be up to 4 hours stale.
    """
    data = client.fetch_all_timeframes(symbol)

    # Add metadata about data freshness
    now = datetime.now(timezone.utc)
    data['metadata'] = {
        'fetched_at': now,
        'weekly_staleness_hours': calculate_staleness(data['1w'][-1]['timestamp'], now),
        'daily_staleness_hours': calculate_staleness(data['1d'][-1]['timestamp'], now),
        '4h_staleness_hours': calculate_staleness(data['4h'][-1]['timestamp'], now)
    }
    return data
```

**Detection:** Test on different days of week - if weekly analysis changes significantly on Monday, staleness not handled

---

### Pitfall 7: LLM JSON Parsing Brittleness

**What goes wrong:**
TAMentor (Claude Opus) prompted to return JSON sometimes wraps it in markdown:
```markdown
```json
{"bias": "bullish"}
```
```
Or includes thinking before JSON:
```
Based on the data, I believe we're in a bullish setup.

{"bias": "bullish", "confidence": 75}
```

Naive `json.loads()` fails on these responses.

**Why it happens:**
LLMs are trained to be helpful and conversational. Even with "output ONLY valid JSON" in prompt, occasional markdown wrapping or explanatory text appears. Parsing code expects perfect JSON, fails on minor deviations.

**Consequences:**
- JSON parsing failures in 5-10% of LLM calls
- Tests pass with mocked JSON responses but fail with real LLM calls
- Intermittent errors that are hard to reproduce
- Production failures during high-volume periods

**Prevention:**
```python
import json
import re

def extract_json_from_llm_response(response: str) -> dict:
    """Extract JSON from LLM response, handling common formats."""
    # Remove markdown code blocks
    cleaned = re.sub(r'```json\s*|\s*```', '', response)

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try finding JSON object in text
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback: raise with helpful error
    raise ValueError(
        f"Could not extract valid JSON from LLM response.\n"
        f"Response preview: {response[:200]}..."
    )
```

**Detection:** Run 50+ real LLM calls, track parsing success rate - should be 100% with robust extraction

---

### Pitfall 8: Missing OHLCV Data Gaps Not Handled

**What goes wrong:**
Exchange downtime, API rate limits, or delisting creates missing candles in OHLCV data. Requesting 100 daily candles returns 97 candles with 3 gaps. Indicator computation assumes continuous data, computes RSI across gap, produces misleading values.

**Why it happens:**
CCXT returns whatever data exchange provides. If exchange had downtime or symbol wasn't trading, gaps exist. Developers assume `fetch_ohlcv(limit=100)` returns exactly 100 consecutive candles.

**Consequences:**
- Different candle counts for same time period across runs
- Sudden indicator jumps at specific dates (gap existed, indicators recomputed)
- S/R levels don't align with chart visual inspection (gaps shifted data)
- Tests with synthetic continuous data pass, live data fails

**Prevention:**
```python
def detect_gaps(candles: list[dict], timeframe: str) -> list[dict]:
    """Detect missing candles in OHLCV data.

    Returns list of gap locations: [{"index": 45, "missing_candles": 2}, ...]
    """
    timeframe_ms = parse_timeframe(timeframe)  # "1d" -> 86400000 ms
    gaps = []

    for i in range(1, len(candles)):
        expected_time = candles[i-1]['timestamp'] + timeframe_ms
        actual_time = candles[i]['timestamp']

        if actual_time > expected_time + timeframe_ms/2:  # Allow small drift
            missing = (actual_time - expected_time) // timeframe_ms
            gaps.append({
                "index": i,
                "missing_candles": int(missing),
                "gap_start": expected_time,
                "gap_end": actual_time
            })

    return gaps

# In analysis code
gaps = detect_gaps(candles, "1d")
if gaps:
    logger.warning(f"OHLCV data has {len(gaps)} gaps: {gaps}")
    # Option 1: Fill gaps with forward-fill or interpolation
    # Option 2: Reject analysis (insufficient data)
    # Option 3: Note in output that data quality is poor
```

**Detection:** Test with synthetic gapped data (remove candles 45-47), verify detection and handling

---

### Pitfall 9: Confidence Score Calibration Drift

**What goes wrong:**
Weekly subagent outputs confidence: 85. Daily outputs confidence: 40. 4H outputs confidence: 90. Over time, WeeklySubagent averages 80+ confidence (overconfident), DailySubagent averages 45 confidence (underconfident). TAMentor's synthesis is biased by miscalibrated inputs.

**Why it happens:**
Each subagent uses LLM to generate confidence scores. LLMs don't have calibrated probability outputs — "confidence: 85" is a guess about how confident to sound, not a statistical likelihood. Different system prompts produce different confidence distributions.

**Consequences:**
- Confidence scores cluster around 70-80 (LLM defaults to "sounds confident")
- No correlation between confidence and actual signal accuracy in backtesting
- WeeklySubagent always more confident than DailySubagent regardless of setup clarity
- High-confidence signals aren't actually more accurate than low-confidence signals

**Prevention:**
Track confidence vs actual outcomes, implement post-hoc calibration:

```python
class ConfidenceCalibrator:
    """Calibrate confidence scores against historical accuracy."""

    def __init__(self):
        self.history = []  # [(predicted_confidence, actual_outcome, agent), ...]

    def calibrate(self, confidence: int, agent: str) -> int:
        """Return calibrated confidence based on agent's historical accuracy."""
        if not self.history:
            return confidence  # No history yet

        # Filter to this agent's history
        agent_history = [(c, o) for c, o, a in self.history if a == agent]

        # Find historical accuracy in this confidence bucket
        bucket = (confidence // 20) * 20  # 0, 20, 40, 60, 80
        bucket_history = [(c, o) for c, o in agent_history if bucket <= c < bucket + 20]

        if len(bucket_history) < 10:
            return confidence  # Insufficient data

        # Calculate actual accuracy in this bucket
        actual_accuracy = sum(o for _, o in bucket_history) / len(bucket_history)

        # Calibrated confidence = historical accuracy converted to 0-100 scale
        return int(actual_accuracy * 100)

    def record_outcome(self, confidence: int, correct: bool, agent: str):
        """Record actual outcome for future calibration."""
        self.history.append((confidence, 1 if correct else 0, agent))
```

**Detection:** Compare predicted confidence to actual accuracy in backtests - should correlate strongly

---

### Pitfall 10: Conflicting Signals Suppressed as Neutral

**What goes wrong:**
Weekly: Bullish bias, confidence 75. Daily: Bearish bias, confidence 70. TAMentor conflict resolution: "Weekly/Daily conflict → NO SIGNAL, output neutral". System outputs "neutral" for 40% of symbols because conflicts are common. Dashboard shows "neutral" majority of time.

**Why it happens:**
PROJECT.md states: "Weekly vs Daily conflict = no signal (genuine uncertainty)". This is conservative but loses information. User doesn't see that higher timeframe is bullish while lower timeframe pulled back — valuable context for entries.

**Consequences:**
- 40%+ of analyses output "neutral" (conflicts suppressed)
- Users complain dashboard "always says neutral"
- Backtesting shows better results when conflicts are traded (with caution) vs ignored
- Missed opportunities when weekly bullish + daily bearish → actual pullback entry

**Prevention:**
Surface conflicts, don't suppress them:

```python
# Bad: Conflict → Neutral (information loss)
if weekly_bias == "bullish" and daily_bias == "bearish":
    return {"bias": "neutral", "confidence": 0, "notes": "Conflicting timeframes"}

# Good: Conflict → Qualified bias with warning
if weekly_bias == "bullish" and daily_bias == "bearish":
    return {
        "bias": "bullish",  # Higher timeframe wins
        "confidence": 55,  # Reduced from 75 due to conflict
        "conflict": True,
        "conflict_details": {
            "weekly": "bullish 75",
            "daily": "bearish 70",
            "4h": "bearish 65"
        },
        "interpretation": "Weekly bullish structure with daily pullback — potential better entry",
        "notes": "CONFLICT: Weekly trend up, daily counter-trend. Watch for daily reversal."
    }
```

**Detection:** Test with known conflicts, verify qualified signal output not neutral

## Moderate Pitfalls

### Pitfall 11: DataFrame Mutation Side Effects
**What goes wrong:** pandas-ta's `append=True` modifies DataFrame in-place, causing unexpected columns in later code

**Why it happens:** `df.ta.rsi(append=True)` adds 'RSI_14' column to df permanently

**Prevention:**
```python
# Make explicit copy for indicators
df_indicators = df.copy()
df_indicators.ta.rsi(append=True)
# Original df unchanged
```

**Detection:** Check `df.columns` before/after indicator calls - should be same if not expecting mutations

---

### Pitfall 12: VWAP Reset Timing
**What goes wrong:** VWAP calculated across all historical data instead of resetting daily/weekly

**Why it happens:** pandas-ta VWAP doesn't auto-reset based on timeframe

**Prevention:**
- For intraday (4H): Reset VWAP at session start (00:00 UTC)
- For daily+: Use standard VWAP (no reset needed)
- Implement custom VWAP with groupby if needed

**Detection:** VWAP value should be close to current price - if 50% different, likely wrong timeframe scope

---

### Pitfall 13: Support/Resistance Over-Fitting
**What goes wrong:** scipy.find_peaks detects 20 S/R levels, none significant

**Why it happens:** Prominence parameter too low, every small wiggle is a "peak"

**Prevention:**
```python
# Dynamic prominence based on volatility
atr = df['ATR_14'].iloc[-1]
prominence = atr * 1.5  # Peaks must be 1.5 ATR apart

peaks, _ = find_peaks(df['close'].values, prominence=prominence)
```

**Detection:** If finding >5 S/R levels per 100 candles → prominence too low

---

### Pitfall 14: Indicator Column Name Confusion
**What goes wrong:** Code expects 'RSI' but pandas-ta creates 'RSI_14', KeyError crashes agent

**Why it happens:** pandas-ta adds period to column name (RSI_14, SMA_50, MACD_12_26_9)

**Prevention:**
```python
# Document expected column names
INDICATOR_COLUMNS = {
    'rsi': 'RSI_14',
    'macd': 'MACD_12_26_9',
    'macd_signal': 'MACDs_12_26_9',
    'macd_hist': 'MACDh_12_26_9',
    'bb_upper': 'BBU_20_2.0',
    'bb_middle': 'BBM_20_2.0',
    'bb_lower': 'BBL_20_2.0',
}

# Access with constants
rsi_value = df[INDICATOR_COLUMNS['rsi']].iloc[-1]
```

**Detection:** KeyError when accessing indicator → check actual column names with `df.columns.tolist()`

---

### Pitfall 15: Division by Zero in Alpha Factors
**What goes wrong:** Calculate `(close - ma) / ma` when MA is 0 or very small, get inf/NaN

**Why it happens:** Edge cases with low-priced assets or errors in MA calculation

**Prevention:**
```python
# Safe division with minimum threshold
def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if abs(denominator) < 1e-10:
        return default
    return numerator / denominator

ma_deviation = safe_divide(close - ma, ma, default=0.0)
```

**Detection:** Check for inf/NaN in alpha factors: `math.isinf(value)` or `math.isnan(value)`

---

### Pitfall 16: Volume Normalization Missing

**What goes wrong:**
Wyckoff relies on "volume climax" and "low volume tests". But absolute volume varies drastically: BTC averages 20B daily volume, SOL averages 2B. Comparing raw volume values across symbols produces false signals.

**Why it happens:**
Developers treat volume as absolute metric, but volume is relative to symbol liquidity, time period, and recent history.

**Consequences:**
- Wyckoff "volume climax" detected on every symbol simultaneously (market-wide surge)
- SOL shows more "low volume tests" than BTC (absolute volume lower)
- Historical Wyckoff signals stop working after 2024 (volume regime shifted)

**Prevention:**
```python
def normalize_volume(candles: list[dict], lookback: int = 30) -> list[dict]:
    """Normalize volume relative to recent average.

    Returns volume as ratio to 30-day average:
    - 1.0 = average volume
    - 2.0 = 2x average (high volume)
    - 0.3 = 30% of average (low volume)
    """
    volumes = [c['volume'] for c in candles]

    normalized = []
    for i, candle in enumerate(candles):
        if i < lookback:
            avg = sum(volumes[:i+1]) / (i + 1)
        else:
            avg = sum(volumes[i-lookback:i]) / lookback

        normalized.append({
            **candle,
            'volume_normalized': candle['volume'] / avg if avg > 0 else 1.0,
            'volume_raw': candle['volume']
        })

    return normalized
```

**Detection:** Test BTC vs SOL, verify both detect "high volume" at appropriate levels

## Minor Pitfalls

### Pitfall 17: OBV Initialization
**What goes wrong:** OBV starts from 0, early values meaningless

**Why it happens:** OBV is cumulative, needs historical baseline

**Prevention:** Only use OBV trend (increasing/decreasing), not absolute values. Compare OBV[t] > OBV[t-10], not OBV absolute magnitude

**Detection:** If OBV absolute values used in decisions → wrong approach

---

### Pitfall 18: ATR Percentage vs Absolute
**What goes wrong:** Use ATR absolute value (e.g., 500 for BTC at $50k) without context

**Why it happens:** ATR is in price units, not percentage - meaningless across different price levels

**Prevention:**
```python
# Convert ATR to percentage of price
atr_pct = (atr / close) * 100  # e.g., 2.5% volatility
```

**Detection:** If comparing ATR across symbols/timeframes without normalization → wrong

---

### Pitfall 19: Pandas-ta Installation Typo
**What goes wrong:** `pip install ta` instead of `pip install pandas-ta` → wrong package

**Why it happens:** Similar names, "ta" is a different (less maintained) library

**Prevention:** Always use full name: `pip install pandas-ta`

**Detection:** If `import pandas_ta` fails after installing "ta" → wrong package

---

### Pitfall 20: RSI Overbought/Oversold Misuse
**What goes wrong:** Sell at RSI 70, buy at RSI 30 → lose money in strong trends

**Why it happens:** "Overbought" doesn't mean "will fall" in uptrends

**Prevention:** Use RSI with trend filter - RSI 70+ in uptrend = strength, not reversal signal

**Detection:** If RSI-only strategy has <50% win rate → missing trend context

---

### Pitfall 21: Indicator Repainting on Incomplete Candles

**What goes wrong:**
Computing indicators on the current (incomplete) candle produces values that change as the candle develops. 4H candle at +1 hour shows RSI 45, same candle at +3 hours shows RSI 62. Analysis based on incomplete data generates signals that "disappear" when candle closes.

**Why it happens:**
Real-time systems need to show current state, so developers include the incomplete candle. Indicators computed on incomplete data are valid but will change.

**Consequences:**
- Backtesting results differ from paper trading (backtesting uses closed candles, live uses incomplete)
- Signals that "trigger" but then "un-trigger" within same timeframe
- Higher signal accuracy in backtesting (80%) vs live trading (50%)

**Prevention:**
```python
def analyze_closed_candles(data: list[dict]) -> dict:
    """Analysis for decision-making - closed candles only."""
    closed_candles = [c for c in data if is_closed(c)]
    return compute_indicators(closed_candles)

def monitor_current_candle(data: list[dict]) -> dict:
    """Live monitoring - informational only, don't generate signals."""
    all_candles = data  # Including incomplete
    current_state = compute_indicators(all_candles)
    return {
        **current_state,
        "warning": "Includes incomplete candle - values will change"
    }
```

For TA Ensemble: **Generate signals only from closed candles.**

**Detection:** Re-run analysis 1 hour later with same data - if results change significantly, repainting issue

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoded warmup periods (50 candles) | Simple, works for current indicators | Breaks when adding EMA(200) or custom indicators | MVP only - replace with calculated warmup in v1.0 |
| Computing indicators in subagents | No shared module, faster to implement | Code duplication, inconsistent calculations | Never - shared indicators module required |
| Using last candle timestamp as "current time" | Avoids timezone complexity | Produces stale analysis (up to 7 days for weekly) | Testing only - production needs staleness awareness |
| Storing raw LLM responses without parsing validation | Faster development, trust LLM output | Brittle when LLM format changes | Never - parsing must be robust from start |
| Single global confidence threshold (>60) | Simple filtering logic | Ignores calibration drift, subagent biases | Until Phase 5 when calibration data exists |
| Forward-filling missing OHLCV data | Allows analysis to continue despite gaps | Produces misleading indicators across large gaps | Acceptable for 1-2 candle gaps only |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OHLCVClient → Subagents | Fetching exactly the display window (100 candles) | Fetch display + warmup buffer (150+ candles), validate sufficient history |
| Subagent output → TAMentor | Passing raw dict, hoping LLM parses it | Validate with Pydantic before passing, ensure schema match |
| CCXT timestamps → Python datetime | Using naive datetime.fromtimestamp() | Explicit UTC timezone: datetime.fromtimestamp(ts/1000, tz=timezone.utc) |
| Weekly/Daily/4H data → Alignment | Assuming all "current" data represents same time | Document staleness per timeframe, validate alignment windows |
| Indicator NaN handling | Ignoring NaN, hoping it doesn't break | Explicit NaN strategy: drop, forward-fill, or reject analysis |
| Volume analysis across symbols | Comparing absolute volume values | Normalize volume relative to symbol's recent average |
| LLM JSON parsing | json.loads() with no error handling | Robust extraction with markdown removal, regex fallback |
| Wyckoff phase transitions | Attempting definitive phase labels | Probabilistic signal detection with confidence scores |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Fetching full 2-year history on every analysis | Analysis takes 5+ seconds, rate limit errors | Cache OHLCV data, only fetch incremental updates | >10 analyses per minute |
| Computing all indicators unconditionally | CPU spikes, slow response times | Lazy evaluation - compute only needed indicators | >100 concurrent analyses |
| Storing full OHLCV in TAMentor prompt | Prompt token costs spike, slow LLM calls | Summarize OHLCV (key levels, patterns) not raw candles | Prompts >8K tokens |
| Recomputing indicators from scratch every update | Unnecessary computation, delays | Incremental updates - recalculate only new candles | Real-time streaming mode |
| No prompt caching for TAMentor | Repeat costs for identical system prompt | Enable Anthropic prompt caching (saves 90% tokens) | >100 LLM calls per day |

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1: Indicators Module | Look-ahead bias in DataFrame operations | Use iloc for time-slicing, document that production uses .iloc[-1] |
| Phase 1: Indicators Module | Insufficient warmup data | Fetch 250+ candles, check for NaN before returning |
| Phase 1: Indicators Module | Timezone bugs | Explicitly use UTC everywhere, test with multiple timezones |
| Phase 2: Subagent Implementation | Multi-timeframe alignment errors | Document staleness, add metadata, test on different weekdays |
| Phase 2: Subagent Implementation | Missing data gaps not detected | Implement gap detection, test with synthetic gapped data |
| Phase 2: Subagent Implementation | Repainting on incomplete candles | Closed-candle-only policy for signals |
| Phase 3: Wyckoff Detection | False positive explosion | Start with strict thresholds (volume >2x, price >1.5 ATR) |
| Phase 3: Wyckoff Detection | Volume not normalized | Implement volume normalization before Wyckoff analysis |
| Phase 3: Wyckoff Detection | Over-complicating algorithm | Start simple (signal detection + confidence), not definitive phases |
| Phase 4: TAMentor Implementation | LLM JSON parsing brittleness | Robust extraction with fallbacks, test with 50+ real responses |
| Phase 4: TAMentor Implementation | Conflict suppression as neutral | Surface conflicts as qualified signals with warnings |
| Phase 5: Testing/Calibration | Confidence scores not calibrated | Track confidence vs actual outcomes, implement calibration |

## Testing Strategies to Prevent Pitfalls

### Strategy 1: Synthetic Data with Known Outputs
Create DataFrames with known patterns:
- Perfect uptrend → RSI should climb to 70+
- Flat price, high volume → OBV flat
- Sine wave → Support/resistance at peaks/troughs

### Strategy 2: Timestamp Boundary Tests
Test with candles at midnight UTC, daylight savings transitions, different days of week

### Strategy 3: Edge Case Coverage
- Single candle (not enough for any indicator)
- Gapped data (remove candles 45-47, verify detection)
- Zero volume candles (some exchanges report this)
- Incomplete candles (verify closed-only policy)

### Strategy 4: Cross-Timeframe Consistency
Calculate daily RSI from daily candles vs aggregating 4H candles to daily → should match within 1%

### Strategy 5: LLM Response Format Variations
Test JSON extraction with:
- Perfect JSON: `{"bias": "bullish"}`
- Markdown wrapped: ` ```json\n{...}\n``` `
- Text before JSON: `Based on analysis:\n{...}`
- Text after JSON: `{...}\nThis indicates...`

### Strategy 6: Multi-Day Testing
Run same analysis on Monday vs Friday to detect:
- Weekly data staleness issues
- Timezone alignment problems
- Repainting from incomplete candles

## "Looks Done But Isn't" Checklist

- [ ] **Indicator Module:** Often missing warmup buffer validation — verify reject() when insufficient history
- [ ] **Wyckoff Detection:** Often missing volume normalization — verify uses relative volume not absolute
- [ ] **Multi-timeframe Alignment:** Often missing staleness documentation — verify timestamp metadata included
- [ ] **TAMentor JSON Parsing:** Often missing markdown/text extraction — verify handles ```json blocks
- [ ] **Subagent Tests:** Often missing gap handling tests — verify behavior with 3-day gap in daily data
- [ ] **Confidence Scores:** Often missing calibration tracking — verify record (confidence, outcome)
- [ ] **OHLCV Timestamps:** Often missing UTC enforcement — verify all datetime objects have timezone.utc
- [ ] **Error Handling:** Often missing specific error types — verify distinguishes "insufficient data" from "API failure"
- [ ] **Conflict Resolution:** Often missing conflict context — verify shows both sides, not just "neutral"
- [ ] **Repainting Prevention:** Often missing closed-candle policy — verify signals only from closed candles

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Insufficient warmup buffer | LOW | Add WARMUP_CANDLES constant, update fetch calls, rerun analysis |
| Timezone inconsistency | MEDIUM | Audit all datetime usage, add explicit UTC, update stored timestamps |
| Wyckoff false positives | HIGH | Redesign as probabilistic signals, retrain/recalibrate, update tests |
| LLM parsing brittleness | LOW | Add robust extraction function, wrap all json.loads(), test with real responses |
| Missing data gaps | MEDIUM | Implement gap detection, add fill or reject policy, reprocess historical |
| Confidence calibration drift | MEDIUM | Implement calibration tracker, backfill historical outcomes, adjust scores |
| Repainting on live data | HIGH | Separate closed-candle vs live monitoring, refactor signal generation |
| Multi-timeframe misalignment | HIGH | Add staleness validation, rewrite alignment logic, update conflict resolution |
| Volume normalization missing | MEDIUM | Implement normalization function, update Wyckoff module, recalibrate |
| Conflict suppression | LOW | Modify TAMentor to surface conflicts with warnings, update output model |

## Sources

**Note:** Research based on training data (Jan 2025 cutoff) + codebase analysis. External verification tools unavailable.

**Training data sources:**
- pandas-ta GitHub issues (installation, column names, VWAP reset)
- CCXT timezone handling documentation
- TA implementation blog posts (look-ahead bias, warmup periods)
- Wyckoff methodology books (false positive patterns, subjective interpretation)
- Anthropic documentation (JSON parsing, prompt engineering)
- Multi-timeframe analysis patterns (alignment, staleness, repainting)

**Codebase analysis:**
- OHLCVClient implementation (CCXT, retry logic, supported timeframes)
- TASignal Pydantic models (confidence scoring, timeframe structure)
- Subagent shells (LLM integration patterns)

**Confidence level:** MEDIUM
- Indicators, multi-timeframe, timezone pitfalls: HIGH confidence (well-established patterns)
- Wyckoff methodology pitfalls: MEDIUM confidence (framework principles known)
- LLM JSON parsing pitfalls: HIGH confidence (documented SDK behavior)
- Integration-specific pitfalls: MEDIUM confidence (inferred from codebase)

**Verification recommended:**
- Test pandas-ta on Python 3.11+ for any recent bugs
- Validate CCXT OHLCV gap handling with real exchange data
- Test LLM JSON parsing with 50+ real Claude Opus responses
- Manual review of Wyckoff signal detection with historical examples

---
*Pitfalls research for TA Ensemble implementation*
*Researched: 2026-02-27*
*Confidence: MEDIUM (training data + codebase analysis, no external verification available)*
