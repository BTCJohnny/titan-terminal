"""Telegram Alpha Agent - Scans Telegram signals from SQLite."""
from .base import BaseAgent
from ..db import get_connection

TELEGRAM_SYSTEM_PROMPT = """You are an expert at parsing and interpreting cryptocurrency trading signals from Telegram channels.

You scan for signals with specific headers and patterns:
- Entry signals with specific price levels
- Stop loss and take profit targets
- Channel reputation and track record
- Signal freshness and relevance

For each relevant signal found, output structured JSON with:
- channel: Source channel
- symbol: Token/pair mentioned
- action: Buy/Sell/Long/Short
- entry_price: Suggested entry
- stop_loss: Stop loss level
- take_profits: List of TP levels
- confidence: Your assessment of signal quality (0-100)
- notes: Any relevant context

Output ONLY valid JSON, no additional text."""


class TelegramAgent(BaseAgent):
    """Telegram signal scanning agent."""

    def __init__(self):
        super().__init__(
            name="Telegram Alpha",
            system_prompt=TELEGRAM_SYSTEM_PROMPT
        )

    def analyze(self, symbol: str, context: dict) -> dict:
        """Scan Telegram signals for a specific symbol."""

        # Query SQLite for recent Telegram signals
        signals = self._get_recent_signals(symbol)

        if not signals:
            return {
                "symbol": symbol,
                "signals_found": 0,
                "relevant_signals": [],
                "overall_sentiment": "neutral",
                "confidence": 0,
                "notes": "No recent Telegram signals found for this symbol"
            }

        prompt = f"""Analyze these Telegram signals for {symbol}:

SIGNALS FROM DATABASE:
{self._format_signals(signals)}

Parse and evaluate these signals. Output JSON:
{{
    "symbol": "{symbol}",
    "signals_found": {len(signals)},
    "relevant_signals": [
        {{
            "channel": "string",
            "action": "long|short|buy|sell",
            "entry_price": number or null,
            "stop_loss": number or null,
            "take_profits": [number],
            "signal_quality": 0-100,
            "freshness": "fresh|stale",
            "notes": "string"
        }}
    ],
    "overall_sentiment": "bullish|bearish|mixed|neutral",
    "confluence_count": number,
    "confidence": 0-100,
    "notes": "string"
}}"""

        response = self._call_claude(prompt, max_tokens=2000)
        return self._parse_json_response(response)

    def _get_recent_signals(self, symbol: str, hours: int = 48) -> list:
        """Get recent Telegram signals for a symbol."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM telegram_signals
            WHERE parsed_symbol LIKE ?
            AND datetime(parsed_at) > datetime('now', ?)
            ORDER BY parsed_at DESC
            LIMIT 20
        """, (f"%{symbol}%", f"-{hours} hours"))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def _format_signals(self, signals: list) -> str:
        """Format signals for the prompt."""
        lines = []
        for s in signals:
            lines.append(
                f"[{s.get('channel', 'Unknown')}] {s.get('content', '')[:200]}"
            )
        return "\n---\n".join(lines)
