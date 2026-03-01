# Phase 20: Risk Agent - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning
**Source:** User-provided context (inline)

<domain>
## Phase Boundary

RiskAgent is a pre-trade validator that enforces the 3 Laws of Trading before any trade is taken. It takes proposed trade parameters plus S/R levels from the TA Ensemble and returns an approved/rejected RiskOutput with full risk parameters.

</domain>

<decisions>
## Implementation Decisions

### 3 Laws Enforcement
- Law 1: Max 2% risk per trade — reject if violated
- Law 2: Min 3:1 reward-to-risk ratio — reject if violated
- Law 3: Max 5 open positions — reject if violated
- If ANY Law is violated, reject the trade and return the reason
- Do NOT silently pass bad trades

### Scope Boundary
- RiskAgent is a pre-trade validator ONLY
- Does NOT manage stops during live trades (no move-to-BE logic)
- Move-to-breakeven belongs in a future paper trading engine

### Input
- Proposed entry price
- Stop loss price
- Account size (optional — enables position sizing)
- Current open position count
- S/R levels array (already computed by TA Ensemble indicators module)

### Output
- Valid RiskOutput Pydantic model (already exists in src/backend/models/)
- Contains: entry zone, stop, TP1, TP2, position size (if account size provided), R:R ratio, approved (bool), rejection reason (if failed)

### Stop & Target Derivation
- Stops and targets MUST be derived from S/R levels from TA data
- NOT arbitrary ATR multiples
- TP1 = nearest S/R level giving at least 3:1 R:R
- TP2 = next S/R level beyond TP1

### Claude's Discretion
- Internal method structure and helper functions
- Error handling for edge cases (empty S/R arrays, etc.)
- How to select the best stop from S/R levels vs. using the proposed stop

</decisions>

<specifics>
## Specific Ideas

- RiskOutput Pydantic model already exists at src/backend/models/risk_output.py — wire it in, don't recreate
- S/R levels come from the shared indicators module (src/backend/analysis/indicators.py)
- Risk constants already in src/backend/config/constants.py (MAX_RISK_PER_TRADE=0.02, MIN_RISK_REWARD=3.0, MAX_POSITIONS=5)

</specifics>

<deferred>
## Deferred Ideas

- Move-to-breakeven logic (future paper trading engine)
- Dynamic position sizing based on conviction score
- Portfolio-level risk aggregation across open positions

</deferred>

### Test Coverage Requirements
- Approved trade (all 3 Laws pass)
- Rejected: Law 1 violation (risk > 2%)
- Rejected: Law 2 violation (R:R < 3:1)
- Rejected: Law 3 violation (max positions exceeded)
- No account size provided (risk zones only mode)
- No valid S/R levels available (edge case)

---

*Phase: 20-risk-agent*
*Context gathered: 2026-03-01 via user-provided inline context*
