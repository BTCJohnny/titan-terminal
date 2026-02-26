"""Weekly Timeframe TA Subagent - Analyzes weekly charts for macro trend."""
from ..base import BaseAgent

WEEKLY_SYSTEM_PROMPT = """You are a technical analyst specializing in WEEKLY timeframe analysis.

Your focus is on the macro trend and long-term momentum:
- Weekly trend direction (EMA 20/50/200 on weekly)
- Major support/resistance zones visible on weekly charts
- Weekly momentum indicators (RSI, MACD on weekly timeframe)
- Long-term pattern recognition (multi-week/month patterns)
- Higher timeframe structure

You provide the "big picture" view that helps frame shorter timeframe analysis.

Output structured JSON with:
- trend: Weekly trend assessment
- momentum: Weekly momentum state
- key_levels: Major weekly support/resistance
- patterns: Weekly chart patterns
- confidence: 0-100 score
- bias: Overall weekly bias (bullish/bearish/neutral)

Output ONLY valid JSON, no additional text."""


class WeeklySubagent(BaseAgent):
    """Weekly timeframe technical analysis subagent."""

    def __init__(self):
        super().__init__(
            name="Weekly TA Subagent",
            system_prompt=WEEKLY_SYSTEM_PROMPT
        )

    def analyze(self, symbol: str, context: dict) -> dict:
        """Analyze weekly timeframe for a symbol.

        TODO: Phase 2 - Replace return dict with Pydantic TASignal model
        """

        ohlcv_weekly = context.get('ohlcv_weekly', [])
        current_price = context.get('current_price')

        prompt = f"""Perform weekly timeframe technical analysis for {symbol}.

CURRENT PRICE: {current_price if current_price else 'Not available'}

WEEKLY OHLCV (last 52 candles):
{self._format_ohlcv(ohlcv_weekly)}

Provide weekly timeframe analysis as JSON:
{{
    "timeframe": "weekly",
    "symbol": "{symbol}",
    "trend": {{
        "direction": "bullish|bearish|sideways",
        "strength": "strong|moderate|weak",
        "ema_alignment": "bullish|bearish|neutral"
    }},
    "momentum": {{
        "rsi_weekly": number or null,
        "macd_bias": "bullish|bearish|neutral",
        "momentum_divergence": true|false
    }},
    "key_levels": {{
        "major_support": number or null,
        "major_resistance": number or null
    }},
    "patterns": {{
        "detected": ["pattern1", "pattern2"],
        "pattern_bias": "bullish|bearish|neutral"
    }},
    "overall": {{
        "bias": "bullish|bearish|neutral",
        "confidence": 0-100,
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
        for candle in data[-52:]:  # Last year of weekly candles
            lines.append(
                f"O:{candle.get('open', 'N/A')} H:{candle.get('high', 'N/A')} "
                f"L:{candle.get('low', 'N/A')} C:{candle.get('close', 'N/A')} "
                f"V:{candle.get('volume', 'N/A')}"
            )
        return "\n".join(lines)
