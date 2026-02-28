---
phase: 10-wyckoff-detection-module
plan: 02
subsystem: analysis
tags: [wyckoff, pattern-detection, volume-analysis, phase-classification]
dependency_graph:
  requires: [WyckoffEvent, WyckoffAnalysis, detect_support_resistance]
  provides: [detect_wyckoff]
  affects: []
tech_stack:
  added: []
  patterns: [event-detection, phase-classification, volume-confirmation, deduplication]
key_files:
  created:
    - src/backend/analysis/wyckoff.py
  modified: []
decisions:
  - "Helper functions return empty lists on errors rather than raising exceptions"
  - "Event deduplication by candle_index to prevent duplicate detections"
  - "Phase classification prioritizes E > D > C > B > A for hierarchical logic"
  - "Volume confirmation thresholds: 0.9x baseline for Phase B, 1.1x for C/D, 1.2x for E"
  - "Confidence scoring: base 50, +20 for 100+ candles, +15 for 2-8 events, +15 for identified phase"
  - "Spring/Upthrust recovery window: 3 candles by default"
  - "SOS/SOW volume threshold: 1.5x baseline by default"
metrics:
  duration_seconds: 277
  tasks_completed: 3
  files_created: 1
  files_modified: 0
  commits: 3
  tests_passing: 82
  completed_at: "2026-02-27T17:38:39Z"
---

# Phase 10 Plan 02: Wyckoff Detection Functions Summary

**One-liner:** Implemented Wyckoff pattern detection with detect_wyckoff entry point for phase classification (A-E) and event detection (Spring, Upthrust, SOS, SOW).

## What Was Built

Created comprehensive Wyckoff pattern detection in `src/backend/analysis/wyckoff.py`:

**Helper functions (Task 1):**
- `_calculate_volume_baseline(df, period=20)` - Calculates mean volume over recent period
- `_detect_spring(df, support_levels, volume_baseline)` - Detects Spring events (price below support + recovery on low volume)
- `_detect_upthrust(df, resistance_levels, volume_baseline)` - Detects Upthrust events (price above resistance + failure on low volume)
- `_detect_sos(df, resistance_levels, volume_baseline)` - Detects Sign of Strength (breakout above resistance with high volume)
- `_detect_sow(df, support_levels, volume_baseline)` - Detects Sign of Weakness (breakdown below support with high volume)

**Phase classification (Task 2):**
- `_classify_phase(df, events, sr_levels, volume_baseline)` - Determines current Wyckoff phase from event sequence and price position
- `_check_volume_confirmation(df, phase, volume_baseline)` - Validates volume pattern confirms detected phase
- `_calculate_confidence(df, events, phase)` - Scores confidence 0-100 based on data quality and event detection
- `detect_wyckoff(df)` - Main entry point returning WyckoffAnalysis with phase, events, confidence, volume confirmation

**Edge case handling (Task 3):**
- Returns None for insufficient data (< 100 candles)
- Handles zero volume baseline (returns None to avoid division by zero)
- Handles empty support/resistance lists gracefully
- Deduplicates events by candle_index (keeps first occurrence)
- Comprehensive try/except blocks in all functions

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Create wyckoff.py with helper functions | e319721 | src/backend/analysis/wyckoff.py |
| 2 | Implement phase classification and detect_wyckoff entry point | ba59367 | src/backend/analysis/wyckoff.py |
| 3 | Handle insufficient data and edge cases | f9f58d7 | (verification only) |

## Deviations from Plan

None - plan executed exactly as written. All edge cases were proactively handled during Task 2 implementation, making Task 3 a verification step.

## Verification Results

All success criteria met:

- detect_wyckoff(df) returns WyckoffAnalysis with populated phase, events, volume_confirms ✓
- Spring detection: price below support + recovery within 1-3 candles + low volume ✓
- Upthrust detection: price above resistance + failure within 1-3 candles + low volume ✓
- SOS detection: close above resistance + volume > 1.5x baseline ✓
- SOW detection: close below support + volume > 1.5x baseline ✓
- Phase classification: A (stopping/climax), B (building/range), C (test/spring/upthrust), D (SOS/SOW), E (trending) ✓
- Returns None for insufficient data (< 100 candles) ✓
- All 82 existing tests pass ✓

## Technical Details

**Phase classification logic (hierarchical):**
1. **Phase E (Trending):** Price outside range after SOS/SOW
   - Accumulation E: SOS detected + price > nearest resistance
   - Distribution E: SOW detected + price < nearest support
2. **Phase D (Signs):** SOS or SOW detected (regardless of price position)
   - Accumulation D: SOS detected
   - Distribution D: SOW detected
3. **Phase C (Tests):** Spring or Upthrust detected
   - Accumulation C: Spring detected
   - Distribution C: Upthrust detected
4. **Phase B (Building Cause):** Range-bound with declining volume
   - Requires 50+ candles to compare volume trends
   - Accumulation B: Low volume volatility
   - Distribution B: Irregular volume pattern
5. **Phase A (Stopping Action):** Recent climax volume (> 2x baseline in last 20 candles)
   - Accumulation A: Climax near support
   - Distribution A: Climax near resistance

**Volume confirmation patterns:**
- Phase B: Recent volume < 0.9x baseline (accumulation/distribution)
- Phase C/D: Recent volume > 1.1x baseline (tests and signs)
- Phase E: Recent volume > 1.2x baseline (trending)

**Confidence scoring algorithm:**
- Base: 50
- Data quality: +20 if ≥100 candles, -20 if <50 candles
- Event detection: +15 if 2-8 events, -30 if 0 events, -20 if >15 events (over-detection)
- Phase certainty: +15 if phase identified (not "unknown")
- Clipped to 0-100 range

**Event detection parameters:**
- Spring/Upthrust recovery window: 3 candles (configurable)
- SOS/SOW volume threshold: 1.5x baseline (configurable)
- Volume baseline period: 20 candles (configurable)

**Robustness features:**
- All helper functions return empty lists on errors (never raise exceptions)
- Event deduplication prevents multiple detections at same candle
- Events auto-sorted chronologically by WyckoffAnalysis model validator
- Comprehensive error handling for missing columns, zero volume, insufficient data

## Next Steps

Ready for 10-03-PLAN.md: Integration of Wyckoff detection with TA signals and subagent analysis.

## Self-Check: PASSED

**Files created:**
- FOUND: src/backend/analysis/wyckoff.py

**Commits:**
- FOUND: e319721
- FOUND: ba59367
- FOUND: f9f58d7

All claims verified.
