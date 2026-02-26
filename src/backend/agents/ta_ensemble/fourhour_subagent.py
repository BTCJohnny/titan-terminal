"""Four-Hour Timeframe TA Subagent - Analyzes 4H charts for entry timing."""
from ..base import BaseAgent

FOURHOUR_SYSTEM_PROMPT = """You are a technical analyst specializing in 4-HOUR timeframe analysis.

Your focus is on entry timing and short-term tactical setups:
- 4H trend direction and momentum
- Intraday support/resistance levels visible on 4H
- 4H momentum indicators for timing entries
- Short-term pattern recognition
- Volume spikes and accumulation/distribution on 4H bars

You provide the tactical "entry timing" layer after weekly/daily confirm the setup.

Output structured JSON with:
- trend: 4H trend assessment
- momentum: 4H momentum state
- key_levels: 4H support/resistance for entries
- patterns: 4H chart patterns
- confidence: 0-100 score
- bias: Overall 4H bias (bullish/bearish/neutral)

Output ONLY valid JSON, no additional text."""


class FourHourSubagent(BaseAgent):
    """Four-hour timeframe technical analysis subagent."""

    def __init__(self):
        super().__init__(
            name="4H TA Subagent",
            system_prompt=FOURHOUR_SYSTEM_PROMPT
        )

    def analyze(self, symbol: str, context: dict) -> dict:
        """Analyze 4-hour timeframe for a symbol.

        TODO: Phase 2 - Replace return dict with Pydantic TASignal model
        """

        ohlcv_4h = context.get('ohlcv_4h', [])
        current_price = context.get('current_price')

        prompt = f"""Perform 4-hour timeframe technical analysis for {symbol}.

CURRENT PRICE: {current_price if current_price else 'Not available'}

4H OHLCV (last 168 candles):
{self._format_ohlcv(ohlcv_4h)}

Provide 4-hour timeframe analysis as JSON:
{{
    "timeframe": "4h",
    "symbol": "{symbol}",
    "trend": {{
        "direction": "bullish|bearish|sideways",
        "strength": "strong|moderate|weak",
        "recent_swing": "higher_highs|lower_lows|ranging"
    }},
    "momentum": {{
        "rsi": number or null,
        "rsi_interpretation": "overbought|oversold|neutral",
        "divergence_present": true|false
    }},
    "volume": {{
        "recent_spike": true|false,
        "accumulation_distribution": "accumulation|distribution|neutral"
    }},
    "key_levels": {{
        "entry_support": number or null,
        "entry_resistance": number or null,
        "invalidation_level": number or null
    }},
    "patterns": {{
        "detected": ["pattern1", "pattern2"],
        "pattern_bias": "bullish|bearish|neutral",
        "pattern_maturity": "forming|mature|completed"
    }},
    "overall": {{
        "bias": "bullish|bearish|neutral",
        "confidence": 0-100,
        "entry_timing": "now|wait_for_pullback|wait_for_breakout",
        "notes": "string"
    }}
}}"""

        response = self._call_claude(prompt, max_tokens=2000)
        return self._parse_json_response(response)

    def _format_ohlcv(self, data: list) -> str:
        """Format OHLCV data for the prompt."""
        if not data:
            return "No data available"

        lines = []
        for candle in data[-168:]:  # Last ~4 weeks of 4H candles
            lines.append(
                f"O:{candle.get('open', 'N/A')} H:{candle.get('high', 'N/A')} "
                f"L:{candle.get('low', 'N/A')} C:{candle.get('close', 'N/A')} "
                f"V:{candle.get('volume', 'N/A')}"
            )
        return "\n".join(lines)
