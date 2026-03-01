"""Tests for /morning-report, /analyze/{symbol}, and /chat API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

from ..api.main import app
from ..models.orchestrator_output import OrchestratorOutput, EntryZoneSimple
from .. import api as _api_package

# Resolve the correct module path for patching.
# In different pytest configurations, the module may be registered under
# 'src.backend.api.main' or 'backend.api.main' depending on how Python resolves
# the package. We detect the actual module name at import time to ensure patches
# land in the correct namespace.
import sys
import importlib
_main_module = sys.modules.get("src.backend.api.main") or sys.modules.get("backend.api.main")
if _main_module is None:
    # Force import and detect correct path
    from ..api import main as _main_module
_MODULE_PATH = _main_module.__name__  # e.g. 'backend.api.main' or 'src.backend.api.main'


def _mock_output(symbol="BTC"):
    """Create a realistic OrchestratorOutput for testing."""
    return OrchestratorOutput(
        symbol=symbol,
        timestamp=datetime.now(),
        direction="BULLISH",
        confidence=82,
        suggested_action="Long Spot",
        accumulation_score=75,
        distribution_score=25,
        reasoning="Strong confluence across agents.",
        entry_zone=EntryZoneSimple(low=94000, high=96000, ideal=95000),
        stop_loss=92000,
        tp1=100000,
        tp2=105000,
        risk_reward=4.0,
    )


def test_morning_report_returns_200():
    """GET /morning-report returns 200 with signals list."""
    mock_orch = MagicMock()
    mock_orch.run_morning_batch.return_value = [_mock_output("BTC"), _mock_output("ETH")]

    with patch(f"{_MODULE_PATH}.get_orchestrator", return_value=mock_orch), \
         patch(f"{_MODULE_PATH}.get_market_data_fetcher", return_value=MagicMock()):
        client = TestClient(app)
        resp = client.get("/api/morning-report")

    assert resp.status_code == 200
    data = resp.json()
    assert "signals" in data
    assert "count" in data
    assert "timestamp" in data
    assert data["count"] == 2


def test_morning_report_signal_fields():
    """GET /morning-report response includes all OrchestratorOutput fields."""
    mock_orch = MagicMock()
    mock_orch.run_morning_batch.return_value = [_mock_output("BTC"), _mock_output("ETH")]

    with patch(f"{_MODULE_PATH}.get_orchestrator", return_value=mock_orch), \
         patch(f"{_MODULE_PATH}.get_market_data_fetcher", return_value=MagicMock()):
        client = TestClient(app)
        resp = client.get("/api/morning-report")

    assert resp.status_code == 200
    signal = resp.json()["signals"][0]
    assert signal["direction"] == "BULLISH"
    assert signal["confidence"] == 82
    assert signal["suggested_action"] == "Long Spot"
    assert signal["accumulation_score"] == 75
    assert signal["distribution_score"] == 25
    assert signal["reasoning"] == "Strong confluence across agents."
    assert signal["stop_loss"] == 92000
    assert signal["tp1"] == 100000
    assert signal["tp2"] == 105000
    assert signal["risk_reward"] == 4.0
    assert signal["entry_zone"] == {"low": 94000.0, "high": 96000.0, "ideal": 95000.0}


def test_morning_report_filters_error_dicts():
    """GET /morning-report filters out error dicts, only returns OrchestratorOutput instances."""
    mock_orch = MagicMock()
    mock_orch.run_morning_batch.return_value = [
        _mock_output("BTC"),
        {"error": "Failed to fetch DOGECOIN", "symbol": "DOGECOIN"},  # error dict — should be filtered
        _mock_output("ETH"),
    ]

    with patch(f"{_MODULE_PATH}.get_orchestrator", return_value=mock_orch), \
         patch(f"{_MODULE_PATH}.get_market_data_fetcher", return_value=MagicMock()):
        client = TestClient(app)
        resp = client.get("/api/morning-report")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    symbols = [s["symbol"] for s in data["signals"]]
    assert "BTC" in symbols
    assert "ETH" in symbols
    assert "DOGECOIN" not in symbols


def test_morning_report_max_5_results():
    """GET /morning-report limits output to top 5 results."""
    symbols = ["BTC", "ETH", "SOL", "AVAX", "ARB", "LINK", "OP"]
    mock_orch = MagicMock()
    mock_orch.run_morning_batch.return_value = [_mock_output(s) for s in symbols]

    with patch(f"{_MODULE_PATH}.get_orchestrator", return_value=mock_orch), \
         patch(f"{_MODULE_PATH}.get_market_data_fetcher", return_value=MagicMock()):
        client = TestClient(app)
        resp = client.get("/api/morning-report")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] <= 5
    assert len(data["signals"]) <= 5


def test_analyze_btc_returns_200():
    """GET /analyze/BTC returns 200 with full signal data."""
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = {"symbol": "BTC", "price": 95000}

    mock_orch = MagicMock()
    mock_orch.analyze_symbol.return_value = _mock_output("BTC")

    with patch(f"{_MODULE_PATH}.get_orchestrator", return_value=mock_orch), \
         patch(f"{_MODULE_PATH}.get_market_data_fetcher", return_value=mock_fetcher):
        client = TestClient(app)
        resp = client.get("/api/analyze/BTC")

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "BTC"


def test_analyze_response_includes_required_fields():
    """GET /analyze/BTC response includes direction, confidence, reasoning fields."""
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = {"symbol": "BTC", "price": 95000}

    mock_orch = MagicMock()
    mock_orch.analyze_symbol.return_value = _mock_output("BTC")

    with patch(f"{_MODULE_PATH}.get_orchestrator", return_value=mock_orch), \
         patch(f"{_MODULE_PATH}.get_market_data_fetcher", return_value=mock_fetcher):
        client = TestClient(app)
        resp = client.get("/api/analyze/BTC")

    assert resp.status_code == 200
    data = resp.json()
    assert data["direction"] == "BULLISH"
    assert data["confidence"] == 82
    assert data["reasoning"] == "Strong confluence across agents."
    assert data["suggested_action"] == "Long Spot"
    assert data["entry_zone"] is not None
    assert data["stop_loss"] == 92000
    assert data["tp1"] == 100000
    assert data["tp2"] == 105000
    assert data["risk_reward"] == 4.0


def test_analyze_symbol_uppercased():
    """GET /analyze/{symbol} uppercases the symbol before passing to orchestrator."""
    mock_fetcher = MagicMock()
    mock_fetcher.fetch.return_value = {"symbol": "BTC", "price": 95000}

    mock_orch = MagicMock()
    mock_orch.analyze_symbol.return_value = _mock_output("BTC")

    with patch(f"{_MODULE_PATH}.get_orchestrator", return_value=mock_orch), \
         patch(f"{_MODULE_PATH}.get_market_data_fetcher", return_value=mock_fetcher):
        client = TestClient(app)
        resp = client.get("/api/analyze/btc")  # lowercase

    assert resp.status_code == 200
    # Verify orchestrator was called with uppercase symbol
    mock_orch.analyze_symbol.assert_called_once_with("BTC", mock_fetcher.fetch.return_value)
    mock_fetcher.fetch.assert_called_once_with("BTC")


def test_morning_report_empty_results():
    """GET /morning-report handles empty orchestrator results gracefully."""
    mock_orch = MagicMock()
    mock_orch.run_morning_batch.return_value = []

    with patch(f"{_MODULE_PATH}.get_orchestrator", return_value=mock_orch), \
         patch(f"{_MODULE_PATH}.get_market_data_fetcher", return_value=MagicMock()):
        client = TestClient(app)
        resp = client.get("/api/morning-report")

    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 0
    assert data["signals"] == []


# --- /chat endpoint tests ---

def _mock_chat_client(response_text="BTC looks strong today."):
    """Create a mock Anthropic client that returns a canned text response."""
    mock_client = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=response_text)]
    mock_client.messages.create.return_value = mock_msg
    return mock_client


def test_chat_returns_200():
    """POST /api/chat returns 200 with 'response' and 'timestamp' fields."""
    mock_client = _mock_chat_client("BTC looks strong today.")

    with patch(f"{_MODULE_PATH}.get_chat_client", return_value=mock_client), \
         patch(f"{_MODULE_PATH}.get_recent_signals", return_value=[]):
        client = TestClient(app)
        resp = client.post("/api/chat", json={"question": "What looks good?"})

    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert "timestamp" in data
    assert data["response"] == "BTC looks strong today."


def test_chat_uses_model_name():
    """POST /api/chat calls messages.create with settings.MODEL_NAME (not MENTOR_MODEL)."""
    from ..config.settings import settings as _settings
    mock_client = _mock_chat_client()

    with patch(f"{_MODULE_PATH}.get_chat_client", return_value=mock_client), \
         patch(f"{_MODULE_PATH}.get_recent_signals", return_value=[]):
        client = TestClient(app)
        client.post("/api/chat", json={"question": "What looks good?"})

    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs is not None
    assert call_kwargs.kwargs.get("model") == _settings.MODEL_NAME
    # Must NOT use MENTOR_MODEL
    assert call_kwargs.kwargs.get("model") != _settings.MENTOR_MODEL


def test_chat_includes_signal_context():
    """POST /api/chat passes recent signal data in the system prompt to the LLM."""
    mock_signal = {
        "symbol": "BTC",
        "confidence": 85,
        "suggested_action": "Long Spot",
        "direction": "BULLISH",
        "entry_zone_low": 94000,
        "entry_zone_high": 96000,
        "stop_loss": 92000,
        "tp1": 100000,
        "tp2": 105000,
        "risk_reward": 4.0,
    }
    mock_client = _mock_chat_client("BTC is looking bullish with 85% confidence.")

    with patch(f"{_MODULE_PATH}.get_chat_client", return_value=mock_client), \
         patch(f"{_MODULE_PATH}.get_recent_signals", return_value=[mock_signal]):
        client = TestClient(app)
        client.post("/api/chat", json={"question": "How does BTC look?"})

    call_kwargs = mock_client.messages.create.call_args
    system_prompt = call_kwargs.kwargs.get("system", "")
    # Signal data (symbol and confidence) must appear in the system prompt
    assert "BTC" in system_prompt
    assert "85" in system_prompt


def test_chat_handles_empty_signals():
    """POST /api/chat returns 200 with fallback message when no signals exist."""
    mock_client = _mock_chat_client("No recent signals found. Run /morning-report first.")

    with patch(f"{_MODULE_PATH}.get_chat_client", return_value=mock_client), \
         patch(f"{_MODULE_PATH}.get_recent_signals", return_value=[]):
        client = TestClient(app)
        resp = client.post("/api/chat", json={"question": "What's the market look like?"})

    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    # The system prompt should note that no data is available
    call_kwargs = mock_client.messages.create.call_args
    system_prompt = call_kwargs.kwargs.get("system", "")
    assert "No recent analysis data" in system_prompt


def test_chat_request_format():
    """POST /api/chat accepts {'question': '...'} (not 'message')."""
    mock_client = _mock_chat_client("Answer here.")

    with patch(f"{_MODULE_PATH}.get_chat_client", return_value=mock_client), \
         patch(f"{_MODULE_PATH}.get_recent_signals", return_value=[]):
        client = TestClient(app)
        # Correct field name: 'question'
        resp = client.post("/api/chat", json={"question": "Is BTC a buy?"})

    assert resp.status_code == 200

    # Wrong field name ('message') should return 422 Unprocessable Entity
    with patch(f"{_MODULE_PATH}.get_chat_client", return_value=mock_client), \
         patch(f"{_MODULE_PATH}.get_recent_signals", return_value=[]):
        client = TestClient(app)
        resp_wrong = client.post("/api/chat", json={"message": "Is BTC a buy?"})

    assert resp_wrong.status_code == 422
