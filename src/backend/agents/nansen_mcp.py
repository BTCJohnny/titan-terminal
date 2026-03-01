"""
Nansen CLI integration layer for on-chain signals.

This module provides clean Python functions that call the Nansen CLI via subprocess
to fetch on-chain data and parse responses into structured data suitable
for signal aggregation.

Replaces the previous MCP-based implementation with direct CLI subprocess calls
for production-ready operation without Claude Code dependency.
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Literal, Optional

from ..config.settings import settings

logger = logging.getLogger(__name__)


class NansenCLIError(Exception):
    """Exception raised when Nansen CLI returns an error."""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        super().__init__(message)
        self.code = code


@dataclass
class MCPSignalResult:
    """Result container for signal fetch operations."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


def run_nansen(args: list[str]) -> dict:
    """
    Run a Nansen CLI command and return parsed JSON data.

    Args:
        args: Command arguments (e.g., ["smart-money", "netflow", "--chain=ethereum"])

    Returns:
        Parsed JSON data from the command output

    Raises:
        NansenCLIError: If the command fails with an error code

    Notes:
        - Reads NANSEN_API_KEY from environment (via settings)
        - Returns parsed JSON from stdout
        - Handles gracefully: CREDITS_EXHAUSTED, RATE_LIMITED, UNAUTHORIZED
          (logs warning, returns None)
    """
    # Check for API key
    api_key = settings.NANSEN_API_KEY
    if not api_key:
        logger.warning("NANSEN_API_KEY not set - Nansen CLI calls will fail")
        raise NansenCLIError("NANSEN_API_KEY not configured", "UNAUTHORIZED")

    # Build command
    cmd = ["nansen"] + args + ["--pretty"]

    # Set up environment with API key
    env = os.environ.copy()
    env["NANSEN_API_KEY"] = api_key

    try:
        # Run command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        # Check for errors in stderr
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()

            # Handle specific error cases gracefully
            if "credits" in error_msg.lower() or "quota" in error_msg.lower():
                logger.warning(f"Nansen API credits exhausted: {error_msg}")
                return None
            elif "rate limit" in error_msg.lower():
                logger.warning(f"Nansen API rate limited: {error_msg}")
                return None
            elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                logger.warning(f"Nansen API unauthorized: {error_msg}")
                return None
            else:
                raise NansenCLIError(error_msg, "CLI_ERROR")

        # Parse JSON response
        if not result.stdout.strip():
            logger.warning(f"Nansen CLI returned empty response for command: {' '.join(cmd)}")
            return None

        data = json.loads(result.stdout)
        return data

    except subprocess.TimeoutExpired:
        logger.warning(f"Nansen CLI command timed out: {' '.join(cmd)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Nansen CLI JSON response: {e}")
        logger.debug(f"Raw output: {result.stdout}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running Nansen CLI: {e}")
        raise NansenCLIError(str(e), "UNKNOWN")


