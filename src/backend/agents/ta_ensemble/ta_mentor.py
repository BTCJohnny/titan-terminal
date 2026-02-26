"""TA Mentor - Synthesizes multi-timeframe TA subagent outputs into unified signal."""
from ..base import BaseAgent

TA_MENTOR_SYSTEM_PROMPT = """You are a multi-timeframe technical analysis mentor who synthesizes signals from 3 timeframes.

You receive analysis from:
- Weekly Subagent: Macro trend and big picture
- Daily Subagent: Swing trading setups and intermediate trend
- 4H Subagent: Entry timing and tactical setups

Your job is to:
1. Detect CONFLUENCE: Do all timeframes align?
2. Detect CONFLICTS: Are timeframes contradicting each other?
3. Adjust confidence based on alignment (high confluence = high confidence)
4. Provide a unified TA signal with clear bias and reasoning

RULES:
- Weekly > Daily > 4H in importance (respect the higher timeframe)
- Perfect alignment across all 3 timeframes = highest confidence
- Conflicting timeframes = reduce confidence or recommend "wait"
- Note divergences between timeframes as important context

Output structured JSON with:
- timeframe_alignment: Degree of confluence
- conflicts_detected: List of conflicts between timeframes
- unified_bias: Final TA bias considering all timeframes
- confidence: Adjusted confidence (0-100)
- recommended_action: Trade recommendation

Output ONLY valid JSON, no additional text."""


class TAMentor(BaseAgent):
    """TA Mentor that synthesizes multi-timeframe subagent outputs."""

    def __init__(self):
        super().__init__(
            name="TA Mentor",
            system_prompt=TA_MENTOR_SYSTEM_PROMPT
        )

    def synthesize(self, weekly: dict, daily: dict, fourhour: dict) -> dict:
        """Synthesize multi-timeframe TA signals into unified output.

        Args:
            weekly: Output from WeeklySubagent
            daily: Output from DailySubagent
            fourhour: Output from FourHourSubagent

        Returns:
            Unified TA signal with confidence adjustments

        TODO: Phase 2 - Replace return dict with Pydantic TAMentorSignal model
        """

        symbol = weekly.get('symbol', daily.get('symbol', fourhour.get('symbol', 'UNKNOWN')))

        prompt = f"""Synthesize multi-timeframe TA analysis for {symbol}.

WEEKLY ANALYSIS:
{self._format_analysis(weekly)}

DAILY ANALYSIS:
{self._format_analysis(daily)}

4-HOUR ANALYSIS:
{self._format_analysis(fourhour)}

Synthesize these into a unified TA signal as JSON:
{{
    "symbol": "{symbol}",
    "timeframe_alignment": {{
        "weekly_bias": "{weekly.get('overall', {}).get('bias', 'unknown')}",
        "daily_bias": "{daily.get('overall', {}).get('bias', 'unknown')}",
        "fourhour_bias": "{fourhour.get('overall', {}).get('bias', 'unknown')}",
        "alignment_score": 0-100,
        "confluence": "perfect|strong|moderate|weak|conflicting"
    }},
    "conflicts_detected": [
        {{
            "type": "trend|momentum|pattern",
            "description": "string",
            "severity": "high|medium|low"
        }}
    ],
    "confidence_adjustment": {{
        "base_confidence": number,
        "confluence_bonus": number,
        "conflict_penalty": number,
        "final_confidence": 0-100,
        "reasoning": "string"
    }},
    "unified_signal": {{
        "bias": "bullish|bearish|neutral",
        "strength": "strong|moderate|weak",
        "confidence": 0-100,
        "recommended_action": "long|short|wait",
        "entry_timing": "immediate|wait_for_pullback|wait_for_confirmation",
        "key_levels": {{
            "support": number or null,
            "resistance": number or null,
            "invalidation": number or null
        }}
    }},
    "synthesis_notes": "string explaining the multi-timeframe picture"
}}"""

        response = self._call_claude(prompt, max_tokens=2500)
        return self._parse_json_response(response)

    def analyze(self, symbol: str, context: dict) -> dict:
        """Wrapper for compatibility with base agent interface.

        Expects context to contain:
        - weekly_analysis: dict from WeeklySubagent
        - daily_analysis: dict from DailySubagent
        - fourhour_analysis: dict from FourHourSubagent
        """
        weekly = context.get('weekly_analysis', {})
        daily = context.get('daily_analysis', {})
        fourhour = context.get('fourhour_analysis', {})

        return self.synthesize(weekly, daily, fourhour)

    def _format_analysis(self, analysis: dict) -> str:
        """Format a subagent analysis for the prompt."""
        if not analysis:
            return "No analysis available"

        # Extract key fields
        timeframe = analysis.get('timeframe', 'unknown')
        overall = analysis.get('overall', {})
        trend = analysis.get('trend', {})
        momentum = analysis.get('momentum', {})

        return f"""Timeframe: {timeframe}
Bias: {overall.get('bias', 'unknown')}
Confidence: {overall.get('confidence', 0)}
Trend: {trend.get('direction', 'unknown')} ({trend.get('strength', 'unknown')})
Momentum: {momentum}
Notes: {overall.get('notes', 'N/A')}"""
