"""Nansen On-Chain Agent - Whale flows and smart money analysis."""
from .base import BaseAgent

NANSEN_SYSTEM_PROMPT = """You are an expert on-chain analyst specializing in:
- Whale wallet tracking and flow analysis
- Smart money accumulation and distribution patterns
- Exchange inflows/outflows
- Perpetual futures activity and funding rates
- Token holder distribution changes
- Notable wallet movements

You focus on HIGH LIQUIDITY tokens to avoid slippage issues.

For each analysis, output structured JSON with:
- whale_activity: Summary of large wallet movements
- smart_money_flow: Net flow direction (accumulating/distributing/neutral)
- exchange_flow: Net exchange inflow/outflow
- perp_activity: Perpetual futures positioning if available
- confidence: 0-100 score
- signals: List of notable on-chain signals

Output ONLY valid JSON, no additional text."""


class NansenAgent(BaseAgent):
    """Nansen on-chain analysis agent."""

    def __init__(self):
        super().__init__(
            name="Nansen On-Chain",
            system_prompt=NANSEN_SYSTEM_PROMPT
        )

    def analyze(self, symbol: str, context: dict) -> dict:
        """Analyze on-chain data for a symbol."""

        # In production, this would call actual Nansen API
        # For MVP, we simulate with Claude's knowledge + any provided data
        nansen_data = context.get('nansen_data', {})
        funding_rate = context.get('funding_rate')
        exchange_flows = context.get('exchange_flows', {})

        prompt = f"""Analyze on-chain activity for {symbol}.

AVAILABLE DATA:
- Funding Rate: {funding_rate if funding_rate else 'Not available'}
- Exchange Flows: {exchange_flows if exchange_flows else 'Not available'}
- Additional Nansen Data: {nansen_data if nansen_data else 'Not available'}

Based on your knowledge of typical on-chain patterns for {symbol} and any data provided,
provide your analysis as JSON:
{{
    "symbol": "{symbol}",
    "whale_activity": {{
        "summary": "string",
        "notable_transactions": ["tx1", "tx2"],
        "net_flow": "accumulating|distributing|neutral"
    }},
    "smart_money_flow": {{
        "direction": "accumulating|distributing|neutral",
        "confidence": 0-100,
        "notable_wallets": ["wallet1", "wallet2"]
    }},
    "exchange_flow": {{
        "net_direction": "inflow|outflow|neutral",
        "magnitude": "high|medium|low",
        "interpretation": "string"
    }},
    "perp_activity": {{
        "funding_rate": {funding_rate if funding_rate else 'null'},
        "funding_interpretation": "string",
        "open_interest_trend": "increasing|decreasing|stable"
    }},
    "overall_signal": {{
        "bias": "bullish|bearish|neutral",
        "confidence": 0-100,
        "key_insights": ["insight1", "insight2"]
    }}
}}"""

        response = self._call_claude(prompt, max_tokens=2000)
        return self._parse_json_response(response)
