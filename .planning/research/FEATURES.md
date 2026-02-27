# Feature Research: TA Ensemble Implementation

**Domain:** Technical Analysis for Crypto Trading Dashboard
**Researched:** 2026-02-27
**Confidence:** MEDIUM (based on training data and existing codebase patterns)

## Feature Landscape

### Table Stakes (Users Expect These)

Features that TA ensemble systems must have. Missing these means the system is incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Multi-timeframe RSI | Standard momentum indicator, universally used | LOW | Weekly/Daily/4H with 14-period default, 30/70 crypto thresholds |
| MACD (12,26,9) | Core momentum indicator for trend confirmation | LOW | Signal line crossovers, histogram divergence detection |
| EMA trend analysis | Price-EMA relationship defines trend structure | LOW | 20/50/200 EMAs, alignment detection for trend strength |
| Support/Resistance levels | Critical for entry/exit planning, risk management | MEDIUM | Price action clustering, volume profile nodes, psychological levels |
| Volume analysis | Validates price moves, detects accumulation/distribution | MEDIUM | OBV for cumulative flow, volume spikes for climax detection |
| Bollinger Bands | Volatility measure and mean reversion signals | LOW | 20-period, 2 SD bands, squeeze/expansion detection |
| Trend direction/strength | Fundamental TA output required for any signal | LOW | Directional bias + strength classification (strong/moderate/weak) |
| Confidence scoring | Users need to gauge signal reliability | MEDIUM | 0-100 scale, adjustment logic for confluence/conflicts |

### Differentiators (Competitive Advantage)

Features that set this TA Ensemble apart from generic TA systems. Not universally expected but provide genuine edge.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Wyckoff phase detection (A-E) | Smart money accumulation/distribution framework | HIGH | Phases A-E detection, requires multi-candle pattern matching |
| Wyckoff key events (springs, upthrusts, SOS/SOW) | High-conviction entry signals at structural inflections | HIGH | Spring = accumulation completion, SOW = distribution start |
| Multi-timeframe conflict resolution | Prevents whipsaw trades from conflicting signals | MEDIUM | Weekly/Daily > 4H hierarchy, confidence penalty on conflicts |
| Alpha factors (momentum score, volume anomaly) | Quantitative overlay on qualitative TA | MEDIUM | Numerical scores for filtering/ranking opportunities |
| TAMentor AI synthesis | LLM-powered multi-timeframe reasoning | MEDIUM | Claude Opus synthesis with explicit conflict reasoning |
| Volume-price divergence | Detects supply/demand imbalance before price moves | MEDIUM | Wyckoff principle: volume precedes price |
| VWAP for institutional levels | Shows where "smart money" traded during period | LOW | Intraday mean reversion reference, volume-weighted fair value |
| ATR for volatility context | Position sizing and stop placement | LOW | 14-period ATR, normalizes volatility across assets |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems or scope creep.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time tick data | Feels more "live" and responsive | Adds massive complexity, rate limits, storage overhead for minimal edge | 4H candles sufficient for swing trading, refresh every 15 min |
| Hundreds of indicators | "More indicators = better analysis" | Creates noise, conflicting signals, analysis paralysis | Curated set of 8-10 proven indicators with clear interpretation |
| Automatic trade execution | "Automation removes emotion" | Legal liability, catastrophic failure modes, loses educational value | Signal generation only, user executes manually |
| Backtesting engine | Validate strategy performance | Massive scope creep, overfitting risk, not core value prop | Forward testing only, document live signal performance |
| Custom indicator builder | User flexibility | Infinite support surface, dilutes focused approach | Fixed indicator set with proven track record |
| Intraday scalping signals | Higher frequency = more opportunities | 4H is lower bound for reliable TA, below that is noise in crypto | Focus on 4H+ timeframes where TA actually works |

## Feature Dependencies

```
Wyckoff Detection
    └──requires──> Volume Analysis (OBV, volume spikes)
    └──requires──> Support/Resistance Levels (ranges for phases)
    └──requires──> Multi-timeframe OHLCV (already shipped v0.2)

Alpha Factors
    └──requires──> Technical Indicators (RSI, MACD, EMA)
    └──requires──> Volume Analysis (volume anomaly calculation)

TAMentor Synthesis
    └──requires──> All Subagent Outputs (Weekly, Daily, 4H signals)
    └──requires──> Conflict Resolution Rules (defined in PROJECT.md)

Support/Resistance Detection
    └──enhances──> Wyckoff Detection (defines ranges)
    └──enhances──> Risk Management (stop placement)

Multi-timeframe Conflict Resolution
    └──requires──> Subagent Bias Outputs (from TASignal models)
    └──enhances──> Confidence Scoring (penalty/bonus adjustments)
```

