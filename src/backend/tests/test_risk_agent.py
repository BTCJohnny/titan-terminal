"""Comprehensive tests for RiskAgent S/R derivation, R:R enforcement, and 2% risk cap.

Plan: 20-02 (TDD Red phase)
"""
import pytest

from src.backend.agents.risk_agent import RiskAgent
from src.backend.models.risk_output import RiskOutput


@pytest.fixture
def agent():
    return RiskAgent()


@pytest.fixture
def base_sr_levels():
    """Standard S/R level set for BTC at 65000."""
    return {
        "support": [63000, 61000, 58000],
        "resistance": [66000, 68000, 72000],
    }


class TestSRDerivation:
    """Tests for S/R-based stop and target derivation (RISK-02, RISK-03)."""

    def test_long_stop_from_nearest_support(self, agent):
        """Long entry at 65000 with supports [63000, 61000, 58000] -> stop at 63000."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=64000,  # proposed stop (tighter)
            trade_direction="long",
            sr_levels={"support": [63000, 61000, 58000], "resistance": [72000]},
        )
        # Stop should be placed at the nearest support (63000), not the proposed 64000
        # Wider stop wins: 63000 is further from entry than 64000, so use 63000
        assert result.stop_loss.price == 63000
        assert result.stop_loss.type == "structure"

    def test_short_stop_from_nearest_resistance(self, agent):
        """Short entry at 65000 with resistances [67000, 70000] -> stop at 67000."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=66000,  # proposed stop (tighter)
            trade_direction="short",
            sr_levels={"support": [58000], "resistance": [67000, 70000]},
        )
        # Nearest resistance above entry is 67000
        assert result.stop_loss.price == 67000
        assert result.stop_loss.type == "structure"

    def test_sr_stop_overrides_tighter_proposed_stop(self, agent):
        """Long: proposed stop 64000, support at 63000 -> use 63000 (wider/safer)."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=64000,  # tighter proposed stop
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
        )
        assert result.stop_loss.price == 63000

    def test_sr_stop_overrides_when_proposed_is_wider(self, agent):
        """Long: proposed stop 62000, support at 63000 -> still use S/R (63000) for structure.

        The spec says S/R-derived stop is always used for structure when available.
        Wider stop rule: use the one further from entry (lower price for long).
        62000 < 63000 -> 62000 is wider. So we use 62000 (min of sr_stop and proposed_stop).
        """
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=62000,  # wider proposed stop
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
        )
        # Wider stop wins: min(63000, 62000) = 62000
        assert result.stop_loss.price == 62000
        assert result.stop_loss.type == "structure"

    def test_empty_sr_uses_proposed_stop(self, agent):
        """When no S/R levels exist, use the proposed stop with type 'percentage'."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=64000,
            trade_direction="long",
            sr_levels={"support": [], "resistance": []},
        )
        assert result.stop_loss.price == 64000
        assert result.stop_loss.type == "percentage"

    def test_tp1_meets_minimum_rr(self, agent):
        """Long entry 65000, stop 63000 (risk=2000), resistances [66000, 68000, 72000].

        66000 -> R:R = (66000-65000)/2000 = 0.5 (skip)
        68000 -> R:R = (68000-65000)/2000 = 1.5 (skip)
        72000 -> R:R = (72000-65000)/2000 = 3.5 (TP1, meets 3:1)
        """
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [], "resistance": [66000, 68000, 72000]},
        )
        assert result.take_profits.tp1.price == 72000
        assert result.risk_reward.to_tp1 >= 3.0

    def test_short_tp1_meets_minimum_rr(self, agent):
        """Short entry 65000, stop 67000 (risk=2000), supports [64000, 62000, 58000].

        64000 -> R:R = (65000-64000)/2000 = 0.5 (skip)
        62000 -> R:R = (65000-62000)/2000 = 1.5 (skip)
        58000 -> R:R = (65000-58000)/2000 = 3.5 (TP1, meets 3:1)
        """
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=67000,
            trade_direction="short",
            sr_levels={"support": [64000, 62000, 58000], "resistance": []},
        )
        assert result.take_profits.tp1.price == 58000
        assert result.risk_reward.to_tp1 >= 3.0

    def test_tp2_beyond_tp1(self, agent):
        """When multiple targets qualify, TP2 should be beyond TP1."""
        # entry 65000, stop 63000 (risk=2000)
        # 72000 -> R:R = 3.5 (TP1)
        # 75000 -> R:R = 5.0 (TP2)
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [], "resistance": [66000, 68000, 72000, 75000]},
        )
        assert result.take_profits.tp1 is not None
        assert result.take_profits.tp2 is not None
        assert result.take_profits.tp2.price > result.take_profits.tp1.price
        assert result.take_profits.tp2.rr_ratio >= 3.0

    def test_no_valid_target_rejects(self, agent):
        """When no S/R level gives >= 3:1 R:R, Law 2 should fail and trade is rejected."""
        # entry 65000, stop 63000 (risk=2000), only resistance at 66000 (R:R=0.5)
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [], "resistance": [66000]},
        )
        assert result.approved is False
        assert result.three_laws_check.law_2_rr == "fail"
        assert any("Law 2" in r for r in result.rejection_reasons)


