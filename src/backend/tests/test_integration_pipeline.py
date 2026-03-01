"""
End-to-end integration tests for the Titan Terminal pipeline.

Tests the full agent chain (OHLCV -> TA Ensemble -> Nansen CLI -> Telegram -> Risk ->
Orchestrator -> API) for BTC, ETH, and SOL by hitting the live FastAPI backend.

Usage:
    # Run against live backend (must be running at localhost:8000):
    pytest src/backend/tests/test_integration_pipeline.py -v -m integration

    # Skip these tests in normal CI runs (default behavior — they are auto-skipped):
    pytest src/backend/tests/  # integration tests skip automatically if backend offline
"""
import httpx
import os
import pytest
import time

# Allow overriding the base URL via environment variable for flexibility across
# different deployment environments. Defaults to localhost:8000 (standard dev port).
# If the primary URL is unavailable, auto-detects the backend on localhost:8001
# (the port used when 8000 is occupied by another process).
_DEFAULT_PORT = 8000
_FALLBACK_PORT = 8001


def _resolve_base_url() -> str:
    """Resolve the backend URL — env var, then port 8000, then fallback to 8001."""
    if env_url := os.environ.get("TITAN_API_URL"):
        return env_url.rstrip("/")
    # Try the standard port first
    for port in (_DEFAULT_PORT, _FALLBACK_PORT):
        try:
            r = httpx.get(f"http://localhost:{port}/", timeout=3)
            if r.status_code == 200 and r.json().get("service") == "Titan Terminal API":
                return f"http://localhost:{port}"
        except Exception:
            continue
    # Return the default — skip logic will handle unavailability
    return f"http://localhost:{_DEFAULT_PORT}"


BASE_URL = _resolve_base_url()


def _backend_available() -> bool:
    """Return True if the Titan Terminal backend is running at BASE_URL."""
    try:
        r = httpx.get(f"{BASE_URL}/", timeout=5)
        return r.status_code == 200 and r.json().get("service") == "Titan Terminal API"
    except Exception:
        return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _backend_available(), reason="Backend not running at localhost:8000"),
]


# ---------------------------------------------------------------------------
# Shared validator
# ---------------------------------------------------------------------------

def _assert_valid_signal(signal: dict) -> None:
    """Validate that a single signal dict matches the AnalyzeResponse schema.

    Called for each element of MorningReportResponse.signals and for the
    single-symbol /analyze/{symbol} response.
    """
    # Required core fields
    assert isinstance(signal.get("symbol"), str) and signal["symbol"], \
        f"'symbol' must be a non-empty string, got {signal.get('symbol')!r}"

    confidence = signal.get("confidence")
    assert isinstance(confidence, int), \
        f"'confidence' must be int, got {type(confidence).__name__}"
    assert 0 <= confidence <= 100, \
        f"'confidence' out of range: {confidence}"

    valid_actions = {"Long Spot", "Long Hyperliquid", "Short Hyperliquid", "Avoid"}
    suggested_action = signal.get("suggested_action")
    assert suggested_action in valid_actions, \
        f"'suggested_action' must be one of {valid_actions}, got {suggested_action!r}"

    accum = signal.get("accumulation_score")
    dist = signal.get("distribution_score")
    assert isinstance(accum, int) and 0 <= accum <= 100, \
        f"'accumulation_score' out of range or wrong type: {accum!r}"
    assert isinstance(dist, int) and 0 <= dist <= 100, \
        f"'distribution_score' out of range or wrong type: {dist!r}"

    timestamp = signal.get("timestamp")
    assert isinstance(timestamp, str) and timestamp, \
        f"'timestamp' must be a non-empty string, got {timestamp!r}"

    # Optional direction — if present must be one of the allowed values
    direction = signal.get("direction")
    if direction is not None:
        assert direction in {"BULLISH", "BEARISH", "NO SIGNAL"}, \
            f"'direction' must be BULLISH/BEARISH/NO SIGNAL, got {direction!r}"

    # Actionable signals require full trade data
    if suggested_action != "Avoid":
        reasoning = signal.get("reasoning")
        assert isinstance(reasoning, str) and reasoning, \
            f"Non-Avoid signal must have non-empty 'reasoning', got {reasoning!r}"

        entry_zone = signal.get("entry_zone")
        assert isinstance(entry_zone, dict), \
            f"Non-Avoid signal must have 'entry_zone' dict, got {entry_zone!r}"
        for key in ("low", "high", "ideal"):
            assert key in entry_zone, \
                f"'entry_zone' missing key '{key}': {entry_zone}"

        stop_loss = signal.get("stop_loss")
        assert isinstance(stop_loss, (int, float)), \
            f"'stop_loss' must be float for non-Avoid signal, got {stop_loss!r}"

        tp1 = signal.get("tp1")
        assert isinstance(tp1, (int, float)), \
            f"'tp1' must be float for non-Avoid signal, got {tp1!r}"

        tp2 = signal.get("tp2")
        assert isinstance(tp2, (int, float)), \
            f"'tp2' must be float for non-Avoid signal, got {tp2!r}"

        rr = signal.get("risk_reward")
        assert isinstance(rr, (int, float)) and rr >= 0, \
            f"'risk_reward' must be float >= 0 for non-Avoid signal, got {rr!r}"

    # three_laws_check — optional but validated if present
    three_laws = signal.get("three_laws_check")
    if three_laws is not None:
        for key in ("law_1_risk", "law_2_rr", "law_3_positions", "overall"):
            assert key in three_laws, \
                f"'three_laws_check' missing key '{key}': {three_laws}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_health_check():
    """Sanity check — verify both health endpoints respond before heavy tests."""
    with httpx.Client(timeout=10) as client:
        # Root health check
        r = client.get(f"{BASE_URL}/")
        assert r.status_code == 200, f"Root health check failed: {r.status_code}"
        body = r.json()
        assert body.get("status") == "ok", f"Root status not 'ok': {body}"

        # API-level health check
        r2 = client.get(f"{BASE_URL}/api/health-test")
        assert r2.status_code == 200, f"/api/health-test failed: {r2.status_code}"


