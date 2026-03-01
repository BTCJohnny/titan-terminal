"""TA Mentor - Synthesizes multi-timeframe TA subagent outputs into unified signal."""
import json
import logging
from typing import Optional

from anthropic import Anthropic

from src.backend.config.settings import settings
from src.backend.models.ta_signal import TASignal
from src.backend.models.ta_mentor_signal import TAMentorSignal

logger = logging.getLogger(__name__)


class TAMentor:
    """TA Mentor that synthesizes multi-timeframe subagent outputs.

    Direct Anthropic SDK implementation with explicit conflict resolution rules.
    Does NOT inherit from BaseAgent.
    """

    def __init__(self):
        """Initialize TAMentor with direct Anthropic client."""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.MENTOR_MODEL
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """Build system prompt with explicit conflict resolution rules."""
        return """You are a multi-timeframe technical analysis mentor who synthesizes signals from 3 timeframes.

You receive analysis from:
- Weekly Subagent: Macro trend and big picture
- Daily Subagent: Swing trading setups and intermediate trend
- 4H Subagent: Entry timing and tactical setups

Your job is to:
1. Detect CONFLUENCE: Do all timeframes align?
2. Detect CONFLICTS: Are timeframes contradicting each other?
3. Apply explicit conflict resolution rules (see below)
4. Adjust confidence based on alignment
5. Provide a unified TA signal with clear bias and reasoning

CONFLICT RESOLUTION RULES (MANDATORY):

1. If Weekly AND Daily are BEARISH but 4H is BULLISH:
   - Output direction: BEARISH
   - Reduce confidence by 20 points
   - Add warning: "4H counter-trend bounce in progress"

2. If Weekly AND Daily are BULLISH but 4H is BEARISH:
   - Output direction: BULLISH
   - Reduce confidence by 20 points
   - Add warning: "4H pullback — potential better entry incoming"

3. If Weekly CONFLICTS with Daily direction:
   - Output bias: "neutral"
   - recommended_action: "wait"
   - Add conflict: "Weekly and Daily timeframes in conflict — genuine uncertainty"

4. 4H timeframe is for ENTRY TIMING ONLY:
   - Use 4H to set entry_timing: "immediate" | "wait_for_pullback" | "wait_for_confirmation"
   - NEVER let 4H override Weekly or Daily direction

HIERARCHY:
- Weekly > Daily > 4H in importance (respect the higher timeframe)
- Perfect alignment across all 3 timeframes = highest confidence
- Conflicting timeframes = reduce confidence or recommend "wait"

Output ONLY valid JSON matching TAMentorSignal schema with:
- symbol: string
- timeframe_alignment: {weekly_bias, daily_bias, fourhour_bias, alignment_score, confluence}
- conflicts_detected: array of {type, description, severity}
- confidence_adjustment: {base_confidence, confluence_bonus, conflict_penalty, final_confidence, reasoning}
- unified_signal: {bias, strength, confidence, recommended_action, entry_timing, key_levels}
- synthesis_notes: string

Do NOT average scores. Reason independently and apply the conflict rules exactly."""

    def synthesize(self, weekly: TASignal, daily: TASignal, four_hour) -> dict:
        """Synthesize multi-timeframe TA signals into unified output.

        Args:
            weekly: TASignal from WeeklySubagent (Pydantic model)
            daily: TASignal from DailySubagent (Pydantic model)
            four_hour: 4-hour signal — TASignal or plain dict (FourHourSubagent returns dict)

        Returns:
            dict with unified trading recommendation. The downstream orchestrator
            consumes this via .get() calls, so returning a plain dict avoids
            Pydantic validation failures when the LLM output violates strict
            Literal field constraints. If the LLM call fails or produces invalid
            JSON/schema, returns a safe fallback neutral dict.
        """
        symbol = weekly.symbol if hasattr(weekly, "symbol") else weekly.get("symbol", "UNKNOWN")
        logger.info(f"Synthesizing multi-timeframe signals for {symbol}")

        prompt = self._build_prompt(weekly, daily, four_hour)
        logger.debug(f"Synthesis prompt:\n{prompt}")

        _fallback = {
            "symbol": symbol,
            "timeframe_alignment": {
                "weekly_bias": "neutral",
                "daily_bias": "neutral",
                "fourhour_bias": "neutral",
                "alignment_score": 50,
                "confluence": "weak",
            },
            "conflicts_detected": [],
            "confidence_adjustment": {
                "base_confidence": 50,
                "confluence_bonus": 0,
                "conflict_penalty": 0,
                "final_confidence": 50,
                "reasoning": "Fallback — synthesis failed or LLM output was invalid",
            },
            "unified_signal": {
                "bias": "neutral",
                "strength": "weak",
                "confidence": 50,
                "recommended_action": "wait",
                "entry_timing": "wait_for_confirmation",
                "key_levels": {"support": None, "resistance": None, "invalidation": None},
            },
            "synthesis_notes": "TA synthesis unavailable — fallback neutral signal.",
        }

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            logger.debug(f"LLM response:\n{response_text}")

            result_dict = self._parse_json_response(response_text)

            # Attempt strict validation — if it passes, use the validated dict.
            # If it fails (LLM returned out-of-schema values), use the raw parsed dict
            # rather than crashing the entire pipeline. The orchestrator only cares
            # about unified_signal.bias and high-level structure.
            try:
                mentor_signal = TAMentorSignal.model_validate(result_dict)
                logger.info(f"Successfully synthesized {symbol} — bias: {mentor_signal.unified_signal.bias}")
                return mentor_signal.model_dump()
            except Exception as validation_err:
                logger.warning(
                    f"TAMentorSignal validation failed for {symbol} — using raw LLM dict. "
                    f"Error: {validation_err}"
                )
                # Return the raw parsed dict — it may have non-Literal values but
                # the orchestrator handles this gracefully via .get() with defaults
                return result_dict

        except Exception as e:
            logger.error(f"Failed to synthesize signals for {symbol}: {e}")
            return _fallback

    @staticmethod
    def _to_dict(signal) -> dict:
        """Serialize a signal to dict regardless of whether it's a Pydantic model or plain dict.

        FourHourSubagent returns a plain dict while WeeklySubagent and DailySubagent
        return TASignal Pydantic models. This helper normalizes both to dict for the
        synthesis prompt.
        """
        if isinstance(signal, dict):
            return signal
        return signal.model_dump()

    def _build_prompt(self, weekly: TASignal, daily: TASignal, four_hour) -> str:
        """Build synthesis prompt with all three timeframe signals.

        Args:
            weekly: Weekly timeframe TASignal (Pydantic model)
            daily: Daily timeframe TASignal (Pydantic model)
            four_hour: 4-hour timeframe signal — TASignal or plain dict (FourHourSubagent
                       currently returns a dict; this method handles both types gracefully)

        Returns:
            Formatted prompt string with JSON-serialized signals
        """
        symbol = weekly.symbol if hasattr(weekly, "symbol") else weekly.get("symbol", "UNKNOWN")
        return f"""Synthesize multi-timeframe TA analysis for {symbol}.

WEEKLY SIGNAL:
{json.dumps(self._to_dict(weekly), indent=2)}

DAILY SIGNAL:
{json.dumps(self._to_dict(daily), indent=2)}

4-HOUR SIGNAL:
{json.dumps(self._to_dict(four_hour), indent=2)}

Apply conflict resolution rules and output TAMentorSignal JSON."""

    def _parse_json_response(self, response: str) -> dict:
        """Extract JSON from Claude's response.

        Handles:
        - Raw JSON responses
        - ```json code blocks
        - Leading/trailing whitespace

        Args:
            response: Raw text response from Claude

        Returns:
            Parsed JSON as dict

        Raises:
            ValueError: If response is not valid JSON
        """
        try:
            # Check for ```json blocks
            if "```json" in response:
                start = response.index("```json") + 7
                end = response.index("```", start)
                return json.loads(response[start:end].strip())

            # Try parsing whole response as JSON
            return json.loads(response.strip())

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Response text: {response}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    def analyze(self, symbol: str, context: dict) -> dict:
        """Wrapper for compatibility with base agent interface.

        Expects context to contain:
        - weekly_analysis: dict or TASignal from WeeklySubagent
        - daily_analysis: dict or TASignal from DailySubagent
        - fourhour_analysis: dict or TASignal from FourHourSubagent

        Returns:
            Dict representation of TAMentorSignal

        Note: Maintains backward compatibility by accepting dict inputs
        and converting them to TASignal objects if needed.
        """
        weekly = context.get('weekly_analysis', {})
        daily = context.get('daily_analysis', {})
        fourhour = context.get('fourhour_analysis', {})

        # Convert dicts to TASignal if needed
        if isinstance(weekly, dict):
            weekly = TASignal.model_validate(weekly)
        if isinstance(daily, dict):
            daily = TASignal.model_validate(daily)
        if isinstance(fourhour, dict):
            fourhour = TASignal.model_validate(fourhour)

        mentor_signal = self.synthesize(weekly, daily, fourhour)
        return mentor_signal.model_dump()