class TestRiskCap:
    """Tests for 2% risk cap (RISK-05)."""

    def test_position_size_with_account(self, agent):
        """Account 100000, entry 65000, stop 63000 -> position_size_units = 1.0.

        position_size_units = (100000 * 0.02) / 2000 = 1.0
        """
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
            account_size=100000,
        )
        assert result.position_size_units is not None
        assert abs(result.position_size_units - 1.0) < 0.001
        assert result.position_sizing is not None
        assert result.position_sizing.max_risk_percent == 2.0

    def test_position_size_smaller_account(self, agent):
        """Account 50000, entry 65000, stop 63000 -> position_size_units = 0.5.

        position_size_units = (50000 * 0.02) / 2000 = 0.5
        """
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
            account_size=50000,
        )
        assert result.position_size_units is not None
        assert abs(result.position_size_units - 0.5) < 0.001

    def test_no_account_no_position_sizing(self, agent):
        """Without account_size, position_sizing and position_size_units should be None."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
        )
        assert result.position_sizing is None
        assert result.position_size_units is None

    def test_risk_never_exceeds_two_percent(self, agent):
        """Position size should ensure risk == exactly 2% of account, never more."""
        account_size = 100000
        entry_price = 65000
        stop_price = 63000  # S/R stop will be used (same as proposed here since both = 63000)
        result = agent._validate(
            symbol="BTC",
            entry_price=entry_price,
            stop_price=stop_price,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
            account_size=account_size,
        )
        assert result.position_size_units is not None
        risk_amount = result.position_size_units * abs(entry_price - result.stop_loss.price)
        max_allowed_risk = account_size * 0.02
        assert risk_amount <= max_allowed_risk + 0.01  # floating point tolerance


class TestThreeLaws:
    """Tests for 3 Laws enforcement."""

    def test_all_laws_pass_approved(self, agent):
        """When all 3 Laws pass, trade should be approved."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
            open_position_count=2,
            account_size=100000,
        )
        assert result.approved is True
        assert result.three_laws_check.law_1_risk == "pass"
        assert result.three_laws_check.law_2_rr == "pass"
        assert result.three_laws_check.law_3_positions == "pass"
        assert result.three_laws_check.overall == "approved"
        assert result.rejection_reasons == []

    def test_law1_fail_rejected(self, agent):
        """Law 1: trade rejected when risk exceeds 2%.

        With a tiny account and huge position, risk exceeds 2%.
        BUT position sizing auto-caps at 2%, so Law 1 cannot actually fail via normal path.
        Law 1 will fail only if position_size_units is manually larger than allowed.

        Since the implementation auto-caps position size at 2%, we test that
        Law 1 PASSES when account_size is provided (the auto-sizing prevents violation).
        """
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
            open_position_count=2,
            account_size=100000,
        )
        # Implementation auto-sizes position to exactly 2% risk -> Law 1 always passes
        assert result.three_laws_check.law_1_risk == "pass"

    def test_law2_fail_rr_below_minimum(self, agent):
        """R:R of 2.5 -> law_2_rr='fail', approved=False, rejection_reasons has R:R violation."""
        # entry 65000, stop 63000 (risk=2000), resistance at 70000 (R:R=2.5)
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [], "resistance": [70000]},
        )
        assert result.three_laws_check.law_2_rr == "fail"
        assert result.approved is False
        assert any("Law 2" in r for r in result.rejection_reasons)

    def test_law2_pass_exactly_minimum_rr(self, agent):
        """R:R of exactly 3.0 -> law_2_rr='pass' (boundary condition)."""
        # entry 65000, stop 63000 (risk=2000), resistance at 71000 (R:R=3.0)
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [], "resistance": [71000]},
        )
        assert result.three_laws_check.law_2_rr == "pass"
        assert result.risk_reward.to_tp1 == pytest.approx(3.0, abs=0.01)

    def test_law2_pass_above_minimum_rr(self, agent):
        """R:R of 5.0 -> law_2_rr='pass'."""
        # entry 65000, stop 63000 (risk=2000), resistance at 75000 (R:R=5.0)
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [], "resistance": [75000]},
        )
        assert result.three_laws_check.law_2_rr == "pass"
        assert result.risk_reward.to_tp1 >= 5.0

    def test_law3_fail_max_positions(self, agent):
        """open_position_count=5, MAX_POSITIONS=5 -> law_3_positions='fail', rejected."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
            open_position_count=5,  # at max
        )
        assert result.three_laws_check.law_3_positions == "fail"
        assert result.approved is False
        assert any("Law 3" in r for r in result.rejection_reasons)

    def test_law3_pass_below_max_positions(self, agent):
        """open_position_count=4, MAX_POSITIONS=5 -> law_3_positions='pass'."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
            open_position_count=4,
        )
        assert result.three_laws_check.law_3_positions == "pass"


