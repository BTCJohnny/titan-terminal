---
phase: 10-wyckoff-detection-module
plan: 01
subsystem: models
tags: [wyckoff, pydantic, validation, data-contracts]
dependency_graph:
  requires: [pydantic]
  provides: [WyckoffEvent, WyckoffAnalysis]
  affects: []
tech_stack:
  added: []
  patterns: [pydantic-models, field-validation, auto-sorting]
key_files:
  created:
    - src/backend/models/wyckoff.py
  modified:
    - src/backend/models/__init__.py
decisions:
  - "Auto-sort events by candle_index using field_validator for chronological ordering"
  - "Use Literal types for phase and event_type to enforce valid values"
  - "Set phase_confidence range to 0-100 with Field constraints"
metrics:
  duration_seconds: 92
  tasks_completed: 2
  files_created: 1
  files_modified: 1
  commits: 2
  tests_passing: 82
  completed_at: "2026-02-27T17:31:46Z"
---

# Phase 10 Plan 01: Wyckoff Models Summary

**One-liner:** Created WyckoffEvent and WyckoffAnalysis Pydantic models with field validation and chronological event sorting.

## What Was Built

Created the data contract models that Wyckoff detection functions will return:

**WyckoffEvent model** validates individual events:
- `candle_index` (int >= 0) - DataFrame index where event occurred
- `event_type` (Literal) - spring, upthrust, sos, sow, lps, lpsy
- `price` (float > 0) - price at event
- `volume_ratio` (float > 0) - volume as multiple of baseline
- `description` (str, min_length=1) - human-readable description

**WyckoffAnalysis model** aggregates phase detection:
- `phase` (Literal) - 10 accumulation/distribution phases + unknown
- `phase_confidence` (int 0-100) - confidence score
- `events` (List[WyckoffEvent]) - auto-sorted chronologically
- `volume_confirms` (bool) - volume confirmation flag
- `analysis_notes` (str) - additional context

Both models follow the established pattern from `alpha_factors.py` with comprehensive Field descriptions and json_schema_extra examples.

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Create WyckoffEvent and WyckoffAnalysis models | 3359e86 | src/backend/models/wyckoff.py |
| 2 | Export Wyckoff models from models module | cefaa01 | src/backend/models/__init__.py |

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All success criteria met:

- WyckoffEvent validates: candle_index >= 0, event_type in valid literals, price > 0, volume_ratio > 0, description non-empty ✓
- WyckoffAnalysis validates: phase in valid literals, phase_confidence 0-100, events list auto-sorted, volume_confirms bool, analysis_notes string ✓
- Models exported from src.backend.models ✓
- All 82 existing tests pass (up from 54 baseline due to Phase 9 additions) ✓
- Confidence constraint enforced: ValidationError raised for values > 100 ✓

## Technical Details

**Field validation highlights:**
- Used `@field_validator('events')` decorator to auto-sort events by candle_index, ensuring chronological order
- Literal types for `phase` (11 valid phases) and `event_type` (6 valid event types) provide compile-time safety
- Field constraints (`ge=0`, `le=100`, `gt=0`, `min_length=1`) enforce data integrity

**Model integration:**
- Models added to `src/backend/models/__init__.py` exports alongside existing AlphaFactors models
- Consistent docstring and Field description patterns maintained across all models
- JSON schema examples provided for API documentation

## Next Steps

Ready for 10-02-PLAN.md: Implement Wyckoff detection functions that return these validated models.

## Self-Check: PASSED

**Files created:**
- FOUND: src/backend/models/wyckoff.py

**Files modified:**
- FOUND: src/backend/models/__init__.py

**Commits:**
- FOUND: 3359e86
- FOUND: cefaa01

All claims verified.