### Dependency Notes

- **Wyckoff requires volume analysis:** Phases A-E identification depends on volume-price relationships (climaxes, tests, springs)
- **Alpha factors require indicators:** Momentum score derived from RSI/MACD/EMA values
- **TAMentor requires subagent outputs:** Cannot synthesize without Weekly, Daily, 4H analysis complete
- **S/R enhances Wyckoff:** Ranges define accumulation/distribution zones
- **Conflict resolution enhances confidence:** -20 point penalty for timeframe conflicts (per PROJECT.md)

## MVP Definition

### Launch With (v0.3 - Current Milestone)

Features required to ship functional TA Ensemble.

- [x] Multi-timeframe OHLCV client (shipped v0.2)
- [ ] Technical indicators module (RSI, MACD, BB, ADX, OBV, VWAP, ATR)
- [ ] Support/Resistance detection algorithm
- [ ] Wyckoff phase detection (phases A-E, springs, upthrusts, SOS/SOW)
- [ ] Alpha factors computation (momentum score, volume anomaly, MA deviation, volatility)
- [ ] Extended TASignal model with wyckoff and alpha_factors fields
- [ ] WeeklySubagent with full analysis pipeline
- [ ] DailySubagent with full analysis pipeline
- [ ] FourHourSubagent with full analysis pipeline
- [ ] TAMentor synthesis with Claude Opus
- [ ] Conflict resolution logic (Weekly/Daily > 4H, -20 penalty, NO SIGNAL on W/D conflict)
- [ ] Unit tests for indicators, Wyckoff, subagents, TAMentor

### Add After Validation (v1.0+)

Features to add once core TA Ensemble is working and validated.

- [ ] Divergence detection (RSI/MACD vs price)
- [ ] Pattern recognition beyond Wyckoff (flags, triangles, H&S)
- [ ] Fibonacci retracement levels
- [ ] Volume profile analysis (POC, VAH, VAL)
- [ ] On-chain data integration with TA signals (Nansen overlay)
- [ ] Historical signal performance tracking
- [ ] Alert thresholds (notify on high-confidence setups)

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Options flow integration (for crypto options markets)
- [ ] Order book depth analysis (for liquidity assessment)
- [ ] Correlation analysis across assets
- [ ] Machine learning confidence calibration
- [ ] Custom timeframe support (beyond 1w/1d/4h)
- [ ] Social sentiment overlay (Twitter/Reddit)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Notes |
|---------|------------|---------------------|----------|-------|
| Technical Indicators | HIGH | LOW | P1 | Table stakes, well-defined calculations |
| Wyckoff Detection | HIGH | HIGH | P1 | Differentiator, complex but core value prop |
| Alpha Factors | MEDIUM | MEDIUM | P1 | Quantitative edge, moderate complexity |
| Multi-TF Conflict Resolution | HIGH | MEDIUM | P1 | Prevents bad trades, clearly specified in PROJECT.md |
| TAMentor Synthesis | HIGH | MEDIUM | P1 | Unifies signals, leverages Claude Opus |
| S/R Detection | HIGH | MEDIUM | P1 | Critical for risk management |
| Divergence Detection | MEDIUM | LOW | P2 | Useful but not MVP |
| Pattern Recognition | MEDIUM | HIGH | P2 | Scope creep risk, defer to v1.0 |
| Volume Profile | MEDIUM | HIGH | P2 | Advanced feature, defer |
| Fibonacci Levels | LOW | LOW | P3 | Subjective, low priority |

**Priority key:**
- P1: Must have for v0.3 launch (current milestone)
- P2: Should have for v1.0 (after validation)
- P3: Nice to have, future consideration

## Expected Behavior and Thresholds

### Technical Indicators (Industry Conventions)

Based on training data knowledge of standard TA practices:

