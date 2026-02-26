"""Smoke tests for Risk Agent."""
import json
import pytest
from unittest.mock import patch

from src.backend.agents.risk_agent import RiskAgent
from src.backend.models.risk_output import RiskOutput


class TestRiskAgent:
    """Smoke tests for RiskAgent."""

    def test_risk_agent_smoke(self):
        """Verify RiskAgent can instantiate and return valid RiskOutput."""
        response = {
            "symbol": "BTC",
            "current_price": 65000.0,
            "trade_direction": "long",
            "entry_zone": {
                "low": 64000.0,
                "high": 65500.0,
                "ideal": 64500.0,
                "entry_reasoning": "Support zone with good R:R"
            },
            "stop_loss": {
                "price": 62000.0,
                "type": "structure",
                "distance_percent": 3.85,
                "reasoning": "Below major support"
            },
            "take_profits": {
                "tp1": {
                    "price": 70000.0,
                    "rr_ratio": 2.2,
                    "reasoning": "Previous resistance"
                },
                "tp2": {
                    "price": 75000.0,
                    "rr_ratio": 4.0,
                    "reasoning": "All-time high area"
                }
            },
            "risk_reward": {
                "to_tp1": 2.2,
                "to_tp2": 4.0,
                "meets_minimum": True
            },
            "position_sizing": {
                "max_risk_percent": 2.0,
                "suggested_position_percent": 5.0,
                "reasoning": "Standard position size"
            },
            "funding_filter": {
                "current_funding": 0.01,
                "funding_bias": "neutral",
                "warning": None
            },
            "three_laws_check": {
                "law_1_risk": "pass",
                "law_2_rr": "pass",
                "law_3_positions": "check_current_positions",
                "overall": "approved"
            },
            "final_verdict": {
                "action": "long_spot",
                "confidence": 75,
                "notes": "Good setup with favorable R:R"
            }
        }

        agent = RiskAgent()

        with patch.object(agent, '_call_claude', return_value=json.dumps(response)):
            result = agent.analyze("BTC", {"current_price": 65000})

        # Verify result can be validated as RiskOutput
        signal = RiskOutput.model_validate(result)
        assert signal.symbol == "BTC"
        assert signal.trade_direction in ["long", "short", "avoid"]
        assert signal.three_laws_check.overall in ["approved", "rejected", "caution"]
        assert signal.risk_reward.meets_minimum is True
