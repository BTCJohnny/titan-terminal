"""
MCP integration layer for Nansen on-chain signals.

This module provides clean Python functions that prepare MCP tool requests
for Nansen on-chain data and parse responses into structured data suitable
for signal aggregation.

NOTE: These functions prepare request parameters and process MCP responses.
Actual MCP tool invocation happens via Claude's tool calling when the agent
with MCP access executes these functions.
"""

import logging
from dataclasses import dataclass
from typing import Literal, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPSignalResult:
    """Result container for MCP signal fetch operations."""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


def fetch_exchange_flows(symbol: str, chain: str = "ethereum") -> MCPSignalResult:
    """
    Fetch exchange flow data via MCP.

    Uses mcp__nansen__token_flows with holder_segment="exchange" to analyze
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
        # MCP tool parameters
        tool_name = "mcp__nansen__token_flows"
        params = {
            "symbol": symbol,
            "chain": chain,
            "holder_segment": "exchange",
            "dateRange": {
                "from": "24H_AGO",
                "to": "NOW"
            }
        }

        # NOTE: Actual MCP invocation happens in agent context
        # This function will be called by an agent with MCP access
        # For now, return the request structure
        logger.info(f"Preparing exchange flows request for {symbol} on {chain}")

        # Parse response (placeholder - actual implementation will process MCP response)
        # When integrated with MCP, this will receive the response data
        # and parse it to determine:
        # - net_direction based on inflows vs outflows
        # - magnitude based on USD volume thresholds (high > $10M, medium > $1M)
        # - interpretation based on the patterns
        # - confidence based on data quality and volume

        data = {
            "net_direction": "neutral",
            "magnitude": "low",
            "interpretation": "MCP integration pending - exchange flows will be analyzed",
            "confidence": 0,
            "mcp_tool": tool_name,
            "mcp_params": params
        }

        return MCPSignalResult(success=True, data=data)

    except Exception as e:
        logger.warning(f"Failed to fetch exchange flows for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))


def fetch_whale_activity(symbol: str, chain: str = "ethereum") -> MCPSignalResult:
    """
    Fetch whale activity data via MCP.

    Uses mcp__nansen__token_flows with holder_segment="whale" for flow data
    and mcp__nansen__token_current_top_holders for notable whale wallets.

    Args:
        symbol: Token symbol (e.g., "BTC", "ETH")
        chain: Blockchain network (default: "ethereum")

    Returns:
        MCPSignalResult with data containing:
        - summary: Summary of whale activity
        - notable_transactions: List of notable transaction IDs
        - net_flow: "accumulating" | "distributing" | "neutral"
        - confidence: 0-100 confidence score
    """
    try:
        # MCP tool parameters for flows
        flow_tool = "mcp__nansen__token_flows"
        flow_params = {
            "symbol": symbol,
            "chain": chain,
            "holder_segment": "whale",
            "dateRange": {
                "from": "24H_AGO",
                "to": "NOW"
            }
        }

        # MCP tool parameters for top holders
        holders_tool = "mcp__nansen__token_current_top_holders"
        holders_params = {
            "symbol": symbol,
            "chain": chain,
            "label_type": "whale"
        }

        logger.info(f"Preparing whale activity request for {symbol} on {chain}")

        # Parse response (placeholder - actual implementation will process MCP response)
        # When integrated with MCP, this will:
        # - Analyze flow data to determine net_flow (accumulating if inflows > outflows)
        # - Extract notable transactions from flow data
        # - Get top whale addresses from holders data
        # - Generate summary based on activity patterns
        # - Calculate confidence based on data quality

        data = {
            "summary": "MCP integration pending - whale activity will be analyzed",
            "notable_transactions": [],
            "net_flow": "neutral",
            "confidence": 0,
            "mcp_tools": [
                {"name": flow_tool, "params": flow_params},
                {"name": holders_tool, "params": holders_params}
            ]
        }

        return MCPSignalResult(success=True, data=data)

    except Exception as e:
        logger.warning(f"Failed to fetch whale activity for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))


def fetch_smart_money(symbol: str, chain: str = "ethereum") -> MCPSignalResult:
    """
    Fetch smart money activity data via MCP.

    Uses mcp__nansen__token_flows with holder_segment="smart_money" for flow data
    and mcp__nansen__smart_traders_and_funds_token_balances for balance change context.

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
        # MCP tool parameters for flows
        flow_tool = "mcp__nansen__token_flows"
        flow_params = {
            "symbol": symbol,
            "chain": chain,
            "holder_segment": "smart_money",
            "dateRange": {
                "from": "24H_AGO",
                "to": "NOW"
            }
        }

        # MCP tool parameters for balances
        balance_tool = "mcp__nansen__smart_traders_and_funds_token_balances"
        balance_params = {
            "symbol": symbol,
            "chain": chain
        }

        logger.info(f"Preparing smart money request for {symbol} on {chain}")

        # Parse response (placeholder - actual implementation will process MCP response)
        # When integrated with MCP, this will:
        # - Analyze flow data for net inflows/outflows
        # - Check balance changes (positive 24h = accumulating)
        # - Determine direction: accumulating if net inflows + positive balance change
        # - Extract top 5 addresses from balance data for notable_wallets
        # - Calculate confidence based on data consistency and volume

        data = {
            "direction": "neutral",
            "confidence": 0,
            "notable_wallets": [],
            "interpretation": "MCP integration pending - smart money activity will be analyzed",
            "mcp_tools": [
                {"name": flow_tool, "params": flow_params},
                {"name": balance_tool, "params": balance_params}
            ]
        }

        return MCPSignalResult(success=True, data=data)

    except Exception as e:
        logger.warning(f"Failed to fetch smart money data for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))


def fetch_top_pnl(symbol: str, chain: str = "ethereum") -> MCPSignalResult:
    """
    Fetch top PnL traders data via MCP.

    Uses mcp__nansen__token_pnl_leaderboard to analyze top trader positioning
    and bias based on 7-day PnL performance.

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
        # MCP tool parameters
        tool_name = "mcp__nansen__token_pnl_leaderboard"
        params = {
            "symbol": symbol,
            "chain": chain,
            "dateRange": {
                "from": "7D_AGO",
                "to": "NOW"
            },
            "order_by": "pnlUsdTotal"
        }

        logger.info(f"Preparing top PnL request for {symbol} on {chain}")

        # Parse response (placeholder - actual implementation will process MCP response)
        # When integrated with MCP, this will:
        # - Analyze top 10 traders from leaderboard
        # - Count positive vs negative PnL
        # - Determine traders_bias: bullish if >60% positive, bearish if <40%, mixed otherwise
        # - Determine average_position: long if net positive, short if net negative
        # - Calculate confidence based on data consistency and trader count

        data = {
            "traders_bias": "neutral",
            "average_position": "neutral",
            "confidence": 0,
            "interpretation": "MCP integration pending - top PnL traders will be analyzed",
            "mcp_tool": tool_name,
            "mcp_params": params
        }

        return MCPSignalResult(success=True, data=data)

    except Exception as e:
        logger.warning(f"Failed to fetch top PnL data for {symbol}: {e}")
        return MCPSignalResult(success=False, error=str(e))
