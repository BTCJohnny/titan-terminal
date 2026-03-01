"""Pre-trade risk validator enforcing the 3 Laws of Trading.

NOT an LLM agent — pure deterministic validation.
Replaces the previous LLM-based RiskAgent to eliminate API costs,
latency, and non-determinism from the risk validation step.
"""
from typing import Literal, Optional

from ..config.constants import MAX_POSITIONS, MAX_RISK_PER_TRADE, MIN_RISK_REWARD
from ..models.risk_output import (
    EntryZone,
    FinalVerdict,
    PositionSizing,
    RiskOutput,
    RiskReward,
    StopLoss,
    TakeProfit,
    TakeProfits,
    ThreeLawsCheck,
)


class RiskAgent:
    """Pre-trade validator enforcing the 3 Laws of Trading.

    NOT an LLM agent — pure deterministic validation.

    3 Laws:
      Law 1: Never risk more than 2% of capital per trade
      Law 2: Minimum 3:1 risk-reward ratio required
      Law 3: Maximum 5 open positions at any time
    """

    def _derive_stop(
        self,
        entry_price: float,
        stop_price: float,
        trade_direction: Literal["long", "short"],
        sr_levels: dict,
    ) -> tuple[float, Literal["structure", "percentage"]]:
        """Derive final stop price from S/R levels.

        For long: nearest support BELOW entry. Wider stop (further from entry) wins.
        For short: nearest resistance ABOVE entry. Wider stop (further from entry) wins.

        Returns (final_stop_price, stop_type).
        """
        if trade_direction == "long":
            supports = sorted(
                [s for s in sr_levels.get("support", []) if s < entry_price],
                reverse=True,
            )
            if supports:
                sr_stop = supports[0]
                # Wider stop is further below entry — use minimum price (further away)
                final_stop = min(sr_stop, stop_price)
                return final_stop, "structure"
        else:  # short
            resistances = sorted(
                [r for r in sr_levels.get("resistance", []) if r > entry_price]
            )
            if resistances:
                sr_stop = resistances[0]
                # Wider stop is further above entry — use maximum price (further away)
                final_stop = max(sr_stop, stop_price)
                return final_stop, "structure"

        return stop_price, "percentage"

    def _derive_targets(
        self,
        entry_price: float,
        final_stop_price: float,
        trade_direction: Literal["long", "short"],
        sr_levels: dict,
    ) -> tuple[Optional[float], Optional[float]]:
        """Derive TP1 and TP2 from S/R levels.

        For long: find resistance levels that give >= 3:1 R:R.
        For short: find support levels that give >= 3:1 R:R.

        Returns (tp1_price, tp2_price) — either may be None.
        """
        risk_per_unit = abs(entry_price - final_stop_price)
        if risk_per_unit == 0:
            return None, None

        if trade_direction == "long":
            # Target levels are resistance above entry
            candidates = sorted(
                [r for r in sr_levels.get("resistance", []) if r > entry_price]
            )
        else:  # short
            # Target levels are support below entry
            candidates = sorted(
                [s for s in sr_levels.get("support", []) if s < entry_price],
                reverse=True,
            )

        valid_targets = []
        best_candidate = None  # Best available even if < 3:1

        for level in candidates:
            rr = abs(level - entry_price) / risk_per_unit
            if best_candidate is None:
                best_candidate = level
            if rr >= MIN_RISK_REWARD:
                valid_targets.append(level)

        if valid_targets:
            tp1 = valid_targets[0]
            tp2 = valid_targets[1] if len(valid_targets) > 1 else None
            return tp1, tp2
        elif best_candidate is not None:
            # Return best available but let R:R check flag it
            return best_candidate, None
        else:
            return None, None

    def _calc_rr(
        self,
        entry_price: float,
        final_stop_price: float,
        tp_price: float,
    ) -> float:
        """Calculate risk/reward ratio."""
        risk = abs(entry_price - final_stop_price)
        if risk == 0:
            return 0.0
        return abs(tp_price - entry_price) / risk

    def _minimal_rejection_output(
        self, symbol: str, entry_price: Optional[float], reasons: list[str]
    ) -> RiskOutput:
        """Build a minimal RiskOutput for hard-stop rejection cases."""
        price = entry_price or 0.0
        return RiskOutput(
            symbol=symbol,
            current_price=entry_price,
            trade_direction="avoid",
            entry_zone=EntryZone(
                low=price,
                high=price,
                ideal=price,
                entry_reasoning="Trade rejected — see rejection_reasons",
            ),
            stop_loss=StopLoss(
                price=price,
                type="percentage",
                distance_percent=0.0,
                reasoning="N/A — trade rejected",
            ),
            take_profits=TakeProfits(
                tp1=TakeProfit(
                    price=price,
                    rr_ratio=0.0,
                    reasoning="N/A — trade rejected",
                )
            ),
            risk_reward=RiskReward(
                to_tp1=0.0,
                meets_minimum=False,
            ),
            three_laws_check=ThreeLawsCheck(
                law_1_risk="fail",
                law_2_rr="fail",
                law_3_positions="fail",
                overall="rejected",
            ),
            final_verdict=FinalVerdict(
                action="avoid",
                confidence=0,
                notes="; ".join(reasons),
            ),
            approved=False,
            rejection_reasons=reasons,
        )

    def _validate(
        self,
        symbol: str,
        entry_price: float,
        stop_price: float,
        trade_direction: Literal["long", "short"],
        sr_levels: dict,
        open_position_count: int = 0,
        account_size: Optional[float] = None,
    ) -> RiskOutput:
        """Core validation logic. Assumes entry_price is a valid float."""
        rejection_reasons: list[str] = []

        # --- Derive stop from S/R levels ---
        final_stop, stop_type = self._derive_stop(
            entry_price, stop_price, trade_direction, sr_levels
        )
        risk_per_unit = abs(entry_price - final_stop)

        # --- Derive targets from S/R levels ---
        tp1_price, tp2_price = self._derive_targets(
            entry_price, final_stop, trade_direction, sr_levels
        )

        if tp1_price is None:
            rejection_reasons.append("No valid target from S/R levels")

        # --- Calculate R:R ratios ---
        rr_to_tp1 = self._calc_rr(entry_price, final_stop, tp1_price) if tp1_price else 0.0
        rr_to_tp2 = self._calc_rr(entry_price, final_stop, tp2_price) if tp2_price else None

        # --- Position sizing (only when account_size provided) ---
        position_sizing = None
        position_size_units = None
        suggested_position_percent = None

        if account_size and account_size > 0 and risk_per_unit > 0:
            position_size_units = (account_size * MAX_RISK_PER_TRADE) / risk_per_unit
            suggested_position_percent = (
                position_size_units * entry_price / account_size
            ) * 100
            position_sizing = PositionSizing(
                max_risk_percent=MAX_RISK_PER_TRADE * 100,
                suggested_position_percent=round(suggested_position_percent, 2),
                reasoning=(
                    f"Risk {MAX_RISK_PER_TRADE*100:.0f}% of ${account_size:,.0f} "
                    f"= ${account_size * MAX_RISK_PER_TRADE:,.0f} risk; "
                    f"{position_size_units:.4f} units at {risk_per_unit:.2f} stop distance"
                ),
            )

        # --- Enforce 3 Laws ---

        # Law 1: Max 2% risk per trade
        if account_size and account_size > 0 and risk_per_unit > 0 and position_size_units:
            actual_risk_amount = position_size_units * risk_per_unit
            law_1 = "pass" if actual_risk_amount <= account_size * MAX_RISK_PER_TRADE else "fail"
            if law_1 == "fail":
                rejection_reasons.append(
                    f"Law 1 violated: risk amount ${actual_risk_amount:.2f} exceeds "
                    f"2% of account (${account_size * MAX_RISK_PER_TRADE:.2f})"
                )
        else:
            # Cannot check without account_size — pass by default
            law_1 = "pass"

        # Law 2: Min 3:1 R:R
        law_2 = "pass" if rr_to_tp1 >= MIN_RISK_REWARD else "fail"
        if law_2 == "fail":
            rejection_reasons.append(
                f"Law 2 violated: R:R to TP1 is {rr_to_tp1:.2f}x "
                f"(minimum {MIN_RISK_REWARD:.0f}:1 required)"
            )

        # Law 3: Max open positions
        law_3 = "pass" if open_position_count < MAX_POSITIONS else "fail"
        if law_3 == "fail":
            rejection_reasons.append(
                f"Law 3 violated: {open_position_count} open positions "
                f"(maximum is {MAX_POSITIONS})"
            )

        approved = len(rejection_reasons) == 0
        overall = "approved" if approved else "rejected"

        # --- Determine stop distance percent ---
        stop_distance_pct = (abs(entry_price - final_stop) / entry_price) * 100

        # --- Determine stop reasoning ---
        stop_reasoning = (
            f"Nearest {'support' if trade_direction == 'long' else 'resistance'} "
            f"level at {final_stop:.2f} (structure stop)"
            if stop_type == "structure"
            else f"Proposed stop at {final_stop:.2f} (no S/R level available)"
        )

        # --- Build entry zone (±0.5% around entry) ---
        entry_spread = entry_price * 0.005
        entry_zone = EntryZone(
            low=round(entry_price - entry_spread, 4),
            high=round(entry_price + entry_spread, 4),
            ideal=entry_price,
            entry_reasoning=f"Entry at current price {entry_price:.2f} with ±0.5% zone",
        )

        # --- Build take profits ---
        tp1_obj = TakeProfit(
            price=tp1_price if tp1_price is not None else entry_price,
            rr_ratio=round(rr_to_tp1, 2),
            reasoning=(
                f"Nearest {'resistance' if trade_direction == 'long' else 'support'} "
                f"level at {tp1_price:.2f} ({rr_to_tp1:.2f}x R:R)"
                if tp1_price
                else "No valid S/R target found"
            ),
        )
        tp2_obj = None
        if tp2_price is not None:
            tp2_obj = TakeProfit(
                price=tp2_price,
                rr_ratio=round(rr_to_tp2, 2) if rr_to_tp2 else 0.0,
                reasoning=(
                    f"Second {'resistance' if trade_direction == 'long' else 'support'} "
                    f"level at {tp2_price:.2f} ({rr_to_tp2:.2f}x R:R)"
                    if rr_to_tp2
                    else f"Second target at {tp2_price:.2f}"
                ),
            )

        # --- Determine action for final verdict ---
        if approved:
            action = "long_perp" if trade_direction == "long" else "short_perp"
        else:
            action = "avoid"

        confidence = 80 if approved else 0

        return RiskOutput(
            symbol=symbol,
            current_price=entry_price,
            trade_direction=trade_direction if approved else "avoid",
            entry_zone=entry_zone,
            stop_loss=StopLoss(
                price=round(final_stop, 4),
                type=stop_type,
                distance_percent=round(stop_distance_pct, 2),
                reasoning=stop_reasoning,
            ),
            take_profits=TakeProfits(tp1=tp1_obj, tp2=tp2_obj),
            risk_reward=RiskReward(
                to_tp1=round(rr_to_tp1, 2),
                to_tp2=round(rr_to_tp2, 2) if rr_to_tp2 is not None else None,
                meets_minimum=law_2 == "pass",
            ),
            position_sizing=position_sizing,
            funding_filter=None,  # RiskAgent does not fetch funding data
            three_laws_check=ThreeLawsCheck(
                law_1_risk=law_1,
                law_2_rr=law_2,
                law_3_positions=law_3,
                overall=overall,
            ),
            final_verdict=FinalVerdict(
                action=action,
                confidence=confidence,
                notes="; ".join(rejection_reasons) if rejection_reasons else "All 3 Laws satisfied",
            ),
            approved=approved,
            rejection_reasons=rejection_reasons,
            position_size_units=round(position_size_units, 6) if position_size_units else None,
        )

    def analyze(self, symbol: str, context: dict) -> RiskOutput:
        """Entry point compatible with orchestrator.

        Extracts entry_price, stop_price, sr_levels from context dict.
        Falls back to sensible defaults when data is missing.

        Context keys used:
          current_price      -> entry_price
          suggested_bias     -> trade_direction ('bullish'/'accumulation' -> 'long',
                                                 'bearish'/'distribution' -> 'short')
          ta_data.key_levels -> sr_levels (if has support/resistance keys)
          sr_levels          -> sr_levels fallback
          open_position_count -> open_position_count
          account_size       -> account_size (optional)
        """
        entry_price: Optional[float] = context.get("current_price")

        if entry_price is None:
            return self._minimal_rejection_output(
                symbol, None, ["No entry price available"]
            )

        # Map bias string to direction
        raw_bias = context.get("suggested_bias", "long")
        if raw_bias in ("bullish", "accumulation"):
            trade_direction: Literal["long", "short"] = "long"
        elif raw_bias in ("bearish", "distribution"):
            trade_direction = "short"
        else:
            trade_direction = "long"  # default to long for neutral/unknown

        # Extract S/R levels — prefer ta_data.key_levels with support/resistance keys
        ta_data = context.get("ta_data", {})
        key_levels = ta_data.get("key_levels", {}) if ta_data else {}
        if isinstance(key_levels, dict) and (
            "support" in key_levels or "resistance" in key_levels
        ):
            sr_levels = key_levels
        else:
            sr_levels = context.get("sr_levels", {"support": [], "resistance": []})

        open_position_count: int = context.get("open_position_count", 0)
        account_size: Optional[float] = context.get("account_size")

        # Derive a default stop from S/R or use 2% below entry as fallback
        proposed_stop = (
            entry_price * 0.98 if trade_direction == "long" else entry_price * 1.02
        )

        return self._validate(
            symbol=symbol,
            entry_price=entry_price,
            stop_price=proposed_stop,
            trade_direction=trade_direction,
            sr_levels=sr_levels,
            open_position_count=open_position_count,
            account_size=account_size,
        )
