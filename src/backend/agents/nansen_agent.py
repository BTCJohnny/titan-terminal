"""Nansen On-Chain Agent - Production implementation using 5-signal framework."""
import logging
from datetime import datetime
from typing import Optional

from ..models import NansenSignal
from ..models.nansen_signal import (
    ExchangeFlows, FreshWallets, SmartMoney, TopPnL,
    WhaleActivity, FundingRate, OnChainOverall
)
from .nansen_mcp import (
    fetch_exchange_flows, fetch_smart_money, fetch_whale_activity,
    fetch_top_pnl, fetch_fresh_wallets, fetch_funding_rate
)
from .vault_logger import log_nansen_analysis

logger = logging.getLogger(__name__)


class NansenAgent:
    """Production Nansen on-chain agent using 5-signal framework.

    Fetches 5 signals via Nansen MCP tools:
    1. Exchange flows (inflow/outflow)
    2. Smart money activity (accumulating/distributing)
    3. Whale activity (accumulating/distributing)
    4. Top PnL wallets (bullish/bearish bias)
    5. Fresh wallets (new buyer activity)

    Plus funding rate from Hyperliquid for contrarian overlay.

    Scoring: 4-5 bullish = ACCUMULATION, 2-3 = MIXED, 0-1 = DISTRIBUTION
    """

    BULLISH_THRESHOLD = 4  # 4-5 signals = bullish
    BEARISH_THRESHOLD = 1  # 0-1 signals = bearish
    FUNDING_RATE_THRESHOLD = 0.0001  # 0.01%

    def __init__(self, chain: str = "ethereum"):
        """Initialize Nansen agent.

        Args:
            chain: Blockchain network to analyze (default: "ethereum")
        """
        self.chain = chain

    def _classify_signal(self, signal_type: str, data: dict) -> tuple[bool, bool, int]:
        """Classify a single signal as bullish, bearish, or neutral.

        Args:
            signal_type: Type of signal ("exchange_flows", "smart_money", etc.)
            data: Signal data dict from MCP fetch function

        Returns:
            Tuple of (is_bullish, is_bearish, confidence)
            Only one of is_bullish/is_bearish can be True
        """
        confidence = data.get("confidence", 0)

        # Only classify if confidence > 50
        if confidence <= 50:
            return (False, False, confidence)

        if signal_type == "exchange_flows":
            # Outflow = bullish (accumulation), inflow = bearish (distribution)
            net_direction = data.get("net_direction", "neutral")
            if net_direction == "outflow":
                return (True, False, confidence)
            elif net_direction == "inflow":
                return (False, True, confidence)

        elif signal_type == "smart_money":
            # Accumulating = bullish, distributing = bearish
            direction = data.get("direction", "neutral")
            if direction == "accumulating":
                return (True, False, confidence)
            elif direction == "distributing":
                return (False, True, confidence)

        elif signal_type == "whale_activity":
            # Accumulating = bullish, distributing = bearish
            net_flow = data.get("net_flow", "neutral")
            if net_flow == "accumulating":
                return (True, False, confidence)
            elif net_flow == "distributing":
                return (False, True, confidence)

        elif signal_type == "top_pnl":
            # Bullish bias = bullish, bearish bias = bearish
            traders_bias = data.get("traders_bias", "neutral")
            if traders_bias == "bullish":
                return (True, False, confidence)
            elif traders_bias == "bearish":
                return (False, True, confidence)

        elif signal_type == "fresh_wallets":
            # High activity = bullish, none = bearish
            activity_level = data.get("activity_level", "none")
            if activity_level == "high":
                return (True, False, confidence)
            elif activity_level == "none":
                return (False, True, confidence)

        # Neutral signal
        return (False, False, confidence)

    def _aggregate_signals(
        self,
        exchange_classification: tuple[bool, bool, int],
        smart_money_classification: tuple[bool, bool, int],
        whale_classification: tuple[bool, bool, int],
        top_pnl_classification: tuple[bool, bool, int],
        fresh_wallets_classification: tuple[bool, bool, int]
    ) -> tuple[str, int, list[str], int, int]:
        """Aggregate 5 signals into overall bias and confidence.

        Args:
            exchange_classification: (is_bullish, is_bearish, confidence) for exchange flows
            smart_money_classification: (is_bullish, is_bearish, confidence) for smart money
            whale_classification: (is_bullish, is_bearish, confidence) for whale activity
            top_pnl_classification: (is_bullish, is_bearish, confidence) for top PnL
            fresh_wallets_classification: (is_bullish, is_bearish, confidence) for fresh wallets

        Returns:
            Tuple of (bias, confidence, key_insights, signal_count_bullish, signal_count_bearish)
        """
        classifications = [
            ("Exchange flows", exchange_classification),
            ("Smart money", smart_money_classification),
            ("Whale activity", whale_classification),
            ("Top PnL traders", top_pnl_classification),
            ("Fresh wallets", fresh_wallets_classification)
        ]

        # Count bullish and bearish signals
        bullish_count = sum(1 for _, (is_bullish, _, _) in classifications if is_bullish)
        bearish_count = sum(1 for _, (_, is_bearish, _) in classifications if is_bearish)

        # Determine overall bias
        if bullish_count >= self.BULLISH_THRESHOLD:
            bias = "bullish"
        elif bullish_count <= self.BEARISH_THRESHOLD:
            bias = "bearish"
        else:
            bias = "neutral"

        # Calculate confidence: base 50 + (alignment_bonus * 10), capped at 100
        alignment_bonus = abs(bullish_count - bearish_count)
        confidence = min(50 + (alignment_bonus * 10), 100)

        # Build key insights from high-confidence signals
        key_insights = []
        for name, (is_bullish, is_bearish, conf) in classifications:
            if conf > 50:
                if is_bullish:
                    key_insights.append(f"{name} showing bullish accumulation")
                elif is_bearish:
                    key_insights.append(f"{name} showing bearish distribution")

        return (bias, confidence, key_insights, bullish_count, bearish_count)

    def analyze(self, symbol: str, log_to_vault: bool = True) -> NansenSignal:
        """Analyze on-chain data for a symbol using 5-signal framework.

        Fetches all 6 signals (5 on-chain + funding rate) via MCP integration layer,
        aggregates them into overall assessment, and returns structured NansenSignal.

        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH")
            log_to_vault: Whether to log analysis to Obsidian vault (default: True)

        Returns:
            NansenSignal Pydantic model with complete on-chain analysis
        """
        logger.info(f"Starting Nansen analysis for {symbol}")

        # Fetch all signals
        try:
            exchange_result = fetch_exchange_flows(symbol, self.chain)
            if not exchange_result.success:
                logger.warning(f"Failed to fetch exchange flows for {symbol}: {exchange_result.error}")
        except Exception as e:
            logger.warning(f"Exception fetching exchange flows for {symbol}: {e}")
            exchange_result = type('obj', (object,), {
                'success': False, 'data': None, 'error': str(e)
            })()

        try:
            smart_money_result = fetch_smart_money(symbol, self.chain)
            if not smart_money_result.success:
                logger.warning(f"Failed to fetch smart money for {symbol}: {smart_money_result.error}")
        except Exception as e:
            logger.warning(f"Exception fetching smart money for {symbol}: {e}")
            smart_money_result = type('obj', (object,), {
                'success': False, 'data': None, 'error': str(e)
            })()

        try:
            whale_result = fetch_whale_activity(symbol, self.chain)
            if not whale_result.success:
                logger.warning(f"Failed to fetch whale activity for {symbol}: {whale_result.error}")
        except Exception as e:
            logger.warning(f"Exception fetching whale activity for {symbol}: {e}")
            whale_result = type('obj', (object,), {
                'success': False, 'data': None, 'error': str(e)
            })()

        try:
            top_pnl_result = fetch_top_pnl(symbol, self.chain)
            if not top_pnl_result.success:
                logger.warning(f"Failed to fetch top PnL for {symbol}: {top_pnl_result.error}")
        except Exception as e:
            logger.warning(f"Exception fetching top PnL for {symbol}: {e}")
            top_pnl_result = type('obj', (object,), {
                'success': False, 'data': None, 'error': str(e)
            })()

        try:
            fresh_wallets_result = fetch_fresh_wallets(symbol, self.chain)
            if not fresh_wallets_result.success:
                logger.warning(f"Failed to fetch fresh wallets for {symbol}: {fresh_wallets_result.error}")
        except Exception as e:
            logger.warning(f"Exception fetching fresh wallets for {symbol}: {e}")
            fresh_wallets_result = type('obj', (object,), {
                'success': False, 'data': None, 'error': str(e)
            })()

        try:
            funding_result = fetch_funding_rate(symbol)
            if not funding_result.success:
                logger.warning(f"Failed to fetch funding rate for {symbol}: {funding_result.error}")
        except Exception as e:
            logger.warning(f"Exception fetching funding rate for {symbol}: {e}")
            funding_result = type('obj', (object,), {
                'success': False, 'data': None, 'error': str(e)
            })()

        # Build nested model objects with fallback defaults
        exchange_data = exchange_result.data if exchange_result.success and exchange_result.data else {
            "net_direction": "neutral",
            "magnitude": "low",
            "interpretation": "Exchange flows data unavailable",
            "confidence": 0
        }

        smart_money_data = smart_money_result.data if smart_money_result.success and smart_money_result.data else {
            "direction": "neutral",
            "confidence": 0,
            "notable_wallets": [],
            "interpretation": "Smart money data unavailable"
        }

        whale_data = whale_result.data if whale_result.success and whale_result.data else {
            "summary": "Whale activity data unavailable",
            "notable_transactions": [],
            "net_flow": "neutral",
            "confidence": 0
        }

        top_pnl_data = top_pnl_result.data if top_pnl_result.success and top_pnl_result.data else {
            "traders_bias": "neutral",
            "average_position": "neutral",
            "confidence": 0,
            "interpretation": "Top PnL data unavailable"
        }

        fresh_wallets_data = fresh_wallets_result.data if fresh_wallets_result.success and fresh_wallets_result.data else {
            "activity_level": "none",
            "trend": "stable",
            "notable_count": 0,
            "interpretation": "Fresh wallets data unavailable"
        }

        # Classify each signal
        exchange_classification = self._classify_signal("exchange_flows", exchange_data)
        smart_money_classification = self._classify_signal("smart_money", smart_money_data)
        whale_classification = self._classify_signal("whale_activity", whale_data)
        top_pnl_classification = self._classify_signal("top_pnl", top_pnl_data)
        fresh_wallets_classification = self._classify_signal("fresh_wallets", fresh_wallets_data)

        # Aggregate into overall assessment
        bias, confidence, key_insights, signal_count_bullish, signal_count_bearish = self._aggregate_signals(
            exchange_classification,
            smart_money_classification,
            whale_classification,
            top_pnl_classification,
            fresh_wallets_classification
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            signal_count_bullish,
            signal_count_bearish,
            exchange_classification,
            smart_money_classification,
            whale_classification,
            top_pnl_classification,
            fresh_wallets_classification,
            funding_result
        )

        # Build funding rate model if available
        funding_rate = None
        if funding_result.success and funding_result.data:
            funding_data = funding_result.data
            if funding_data.get("available", False):
                funding_rate = FundingRate(
                    rate=funding_data.get("rate"),
                    available=True,
                    interpretation=funding_data.get("interpretation", "Funding rate analysis")
                )

        # Construct NansenSignal
        signal = NansenSignal(
            symbol=symbol,
            exchange_flows=ExchangeFlows(**exchange_data),
            fresh_wallets=FreshWallets(**fresh_wallets_data),
            smart_money=SmartMoney(**smart_money_data),
            top_pnl=TopPnL(**top_pnl_data),
            whale_activity=WhaleActivity(**whale_data),
            funding_rate=funding_rate,
            overall_signal=OnChainOverall(
                bias=bias,
                confidence=confidence,
                key_insights=key_insights
            ),
            signal_count_bullish=signal_count_bullish,
            signal_count_bearish=signal_count_bearish,
            reasoning=reasoning,
            timestamp=datetime.utcnow()
        )

        logger.debug(f"Generated NansenSignal for {symbol}: {signal.overall_signal.bias} with {signal.overall_signal.confidence}% confidence")

        # Log to Obsidian vault (per NANS-09)
        if log_to_vault:
            if not log_nansen_analysis(signal):
                logger.warning(f"Failed to log analysis for {symbol} to Obsidian vault")
            else:
                logger.debug(f"Logged {symbol} analysis to Obsidian vault")

        return signal

    def _generate_reasoning(
        self,
        bullish_count: int,
        bearish_count: int,
        exchange_classification: tuple[bool, bool, int],
        smart_money_classification: tuple[bool, bool, int],
        whale_classification: tuple[bool, bool, int],
        top_pnl_classification: tuple[bool, bool, int],
        fresh_wallets_classification: tuple[bool, bool, int],
        funding_result
    ) -> str:
        """Generate human-readable reasoning for the overall signal.

        Args:
            bullish_count: Number of bullish signals
            bearish_count: Number of bearish signals
            exchange_classification: Exchange flows classification
            smart_money_classification: Smart money classification
            whale_classification: Whale activity classification
            top_pnl_classification: Top PnL classification
            fresh_wallets_classification: Fresh wallets classification
            funding_result: Funding rate fetch result

        Returns:
            Human-readable reasoning string
        """
        # Map classifications to names
        signal_names = [
            ("exchange flows", exchange_classification),
            ("smart money", smart_money_classification),
            ("whale activity", whale_classification),
            ("top PnL traders", top_pnl_classification),
            ("fresh wallets", fresh_wallets_classification)
        ]

        # Build lists of contributing signals
        bullish_signals = [name for name, (is_bullish, _, _) in signal_names if is_bullish]
        bearish_signals = [name for name, (_, is_bearish, _) in signal_names if is_bearish]
        unavailable_signals = [name for name, (is_bull, is_bear, conf) in signal_names if not is_bull and not is_bear and conf == 0]

        # Build reasoning sentence
        parts = []

        if bullish_count > 0 and bearish_count > 0:
            parts.append(f"{bullish_count} out of 5 on-chain signals show bullish bias ({', '.join(bullish_signals)})")
            parts.append(f"{bearish_count} signals show bearish bias ({', '.join(bearish_signals)})")
        elif bullish_count > 0:
            parts.append(f"{bullish_count} out of 5 on-chain signals show bullish bias ({', '.join(bullish_signals)})")
        elif bearish_count > 0:
            parts.append(f"{bearish_count} out of 5 on-chain signals show bearish bias ({', '.join(bearish_signals)})")
        else:
            parts.append("No clear directional bias from on-chain signals")

        # Note unavailable signals
        if unavailable_signals:
            parts.append(f"{', '.join(unavailable_signals)} data unavailable")

        # Add funding rate context if available
        if funding_result and funding_result.success and funding_result.data:
            funding_data = funding_result.data
            if funding_data.get("available", False):
                interpretation = funding_data.get("interpretation", "")
                if interpretation:
                    parts.append(f"Funding rate: {interpretation}")

        return ". ".join(parts) + "."

    def _build_key_insights(
        self,
        exchange_data: dict,
        smart_money_data: dict,
        whale_data: dict,
        top_pnl_data: dict,
        fresh_wallets_data: dict
    ) -> list[str]:
        """Build list of key insights from high-confidence signals.

        Args:
            exchange_data: Exchange flows data
            smart_money_data: Smart money data
            whale_data: Whale activity data
            top_pnl_data: Top PnL data
            fresh_wallets_data: Fresh wallets data

        Returns:
            List of 2-4 key insights
        """
        insights = []

        # Exchange flows
        if exchange_data.get("confidence", 0) > 50:
            net_direction = exchange_data.get("net_direction", "neutral")
            if net_direction == "outflow":
                insights.append("Strong exchange outflows indicating accumulation")
            elif net_direction == "inflow":
                insights.append("Increasing exchange inflows suggesting distribution")

        # Smart money
        if smart_money_data.get("confidence", 0) > 50:
            direction = smart_money_data.get("direction", "neutral")
            if direction == "accumulating":
                insights.append("Smart money actively accumulating")
            elif direction == "distributing":
                insights.append("Smart money actively distributing")

        # Whale activity
        if whale_data.get("confidence", 0) > 50:
            net_flow = whale_data.get("net_flow", "neutral")
            if net_flow == "accumulating":
                insights.append("Whale wallets accumulating positions")
            elif net_flow == "distributing":
                insights.append("Whale wallets distributing holdings")

        # Top PnL traders
        if top_pnl_data.get("confidence", 0) > 50:
            traders_bias = top_pnl_data.get("traders_bias", "neutral")
            avg_position = top_pnl_data.get("average_position", "neutral")
            if traders_bias == "bullish" and avg_position == "long":
                insights.append("Top traders predominantly positioned long")
            elif traders_bias == "bearish" and avg_position == "short":
                insights.append("Top traders predominantly positioned short")

        # Fresh wallets
        if fresh_wallets_data.get("activity_level", "none") == "high":
            insights.append("High fresh wallet activity indicating new buyer interest")

        return insights[:4]  # Return max 4 insights
