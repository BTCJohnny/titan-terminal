"""Tests for Orchestrator with Mentor SDK synthesis."""
import json
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from src.backend.agents.orchestrator import Orchestrator
from src.backend.models.orchestrator_output import OrchestratorOutput
from src.backend.models.nansen_signal import (
    NansenSignal, ExchangeFlows, FreshWallets, SmartMoney,
    TopPnL, WhaleActivity, OnChainOverall
)
from src.backend.models.telegram_signal import TelegramSignal
from src.backend.models.risk_output import (
    RiskOutput, EntryZone, StopLoss, TakeProfit, TakeProfits,
    RiskReward, PositionSizing, ThreeLawsCheck, FinalVerdict
)


def _make_risk_output(symbol="BTC"):
    """Create a valid RiskOutput instance for use in tests."""
    return RiskOutput(
        symbol=symbol,
        current_price=65000.0,
        trade_direction="long",
        approved=True,
        rejection_reasons=[],
        entry_zone=EntryZone(low=64000, high=65500, ideal=64500, entry_reasoning="S/R zone"),
        stop_loss=StopLoss(price=63000, type="structure", distance_percent=3.08, reasoning="Below support"),
        take_profits=TakeProfits(
            tp1=TakeProfit(price=72000, rr_ratio=3.5, reasoning="Resistance level"),
            tp2=TakeProfit(price=75000, rr_ratio=5.0, reasoning="Major resistance"),
        ),
        risk_reward=RiskReward(to_tp1=3.5, to_tp2=5.0, meets_minimum=True),
        position_sizing=None,
        funding_filter=None,
        three_laws_check=ThreeLawsCheck(law_1_risk="pass", law_2_rr="pass", law_3_positions="pass", overall="approved"),
        final_verdict=FinalVerdict(action="long_spot", confidence=75, notes="Good setup"),
        position_size_units=None,
    )


def _make_nansen_signal():
    return NansenSignal(
        symbol="BTC",
        exchange_flows=ExchangeFlows(net_direction="outflow", magnitude="high", interpretation="test", confidence=70),
        fresh_wallets=FreshWallets(activity_level="medium", trend="stable", notable_count=0, interpretation="test"),
        smart_money=SmartMoney(direction="accumulating", confidence=75, notable_wallets=[], interpretation="test"),
        top_pnl=TopPnL(traders_bias="bullish", average_position="long", confidence=70, interpretation="test"),
        whale_activity=WhaleActivity(summary="test", notable_transactions=[], net_flow="accumulating", confidence=70),
        overall_signal=OnChainOverall(bias="bullish", confidence=70, key_insights=["Smart money accumulating"]),
        signal_count_bullish=4,
        signal_count_bearish=1,
        reasoning="4 of 5 signals bullish.",
    )


def _make_telegram_signal():
    return TelegramSignal(
        symbol="BTC",
        signals_found=0,
        active_signals=0,
        relevant_signals=[],
        overall_sentiment="neutral",
        confluence_count=0,
        confidence=0,
        avg_confidence=0.0,
        reasoning="No signals found.",
    )


def _make_mentor_response(direction="BULLISH", confidence=78, action="Long Spot"):
    """Build mock Anthropic API response for Mentor call."""
    mentor_json = json.dumps({
        "direction": direction,
        "confidence": confidence,
        "suggested_action": action,
        "accumulation_score": 72,
        "distribution_score": 28,
        "reasoning": "Wyckoff shows accumulation spring. Nansen confirms smart money inflow. TA ensemble bullish across timeframes. Risk approved with 3.5:1 R:R. Full conviction on this setup."
    })
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=mentor_json)]
    return mock_response