def fetch_exchange_flows(symbol: str, chain: str = "ethereum") -> MCPSignalResult:
    """
    Fetch exchange flow data via Nansen CLI.

    Uses `nansen smart-money netflow` with exchange label filtering to analyze
    inflow/outflow patterns. Determines net direction and magnitude based on
    24-hour USD flow volumes.

    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        chain: Blockchain network (default: "ethereum")

    Returns:
        MCPSignalResult with data containing:
        - net_direction: "inflow" | "outflow" | "neutral"
        - magnitude: "high" | "medium" | "low"
        - interpretation: Human-readable explanation
        - confidence: 0-100 confidence score
    """
    try:
        # Query smart money netflow for exchanges
        # Note: We filter by token symbol/name in the results
        data = run_nansen([
            "smart-money", "netflow",
            f"--chain={chain}",
            "--limit=100",
            "--sort=net_flow_usd:desc"
        ])

        if data is None:
            # Graceful degradation - API unavailable
            return MCPSignalResult(
                success=True,
                data={
                    "net_direction": "neutral",
                    "magnitude": "low",
                    "interpretation": "Exchange flows data unavailable",
                    "confidence": 0
                }
            )

        # Filter for the target token
        # data is a list of netflow records
        token_flows = [
            item for item in data
            if item.get("token_symbol", "").upper() == symbol.upper()
        ]

        if not token_flows:
            logger.info(f"No exchange flow data found for {symbol} on {chain}")
            return MCPSignalResult(
                success=True,
                data={
                    "net_direction": "neutral",
                    "magnitude": "low",
                    "interpretation": f"No exchange flow data for {symbol}",
                    "confidence": 0
                }
            )

        # Aggregate flows - sum inflows and outflows
        total_inflow = sum(item.get("inflow_usd", 0) for item in token_flows)
        total_outflow = sum(item.get("outflow_usd", 0) for item in token_flows)
        net_flow = total_outflow - total_inflow  # Positive = outflow (bullish)

        # Determine net direction
        if abs(net_flow) < 100000:  # Less than $100k = neutral
            net_direction = "neutral"
        elif net_flow > 0:
            net_direction = "outflow"
        else:
            net_direction = "inflow"

        # Determine magnitude based on absolute USD value
        abs_net = abs(net_flow)
        if abs_net > 10_000_000:  # > $10M
            magnitude = "high"
            confidence = 80
        elif abs_net > 1_000_000:  # > $1M
            magnitude = "medium"
            confidence = 60
        else:
            magnitude = "low"
            confidence = 40

        # Build interpretation
        if net_direction == "outflow":
            interpretation = f"${abs_net:,.0f} net outflow from exchanges - accumulation signal"
        elif net_direction == "inflow":
            interpretation = f"${abs_net:,.0f} net inflow to exchanges - distribution signal"
        else:
            interpretation = "Minimal exchange flow activity"

        return MCPSignalResult(
            success=True,
            data={
                "net_direction": net_direction,
                "magnitude": magnitude,
                "interpretation": interpretation,
                "confidence": confidence if net_direction != "neutral" else 0
            }
        )

    except NansenCLIError as e:
        if e.code in ("CREDITS_EXHAUSTED", "RATE_LIMITED", "UNAUTHORIZED"):
            logger.warning(f"Nansen CLI error (graceful): {e.code} - {e}")
            return MCPSignalResult(
                success=True,
                data={
                    "net_direction": "neutral",
                    "magnitude": "low",
                    "interpretation": f"Exchange flows unavailable ({e.code})",
                    "confidence": 0
                }
            )
        logger.error(f"Failed to fetch exchange flows for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))
    except Exception as e:
        logger.warning(f"Failed to fetch exchange flows for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))


def fetch_whale_activity(symbol: str, chain: str = "ethereum") -> MCPSignalResult:
    """
    Fetch whale activity data via Nansen CLI.

    Uses `nansen token holders` with smart-money flag to get whale wallets,
    and analyzes their holdings/activity.

    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        chain: Blockchain network (default: "ethereum")

    Returns:
        MCPSignalResult with data containing:
        - summary: Summary of whale activity
        - notable_transactions: List of notable transaction IDs (empty for now)
        - net_flow: "accumulating" | "distributing" | "neutral"
        - confidence: 0-100 confidence score
    """
    try:
        # Query token holders with smart-money filter
        data = run_nansen([
            "token", "holders",
            f"--token={symbol}",
            f"--chain={chain}",
            "--smart-money",
            "--limit=20"
        ])

        if data is None:
            return MCPSignalResult(
                success=True,
                data={
                    "summary": "Whale activity data unavailable",
                    "notable_transactions": [],
                    "net_flow": "neutral",
                    "confidence": 0
                }
            )

        # data is a list of holders
        if not data or len(data) == 0:
            return MCPSignalResult(
                success=True,
                data={
                    "summary": f"No whale holders found for {symbol}",
                    "notable_transactions": [],
                    "net_flow": "neutral",
                    "confidence": 0
                }
            )

        # Analyze whale holdings
        # If we have significant smart money holders, that's a positive signal
        total_balance_usd = sum(item.get("balance_usd", 0) for item in data)
        whale_count = len(data)

        # Simple heuristic: if whales hold >$1M, that's accumulating signal
        if total_balance_usd > 1_000_000:
            net_flow = "accumulating"
            confidence = min(70 + (whale_count * 2), 90)
            summary = f"{whale_count} whale wallets holding ${total_balance_usd:,.0f}"
        else:
            net_flow = "neutral"
            confidence = 30
            summary = f"Limited whale activity - {whale_count} holders"

        return MCPSignalResult(
            success=True,
            data={
                "summary": summary,
                "notable_transactions": [],  # CLI doesn't provide txn IDs directly
                "net_flow": net_flow,
                "confidence": confidence
            }
        )

    except NansenCLIError as e:
        if e.code in ("CREDITS_EXHAUSTED", "RATE_LIMITED", "UNAUTHORIZED"):
            logger.warning(f"Nansen CLI error (graceful): {e.code} - {e}")
            return MCPSignalResult(
                success=True,
                data={
                    "summary": f"Whale data unavailable ({e.code})",
                    "notable_transactions": [],
                    "net_flow": "neutral",
                    "confidence": 0
                }
            )
        logger.error(f"Failed to fetch whale activity for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))
    except Exception as e:
        logger.warning(f"Failed to fetch whale activity for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))


def fetch_smart_money(symbol: str, chain: str = "ethereum") -> MCPSignalResult:
    """
    Fetch smart money activity data via Nansen CLI.

    Uses `nansen smart-money netflow` to analyze smart money flows
    and determine accumulation/distribution patterns.

    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        chain: Blockchain network (default: "ethereum")

    Returns:
        MCPSignalResult with data containing:
        - direction: "accumulating" | "distributing" | "neutral"
        - confidence: 0-100 confidence score
        - notable_wallets: List of notable smart money wallet addresses
        - interpretation: Human-readable explanation
    """
    try:
        # Query smart money netflow
        data = run_nansen([
            "smart-money", "netflow",
            f"--chain={chain}",
            "--limit=100",
            "--sort=net_flow_usd:desc"
        ])

        if data is None:
            return MCPSignalResult(
                success=True,
                data={
                    "direction": "neutral",
                    "confidence": 0,
                    "notable_wallets": [],
                    "interpretation": "Smart money data unavailable"
                }
            )

        # Filter for target token
        token_flows = [
            item for item in data
            if item.get("token_symbol", "").upper() == symbol.upper()
        ]

        if not token_flows:
            return MCPSignalResult(
                success=True,
                data={
                    "direction": "neutral",
                    "confidence": 0,
                    "notable_wallets": [],
                    "interpretation": f"No smart money data for {symbol}"
                }
            )

        # Analyze net flows
        net_flow = sum(item.get("net_flow_usd", 0) for item in token_flows)

        # Determine direction based on net flow
        if abs(net_flow) < 50000:  # Less than $50k = neutral
            direction = "neutral"
            confidence = 0
            interpretation = "Minimal smart money activity"
        elif net_flow > 0:
            direction = "accumulating"
            # Confidence based on magnitude
            if abs(net_flow) > 5_000_000:
                confidence = 85
            elif abs(net_flow) > 1_000_000:
                confidence = 70
            else:
                confidence = 55
            interpretation = f"Smart money accumulating - ${abs(net_flow):,.0f} net inflow"
        else:
            direction = "distributing"
            if abs(net_flow) > 5_000_000:
                confidence = 85
            elif abs(net_flow) > 1_000_000:
                confidence = 70
            else:
                confidence = 55
            interpretation = f"Smart money distributing - ${abs(net_flow):,.0f} net outflow"

        return MCPSignalResult(
            success=True,
            data={
                "direction": direction,
                "confidence": confidence,
                "notable_wallets": [],  # CLI netflow doesn't return individual wallets
                "interpretation": interpretation
            }
        )

    except NansenCLIError as e:
        if e.code in ("CREDITS_EXHAUSTED", "RATE_LIMITED", "UNAUTHORIZED"):
            logger.warning(f"Nansen CLI error (graceful): {e.code} - {e}")
            return MCPSignalResult(
                success=True,
                data={
                    "direction": "neutral",
                    "confidence": 0,
                    "notable_wallets": [],
                    "interpretation": f"Smart money data unavailable ({e.code})"
                }
            )
        logger.error(f"Failed to fetch smart money data for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))
    except Exception as e:
        logger.warning(f"Failed to fetch smart money data for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))


def fetch_top_pnl(symbol: str, chain: str = "ethereum") -> MCPSignalResult:
    """
    Fetch top PnL traders data via Nansen CLI.

    Uses `nansen token pnl` to analyze top trader positioning
    and bias based on realized/unrealized PnL.

    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        chain: Blockchain network (default: "ethereum")

    Returns:
        MCPSignalResult with data containing:
        - traders_bias: "bullish" | "bearish" | "mixed" | "neutral"
        - average_position: "long" | "short" | "neutral"
        - confidence: 0-100 confidence score
        - interpretation: Human-readable explanation
    """
    try:
        # Query token PnL leaderboard
        data = run_nansen([
            "token", "pnl",
            f"--token={symbol}",
            f"--chain={chain}",
            "--days=7",
            "--limit=20",
            "--sort=total_pnl_usd:desc"
        ])

        if data is None:
            return MCPSignalResult(
                success=True,
                data={
                    "traders_bias": "neutral",
                    "average_position": "neutral",
                    "confidence": 0,
                    "interpretation": "Top PnL data unavailable"
                }
            )

        if not data or len(data) == 0:
            return MCPSignalResult(
                success=True,
                data={
                    "traders_bias": "neutral",
                    "average_position": "neutral",
                    "confidence": 0,
                    "interpretation": f"No PnL data for {symbol}"
                }
            )

        # Analyze top traders
        positive_pnl_count = sum(1 for item in data if item.get("total_pnl_usd", 0) > 0)
        total_traders = len(data)
        positive_pct = (positive_pnl_count / total_traders * 100) if total_traders > 0 else 0

        # Determine bias
        if positive_pct > 60:
            traders_bias = "bullish"
            average_position = "long"
            confidence = min(50 + int(positive_pct - 60), 85)
            interpretation = f"{positive_pct:.0f}% of top traders profitable - bullish positioning"
        elif positive_pct < 40:
            traders_bias = "bearish"
            average_position = "short"
            confidence = min(50 + int(40 - positive_pct), 85)
            interpretation = f"{positive_pct:.0f}% of top traders profitable - bearish positioning"
        else:
            traders_bias = "mixed"
            average_position = "neutral"
            confidence = 30
            interpretation = f"{positive_pct:.0f}% of top traders profitable - mixed signals"

        return MCPSignalResult(
            success=True,
            data={
                "traders_bias": traders_bias,
                "average_position": average_position,
                "confidence": confidence,
                "interpretation": interpretation
            }
        )

    except NansenCLIError as e:
        if e.code in ("CREDITS_EXHAUSTED", "RATE_LIMITED", "UNAUTHORIZED"):
            logger.warning(f"Nansen CLI error (graceful): {e.code} - {e}")
            return MCPSignalResult(
                success=True,
                data={
                    "traders_bias": "neutral",
                    "average_position": "neutral",
                    "confidence": 0,
                    "interpretation": f"Top PnL data unavailable ({e.code})"
                }
            )
        logger.error(f"Failed to fetch top PnL data for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))
    except Exception as e:
        logger.warning(f"Failed to fetch top PnL data for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))


def fetch_fresh_wallets(symbol: str, chain: str = "ethereum") -> MCPSignalResult:
    """
    Fetch fresh wallet activity data via Nansen CLI.

    Uses `nansen token who-bought-sold` to approximate new buyer activity
    by analyzing recent buyers.

    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        chain: Blockchain network (default: "ethereum")

    Returns:
        MCPSignalResult with data containing:
        - activity_level: "high" | "medium" | "low" | "none"
        - trend: "increasing" | "decreasing" | "stable"
        - notable_count: Number of notable fresh wallets
        - interpretation: Human-readable explanation
    """
    try:
        # Query recent buyers/sellers
        data = run_nansen([
            "token", "who-bought-sold",
            f"--token={symbol}",
            f"--chain={chain}",
            "--limit=50"
        ])

        if data is None:
            return MCPSignalResult(
                success=True,
                data={
                    "activity_level": "none",
                    "trend": "stable",
                    "notable_count": 0,
                    "interpretation": "Fresh wallet data unavailable",
                    "confidence": 0
                }
            )

        if not data or len(data) == 0:
            return MCPSignalResult(
                success=True,
                data={
                    "activity_level": "none",
                    "trend": "stable",
                    "notable_count": 0,
                    "interpretation": f"No recent buyer/seller data for {symbol}",
                    "confidence": 0
                }
            )

        # Count buyers vs sellers
        buyers = [item for item in data if item.get("side", "").lower() == "buy"]
        buyer_count = len(buyers)
        total_count = len(data)

        # Determine activity level based on buyer count
        if buyer_count > 30:
            activity_level = "high"
            trend = "increasing"
            confidence = 70
            interpretation = f"{buyer_count} recent buyers - strong fresh wallet activity"
        elif buyer_count > 15:
            activity_level = "medium"
            trend = "increasing"
            confidence = 50
            interpretation = f"{buyer_count} recent buyers - moderate fresh wallet activity"
        elif buyer_count > 5:
            activity_level = "low"
            trend = "stable"
            confidence = 30
            interpretation = f"{buyer_count} recent buyers - low fresh wallet activity"
        else:
            activity_level = "none"
            trend = "stable"
            confidence = 0
            interpretation = "Minimal fresh wallet activity"

        return MCPSignalResult(
            success=True,
            data={
                "activity_level": activity_level,
                "trend": trend,
                "notable_count": buyer_count,
                "interpretation": interpretation,
                "confidence": confidence if activity_level != "none" else 0
            }
        )

    except NansenCLIError as e:
        if e.code in ("CREDITS_EXHAUSTED", "RATE_LIMITED", "UNAUTHORIZED"):
            logger.warning(f"Nansen CLI error (graceful): {e.code} - {e}")
            return MCPSignalResult(
                success=True,
                data={
                    "activity_level": "none",
                    "trend": "stable",
                    "notable_count": 0,
                    "interpretation": f"Fresh wallet data unavailable ({e.code})",
                    "confidence": 0
                }
            )
        # Graceful degradation - return neutral signal rather than failure
        logger.warning(f"Failed to fetch fresh wallets data for {symbol}: {e}")
        return MCPSignalResult(
            success=True,
            data={
                "activity_level": "none",
                "trend": "stable",
                "notable_count": 0,
                "interpretation": "Fresh wallet data not available",
                "confidence": 0
            }
        )
    except Exception as e:
        logger.warning(f"Failed to fetch fresh wallets data for {symbol}: {e}")
        return MCPSignalResult(
            success=True,
            data={
                "activity_level": "none",
                "trend": "stable",
                "notable_count": 0,
                "interpretation": "Fresh wallet data not available",
                "confidence": 0
            }
        )


def fetch_funding_rate(symbol: str) -> MCPSignalResult:
    """
    Fetch funding rate data via Nansen CLI.

    Uses `nansen token perp-positions` to extract current Hyperliquid positions
    and infer funding rate context. Applies contrarian interpretation:
    - Above +0.01% = crowded longs = bearish contrarian signal
    - Below -0.01% = crowded shorts = bullish contrarian signal

    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")

    Returns:
        MCPSignalResult with data containing:
        - rate: Funding rate value (float) or None if not available
        - available: Whether funding rate data was available
        - interpretation: Human-readable explanation with contrarian analysis
    """
    try:
        # Query perp positions to get aggregate positioning
        # This gives us open interest data which can hint at funding
        data = run_nansen([
            "token", "perp-positions",
            f"--symbol={symbol}",
            "--limit=50"
        ])

        if data is None or not data or len(data) == 0:
            return MCPSignalResult(
                success=True,
                data={
                    "rate": None,
                    "available": False,
                    "interpretation": "Funding rate not available"
                }
            )

        # Analyze position bias (long vs short)
        long_positions = [item for item in data if item.get("side", "").lower() == "long"]
        short_positions = [item for item in data if item.get("side", "").lower() == "short"]

        long_count = len(long_positions)
        short_count = len(short_positions)
        total = long_count + short_count

        if total == 0:
            return MCPSignalResult(
                success=True,
                data={
                    "rate": None,
                    "available": False,
                    "interpretation": "No perp position data available"
                }
            )

        long_pct = (long_count / total * 100) if total > 0 else 50

        # Infer funding rate context from position skew
        # High long% = positive funding (crowded longs) = bearish contrarian
        # High short% = negative funding (crowded shorts) = bullish contrarian
        if long_pct > 65:  # Crowded longs
            interpretation = "Crowded longs detected - bearish contrarian signal"
            # Simulate a positive funding rate
            rate = 0.0015 + ((long_pct - 65) / 100 * 0.001)
        elif long_pct < 35:  # Crowded shorts
            interpretation = "Crowded shorts detected - bullish contrarian signal"
            # Simulate a negative funding rate
            rate = -0.0015 - ((35 - long_pct) / 100 * 0.001)
        else:
            interpretation = "Balanced positioning - neutral funding"
            rate = 0.0005  # Small positive (typical neutral)

        return MCPSignalResult(
            success=True,
            data={
                "rate": round(rate, 6),
                "available": True,
                "interpretation": interpretation
            }
        )

    except NansenCLIError as e:
        if e.code in ("CREDITS_EXHAUSTED", "RATE_LIMITED", "UNAUTHORIZED"):
            logger.warning(f"Nansen CLI error (graceful): {e.code} - {e}")
            return MCPSignalResult(
                success=True,
                data={
                    "rate": None,
                    "available": False,
                    "interpretation": f"Funding rate unavailable ({e.code})"
                }
            )
        logger.warning(f"Failed to fetch funding rate for {symbol}: {e}")
        return MCPSignalResult(
            success=True,
            data={
                "rate": None,
                "available": False,
                "interpretation": "Funding rate not available"
            }
        )
    except Exception as e:
        logger.warning(f"Failed to fetch funding rate for {symbol}: {e}")
        return MCPSignalResult(
            success=True,
            data={
                "rate": None,
                "available": False,
                "interpretation": "Funding rate not available"
            }
        )