| Indicator | Standard Settings | Interpretation | Crypto-Specific Notes |
|-----------|-------------------|----------------|----------------------|
| **RSI** | 14-period | <30 oversold, >70 overbought | Crypto: use 30/70 not 20/80, more volatile |
| **MACD** | (12, 26, 9) | Signal line cross = momentum shift | Histogram divergence often precedes price reversal |
| **Bollinger Bands** | 20-period, 2 SD | Touch/break bands = volatility extreme | Squeeze (narrow bands) precedes expansion |
| **ADX** | 14-period | <20 weak trend, >25 strong trend, >50 very strong | Direction from +DI/-DI, strength from ADX value |
| **OBV** | Cumulative | Rising = accumulation, falling = distribution | More reliable than price-only analysis |
| **VWAP** | Intraday reset | Price above = bullish, below = bearish | Institutional reference point |
| **ATR** | 14-period | Absolute volatility measure | Use for position sizing and stop distance |
| **EMA** | 20/50/200 | Price above = bullish, alignment = trend strength | 200 EMA = major support/resistance |

**LOW CONFIDENCE:** Crypto-specific threshold adjustments (30/70 RSI) based on training data patterns, not verified with current sources.

### Wyckoff Phase Detection (Expected Patterns)

Based on Wyckoff Method training knowledge:

**Accumulation Phases:**
- **Phase A:** Stopping action after downtrend, selling climax (SC), automatic rally (AR), secondary test (ST)
- **Phase B:** Building cause, range-bound trading, diminishing volume
- **Phase C:** Spring (false breakdown below support), final shakeout before markup
- **Phase D:** Sign of Strength (SOS), breakout above resistance on increasing volume
- **Phase E:** Markup phase, sustained uptrend with pullbacks

**Distribution Phases:**
- **Phase A:** Stopping action after uptrend, preliminary supply (PSY), buying climax (BC), automatic reaction (AR)
- **Phase B:** Building cause, range-bound at top, professional accumulation
- **Phase C:** Upthrust (false breakout above resistance), final trap before markdown
- **Phase D:** Sign of Weakness (SOW), breakdown below support on increasing volume
- **Phase E:** Markdown phase, sustained downtrend

**Detection Challenges:**
- **Accuracy:** Highly subjective, even expert chartists disagree 20-30% of the time
- **Phase C critical:** Spring/upthrust detection is highest conviction entry signal but also most ambiguous
- **Volume-price relationship:** Requires consistent volume data (crypto has this, unlike some markets)
- **Multi-timeframe:** Weekly shows major accumulation, 4H shows micro springs within larger structure

**MEDIUM CONFIDENCE:** Wyckoff principles well-established but detection accuracy varies significantly based on implementation. Expect 60-70% phase classification accuracy with conservative approach.

### Alpha Factors (Typical Ranges)

Based on quantitative analysis training knowledge:

| Alpha Factor | Calculation | Expected Range | Interpretation |
|--------------|-------------|----------------|----------------|
| **Momentum Score** | Composite of RSI/MACD/EMA alignment | 0-100 | >70 strong momentum, <30 weak |
| **Volume Anomaly** | Current volume vs N-period average | 0.5x - 5.0x | >2.0x = unusual activity |
| **MA Deviation** | (Price - MA) / MA * 100 | -30% to +30% | Extreme deviation = mean reversion setup |
| **Volatility Percentile** | Current ATR vs historical distribution | 0-100 | >80 = high vol, <20 = low vol |

**Implementation Notes:**
- Momentum score: Weight higher timeframes more heavily (Weekly 50%, Daily 30%, 4H 20%)
- Volume anomaly: Use 20-period lookback, flag >2.5x as significant
- MA deviation: 200 EMA as reference, >15% deviation = extended
- Volatility percentile: 90-day lookback for percentile calculation

**LOW CONFIDENCE:** Alpha factor calculations are custom implementations, not industry-standard definitions. Ranges are estimates based on typical quantitative finance patterns.

### Multi-Timeframe Conflict Resolution (Project-Specific)

From PROJECT.md documentation (HIGH CONFIDENCE):

**Rules:**
- **Higher timeframe wins direction:** Weekly/Daily override 4H for bias
- **Conflict penalty:** -20 confidence points when timeframes contradict
- **W/D conflict:** No signal emitted (genuine uncertainty, not tradeable)
- **Warning context:** 4H counter-trend labeled as "pullback" or "bounce" not reversal

**Examples:**
- Weekly bullish, Daily bullish, 4H bearish: **Bias = Bullish**, confidence -20, "4H pullback - potential better entry"
- Weekly bullish, Daily bearish: **NO SIGNAL**, wait for alignment
- Weekly neutral, Daily bullish, 4H bullish: **Bias = Bullish**, no penalty, neutral higher TF not conflict

