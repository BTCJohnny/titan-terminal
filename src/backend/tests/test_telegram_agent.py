"""Smoke tests for Telegram Agent."""
import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.backend.agents.telegram_agent import TelegramAgent
from src.backend.models.telegram_signal import TelegramSignal


class TestTelegramAgent:
    """Smoke tests for TelegramAgent."""

    def test_telegram_agent_smoke_no_signals(self):
        """Verify TelegramAgent handles empty signal case."""
        agent = TelegramAgent()

        # Mock DB to return no signals
        with patch('src.backend.agents.telegram_agent._query_signals', return_value=[]):
            result = agent.analyze("BTC", {})

        # Should return valid structure even with no signals
        assert isinstance(result, TelegramSignal)
        assert result.symbol == "BTC"
        assert result.signals_found == 0
        assert result.overall_sentiment == "neutral"

    def test_telegram_agent_smoke_with_signals(self):
        """Verify TelegramAgent processes signals and returns valid TelegramSignal."""
        # Mock database row structure
        mock_db_rows = [
            {
                'symbol': 'BTC',
                'direction': 'long',
                'signal_type': 'breakout',
                'timeframe': '4h',
                'entry_1': 65000.0,
                'entry_2': None,
                'entry_3': None,
                'stop_loss': 63000.0,
                'target_1': 68000.0,
                'target_2': 70000.0,
                'target_3': None,
                'target_4': None,
                'target_5': None,
                'confidence_score': 75,
                'pattern_type': 'bull_flag',
                'setup_description': 'Strong setup',
                'provider': 'CryptoAlpha',
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'pnl_percent': None
            }
        ]

        agent = TelegramAgent()

        # Mock _query_signals to return database rows
        with patch('src.backend.agents.telegram_agent._query_signals', return_value=mock_db_rows):
            result = agent.analyze("BTC", {})

        assert isinstance(result, TelegramSignal)
        assert result.symbol == "BTC"
        assert result.signals_found > 0
        assert result.overall_sentiment in ["bullish", "bearish", "mixed", "neutral"]
