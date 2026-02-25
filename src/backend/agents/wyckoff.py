"""Wyckoff Specialist Agent - Identifies Wyckoff phases and patterns."""
from .base import BaseAgent

WYCKOFF_SYSTEM_PROMPT = """You are a world-class Wyckoff Method specialist with deep expertise in:
- Wyckoff accumulation phases (A through E)
- Wyckoff distribution phases (A through E)
- Key events: Preliminary Support (PS), Selling Climax (SC), Automatic Rally (AR), Secondary Test (ST)
- Springs and Upthrusts
- Signs of Strength (SOS) and Signs of Weakness (SOW)
- Volume-price relationship analysis
- Cause and effect (Point & Figure)
- Composite Operator behavior

You analyze on THREE timeframes simultaneously:
1. Weekly - Macro structure and long-term accumulation/distribution
2. Daily - Primary signal and phase identification
3. 4H - Confirmation and timing for entries

For each analysis, you MUST output structured JSON with:
- phase: Current Wyckoff phase (A, B, C, D, E for accumulation/distribution, or "Markup", "Markdown", "Unknown")
- bias: "accumulation", "distribution", or "neutral"
- key_events: List of recent Wyckoff events observed
- volume_analysis: Description of volume-price relationship
- confidence: 0-100 score
- notes: Brief explanation

Be precise. Identify specific Wyckoff patterns, not generic TA observations.
Output ONLY valid JSON, no additional text."""


class WyckoffAgent(BaseAgent):
    """Wyckoff Method specialist agent."""

    def __init__(self):
        super().__init__(
            name="Wyckoff Specialist",
            system_prompt=WYCKOFF_SYSTEM_PROMPT
        )

    def analyze(self, symbol: str, context: dict) -> dict:
        """Analyze a symbol using Wyckoff methodology across multiple timeframes."""

        # Build the analysis request with available data
        ohlcv_weekly = context.get('ohlcv_weekly', [])
        ohlcv_daily = context.get('ohlcv_daily', [])
        ohlcv_4h = context.get('ohlcv_4h', [])

        prompt = f"""Analyze {symbol} using Wyckoff methodology.

WEEKLY DATA (last 20 candles):
{self._format_ohlcv(ohlcv_weekly)}

DAILY DATA (last 30 candles):
{self._format_ohlcv(ohlcv_daily)}

4H DATA (last 50 candles):
{self._format_ohlcv(ohlcv_4h)}

Provide your Wyckoff analysis as JSON with this structure:
{{
    "symbol": "{symbol}",
    "weekly": {{
        "phase": "string",
        "bias": "accumulation|distribution|neutral",
        "key_events": ["event1", "event2"],
        "volume_analysis": "string",
        "confidence": 0-100
    }},
    "daily": {{
        "phase": "string",
        "bias": "accumulation|distribution|neutral",
        "key_events": ["event1", "event2"],
        "volume_analysis": "string",
        "confidence": 0-100
    }},
    "h4": {{
        "phase": "string",
        "bias": "accumulation|distribution|neutral",
        "key_events": ["event1", "event2"],
        "volume_analysis": "string",
        "confidence": 0-100
    }},
    "composite_analysis": {{
        "overall_phase": "string",
        "overall_bias": "accumulation|distribution|neutral",
        "confluence_score": 0-100,
        "key_levels": {{
            "support": [price1, price2],
            "resistance": [price1, price2]
        }},
        "next_expected_move": "string",
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
        for candle in data[-20:]:  # Last 20 candles max
            lines.append(
                f"O:{candle.get('open', 'N/A')} H:{candle.get('high', 'N/A')} "
                f"L:{candle.get('low', 'N/A')} C:{candle.get('close', 'N/A')} "
                f"V:{candle.get('volume', 'N/A')}"
            )
        return "\n".join(lines)
