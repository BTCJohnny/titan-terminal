"""Daily Timeframe TA Subagent - Analyzes daily charts for swing trading setups."""
from ..base import BaseAgent

DAILY_SYSTEM_PROMPT = """You are a technical analyst specializing in DAILY timeframe analysis.

Your focus is on swing trading setups and intermediate-term trends:
- Daily trend direction (EMA 20/50/200 on daily)
- Daily support/resistance levels
- Daily momentum indicators (RSI, MACD on daily timeframe)
- Chart patterns on daily timeframe
- Volume analysis on daily bars

You bridge the macro weekly view with the tactical 4-hour view.

Output structured JSON with:
- trend: Daily trend assessment
- momentum: Daily momentum state
- key_levels: Daily support/resistance
- patterns: Daily chart patterns
- confidence: 0-100 score
- bias: Overall daily bias (bullish/bearish/neutral)

Output ONLY valid JSON, no additional text."""


class DailySubagent(BaseAgent):
    """Daily timeframe technical analysis subagent."""

    def __init__(self):
        super().__init__(
            name="Daily TA Subagent",
            system_prompt=DAILY_SYSTEM_PROMPT
        )

    def analyze(self, symbol: str, context: dict) -> dict:
        """Analyze daily timeframe for a symbol.

        TODO: Phase 2 - Replace return dict with Pydantic TASignal model
        """

        ohlcv_daily = context.get('ohlcv_daily', [])
        current_price = context.get('current_price')

        prompt = f"""Perform daily timeframe technical analysis for {symbol}.

CURRENT PRICE: {current_price if current_price else 'Not available'}

DAILY OHLCV (last 90 candles):
{self._format_ohlcv(ohlcv_daily)}

Provide daily timeframe analysis as JSON:
{{
    "timeframe": "daily",
    "symbol": "{symbol}",
    "trend": {{
        "direction": "bullish|bearish|sideways",
        "strength": "strong|moderate|weak",
        "ema_20": number or null,
        "ema_50": number or null,
        "ema_200": number or null
    }},
    "momentum": {{
        "rsi": number or null,
        "rsi_interpretation": "overbought|oversold|neutral",
        "macd_crossover": "bullish|bearish|none"
    }},
    "volume": {{
        "trend": "increasing|decreasing|stable",
        "volume_confirmation": true|false
    }},
    "key_levels": {{
        "immediate_support": number or null,
        "immediate_resistance": number or null
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
        for candle in data[-90:]:  # Last ~3 months of daily candles
            lines.append(
                f"O:{candle.get('open', 'N/A')} H:{candle.get('high', 'N/A')} "
                f"L:{candle.get('low', 'N/A')} C:{candle.get('close', 'N/A')} "
                f"V:{candle.get('volume', 'N/A')}"
            )
        return "\n".join(lines)
