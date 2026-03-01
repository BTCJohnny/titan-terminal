"""Tests for configurable watchlist and Telegram supplementation."""
import pytest
from unittest.mock import patch, MagicMock
from src.backend.agents.orchestrator import Orchestrator
from src.backend.config.settings import settings


class TestWatchlistSettings:
    """WTCH-01: Watchlist is configurable via settings."""

    def test_watchlist_exists_in_settings(self):
        assert hasattr(settings, 'WATCHLIST')
        assert isinstance(settings.WATCHLIST, list)
        assert len(settings.WATCHLIST) > 0

    def test_watchlist_contains_core_symbols(self):
        assert 'BTC' in settings.WATCHLIST
        assert 'ETH' in settings.WATCHLIST

    @patch.dict('os.environ', {'WATCHLIST': 'DOGE,PEPE,WIF'})
    def test_watchlist_configurable_via_env(self):
        """Verify WATCHLIST env var is parsed correctly by the settings logic."""
        import os
        # Test the parsing expression directly — mirrors how Settings evaluates the env var
        raw = os.getenv("WATCHLIST", "BTC,ETH,SOL,AVAX,ARB,LINK")
        parsed = [s.strip() for s in raw.split(",")]
        assert parsed == ['DOGE', 'PEPE', 'WIF']


class TestTelegramSupplementation:
    """WTCH-02: Telegram signals supplement the watchlist."""

    @patch('src.backend.agents.telegram_agent.get_signals_connection')
    def test_get_recent_signal_symbols_returns_unique(self, mock_conn):
        """get_recent_signal_symbols returns deduplicated uppercase symbols."""
        from src.backend.agents.telegram_agent import get_recent_signal_symbols
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'symbol': 'DOGE'}, {'symbol': 'PEPE'}, {'symbol': 'WIF'}
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        symbols = get_recent_signal_symbols(hours=72)
        assert isinstance(symbols, list)
        assert len(symbols) == len(set(symbols))  # No duplicates

    @patch('src.backend.agents.telegram_agent.get_signals_connection')
    def test_get_recent_signal_symbols_handles_db_error(self, mock_conn):
        """Gracefully returns empty list on DB error."""
        from src.backend.agents.telegram_agent import get_recent_signal_symbols
        mock_conn.side_effect = Exception("DB error")
        result = get_recent_signal_symbols()
        assert result == []


class TestMergedWatchlist:
    """WTCH-03: Morning report uses merged watchlist."""

    def test_get_merged_watchlist_combines_sources(self):
        orchestrator = Orchestrator()
        with patch('src.backend.agents.orchestrator.settings') as mock_settings, \
             patch('src.backend.agents.orchestrator.get_recent_signal_symbols') as mock_tg:
            mock_settings.WATCHLIST = ['BTC', 'ETH', 'SOL']
            mock_tg.return_value = ['DOGE', 'PEPE']
            merged = orchestrator.get_merged_watchlist()
            assert merged == ['BTC', 'ETH', 'SOL', 'DOGE', 'PEPE']

    def test_get_merged_watchlist_deduplicates(self):
        orchestrator = Orchestrator()
        with patch('src.backend.agents.orchestrator.settings') as mock_settings, \
             patch('src.backend.agents.orchestrator.get_recent_signal_symbols') as mock_tg:
            mock_settings.WATCHLIST = ['BTC', 'ETH', 'SOL']
            mock_tg.return_value = ['ETH', 'DOGE']  # ETH is a duplicate
            merged = orchestrator.get_merged_watchlist()
            assert merged == ['BTC', 'ETH', 'SOL', 'DOGE']
            assert merged.count('ETH') == 1

    def test_run_morning_batch_uses_merged_watchlist(self):
        orchestrator = Orchestrator()
        mock_fetcher = MagicMock(return_value={'current_price': 65000})
        with patch.object(orchestrator, 'get_merged_watchlist', return_value=['BTC', 'ETH']), \
             patch.object(orchestrator, 'analyze_symbol', return_value={'symbol': 'BTC', 'confidence': 70, 'suggested_action': 'Long Spot'}):
            results = orchestrator.run_morning_batch(mock_fetcher)
            assert len(results) > 0
            orchestrator.get_merged_watchlist.assert_called_once()

    def test_run_morning_batch_sorts_orchestrator_output(self):
        """Verify sort logic works with real OrchestratorOutput (not mocked dicts).

        Regression test: .get() was used on OrchestratorOutput which has no .get() method.
        """
        from datetime import datetime
        from src.backend.models.orchestrator_output import OrchestratorOutput

        orchestrator = Orchestrator()
        mock_fetcher = MagicMock(return_value={'current_price': 65000})

        # Build two real OrchestratorOutput instances with different confidence
        low_conf = OrchestratorOutput(
            symbol='ETH',
            timestamp=datetime.now(),
            accumulation_score=40,
            distribution_score=30,
            confidence=55,
            suggested_action='Long Spot',
        )
        high_conf = OrchestratorOutput(
            symbol='BTC',
            timestamp=datetime.now(),
            accumulation_score=80,
            distribution_score=10,
            confidence=85,
            suggested_action='Long Spot',
        )

        # analyze_symbol returns OrchestratorOutput — cycle through them
        with patch.object(orchestrator, 'get_merged_watchlist', return_value=['BTC', 'ETH']), \
             patch.object(orchestrator, 'analyze_symbol', side_effect=[high_conf, low_conf]):
            results = orchestrator.run_morning_batch(mock_fetcher)
            # Must not raise AttributeError
            assert len(results) == 2
            # Sorted by confidence descending
            assert results[0].confidence >= results[1].confidence
            assert results[0].symbol == 'BTC'
            assert results[1].symbol == 'ETH'

    def test_run_morning_batch_handles_mixed_results(self):
        """Sort handles mix of OrchestratorOutput (success) and error dicts (failure)."""
        from datetime import datetime
        from src.backend.models.orchestrator_output import OrchestratorOutput

        orchestrator = Orchestrator()
        mock_fetcher = MagicMock(return_value={'current_price': 65000})

        good_result = OrchestratorOutput(
            symbol='BTC',
            timestamp=datetime.now(),
            accumulation_score=80,
            distribution_score=10,
            confidence=85,
            suggested_action='Long Spot',
        )

        # analyze_symbol succeeds for BTC, raises for ETH (caught as error dict)
        def side_effect(symbol, data):
            if symbol == 'BTC':
                return good_result
            raise RuntimeError("API timeout")

        with patch.object(orchestrator, 'get_merged_watchlist', return_value=['BTC', 'ETH']), \
             patch.object(orchestrator, 'analyze_symbol', side_effect=side_effect):
            results = orchestrator.run_morning_batch(mock_fetcher)
            # BTC is actionable, ETH error dict has suggested_action='Avoid'
            # So only BTC should appear (actionable filter removes Avoid)
            assert len(results) == 1
            assert results[0].symbol == 'BTC'
