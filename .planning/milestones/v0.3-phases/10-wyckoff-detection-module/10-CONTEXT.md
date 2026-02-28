# Phase 10: Wyckoff Detection Module - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning
**Source:** User-provided via discuss-phase prompt

<domain>
## Phase Boundary

Implement Wyckoff accumulation/distribution pattern detection for market structure analysis. Single module at `src/backend/analysis/wyckoff.py` with one entry point function and a Pydantic output model.

</domain>

<decisions>
## Implementation Decisions

### Module Structure
- File: `src/backend/analysis/wyckoff.py`
- Single entry point: `detect_wyckoff(df: DataFrame) -> WyckoffAnalysis`

### Pydantic Model: WyckoffAnalysis
- `phase`: Current Wyckoff phase (Accumulation A-E or Distribution A-E)
- `phase_confidence`: 0-100 confidence score
- `events`: List of detected events with candle index and description
- `volume_confirms`: Boolean - volume confirming or diverging from price
- `analysis_notes`: String with additional analysis context

### Phase Detection Logic
- **Phase A (Stopping Action)**: High volume climax candle + price reversal
- **Phase B (Building Cause)**: Range-bound, volume declining
- **Phase C (Test)**: Spring (accumulation) or Upthrust (distribution)
- **Phase D (SOS/SOW)**: Strong move out of range with expanding volume
- **Phase E (Trending)**: Markup or markdown phase

### Event Detection Rules
- **Spring**: Price closes below prior support then recovers above it within 1-3 candles, volume on dip below 20-period average
- **Upthrust**: Mirror of spring at resistance
- **SOS (Sign of Strength)**: Closes above resistance with volume > 1.5x average
- **SOW (Sign of Weakness)**: Closes below support with volume > 1.5x average
- **Creek/Ice Break**: Not explicitly specified - Claude's discretion

### Integration Requirements
- Use existing support/resistance levels from `indicators.py` (do NOT recalculate)
- Must integrate with Phase 8 indicator infrastructure

### Claude's Discretion
- Internal helper function organization
- Specific confidence calculation algorithm
- Edge case handling (insufficient data, unclear patterns)
- Creek/ice break detection implementation details

</decisions>

<specifics>
## Specific Ideas

- Volume threshold: 1.5x average for SOS/SOW, below average for spring/upthrust
- Recovery window: 1-3 candles for spring/upthrust
- Use 20-period volume average as baseline

</specifics>

<deferred>
## Deferred Ideas

None - this phase is self-contained.

</deferred>

---

*Phase: 10-wyckoff-detection-module*
*Context gathered: 2026-02-27 via user prompt*
