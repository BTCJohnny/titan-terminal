"""Obsidian vault logger for Nansen signal analysis.

This module provides functionality to log every Nansen analysis to an Obsidian vault
for historical tracking and review. Logs are written as markdown table rows to
signal-combinations.md.

Uses direct Python file I/O (not MCP) for vault logging.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import NansenSignal

logger = logging.getLogger(__name__)

# Obsidian vault path configuration
VAULT_PATH = Path("/Users/johnny_main/Developer/obsidian-vault/obsidian-vault/agents/nansen")
SIGNAL_LOG_FILE = VAULT_PATH / "signal-combinations.md"


def _ensure_log_file_exists() -> None:
    """Ensure the signal log file exists with proper header.

    Creates the vault directory structure and log file if they don't exist.
    If the file already exists, does nothing.
    """
    if SIGNAL_LOG_FILE.exists():
        return

    # Create directory structure
    os.makedirs(VAULT_PATH, exist_ok=True)

    # Create file with header
    header = """# Nansen Signal Combinations Log

| Date | Symbol | Exchange Flow | Smart Money | Whales | Top PnL | Fresh Wallets | Funding | Overall | Confidence | Signals B/Be |
|------|--------|---------------|-------------|--------|---------|---------------|---------|---------|------------|--------------|
"""
    with open(SIGNAL_LOG_FILE, "w") as f:
        f.write(header)

    logger.info(f"Created Nansen signal log file at {SIGNAL_LOG_FILE}")


def log_nansen_analysis(signal: "NansenSignal") -> bool:
    """Log a Nansen analysis to the Obsidian vault.

    Appends a markdown table row to signal-combinations.md with all signal data.
    Creates the log file with header if it doesn't exist.

    Args:
        signal: NansenSignal Pydantic model to log

    Returns:
        True if logging succeeded, False if failed

    Note:
        Failures are logged but do not raise exceptions (graceful degradation).
        Analysis should continue even if vault logging fails.
    """
    try:
        # Ensure log file exists
        _ensure_log_file_exists()

        # Format timestamp
        date_str = signal.timestamp.strftime("%Y-%m-%d %H:%M")

        # Extract signal values
        exchange_flow = signal.exchange_flows.net_direction
        smart_money = signal.smart_money.direction
        whales = signal.whale_activity.net_flow
        top_pnl = signal.top_pnl.traders_bias
        fresh_wallets = signal.fresh_wallets.activity_level

        # Handle optional funding rate
        if signal.funding_rate and signal.funding_rate.available:
            funding = f"{signal.funding_rate.rate:.4f}"
        else:
            funding = "N/A"

        # Overall assessment
        overall = signal.overall_signal.bias
        confidence = signal.overall_signal.confidence

        # Signal counts
        signals_b_be = f"{signal.signal_count_bullish}/{signal.signal_count_bearish}"

        # Build table row
        row = f"| {date_str} | {signal.symbol} | {exchange_flow} | {smart_money} | {whales} | {top_pnl} | {fresh_wallets} | {funding} | {overall} | {confidence} | {signals_b_be} |"

        # Append to file
        with open(SIGNAL_LOG_FILE, "a") as f:
            f.write(row + "\n")

        logger.debug(f"Logged {signal.symbol} analysis to Obsidian vault")
        return True

    except Exception as e:
        logger.warning(f"Failed to log Nansen analysis to vault: {e}")
        return False