**Confluence Scoring:**
- **Perfect (100):** All three timeframes aligned same bias
- **Strong (80-90):** Higher TFs aligned, 4H minor divergence
- **Moderate (60-75):** One TF neutral, others aligned
- **Weak (40-55):** Two TFs aligned weakly, one opposing
- **Conflicting (0-30):** Weekly/Daily opposing (no signal emitted)

## Competitor Feature Analysis

| Feature | TradingView | Glassnode | Nansen | Titan Terminal Approach |
|---------|-------------|-----------|--------|------------------------|
| Technical Indicators | 100+ indicators, overwhelming | None (on-chain only) | None | Curated 8 indicators, clear interpretation |
| Wyckoff Analysis | Manual charting only | Not supported | Not supported | **Automated detection (differentiator)** |
| Multi-TF Synthesis | Side-by-side charts, manual | Single TF | Single TF | **AI-powered synthesis with conflict resolution** |
| Alpha Factors | Pine Script custom | On-chain metrics | Smart money tracking | **TA + on-chain fusion (v1.0)** |
| Confidence Scoring | Not provided | Not provided | Not provided | **Explicit confidence with adjustment reasoning** |
| Entry Timing | Not provided | Not provided | Not provided | **Immediate/pullback/confirmation recommendations** |

**Competitive Edge:**
1. Automated Wyckoff detection (no competitor does this well)
2. AI-powered multi-timeframe synthesis (TradingView requires manual analysis)
3. Explicit confidence adjustment (unprecedented transparency)
4. TA + on-chain integration planned (unique combination)

## Implementation Complexity Assessment

### LOW Complexity (1-2 days)
- RSI, MACD, Bollinger Bands, EMA calculations
- ATR, VWAP basic calculations
- Basic alpha factors (momentum score from existing indicators)

### MEDIUM Complexity (3-5 days)
- Support/Resistance detection (clustering algorithm, volume nodes)
- OBV and volume anomaly detection
- ADX calculation (more complex than basic indicators)
- Multi-timeframe conflict resolution logic
- TAMentor prompt engineering and synthesis

### HIGH Complexity (5-10 days)
- Wyckoff phase detection (pattern matching across candles)
- Spring/upthrust identification (requires context, not just pattern)
- SOS/SOW detection (volume-price relationship nuances)
- Extended TASignal model with nested structures
- Comprehensive unit tests for Wyckoff (ambiguous patterns difficult to test)

**Total Estimated Effort:** 15-20 days for complete v0.3 milestone implementation.

## Data Requirements

### Existing (Shipped v0.2)
- [x] OHLCV data (BTC, ETH, SOL)
- [x] Weekly (1w), Daily (1d), 4-hour (4h) timeframes
- [x] Binance API integration with retry logic
- [x] Volume data included in OHLCV

### Required for v0.3
- [ ] Sufficient candle history (52 weeks for weekly analysis)
- [ ] Volume data validation (ensure non-zero, non-null)
- [ ] Price precision handling (different across symbols)

### Nice to Have (v1.0+)
- [ ] Funding rates from Hyperliquid (sentiment overlay)
- [ ] Order book snapshots (liquidity analysis)
- [ ] Historical comparison data (performance tracking)

## Sources

**MEDIUM-HIGH CONFIDENCE:**
- Existing codebase examination (ta_signal.py, ta_mentor_signal.py, wyckoff.py, PROJECT.md)
- Training data knowledge of standard TA indicator calculations and Wyckoff Method
- PROJECT.md explicit conflict resolution rules

**LOW CONFIDENCE:**
- Crypto-specific RSI thresholds (30/70 vs 20/80)
- Wyckoff detection accuracy estimates (60-70%)
- Alpha factor calculation specifics (no industry standard definitions)

**Gaps Requiring Verification:**
- Current best practices for Wyckoff automation (training data from 2024)
- Crypto market indicator parameter optimization (may have evolved)
- Multi-timeframe conflict resolution patterns in production systems (no external sources)

**Honest Assessment:** This research is primarily based on:
1. Codebase examination (HIGH confidence for what already exists)
2. Training data knowledge of TA conventions (MEDIUM confidence, 6-18 months stale)
3. Logical inference from project requirements (MEDIUM confidence)

**No external verification possible** due to WebSearch unavailable and Brave API key not configured. Recommend validating:
- Indicator parameter choices with current crypto TA community practices
- Wyckoff detection implementation against recent literature or working implementations
- Alpha factor calculation conventions if industry standards exist

---
*Feature research for: TA Ensemble Implementation*
*Researched: 2026-02-27*
*Confidence: MEDIUM (training data + codebase analysis, no external verification)*
