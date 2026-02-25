"""TA Ensemble Agent - Technical analysis with multiple indicators."""
from .base import BaseAgent

TA_ENSEMBLE_SYSTEM_PROMPT = """You are an expert technical analyst combining multiple indicators and patterns.

Your analysis includes:
- Trend indicators: EMA 20/50/200, SMA crossovers
- Momentum: RSI, MACD, Stochastic
- Volume: OBV, Volume Profile, VWAP
- Volatility: Bollinger Bands, ATR
- Pattern recognition: Head & Shoulders, Double Tops/Bottoms, Triangles, Flags
- Support/Resistance levels
- Fibonacci retracements and extensions

You combine all indicators into a unified view, noting confluence and divergence.

Output structured JSON with:
- trend: Overall trend assessment
- momentum: Momentum state
- volume: Volume analysis
- patterns: Detected chart patterns
- key_levels: Important price levels
- confidence: 0-100 score
- recommended_action: Long/Short/Wait

Output ONLY valid JSON, no additional text."""


class TAEnsembleAgent(BaseAgent):
    """Technical analysis ensemble agent."""

    def __init__(self):
        super().__init__(
            name="TA Ensemble",
            system_prompt=TA_ENSEMBLE_SYSTEM_PROMPT
        )

    def analyze(self, symbol: str, context: dict) -> dict:
        """Perform comprehensive technical analysis."""

        ohlcv_daily = context.get('ohlcv_daily', [])
        ohlcv_4h = context.get('ohlcv_4h', [])
        current_price = context.get('current_price')

        # Calculate basic indicators from OHLCV if available
        indicators = self._calculate_indicators(ohlcv_daily) if ohlcv_daily else {}

        prompt = f"""Perform comprehensive technical analysis for {symbol}.

CURRENT PRICE: {current_price if current_price else 'Not available'}

DAILY OHLCV (last 30 candles):
{self._format_ohlcv(ohlcv_daily)}

4H OHLCV (last 50 candles):
{self._format_ohlcv(ohlcv_4h)}

PRE-CALCULATED INDICATORS:
{indicators if indicators else 'Calculate from OHLCV data'}

Provide comprehensive TA analysis as JSON:
{{
    "symbol": "{symbol}",
    "current_price": {current_price if current_price else 'null'},
    "trend": {{
        "direction": "bullish|bearish|sideways",
        "strength": "strong|moderate|weak",
        "ema_20": number or null,
        "ema_50": number or null,
        "ema_200": number or null,
        "trend_notes": "string"
    }},
    "momentum": {{
        "rsi": number or null,
        "rsi_interpretation": "overbought|oversold|neutral",
        "macd": {{
            "value": number or null,
            "signal": number or null,
            "histogram": number or null,
            "crossover": "bullish|bearish|none"
        }},
        "stochastic": {{
            "k": number or null,
            "d": number or null,
            "interpretation": "overbought|oversold|neutral"
        }},
        "momentum_bias": "bullish|bearish|neutral"
    }},
    "volume": {{
        "trend": "increasing|decreasing|stable",
        "obv_trend": "bullish|bearish|neutral",
        "volume_price_confirmation": true|false,
        "notes": "string"
    }},
    "volatility": {{
        "atr": number or null,
        "bollinger_position": "upper|middle|lower",
        "squeeze": true|false,
        "notes": "string"
    }},
    "patterns": {{
        "detected": ["pattern1", "pattern2"],
        "pattern_bias": "bullish|bearish|neutral",
        "pattern_confidence": 0-100
    }},
    "key_levels": {{
        "immediate_support": number or null,
        "immediate_resistance": number or null,
        "major_support": number or null,
        "major_resistance": number or null,
        "pivot_points": {{
            "pivot": number or null,
            "r1": number or null,
            "r2": number or null,
            "s1": number or null,
            "s2": number or null
        }}
    }},
    "overall": {{
        "bias": "bullish|bearish|neutral",
        "confidence": 0-100,
        "recommended_action": "long|short|wait",
        "notes": "string"
    }}
}}"""

        response = self._call_claude(prompt, max_tokens=3000)
        return self._parse_json_response(response)

    def _format_ohlcv(self, data: list) -> str:
        """Format OHLCV data for the prompt."""
        if not data:
            return "No data available"

        lines = []
        for candle in data[-20:]:
            lines.append(
                f"O:{candle.get('open', 'N/A')} H:{candle.get('high', 'N/A')} "
                f"L:{candle.get('low', 'N/A')} C:{candle.get('close', 'N/A')} "
                f"V:{candle.get('volume', 'N/A')}"
            )
        return "\n".join(lines)

    def _calculate_indicators(self, ohlcv: list) -> dict:
        """Calculate basic indicators from OHLCV data."""
        if not ohlcv or len(ohlcv) < 20:
            return {}

        closes = [c.get('close', 0) for c in ohlcv if c.get('close')]
        if not closes:
            return {}

        # Simple EMA calculation
        def ema(data, period):
            if len(data) < period:
                return None
            multiplier = 2 / (period + 1)
            ema_val = sum(data[:period]) / period
            for price in data[period:]:
                ema_val = (price - ema_val) * multiplier + ema_val
            return round(ema_val, 4)

        # Simple RSI calculation
        def rsi(data, period=14):
            if len(data) < period + 1:
                return None
            gains, losses = [], []
            for i in range(1, len(data)):
                change = data[i] - data[i-1]
                gains.append(max(0, change))
                losses.append(max(0, -change))
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            if avg_loss == 0:
                return 100
            rs = avg_gain / avg_loss
            return round(100 - (100 / (1 + rs)), 2)

        return {
            "ema_20": ema(closes, 20),
            "ema_50": ema(closes, 50),
            "ema_200": ema(closes, 200) if len(closes) >= 200 else None,
            "rsi_14": rsi(closes, 14),
            "current_close": closes[-1] if closes else None
        }
