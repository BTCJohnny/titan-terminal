"""Smoke tests for TAMentor agent."""
import json
import pytest
from unittest.mock import patch

from src.backend.agents.ta_ensemble import TAMentor
from src.backend.models.ta_mentor_signal import TAMentorSignal


class TestTAMentor:
    """Smoke tests for TAMentor."""

    def test_ta_mentor_smoke(self, ta_mentor_response):
        """Verify TAMentor can synthesize multi-timeframe signals and return valid TAMentorSignal."""
        # Mock inputs from subagents
        weekly_input = {
            "symbol": "BTC",
            "timeframe": "weekly",
            "overall": {"bias": "bullish", "confidence": 75}
        }
        daily_input = {
            "symbol": "BTC",
            "timeframe": "daily",
            "overall": {"bias": "bullish", "confidence": 70}
        }
        fourhour_input = {
            "symbol": "BTC",
            "timeframe": "4h",
            "overall": {"bias": "neutral", "confidence": 55}
        }

        agent = TAMentor()

        with patch.object(agent, '_call_claude', return_value=json.dumps(ta_mentor_response)):
            result = agent.synthesize(weekly_input, daily_input, fourhour_input)

        # Verify result can be validated as TAMentorSignal
        signal = TAMentorSignal.model_validate(result)
        assert signal.symbol == "BTC"
        assert signal.timeframe_alignment.confluence in ["perfect", "strong", "moderate", "weak", "conflicting"]
        assert 0 <= signal.unified_signal.confidence <= 100
        assert signal.unified_signal.recommended_action in ["long", "short", "wait"]

    def test_ta_mentor_analyze_wrapper(self, ta_mentor_response):
        """Verify TAMentor.analyze() wrapper works correctly."""
        context = {
            "weekly_analysis": {"symbol": "BTC", "overall": {"bias": "bullish"}},
            "daily_analysis": {"symbol": "BTC", "overall": {"bias": "bullish"}},
            "fourhour_analysis": {"symbol": "BTC", "overall": {"bias": "neutral"}}
        }

        agent = TAMentor()

        with patch.object(agent, '_call_claude', return_value=json.dumps(ta_mentor_response)):
            result = agent.analyze("BTC", context)

        signal = TAMentorSignal.model_validate(result)
        assert signal.symbol == "BTC"
