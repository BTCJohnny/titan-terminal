"""Comprehensive unit tests for Nansen Agent - 5-signal framework.

Tests cover:
- Individual signal fetching with mocked subprocess.run (TestNansenMCPSignals)
- Graceful degradation for CLI errors (TestNansenGracefulHandling)
- Aggregation scoring tiers: bullish/neutral/bearish (TestNansenAggregation)
- Vault logging: file creation, row appending, error handling (TestNansenVaultLogging)
"""
import json
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call

from src.backend.agents.nansen_agent import NansenAgent
from src.backend.agents.nansen_mcp import (
    MCPSignalResult,
    fetch_exchange_flows,
    fetch_smart_money,
    fetch_whale_activity,
    fetch_top_pnl,
    fetch_fresh_wallets,
    fetch_funding_rate,
)
from src.backend.agents import vault_logger
from src.backend.agents.vault_logger import log_nansen_analysis, _ensure_log_file_exists
from src.backend.models.nansen_signal import (
    NansenSignal, ExchangeFlows, FreshWallets, SmartMoney,
    TopPnL, WhaleActivity, OnChainOverall, FundingRate
)


# ---------------------------------------------------------------------------
# Shared mock subprocess helper
# ---------------------------------------------------------------------------

def _mock_subprocess(stdout_data, returncode=0, stderr=""):
    """Return a MagicMock that mimics subprocess.run with JSON stdout."""
    mock_result = MagicMock()
    mock_result.returncode = returncode
    mock_result.stdout = json.dumps(stdout_data) if not isinstance(stdout_data, str) else stdout_data
    mock_result.stderr = stderr
    return mock_result


# ---------------------------------------------------------------------------
# Task 1: TestNansenMCPSignals
# ---------------------------------------------------------------------------