class TestOrchestrator:
    """Tests for Orchestrator with Mentor SDK synthesis."""

    def test_orchestrator_instantiates_without_mentor_critic(self):
        """MentorCriticAgent is no longer initialized."""
        orchestrator = Orchestrator()
        assert not hasattr(orchestrator, 'mentor') or not hasattr(getattr(orchestrator, 'mentor', None), 'critique')
        assert hasattr(orchestrator, 'mentor_client')

    def test_analyze_symbol_returns_orchestrator_output(self):
        """analyze_symbol returns OrchestratorOutput (not raw dict)."""
        orchestrator = Orchestrator()

        with patch.object(orchestrator.wyckoff, 'analyze', return_value={"composite_analysis": {"overall_phase": "Phase C", "overall_bias": "accumulation", "confluence_score": 75}}), \
             patch.object(orchestrator.nansen, 'analyze', return_value=_make_nansen_signal()), \
             patch.object(orchestrator.telegram, 'analyze', return_value=_make_telegram_signal()), \
             patch.object(orchestrator.weekly_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 75}}), \
             patch.object(orchestrator.daily_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 70}}), \
             patch.object(orchestrator.fourhour_subagent, 'analyze', return_value={"overall": {"bias": "neutral", "confidence": 55}}), \
             patch.object(orchestrator.ta_mentor, 'synthesize', return_value={"unified_signal": {"bias": "bullish"}, "overall": {"confidence": 70, "notes": "Bullish"}, "key_levels": {}}), \
             patch.object(orchestrator.risk, 'analyze', return_value=_make_risk_output("BTC")), \
             patch.object(orchestrator.mentor_client.messages, 'create', return_value=_make_mentor_response()), \
             patch('src.backend.agents.orchestrator.get_similar_patterns', return_value=[]), \
             patch('src.backend.agents.orchestrator.get_pattern_stats', return_value=None), \
             patch('src.backend.agents.orchestrator.record_signal', return_value=1), \
             patch.object(orchestrator, '_log_to_obsidian'):
            result = orchestrator.analyze_symbol("BTC", {"current_price": 65000})

        assert isinstance(result, OrchestratorOutput)
        assert result.symbol == "BTC"
        assert result.direction == "BULLISH"
        assert result.confidence == 78
        assert result.reasoning is not None
        assert len(result.reasoning) > 0
        assert result.suggested_action == "Long Spot"

    def test_mentor_sdk_call_uses_correct_model(self):
        """Mentor SDK call uses settings.MENTOR_MODEL."""
        orchestrator = Orchestrator()

        with patch.object(orchestrator.wyckoff, 'analyze', return_value={"composite_analysis": {"overall_phase": "Phase C", "overall_bias": "accumulation", "confluence_score": 75}}), \
             patch.object(orchestrator.nansen, 'analyze', return_value=_make_nansen_signal()), \
             patch.object(orchestrator.telegram, 'analyze', return_value=_make_telegram_signal()), \
             patch.object(orchestrator.weekly_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 75}}), \
             patch.object(orchestrator.daily_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 70}}), \
             patch.object(orchestrator.fourhour_subagent, 'analyze', return_value={"overall": {"bias": "neutral", "confidence": 55}}), \
             patch.object(orchestrator.ta_mentor, 'synthesize', return_value={"unified_signal": {"bias": "bullish"}, "overall": {"confidence": 70, "notes": "Bullish"}, "key_levels": {}}), \
             patch.object(orchestrator.risk, 'analyze', return_value=_make_risk_output("BTC")), \
             patch.object(orchestrator.mentor_client.messages, 'create', return_value=_make_mentor_response()) as mock_create, \
             patch('src.backend.agents.orchestrator.get_similar_patterns', return_value=[]), \
             patch('src.backend.agents.orchestrator.get_pattern_stats', return_value=None), \
             patch('src.backend.agents.orchestrator.record_signal', return_value=1), \
             patch.object(orchestrator, '_log_to_obsidian'):
            orchestrator.analyze_symbol("BTC", {"current_price": 65000})

        # Verify the SDK call used correct model and temperature
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args
        assert call_kwargs.kwargs.get('model') or call_kwargs[1].get('model')
        assert call_kwargs.kwargs.get('temperature', call_kwargs[1].get('temperature')) == 0.2

    def test_high_conviction_signal_logs_to_obsidian(self):
        """Signals with confidence > 75 trigger Obsidian logging."""
        orchestrator = Orchestrator()

        with patch.object(orchestrator.wyckoff, 'analyze', return_value={"composite_analysis": {"overall_phase": "Phase C", "overall_bias": "accumulation", "confluence_score": 75}}), \
             patch.object(orchestrator.nansen, 'analyze', return_value=_make_nansen_signal()), \
             patch.object(orchestrator.telegram, 'analyze', return_value=_make_telegram_signal()), \
             patch.object(orchestrator.weekly_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 75}}), \
             patch.object(orchestrator.daily_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 70}}), \
             patch.object(orchestrator.fourhour_subagent, 'analyze', return_value={"overall": {"bias": "neutral", "confidence": 55}}), \
             patch.object(orchestrator.ta_mentor, 'synthesize', return_value={"unified_signal": {"bias": "bullish"}, "overall": {"confidence": 70, "notes": "Bullish"}, "key_levels": {}}), \
             patch.object(orchestrator.risk, 'analyze', return_value=_make_risk_output("BTC")), \
             patch.object(orchestrator.mentor_client.messages, 'create', return_value=_make_mentor_response(confidence=80)), \
             patch('src.backend.agents.orchestrator.get_similar_patterns', return_value=[]), \
             patch('src.backend.agents.orchestrator.get_pattern_stats', return_value=None), \
             patch('src.backend.agents.orchestrator.record_signal', return_value=1), \
             patch.object(orchestrator, '_log_to_obsidian') as mock_obsidian:
            result = orchestrator.analyze_symbol("BTC", {"current_price": 65000})

        # Confidence 80 > 75 threshold — should log
        mock_obsidian.assert_called_once()

    def test_low_conviction_signal_skips_obsidian(self):
        """Signals with confidence <= 75 do NOT trigger Obsidian logging."""
        orchestrator = Orchestrator()

        with patch.object(orchestrator.wyckoff, 'analyze', return_value={"composite_analysis": {"overall_phase": "Phase C", "overall_bias": "accumulation", "confluence_score": 75}}), \
             patch.object(orchestrator.nansen, 'analyze', return_value=_make_nansen_signal()), \
             patch.object(orchestrator.telegram, 'analyze', return_value=_make_telegram_signal()), \
             patch.object(orchestrator.weekly_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 75}}), \
             patch.object(orchestrator.daily_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 70}}), \
             patch.object(orchestrator.fourhour_subagent, 'analyze', return_value={"overall": {"bias": "neutral", "confidence": 55}}), \
             patch.object(orchestrator.ta_mentor, 'synthesize', return_value={"unified_signal": {"bias": "bullish"}, "overall": {"confidence": 70, "notes": "Bullish"}, "key_levels": {}}), \
             patch.object(orchestrator.risk, 'analyze', return_value=_make_risk_output("BTC")), \
             patch.object(orchestrator.mentor_client.messages, 'create', return_value=_make_mentor_response(confidence=50)), \
             patch('src.backend.agents.orchestrator.get_similar_patterns', return_value=[]), \
             patch('src.backend.agents.orchestrator.get_pattern_stats', return_value=None), \
             patch('src.backend.agents.orchestrator.record_signal', return_value=1), \
             patch.object(orchestrator, '_log_to_obsidian') as mock_obsidian:
            result = orchestrator.analyze_symbol("BTC", {"current_price": 65000})

        mock_obsidian.assert_not_called()
