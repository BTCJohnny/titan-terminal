"""Smoke tests for Nansen Agent."""
import json
import pytest
from unittest.mock import patch

from src.backend.agents.nansen_agent import NansenAgent
from src.backend.models.nansen_signal import NansenSignal


class TestNansenAgent:
    """Smoke tests for NansenAgent."""

    def test_nansen_agent_smoke(self):
        """Verify NansenAgent can instantiate and return valid NansenSignal."""
        response = {
            "symbol": "BTC",
            "exchange_flows": {
                "net_direction": "outflow",
                "magnitude": "high",
                "interpretation": "Bullish - coins leaving exchanges",
                "confidence": 75
            },
            "fresh_wallets": {
                "activity_level": "medium",
                "trend": "increasing",
                "notable_count": 150,
                "interpretation": "Growing accumulation wallets"
            },
            "smart_money": {
                "direction": "accumulating",
                "confidence": 80,
                "notable_wallets": ["0xabc...123"],
                "interpretation": "Smart money accumulating"
            },
            "top_pnl": {
                "traders_bias": "bullish",
                "average_position": "long",
                "confidence": 70,
                "interpretation": "Top traders positioned long"
            },
            "whale_activity": {
                "summary": "Large accumulation by whales",
                "notable_transactions": ["txn_123"],
                "net_flow": "accumulating",
                "confidence": 85
            },
            "overall_signal": {
                "bias": "bullish",
                "confidence": 78,
                "key_insights": ["Strong exchange outflows", "Smart money accumulating"]
            }
        }

        agent = NansenAgent()

        with patch.object(agent, '_call_claude', return_value=json.dumps(response)):
            result = agent.analyze("BTC", {"current_price": 65000})

        # Verify result can be validated as NansenSignal
        signal = NansenSignal.model_validate(result)
        assert signal.symbol == "BTC"
        assert signal.exchange_flows.net_direction in ["inflow", "outflow", "neutral"]
        assert signal.smart_money.direction in ["accumulating", "distributing", "neutral"]
        assert 0 <= signal.overall_signal.confidence <= 100