def test_morning_report_btc_eth_sol():
    """INTG-01/02/03 — batch pipeline for BTC, ETH, SOL via /api/morning-report.

    Validates:
    - Response structure matches MorningReportResponse schema
    - At least 1 valid signal returned
    - All returned signals pass _assert_valid_signal
    - Returned symbols are a subset of {BTC, ETH, SOL}
    """
    # Each symbol requires 3 LLM calls (4h subagent + TA mentor + orchestrator mentor).
    # With 3 symbols in batch, allow up to 600s to handle sequential processing.
    with httpx.Client(timeout=600) as client:
        r = client.get(f"{BASE_URL}/api/morning-report", params={"symbols": "BTC,ETH,SOL"})

    assert r.status_code == 200, (
        f"/api/morning-report returned {r.status_code}: {r.text[:500]}"
    )

    body = r.json()

    # Top-level shape
    assert "timestamp" in body, f"'timestamp' missing from response: {list(body.keys())}"
    assert "count" in body, f"'count' missing from response: {list(body.keys())}"
    assert "signals" in body, f"'signals' missing from response: {list(body.keys())}"
    assert isinstance(body["signals"], list), "'signals' must be a list"

    # At least one signal returned (some may fail gracefully in live environments)
    assert body["count"] >= 1, "No signals returned — pipeline produced zero results"
    assert len(body["signals"]) >= 1, "'signals' list is empty"

    # Validate each signal
    returned_symbols = []
    for signal in body["signals"]:
        _assert_valid_signal(signal)
        returned_symbols.append(signal["symbol"])

    # All returned symbols must be within our requested set
    valid_symbols = {"BTC", "ETH", "SOL"}
    assert set(returned_symbols).issubset(valid_symbols), (
        f"Unexpected symbols in response: {set(returned_symbols) - valid_symbols}"
    )


@pytest.mark.parametrize("symbol", ["BTC", "ETH", "SOL"])
def test_analyze_single_symbol(symbol: str):
    """Per-symbol pipeline via /api/analyze/{symbol}.

    Validates:
    - 200 status
    - Response body passes _assert_valid_signal
    - 'symbol' in response matches requested symbol
    """
    # Each symbol requires 3 LLM calls; allow up to 300s for a single symbol.
    with httpx.Client(timeout=300) as client:
        r = client.get(f"{BASE_URL}/api/analyze/{symbol}")

    assert r.status_code == 200, (
        f"/api/analyze/{symbol} returned {r.status_code}: {r.text[:500]}"
    )

    body = r.json()
    _assert_valid_signal(body)
    assert body["symbol"] == symbol, (
        f"Response symbol '{body['symbol']}' does not match requested '{symbol}'"
    )


def test_morning_report_response_shape_matches_mock():
    """Regression: real /morning-report and mock share identical field structure.

    Catches the 'mock-vs-real rendering bug' where the real API returns different
    field names than the mock, causing the dashboard to silently display empty data.

    Both responses must have:
    - Identical top-level keys: timestamp, count, signals
    - Each signal with identical field names (values may differ)
    """
    with httpx.Client(timeout=600) as client:
        mock_r = client.get(f"{BASE_URL}/api/morning-report-mock")
        assert mock_r.status_code == 200, \
            f"/api/morning-report-mock returned {mock_r.status_code}"

        real_r = client.get(
            f"{BASE_URL}/api/morning-report",
            params={"symbols": "BTC"},
            timeout=300
        )
        assert real_r.status_code == 200, \
            f"/api/morning-report?symbols=BTC returned {real_r.status_code}: {real_r.text[:500]}"

    mock_body = mock_r.json()
    real_body = real_r.json()

    # Top-level keys must match
    mock_top_keys = set(mock_body.keys())
    real_top_keys = set(real_body.keys())
    assert mock_top_keys == real_top_keys, (
        f"Top-level key mismatch.\n"
        f"  Mock has:  {sorted(mock_top_keys)}\n"
        f"  Real has:  {sorted(real_top_keys)}\n"
        f"  Missing from real: {mock_top_keys - real_top_keys}\n"
        f"  Extra in real:     {real_top_keys - mock_top_keys}"
    )

    # Per-signal field names must match (pick first signal from each)
    mock_signals = mock_body.get("signals", [])
    real_signals = real_body.get("signals", [])

    if mock_signals and real_signals:
        mock_signal_keys = set(mock_signals[0].keys())
        real_signal_keys = set(real_signals[0].keys())

        assert mock_signal_keys == real_signal_keys, (
            f"Signal field key mismatch.\n"
            f"  Mock has:  {sorted(mock_signal_keys)}\n"
            f"  Real has:  {sorted(real_signal_keys)}\n"
            f"  Missing from real: {mock_signal_keys - real_signal_keys}\n"
            f"  Extra in real:     {real_signal_keys - mock_signal_keys}"
        )
