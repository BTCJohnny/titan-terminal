---
phase: 09-alpha-factors-module
plan: 01
subsystem: analysis
tags: [alpha-factors, momentum, volume, volatility, pydantic]
completed: 2026-02-27T16:15:10Z
duration: 110

dependencies:
  requires:
    - phase-08-02 (indicators.py for calculate_atr)
  provides:
    - calculate_momentum_score
    - detect_volume_anomaly
    - calculate_ma_deviation
    - calculate_volatility_score
    - AlphaFactors Pydantic models
  affects:
    - Future subagent implementations (phase 11+)

tech_stack:
  added:
    - pandas (ewm for EMA calculations)
    - numpy (tanh, clip for normalization)
  patterns:
    - Optional[dict] return pattern for insufficient data
    - Import reuse (calculate_atr from indicators.py)
    - Pydantic v2 Field constraints (ge, le, gt)

key_files:
  created:
    - src/backend/analysis/alpha_factors.py
    - src/backend/models/alpha_factors.py
  modified: []

decisions:
  - "Used np.tanh for momentum normalization to bound scores to -100/+100"
  - "Volume anomaly threshold set at 2.0x (configurable parameter)"
  - "EMA deviations use adjust=False for TradingView compatibility"
  - "Volatility score scales linearly: 5% ATR = 100 score"
  - "All functions follow established indicators.py pattern"

metrics:
  tests_added: 0
  tests_passing: 54
  lines_added: 330
  files_created: 2
---

# Phase 09 Plan 01: Alpha Factors Implementation Summary

**One-liner:** Four alpha factor calculation functions (momentum, volume anomaly, MA deviation, volatility) with Pydantic validation models

## Tasks Completed

| Task | Name | Status | Commit | Files |
|------|------|--------|--------|-------|
| 1 | Create alpha factor calculation functions | ✓ | 45d14e0 | src/backend/analysis/alpha_factors.py |
| 2 | Create AlphaFactors Pydantic models | ✓ | 078af0e | src/backend/models/alpha_factors.py |

## What Was Built

### Alpha Factor Functions (alpha_factors.py)

Implemented four quantitative market analysis functions following the established indicators.py pattern:

1. **calculate_momentum_score(df, short_period=10, long_period=20)**
   - Computes short and long-term rate of change (ROC)
   - Combines with weighted average (60% short, 40% long)
   - Normalizes using hyperbolic tangent to -100/+100 range
   - Returns dict with short_roc, long_roc, momentum_score
   - Minimum data: 21 candles

2. **detect_volume_anomaly(df, ma_period=20, threshold=2.0)**
   - Compares current volume to 20-period rolling average
   - Calculates volume ratio and flags anomalies (>2x threshold)
   - Returns dict with current_volume, avg_volume, volume_ratio, is_anomaly
   - Minimum data: 20 candles

3. **calculate_ma_deviation(df)**
   - Calculates percentage deviation from 20, 50, and 200 EMAs
   - Uses adjust=False for TradingView-compatible EMA calculation
   - Returns dict with deviation_20, deviation_50, deviation_200
   - Minimum data: 200 candles

4. **calculate_volatility_score(df, atr_period=14)**
   - Imports calculate_atr from indicators.py (no reimplementation)
   - Normalizes ATR to percentage of current price
   - Scales linearly: 5% ATR = 100 score (caps at 100)
   - Returns dict with atr, atr_percent, volatility_score
   - Minimum data: 15 candles

All functions:
- Return Optional[dict] - None for insufficient data
- Include comprehensive docstrings with Args, Returns, Minimum data
- Handle edge cases (zero division, missing data)
- Follow try/except pattern for robustness

### Pydantic Models (alpha_factors.py)

Created five Pydantic v2 models for validating alpha factor outputs:

1. **MomentumData** - Validates momentum scores with -100/+100 constraint
2. **VolumeAnomalyData** - Validates volume ratios (all values > 0)
3. **MADeviationData** - Validates EMA deviation percentages
4. **VolatilityData** - Validates ATR-based scores with 0-100 constraint
5. **AlphaFactors** - Aggregates all factors with Optional fields

All models include:
- Field(...) with description parameters
- Validation constraints (ge, le, gt)
- JSON schema examples for documentation
- Pattern matching with existing models (ta_signal.py)

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

**Function Imports:**
```bash
python -c "from src.backend.analysis.alpha_factors import calculate_momentum_score, detect_volume_anomaly, calculate_ma_deviation, calculate_volatility_score"
# Result: OK
```

**Model Imports:**
```bash
python -c "from src.backend.models.alpha_factors import AlphaFactors"
# Result: OK
```

**Existing Tests:**
```bash
PYTHONPATH=/Users/johnny_main/Developer/projects/titan-terminal pytest src/backend/tests/ -x
# Result: 54 passed, 1 warning in 2.21s
```

All verification criteria passed.

## Success Criteria Met

- [x] Four alpha factor functions exist in alpha_factors.py
- [x] calculate_volatility_score imports calculate_atr from indicators.py (no reimplementation)
- [x] All functions return Optional[dict] with correct keys
- [x] AlphaFactors Pydantic model validates factor outputs with proper constraints
- [x] Existing 54 tests still pass

## Technical Decisions

1. **Momentum Normalization:** Used np.tanh(combined / 10) * 100 to smoothly bound momentum scores to -100/+100 range. This provides non-linear scaling that prevents extreme values while preserving relative differences.

2. **Volume Threshold:** Set default anomaly threshold at 2.0x average volume (configurable). Research suggests 1.5x-2x is typical for "high volume" detection.

3. **EMA Calculation:** Used ewm(span=X, adjust=False) for TradingView compatibility. The adjust=False parameter ensures consistent behavior with trading platforms.

4. **Volatility Scaling:** Linear scaling where 5% ATR = 100 score. This provides intuitive interpretation (higher score = more volatile) with practical maximum threshold.

5. **Code Reuse:** Imported calculate_atr from indicators.py rather than reimplementing. Maintains single source of truth for ATR calculation.

## Impact

**Immediate:**
- Provides quantitative factors for subagent signal generation
- Establishes pattern for alpha factor modules
- Enables momentum-based trading strategies

**Next Steps:**
- Phase 09 Plan 02: Unit tests for all alpha factor functions
- Phase 10: Wyckoff phase detection using volume and price analysis
- Phase 11+: Subagent implementations consuming these factors

## Files Modified

**Created:**
- `src/backend/analysis/alpha_factors.py` (226 lines) - Four calculation functions
- `src/backend/models/alpha_factors.py` (104 lines) - Five Pydantic models

**Modified:** None

## Commits

1. `45d14e0` - feat(09-01): implement alpha factor calculation functions
2. `078af0e` - feat(09-01): add AlphaFactors Pydantic validation models

## Self-Check: PASSED

**Files exist:**
```bash
[ -f "src/backend/analysis/alpha_factors.py" ] && echo "FOUND: src/backend/analysis/alpha_factors.py"
# FOUND: src/backend/analysis/alpha_factors.py

[ -f "src/backend/models/alpha_factors.py" ] && echo "FOUND: src/backend/models/alpha_factors.py"
# FOUND: src/backend/models/alpha_factors.py
```

**Commits exist:**
```bash
git log --oneline --all | grep -q "45d14e0" && echo "FOUND: 45d14e0"
# FOUND: 45d14e0

git log --oneline --all | grep -q "078af0e" && echo "FOUND: 078af0e"
# FOUND: 078af0e
```

All claims verified.
