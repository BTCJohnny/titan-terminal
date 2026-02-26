---
phase: 02-pydantic-models
plan: 01
subsystem: backend-models
tags: [pydantic, models, type-safety, ta-signals, onchain-signals]
dependency_graph:
  requires: [01-01]
  provides: [signal-models, ta-signal-types, nansen-signal-types]
  affects: [02-02, ta-agents, nansen-agent]
tech_stack:
  added: [pydantic-v2]
  patterns: [nested-models, field-validation, json-schema]
key_files:
  created:
    - src/backend/models/__init__.py
    - src/backend/models/ta_signal.py
    - src/backend/models/ta_mentor_signal.py
    - src/backend/models/nansen_signal.py
  modified: []
decisions:
  - id: MODL-NESTED
    summary: Use nested Pydantic models for complex signal structures
    rationale: Provides better type safety and validation for hierarchical data
  - id: MODL-CONFIDENCE
    summary: Standardize confidence scoring as 0-100 integers across all models
    rationale: Consistent confidence representation makes signal comparison easier
  - id: MODL-LITERALS
    summary: Use Literal types for enums (bias, direction, strength, etc.)
    rationale: Better IDE support and type checking than string enums
metrics:
  duration_minutes: 2
  tasks_completed: 3
  files_created: 4
  commits: 3
  completed_date: "2026-02-26"
---

# Phase 02 Plan 01: Core Signal Pydantic Models Summary

**One-liner:** Implemented type-safe Pydantic v2 models for TASignal (timeframe-specific TA), TAMentorSignal (multi-timeframe synthesis), and NansenSignal (5-signal on-chain framework) with nested structures and field validation.

## Objective Completion

Created three core Pydantic models that provide type-safe output structures for TA analysis agents:

1. **TASignal** - Timeframe-specific technical analysis (weekly, daily, 4h) with trend, momentum, key levels, patterns, and overall assessment
2. **TAMentorSignal** - Multi-timeframe synthesis with alignment scoring, conflict detection, confidence adjustments, and unified trading signal
3. **NansenSignal** - On-chain analysis using 5-signal framework (exchange flows, fresh wallets, smart money, top PnL, whale activity)

All models support JSON serialization and include comprehensive field validation.

## Tasks Completed

### Task 1: Create models package and TASignal model
**Status:** Complete
**Commit:** f22557c
**Files:**
- Created src/backend/models/__init__.py with package exports
- Created src/backend/models/ta_signal.py with TASignal model

**Implementation:**
- Defined nested models: TrendData, MomentumData, KeyLevels, PatternData, OverallAssessment
- Used Literal types for direction (bullish/bearish/sideways/neutral), strength (strong/moderate/weak), and timeframe (weekly/daily/4h)
- Added field validation for confidence (0-100 range)
- Included JSON schema examples
- All fields match Phase 1 agent dict structures

**Verification:** Tested import, instantiation, and JSON serialization successfully

### Task 2: Create TAMentorSignal model
**Status:** Complete
**Commit:** 62b34db
**Files:**
- Created src/backend/models/ta_mentor_signal.py with TAMentorSignal model
- Updated src/backend/models/__init__.py to export TAMentorSignal

**Implementation:**
- Defined nested models: TimeframeAlignment, ConflictDetail, ConfidenceAdjustment, UnifiedSignalLevels, UnifiedSignal
- TimeframeAlignment tracks weekly/daily/fourhour bias with alignment_score and confluence level
- ConflictDetail captures type (trend/momentum/pattern), description, and severity
- ConfidenceAdjustment shows base, bonus, penalty, and final confidence with reasoning
- UnifiedSignal provides actionable recommendation with bias, strength, action, timing, and key levels
- Supports conflict detection list (defaults to empty)

**Verification:** Tested import, instantiation, and JSON serialization successfully

### Task 3: Create NansenSignal model with 5-signal framework
**Status:** Complete
**Commit:** a580372
**Files:**
- Created src/backend/models/nansen_signal.py with NansenSignal model
- Updated src/backend/models/__init__.py to export NansenSignal