class TestNansenMCPSignals:
    """Test each of the 5 fetch_* functions with mocked subprocess.run."""

    # --- Exchange Flows ---

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_exchange_flows_outflow(self, mock_run, mock_settings):
        """Exchange flows: outflow_usd > inflow_usd should yield net_direction=outflow."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        mock_run.return_value = _mock_subprocess([
            {"token_symbol": "ETH", "inflow_usd": 500_000, "outflow_usd": 5_000_000},
            {"token_symbol": "ETH", "inflow_usd": 100_000, "outflow_usd": 2_000_000},
        ])

        result = fetch_exchange_flows("ETH")

        assert result.success is True
        assert result.data["net_direction"] == "outflow"
        assert result.data["confidence"] > 0
        assert "outflow" in result.data["interpretation"].lower() or "accumulation" in result.data["interpretation"].lower()

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_exchange_flows_inflow(self, mock_run, mock_settings):
        """Exchange flows: inflow_usd > outflow_usd should yield net_direction=inflow."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        mock_run.return_value = _mock_subprocess([
            {"token_symbol": "ETH", "inflow_usd": 10_000_000, "outflow_usd": 200_000},
        ])

        result = fetch_exchange_flows("ETH")

        assert result.success is True
        assert result.data["net_direction"] == "inflow"
        assert result.data["confidence"] > 0

    # --- Smart Money ---

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_smart_money_accumulating(self, mock_run, mock_settings):
        """Smart money: positive net_flow_usd > $1M should yield direction=accumulating, confidence>=55."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        mock_run.return_value = _mock_subprocess([
            {"token_symbol": "ETH", "net_flow_usd": 2_500_000},
            {"token_symbol": "ETH", "net_flow_usd": 800_000},
        ])

        result = fetch_smart_money("ETH")

        assert result.success is True
        assert result.data["direction"] == "accumulating"
        assert result.data["confidence"] >= 55

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_smart_money_distributing(self, mock_run, mock_settings):
        """Smart money: negative net_flow_usd should yield direction=distributing."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        mock_run.return_value = _mock_subprocess([
            {"token_symbol": "ETH", "net_flow_usd": -3_000_000},
        ])

        result = fetch_smart_money("ETH")

        assert result.success is True
        assert result.data["direction"] == "distributing"
        assert result.data["confidence"] >= 55

    # --- Whale Activity ---

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_whale_activity_accumulating(self, mock_run, mock_settings):
        """Whale activity: total balance_usd > $1M should yield net_flow=accumulating."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        mock_run.return_value = _mock_subprocess([
            {"address": "0xaaa", "balance_usd": 500_000},
            {"address": "0xbbb", "balance_usd": 750_000},
            {"address": "0xccc", "balance_usd": 1_200_000},
        ])

        result = fetch_whale_activity("ETH")

        assert result.success is True
        assert result.data["net_flow"] == "accumulating"
        assert result.data["confidence"] > 0

    # --- Top PnL ---

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_top_pnl_bullish(self, mock_run, mock_settings):
        """Top PnL: >60% traders with positive PnL should yield traders_bias=bullish."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        # 8 positive out of 10 = 80% bullish
        pnl_data = [{"total_pnl_usd": 5000} for _ in range(8)]
        pnl_data += [{"total_pnl_usd": -1000} for _ in range(2)]
        mock_run.return_value = _mock_subprocess(pnl_data)

        result = fetch_top_pnl("ETH")

        assert result.success is True
        assert result.data["traders_bias"] == "bullish"
        assert result.data["confidence"] > 50

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_top_pnl_bearish(self, mock_run, mock_settings):
        """Top PnL: <40% traders with positive PnL should yield traders_bias=bearish."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        # 2 positive out of 10 = 20% bullish
        pnl_data = [{"total_pnl_usd": 5000} for _ in range(2)]
        pnl_data += [{"total_pnl_usd": -1000} for _ in range(8)]
        mock_run.return_value = _mock_subprocess(pnl_data)

        result = fetch_top_pnl("ETH")

        assert result.success is True
        assert result.data["traders_bias"] == "bearish"
        assert result.data["confidence"] > 50

    # --- Fresh Wallets ---

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_fresh_wallets_high(self, mock_run, mock_settings):
        """Fresh wallets: >30 buy-side items should yield activity_level=high."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        wallet_data = [{"side": "buy"} for _ in range(35)]
        mock_run.return_value = _mock_subprocess(wallet_data)

        result = fetch_fresh_wallets("ETH")

        assert result.success is True
        assert result.data["activity_level"] == "high"
        assert result.data["confidence"] > 0

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_fresh_wallets_none(self, mock_run, mock_settings):
        """Fresh wallets: empty list should yield activity_level=none."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        mock_run.return_value = _mock_subprocess([])

        result = fetch_fresh_wallets("ETH")

        assert result.success is True
        assert result.data["activity_level"] == "none"

    # --- Funding Rate ---

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_funding_rate_crowded_longs(self, mock_run, mock_settings):
        """Funding rate: >65% long positions should yield positive rate and 'crowded longs'."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        # 7 longs out of 10 = 70% longs
        perp_data = [{"side": "long"} for _ in range(7)]
        perp_data += [{"side": "short"} for _ in range(3)]
        mock_run.return_value = _mock_subprocess(perp_data)

        result = fetch_funding_rate("ETH")

        assert result.success is True
        assert result.data["rate"] is not None
        assert result.data["rate"] > 0
        assert "crowded longs" in result.data["interpretation"].lower()

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_funding_rate_crowded_shorts(self, mock_run, mock_settings):
        """Funding rate: <35% long positions should yield negative rate and 'crowded shorts'."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        # 2 longs out of 10 = 20% longs
        perp_data = [{"side": "long"} for _ in range(2)]
        perp_data += [{"side": "short"} for _ in range(8)]
        mock_run.return_value = _mock_subprocess(perp_data)

        result = fetch_funding_rate("ETH")

        assert result.success is True
        assert result.data["rate"] is not None
        assert result.data["rate"] < 0
        assert "crowded shorts" in result.data["interpretation"].lower()


# ---------------------------------------------------------------------------
# Task 1: TestNansenGracefulHandling
# ---------------------------------------------------------------------------

class TestNansenGracefulHandling:
    """Test graceful degradation when Nansen CLI returns errors (TEST-04)."""

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_exchange_flows_credits_exhausted(self, mock_run, mock_settings):
        """Credits exhausted: non-zero returncode with 'credits' in stderr => confidence 0."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: API credits exhausted. Please upgrade your plan."
        mock_run.return_value = mock_result

        result = fetch_exchange_flows("ETH")

        assert result.success is True
        assert result.data["confidence"] == 0
        assert result.data["net_direction"] == "neutral"

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_smart_money_rate_limited(self, mock_run, mock_settings):
        """Rate limited: non-zero returncode with 'rate limit' in stderr => confidence 0."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: rate limit exceeded. Retry after 60 seconds."
        mock_run.return_value = mock_result

        result = fetch_smart_money("ETH")

        assert result.success is True
        assert result.data["confidence"] == 0

    @patch('src.backend.agents.nansen_mcp.settings')
    @patch('src.backend.agents.nansen_mcp.subprocess.run')
    def test_fetch_whale_activity_cli_returns_none(self, mock_run, mock_settings):
        """Empty stdout from CLI should yield net_flow=neutral, confidence=0."""
        mock_settings.NANSEN_API_KEY = 'test-key'
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""  # Empty stdout
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = fetch_whale_activity("ETH")

        assert result.success is True
        assert result.data["net_flow"] == "neutral"
        assert result.data["confidence"] == 0

    @patch('src.backend.agents.nansen_agent.fetch_fresh_wallets')
    @patch('src.backend.agents.nansen_agent.fetch_top_pnl')
    @patch('src.backend.agents.nansen_agent.fetch_whale_activity')
    @patch('src.backend.agents.nansen_agent.fetch_smart_money')
    @patch('src.backend.agents.nansen_agent.fetch_exchange_flows')
    @patch('src.backend.agents.nansen_agent.fetch_funding_rate')
    @patch('src.backend.agents.nansen_agent.log_nansen_analysis')
    def test_analyze_all_signals_fail(
        self,
        mock_log,
        mock_funding,
        mock_exchange,
        mock_smart_money,
        mock_whale,
        mock_top_pnl,
        mock_fresh_wallets,
    ):
        """When all signals return neutral defaults, analyze() returns valid NansenSignal.

        All 5 MCP signals return success=True with neutral/zero-confidence data.
        NansenAgent.analyze() should still produce a valid NansenSignal with
        signal_count_bullish == 0.
        """
        neutral_exchange = MCPSignalResult(success=True, data={
            "net_direction": "neutral",
            "magnitude": "low",
            "interpretation": "Exchange flows data unavailable",
            "confidence": 0
        })
        neutral_smart_money = MCPSignalResult(success=True, data={
            "direction": "neutral",
            "confidence": 0,
            "notable_wallets": [],
            "interpretation": "Smart money data unavailable"
        })
        neutral_whale = MCPSignalResult(success=True, data={
            "summary": "Whale activity data unavailable",
            "notable_transactions": [],
            "net_flow": "neutral",
            "confidence": 0
        })
        neutral_top_pnl = MCPSignalResult(success=True, data={
            "traders_bias": "neutral",
            "average_position": "neutral",
            "confidence": 0,
            "interpretation": "Top PnL data unavailable"
        })
        neutral_fresh_wallets = MCPSignalResult(success=True, data={
            "activity_level": "none",
            "trend": "stable",
            "notable_count": 0,
            "interpretation": "Fresh wallets data unavailable",
            "confidence": 0
        })
        neutral_funding = MCPSignalResult(success=True, data={
            "rate": None,
            "available": False,
            "interpretation": "Funding rate not available"
        })

        mock_exchange.return_value = neutral_exchange
        mock_smart_money.return_value = neutral_smart_money
        mock_whale.return_value = neutral_whale
        mock_top_pnl.return_value = neutral_top_pnl
        mock_fresh_wallets.return_value = neutral_fresh_wallets
        mock_funding.return_value = neutral_funding
        mock_log.return_value = True

        agent = NansenAgent()
        signal = agent.analyze("BTC", log_to_vault=False)

        assert isinstance(signal, NansenSignal)
        assert signal.overall_signal.bias in ("neutral", "bearish", "bullish")
        assert signal.overall_signal.confidence >= 0
        assert signal.signal_count_bullish == 0


# ---------------------------------------------------------------------------
# Task 2: TestNansenAggregation
# ---------------------------------------------------------------------------

class TestNansenAggregation:
    """Test _aggregate_signals and _classify_signal directly (pure logic tests)."""

    def setup_method(self):
        """Create a NansenAgent instance for each test."""
        self.agent = NansenAgent()

    def test_aggregation_all_bullish(self):
        """5 bullish classifications => bias=bullish, counts correctly set."""
        bullish = (True, False, 75)
        bias, confidence, insights, bullish_count, bearish_count = self.agent._aggregate_signals(
            bullish, bullish, bullish, bullish, bullish
        )

        assert bias == "bullish"
        assert bullish_count == 5
        assert bearish_count == 0

    def test_aggregation_all_bearish(self):
        """5 bearish classifications => bias=bearish, counts correctly set."""
        bearish = (False, True, 75)
        bias, confidence, insights, bullish_count, bearish_count = self.agent._aggregate_signals(
            bearish, bearish, bearish, bearish, bearish
        )

        assert bias == "bearish"
        assert bearish_count == 5
        assert bullish_count == 0

    def test_aggregation_mixed_3_bullish(self):
        """3 bullish + 2 bearish => bias=neutral (between thresholds 2-3)."""
        bullish = (True, False, 75)
        bearish = (False, True, 75)
        bias, confidence, insights, bullish_count, bearish_count = self.agent._aggregate_signals(
            bullish, bullish, bullish, bearish, bearish
        )

        assert bias == "neutral"
        assert bullish_count == 3
        assert bearish_count == 2

    def test_aggregation_4_bullish_threshold(self):
        """4 bullish + 1 bearish => bias=bullish (hits BULLISH_THRESHOLD of 4)."""
        bullish = (True, False, 75)
        bearish = (False, True, 75)
        bias, confidence, insights, bullish_count, bearish_count = self.agent._aggregate_signals(
            bullish, bullish, bullish, bullish, bearish
        )

        assert bias == "bullish"
        assert bullish_count == 4
        assert bearish_count == 1

    def test_aggregation_1_bullish_threshold(self):
        """1 bullish + 4 bearish => bias=bearish (hits BEARISH_THRESHOLD of 1)."""
        bullish = (True, False, 75)
        bearish = (False, True, 75)
        bias, confidence, insights, bullish_count, bearish_count = self.agent._aggregate_signals(
            bullish, bearish, bearish, bearish, bearish
        )

        assert bias == "bearish"
        assert bullish_count == 1
        assert bearish_count == 4

    def test_aggregation_confidence_calculation(self):
        """Confidence = min(50 + alignment_bonus * 10, 100).

        5 bullish: alignment_bonus = abs(5-0) = 5 => min(50+50, 100) = 100
        2 bullish 3 bearish: alignment_bonus = abs(2-3) = 1 => min(50+10, 100) = 60
        """
        bullish = (True, False, 75)
        bearish = (False, True, 75)

        # All 5 bullish
        _, confidence_all_bull, _, _, _ = self.agent._aggregate_signals(
            bullish, bullish, bullish, bullish, bullish
        )
        assert confidence_all_bull == 100

        # 2 bullish, 3 bearish
        _, confidence_mixed, _, _, _ = self.agent._aggregate_signals(
            bullish, bullish, bearish, bearish, bearish
        )
        assert confidence_mixed == 60

    def test_classify_signal_low_confidence_neutral(self):
        """Confidence <= 50 should always return (False, False, confidence) regardless of direction."""
        # Exchange flows with outflow direction but low confidence
        data_low_conf = {"net_direction": "outflow", "confidence": 40}
        result = self.agent._classify_signal("exchange_flows", data_low_conf)

        assert result == (False, False, 40)

        # Smart money accumulating but confidence exactly 50 (boundary)
        data_boundary = {"direction": "accumulating", "confidence": 50}
        result_boundary = self.agent._classify_signal("smart_money", data_boundary)
        assert result_boundary == (False, False, 50)

    def test_classify_signal_each_type(self):
        """Each of 5 signal types: confidence>50 + bullish direction => (True, False, confidence)."""
        test_cases = [
            ("exchange_flows", {"net_direction": "outflow", "confidence": 75}),
            ("smart_money", {"direction": "accumulating", "confidence": 70}),
            ("whale_activity", {"net_flow": "accumulating", "confidence": 80}),
            ("top_pnl", {"traders_bias": "bullish", "confidence": 65}),
            ("fresh_wallets", {"activity_level": "high", "confidence": 70}),
        ]

        for signal_type, data in test_cases:
            result = self.agent._classify_signal(signal_type, data)
            assert result == (True, False, data["confidence"]), (
                f"Expected (True, False, {data['confidence']}) for {signal_type}, got {result}"
            )


# ---------------------------------------------------------------------------
# Task 2: TestNansenVaultLogging
# ---------------------------------------------------------------------------

class TestNansenVaultLogging:
    """Test vault logging: file creation, row appending, graceful failure (TEST-03)."""

    def _make_nansen_signal(self, symbol="BTC", bias="bullish", bullish_count=3, bearish_count=1):
        """Helper: Build a NansenSignal with known values for testing."""
        return NansenSignal(
            symbol=symbol,
            exchange_flows=ExchangeFlows(
                net_direction="outflow",
                magnitude="medium",
                interpretation="Test exchange flows",
                confidence=70,
            ),
            fresh_wallets=FreshWallets(
                activity_level="high",
                trend="increasing",
                notable_count=35,
                interpretation="Test fresh wallets",
            ),
            smart_money=SmartMoney(
                direction="accumulating",
                confidence=75,
                notable_wallets=[],
                interpretation="Test smart money",
            ),
            top_pnl=TopPnL(
                traders_bias="bullish",
                average_position="long",
                confidence=65,
                interpretation="Test top PnL",
            ),
            whale_activity=WhaleActivity(
                summary="Test whale activity",
                notable_transactions=[],
                net_flow="accumulating",
                confidence=80,
            ),
            funding_rate=None,
            overall_signal=OnChainOverall(
                bias=bias,
                confidence=80,
                key_insights=["Test insight 1"],
            ),
            signal_count_bullish=bullish_count,
            signal_count_bearish=bearish_count,
            reasoning="Test reasoning.",
            timestamp=datetime(2026, 3, 1, 10, 0, 0),
        )

    def test_vault_log_creates_file_with_header(self, tmp_path):
        """_ensure_log_file_exists() creates file with proper markdown table header."""
        test_vault_path = tmp_path / "nansen"
        test_log_file = test_vault_path / "signal-combinations.md"

        with patch.object(vault_logger, 'VAULT_PATH', test_vault_path), \
             patch.object(vault_logger, 'SIGNAL_LOG_FILE', test_log_file):
            _ensure_log_file_exists()

        assert test_log_file.exists()
        content = test_log_file.read_text()
        # Verify markdown table header columns
        assert "| Date |" in content
        assert "Symbol" in content
        assert "Exchange Flow" in content
        assert "Smart Money" in content
        assert "Whales" in content or "Whale" in content
        assert "Overall" in content

    def test_vault_log_appends_row(self, tmp_path):
        """log_nansen_analysis() appends a row with symbol, bias, signal counts."""
        test_vault_path = tmp_path / "nansen"
        test_log_file = test_vault_path / "signal-combinations.md"

        signal = self._make_nansen_signal(symbol="ETH", bias="bullish", bullish_count=4, bearish_count=1)

        with patch.object(vault_logger, 'VAULT_PATH', test_vault_path), \
             patch.object(vault_logger, 'SIGNAL_LOG_FILE', test_log_file):
            result = log_nansen_analysis(signal)

        assert result is True
        content = test_log_file.read_text()
        assert "ETH" in content
        assert "bullish" in content
        # Signal counts appear in the row
        assert "4" in content
        assert "1" in content

    def test_vault_log_graceful_on_write_error(self, tmp_path):
        """log_nansen_analysis() returns False (no raise) when open() raises IOError."""
        test_vault_path = tmp_path / "nansen"
        test_log_file = test_vault_path / "signal-combinations.md"

        signal = self._make_nansen_signal()

        with patch.object(vault_logger, 'VAULT_PATH', test_vault_path), \
             patch.object(vault_logger, 'SIGNAL_LOG_FILE', test_log_file), \
             patch('builtins.open', side_effect=IOError("Permission denied")):
            result = log_nansen_analysis(signal)

        assert result is False

    @patch('src.backend.agents.nansen_agent.fetch_fresh_wallets')
    @patch('src.backend.agents.nansen_agent.fetch_top_pnl')
    @patch('src.backend.agents.nansen_agent.fetch_whale_activity')
    @patch('src.backend.agents.nansen_agent.fetch_smart_money')
    @patch('src.backend.agents.nansen_agent.fetch_exchange_flows')
    @patch('src.backend.agents.nansen_agent.fetch_funding_rate')
    @patch('src.backend.agents.nansen_agent.log_nansen_analysis')
    def test_analyze_calls_vault_logger(
        self,
        mock_log,
        mock_funding,
        mock_exchange,
        mock_smart_money,
        mock_whale,
        mock_top_pnl,
        mock_fresh_wallets,
    ):
        """NansenAgent.analyze(..., log_to_vault=True) calls log_nansen_analysis once."""
        self._setup_all_fetch_mocks(
            mock_exchange, mock_smart_money, mock_whale, mock_top_pnl, mock_fresh_wallets, mock_funding
        )
        mock_log.return_value = True

        agent = NansenAgent()
        agent.analyze("BTC", log_to_vault=True)

        mock_log.assert_called_once()
        call_args = mock_log.call_args[0]
        assert isinstance(call_args[0], NansenSignal)

    @patch('src.backend.agents.nansen_agent.fetch_fresh_wallets')
    @patch('src.backend.agents.nansen_agent.fetch_top_pnl')
    @patch('src.backend.agents.nansen_agent.fetch_whale_activity')
    @patch('src.backend.agents.nansen_agent.fetch_smart_money')
    @patch('src.backend.agents.nansen_agent.fetch_exchange_flows')
    @patch('src.backend.agents.nansen_agent.fetch_funding_rate')
    @patch('src.backend.agents.nansen_agent.log_nansen_analysis')
    def test_analyze_skips_vault_logger(
        self,
        mock_log,
        mock_funding,
        mock_exchange,
        mock_smart_money,
        mock_whale,
        mock_top_pnl,
        mock_fresh_wallets,
    ):
        """NansenAgent.analyze(..., log_to_vault=False) does NOT call log_nansen_analysis."""
        self._setup_all_fetch_mocks(
            mock_exchange, mock_smart_money, mock_whale, mock_top_pnl, mock_fresh_wallets, mock_funding
        )

        agent = NansenAgent()
        agent.analyze("BTC", log_to_vault=False)

        mock_log.assert_not_called()

    # ------------------------------------------------------------------
    # Internal helper for vault logging integration tests
    # ------------------------------------------------------------------

    def _setup_all_fetch_mocks(
        self, mock_exchange, mock_smart_money, mock_whale,
        mock_top_pnl, mock_fresh_wallets, mock_funding
    ):
        """Configure all 6 fetch mocks with valid MCPSignalResult data."""
        mock_exchange.return_value = MCPSignalResult(success=True, data={
            "net_direction": "outflow",
            "magnitude": "medium",
            "interpretation": "Test exchange flows",
            "confidence": 70,
        })
        mock_smart_money.return_value = MCPSignalResult(success=True, data={
            "direction": "accumulating",
            "confidence": 75,
            "notable_wallets": [],
            "interpretation": "Test smart money",
        })
        mock_whale.return_value = MCPSignalResult(success=True, data={
            "summary": "Test whales",
            "notable_transactions": [],
            "net_flow": "accumulating",
            "confidence": 80,
        })
        mock_top_pnl.return_value = MCPSignalResult(success=True, data={
            "traders_bias": "bullish",
            "average_position": "long",
            "confidence": 65,
            "interpretation": "Test top PnL",
        })
        mock_fresh_wallets.return_value = MCPSignalResult(success=True, data={
            "activity_level": "high",
            "trend": "increasing",
            "notable_count": 35,
            "interpretation": "Test fresh wallets",
            "confidence": 70,
        })
        mock_funding.return_value = MCPSignalResult(success=True, data={
            "rate": None,
            "available": False,
            "interpretation": "Funding rate not available",
        })
