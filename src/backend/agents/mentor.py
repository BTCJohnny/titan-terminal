"""Mentor Critic Agent - Second opinion on final signals.

DEPRECATED: MentorCriticAgent will be refactored in Phase 2.
The TA Mentor functionality has been moved to ta_ensemble/ta_mentor.py
This file will be removed in v1.0.
"""
from .base import BaseAgent
from ..config import config

MENTOR_SYSTEM_PROMPT = """You are a seasoned trading mentor with 20+ years of experience.

Your role is to provide a SECOND OPINION on trading signals before they're presented to the user.

You are skeptical but fair. You look for:
- Overconfidence in analysis
- Missing risk factors
- Conflicting signals that weren't addressed
- Market conditions that might invalidate the thesis
- Historical patterns that suggest caution

You can:
- APPROVE: Signal looks solid, proceed
- CAUTION: Signal has merit but note these concerns
- REJECT: Too many red flags, recommend avoiding

Keep your critique brief but substantive.
Output ONLY valid JSON, no additional text."""


class MentorCriticAgent(BaseAgent):
    """Mentor critic agent for second opinions."""

    def __init__(self):
        super().__init__(
            name="Mentor Critic",
            system_prompt=MENTOR_SYSTEM_PROMPT
        )
        # Use the mentor model (can be different/cheaper)
        self.model = config.MENTOR_MODEL

    def critique(self, signal_data: dict) -> dict:
        """Provide second opinion on a trading signal."""

        prompt = f"""Review this trading signal and provide your critique.

SIGNAL SUMMARY:
Symbol: {signal_data.get('symbol')}
Action: {signal_data.get('suggested_action')}
Confidence: {signal_data.get('confidence')}

ACCUMULATION/DISTRIBUTION:
Accumulation Score: {signal_data.get('accumulation_score')}
Distribution Score: {signal_data.get('distribution_score')}

WYCKOFF ANALYSIS:
{signal_data.get('wyckoff_summary', 'Not available')}

TECHNICAL ANALYSIS:
{signal_data.get('ta_summary', 'Not available')}

ON-CHAIN DATA:
{signal_data.get('nansen_summary', 'Not available')}

PROPOSED LEVELS:
Entry: {signal_data.get('entry_zone')}
Stop: {signal_data.get('stop_loss')}
TP1: {signal_data.get('tp1')}
TP2: {signal_data.get('tp2')}
R:R: {signal_data.get('risk_reward')}

Provide your critique as JSON:
{{
    "symbol": "{signal_data.get('symbol')}",
    "verdict": "approve|caution|reject",
    "confidence_adjustment": number (-20 to +10),
    "concerns": ["concern1", "concern2"],
    "strengths": ["strength1", "strength2"],
    "risk_factors_missed": ["factor1", "factor2"],
    "historical_context": "string",
    "revised_recommendation": "string or null",
    "mentor_notes": "string"
}}"""

        response = self._call_claude(prompt, max_tokens=1500)
        return self._parse_json_response(response)

    def analyze(self, symbol: str, context: dict) -> dict:
        """Wrapper for compatibility with base agent interface."""
        return self.critique(context)
