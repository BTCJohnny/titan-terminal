"""Smoke tests for Orchestrator agent."""
import json
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock

from src.backend.agents.orchestrator import Orchestrator
from src.backend.models.orchestrator_output import OrchestratorOutput
from src.backend.models.nansen_signal import (
    NansenSignal, ExchangeFlows, FreshWallets, SmartMoney,
    TopPnL, WhaleActivity, OnChainOverall
)
from src.backend.models.telegram_signal import TelegramSignal


class TestOrchestrator:
    """Smoke tests for Orchestrator."""

    def test_orchestrator_smoke(self):
        """Verify Orchestrator can instantiate and return valid OrchestratorOutput."""
        # Create expected final output structure
        expected_output = {
            "symbol": "BTC",
            "signal_id": 1,
            "timestamp": datetime.now().isoformat(),
            "accumulation_score": 75,
            "distribution_score": 25,
            "confidence": 70,
            "wyckoff_phase": "Phase C - Spring",
            "wyckoff_summary": "Accumulation with spring detected",
            "nansen_summary": ["Smart money accumulating", "Exchange outflows"],
            "ta_summary": "Bullish across timeframes",
            "telegram_signals": [],
            "suggested_action": "Long Spot",
            "entry_zone": {"low": 64000.0, "high": 65500.0, "ideal": 64500.0},
            "stop_loss": 62000.0,
            "tp1": 70000.0,
            "tp2": 75000.0,
            "risk_reward": 2.5,
            "key_levels": {"support": 62000.0, "resistance": 70000.0, "invalidation": 60000.0},
            "three_laws_check": {
                "law_1_risk": "pass",
                "law_2_rr": "pass",
                "law_3_positions": "check_current_positions",
                "overall": "approved"
            },
            "learning_context": "Past similar signals: 3/5 wins",
            "mentor": {
                "verdict": "proceed",
                "concerns": [],
                "notes": "Good setup"
            }
        }

        orchestrator = Orchestrator()

        # Build NansenSignal Pydantic model for mock (orchestrator uses attribute access)
        mock_nansen_signal = NansenSignal(
            symbol="BTC",
            exchange_flows=ExchangeFlows(net_direction="outflow", magnitude="high", interpretation="test", confidence=70),
            fresh_wallets=FreshWallets(activity_level="medium", trend="stable", notable_count=0, interpretation="test"),
            smart_money=SmartMoney(direction="accumulating", confidence=75, notable_wallets=[], interpretation="test"),
            top_pnl=TopPnL(traders_bias="bullish", average_position="long", confidence=70, interpretation="test"),
            whale_activity=WhaleActivity(summary="test", notable_transactions=[], net_flow="accumulating", confidence=70),
            overall_signal=OnChainOverall(bias="bullish", confidence=70, key_insights=[]),
            signal_count_bullish=4,
            signal_count_bearish=1,
            reasoning="4 of 5 signals bullish.",
        )

        # Build TelegramSignal Pydantic model for mock (orchestrator uses attribute access)
        mock_telegram_signal = TelegramSignal(
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

        # Mock all specialist agents and DB calls
        with patch.object(orchestrator.wyckoff, 'analyze', return_value={"composite_analysis": {"overall_phase": "Phase C", "overall_bias": "accumulation", "confluence_score": 75}}):
            with patch.object(orchestrator.nansen, 'analyze', return_value=mock_nansen_signal):
                with patch.object(orchestrator.telegram, 'analyze', return_value=mock_telegram_signal):
                    with patch.object(orchestrator.weekly_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 75}}):
                        with patch.object(orchestrator.daily_subagent, 'analyze', return_value={"overall": {"bias": "bullish", "confidence": 70}}):
                            with patch.object(orchestrator.fourhour_subagent, 'analyze', return_value={"overall": {"bias": "neutral", "confidence": 55}}):
                                with patch.object(orchestrator.ta_mentor, 'synthesize', return_value={"unified_signal": {"bias": "bullish"}, "overall": {"confidence": 70, "notes": "Bullish"}, "key_levels": {}}):
                                    with patch.object(orchestrator.risk, 'analyze', return_value={"final_verdict": {"action": "long_spot", "confidence": 75}, "entry_zone": {}, "stop_loss": {}, "take_profits": {}, "risk_reward": {}, "three_laws_check": {}}):
                                        with patch.object(orchestrator.mentor, 'critique', return_value={"verdict": "proceed", "confidence_adjustment": 0, "concerns": []}):
                                            with patch('src.backend.agents.orchestrator.get_similar_patterns', return_value=[]):
                                                with patch('src.backend.agents.orchestrator.get_pattern_stats', return_value=None):
                                                    with patch('src.backend.agents.orchestrator.record_signal', return_value=1):
                                                        result = orchestrator.analyze_symbol("BTC", {"current_price": 65000})

        # The result is a dict - validate key fields exist
        assert result["symbol"] == "BTC"
        assert "accumulation_score" in result
        assert "distribution_score" in result
        assert "confidence" in result
        assert result["suggested_action"] in ["Long Spot", "Long Hyperliquid", "Short Hyperliquid", "Avoid"]

        # Validate timestamp is parseable
        datetime.fromisoformat(result["timestamp"])

    def test_orchestrator_instantiates_all_agents(self):
        """Verify Orchestrator correctly instantiates all specialist agents."""
        orchestrator = Orchestrator()

        # Check all agents are instantiated
        assert orchestrator.wyckoff is not None
        assert orchestrator.nansen is not None
        assert orchestrator.telegram is not None
        assert orchestrator.weekly_subagent is not None
        assert orchestrator.daily_subagent is not None
        assert orchestrator.fourhour_subagent is not None
        assert orchestrator.ta_mentor is not None
        assert orchestrator.risk is not None
        assert orchestrator.mentor is not None
