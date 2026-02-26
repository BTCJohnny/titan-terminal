"""Smoke tests for Telegram Agent."""
import json
import pytest
from unittest.mock import patch, MagicMock

from src.backend.agents.telegram_agent import TelegramAgent
from src.backend.models.telegram_signal import TelegramSignal


class TestTelegramAgent:
    """Smoke tests for TelegramAgent."""

    def test_telegram_agent_smoke_no_signals(self):
        """Verify TelegramAgent handles empty signal case."""
        agent = TelegramAgent()

        # Mock DB to return no signals
        with patch.object(agent, '_get_recent_signals', return_value=[]):
            result = agent.analyze("BTC", {})

        # Should return valid structure even with no signals
        signal = TelegramSignal.model_validate(result)
        assert signal.symbol == "BTC"
        assert signal.signals_found == 0
        assert signal.overall_sentiment == "neutral"

    def test_telegram_agent_smoke_with_signals(self):
        """Verify TelegramAgent processes signals and returns valid TelegramSignal."""
        response = {
            "symbol": "BTC",
            "signals_found": 2,
            "relevant_signals": [
                {
                    "channel": "CryptoAlpha",
                    "action": "long",
                    "entry_price": 65000.0,
                    "stop_loss": 63000.0,
                    "take_profits": [68000.0, 70000.0],
                    "signal_quality": 75,
                    "freshness": "fresh",
                    "notes": "Strong setup"
                }
            ],
            "overall_sentiment": "bullish",
            "confluence_count": 2,
            "confidence": 70,
            "notes": "Multiple channels agree on long"
        }

        agent = TelegramAgent()

        # Mock both DB query and Claude call
        mock_signals = [{"channel": "CryptoAlpha", "content": "BTC long 65k"}]
        with patch.object(agent, '_get_recent_signals', return_value=mock_signals):
            with patch.object(agent, '_call_claude', return_value=json.dumps(response)):
                result = agent.analyze("BTC", {})

        signal = TelegramSignal.model_validate(result)
        assert signal.symbol == "BTC"
        assert signal.signals_found > 0
        assert signal.overall_sentiment in ["bullish", "bearish", "mixed", "neutral"]