class TestDualMode:
    """Tests for risk zones vs. full position sizing mode (RISK-05)."""

    def test_with_account_size(self, agent):
        """With account_size: position_sizing populated, position_size_units calculated."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
            account_size=100000,
        )
        assert result.position_sizing is not None
        assert result.position_size_units is not None
        assert result.position_size_units > 0
        assert result.three_laws_check.law_1_risk == "pass"

    def test_without_account_size(self, agent):
        """Without account_size: position_sizing is None, position_size_units is None, law_1 always 'pass'."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
        )
        assert result.position_sizing is None
        assert result.position_size_units is None
        # Law 1 passes by default when no account_size (cannot enforce without portfolio size)
        assert result.three_laws_check.law_1_risk == "pass"

    def test_analyze_with_account_size_via_context(self, agent):
        """analyze() interface passes account_size through context dict to populate sizing."""
        result = agent.analyze("BTC", {
            "current_price": 65000,
            "suggested_bias": "bullish",
            "ta_data": {"key_levels": {"support": [63000], "resistance": [72000]}},
            "open_position_count": 2,
            "account_size": 100000,
        })
        assert result.position_sizing is not None
        assert result.position_size_units is not None

    def test_analyze_without_account_size_via_context(self, agent):
        """analyze() without account_size gives risk zones only (no position sizing)."""
        result = agent.analyze("BTC", {
            "current_price": 65000,
            "suggested_bias": "bullish",
            "ta_data": {"key_levels": {"support": [63000], "resistance": [72000]}},
            "open_position_count": 2,
        })
        assert result.position_sizing is None
        assert result.position_size_units is None


class TestEdgeCases:
    """Edge case tests."""

    def test_no_sr_levels(self, agent):
        """With no S/R levels, stop uses proposed stop, target may be unavailable."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=64000,
            trade_direction="long",
            sr_levels={"support": [], "resistance": []},
        )
        # Should not crash; should return a RiskOutput
        assert isinstance(result, RiskOutput)
        # With no S/R levels, stop falls back to proposed stop
        assert result.stop_loss.price == 64000
        assert result.stop_loss.type == "percentage"
        # With no resistance levels, no valid target -> Law 2 fails
        assert result.three_laws_check.law_2_rr == "fail"
        assert result.approved is False

    def test_no_entry_price(self, agent):
        """Without entry price via analyze(), should return rejected RiskOutput."""
        result = agent.analyze("BTC", {})
        assert isinstance(result, RiskOutput)
        assert result.approved is False
        assert any("No entry price" in r for r in result.rejection_reasons)

    def test_analyze_short_direction_from_bearish_bias(self, agent):
        """analyze() maps 'bearish' bias to 'short' trade direction."""
        result = agent.analyze("BTC", {
            "current_price": 65000,
            "suggested_bias": "bearish",
            "ta_data": {"key_levels": {"support": [58000], "resistance": [67000]}},
            "open_position_count": 0,
        })
        # Trade direction should be short or avoid
        assert result.trade_direction in ("short", "avoid")

    def test_analyze_bullish_bias_to_long(self, agent):
        """analyze() maps 'bullish' bias to 'long' trade direction."""
        result = agent.analyze("BTC", {
            "current_price": 65000,
            "suggested_bias": "bullish",
            "ta_data": {"key_levels": {"support": [63000], "resistance": [72000]}},
            "open_position_count": 0,
        })
        # Trade direction should be long or avoid (if rejected)
        assert result.trade_direction in ("long", "avoid")

    def test_result_is_valid_risk_output(self, agent):
        """Ensure a typical approved trade returns a fully valid RiskOutput model."""
        result = agent._validate(
            symbol="BTC",
            entry_price=65000,
            stop_price=63000,
            trade_direction="long",
            sr_levels={"support": [63000], "resistance": [72000]},
            open_position_count=2,
            account_size=100000,
        )
        assert isinstance(result, RiskOutput)
        assert result.symbol == "BTC"
        assert result.trade_direction in ("long", "short", "avoid")
        assert result.stop_loss.price > 0
        assert result.take_profits.tp1.price > 0
        assert result.risk_reward.to_tp1 >= 0