**Implementation:**
- Defined 5-signal framework models: ExchangeFlows, FreshWallets, SmartMoney, TopPnL, WhaleActivity
- OnChainOverall for unified assessment
- Each signal component includes confidence scoring (0-100)
- ExchangeFlows: net_direction, magnitude, interpretation, confidence
- FreshWallets: activity_level, trend, notable_count, interpretation
- SmartMoney: direction, confidence, notable_wallets list, interpretation
- TopPnL: traders_bias, average_position, confidence, interpretation
- WhaleActivity: summary, notable_transactions list, net_flow, confidence
- All fields use Literal types for constrained string values

**Verification:** Tested import, instantiation with all 5 signals, and JSON serialization successfully

## Deviations from Plan

None - plan executed exactly as written. All three models implemented according to specifications with proper Pydantic v2 syntax, field validation, and JSON schema support.

## Technical Implementation

### Architecture
- Models package structure: `src/backend/models/`
- Each signal type in its own module file
- Centralized exports through `__init__.py`
- Nested model classes for complex structures

### Pydantic v2 Features Used
- BaseModel for all models
- Field() with descriptions, validation, and defaults
- field_validator for custom validation (confidence range)
- Literal types for enumerated values
- Optional fields for nullable data
- model_config with json_schema_extra for examples
- Automatic JSON serialization via model_dump_json()

### Type Safety Improvements
- Replaced dict returns with strongly-typed Pydantic models
- All string enums replaced with Literal types
- Confidence scores validated at 0-100 range
- Optional floats for nullable numeric fields (RSI, support/resistance)
- Default empty lists for optional list fields

## Verification Results

**All verification checks passed:**

1. ✓ TASignal model imports successfully from src.backend.models
2. ✓ TASignal instantiates with valid test data
3. ✓ TASignal serializes to JSON without errors
4. ✓ TAMentorSignal model imports successfully from src.backend.models
5. ✓ TAMentorSignal instantiates with valid test data including conflicts
6. ✓ TAMentorSignal serializes to JSON without errors
7. ✓ NansenSignal model imports successfully from src.backend.models
8. ✓ NansenSignal instantiates with all 5-signal framework fields
9. ✓ NansenSignal serializes to JSON without errors
10. ✓ All three models can be imported together

## Requirements Mapping

**MODL-01: TASignal model** - Complete
- Fields: symbol, timeframe, trend (direction, strength, ema_alignment), momentum (rsi, macd_bias, divergence), key_levels, patterns, overall (bias, confidence, notes)
- Supports weekly, daily, 4h timeframes
- JSON serialization working

**MODL-02: TAMentorSignal model** - Complete
- Fields: symbol, timeframe_alignment, conflicts_detected, confidence_adjustment, unified_signal, synthesis_notes
- overall_direction mapped to unified_signal.bias
- confidence mapped to unified_signal.confidence
- conflicts as list of ConflictDetail objects
- warnings derivable from high-severity conflicts

**MODL-03: NansenSignal 5-signal framework** - Complete
- All 5 signals implemented: exchange_flows, fresh_wallets, smart_money, top_pnl, whale_activity
- overall_signal as OnChainOverall with bias, confidence, key_insights
- Each signal has confidence scoring and interpretation

## Next Steps

**For Plan 02-02:**
- Integrate these models into agent return types
- Update agent implementations to return model instances instead of dicts
- Add model serialization tests

**For downstream plans:**
- API endpoints can now use these models for request/response validation
- Database schemas can be generated from these models
- Frontend TypeScript types can be auto-generated from JSON schemas

## Self-Check: PASSED

**Files verified:**
- FOUND: src/backend/models/__init__.py
- FOUND: src/backend/models/ta_signal.py
- FOUND: src/backend/models/ta_mentor_signal.py
- FOUND: src/backend/models/nansen_signal.py

**Commits verified:**
- FOUND: f22557c (TASignal model)
- FOUND: 62b34db (TAMentorSignal model)
- FOUND: a580372 (NansenSignal model)

All planned artifacts exist and all task commits are in repository.
