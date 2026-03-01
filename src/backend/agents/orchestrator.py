"""Orchestrator - Main brain that coordinates all specialist agents."""
import json
import anthropic
from datetime import datetime
from typing import Optional
import uuid

from .base import BaseAgent
from .wyckoff import WyckoffAgent
from .nansen_agent import NansenAgent
from .telegram_agent import TelegramAgent, get_recent_signal_symbols
from .ta_ensemble import WeeklySubagent, DailySubagent, FourHourSubagent, TAMentor
from .risk_agent import RiskAgent
from ..db import record_signal, get_similar_patterns, get_pattern_stats
from ..config.constants import HYPERLIQUID_PERPS
from ..config.settings import settings
from ..models.risk_output import RiskOutput
from ..models.orchestrator_output import OrchestratorOutput, EntryZoneSimple, ThreeLawsCheckSimple

def _get_field(item, field, default=None):
    """Extract field from OrchestratorOutput (attr) or error dict (.get()).

    run_morning_batch() results contain a MIX of OrchestratorOutput instances
    (success path) and plain dicts (error path).  Using .get() on a Pydantic
    model raises AttributeError; using getattr on a dict silently returns None.
    This helper abstracts the difference so sort/filter logic is type-safe.
    """
    if isinstance(item, dict):
        return item.get(field, default)
    return getattr(item, field, default)


ORCHESTRATOR_SYSTEM_PROMPT = """You are Titan Terminal Orchestrator - the main brain that synthesizes all specialist agent outputs.

Your role:
1. Read all specialist agent analyses (Wyckoff, Nansen, Telegram, TA, Risk)
2. Apply the 3 Laws of trading
3. Calculate Accumulation Score OR Distribution Score (0-100)
4. Determine suggested action: Long Spot / Long Hyperliquid / Short Hyperliquid / Avoid
5. Produce final ranked list with confidence scores
6. Reference past similar patterns from SignalJournal for self-learning

You weight the specialists:
- Wyckoff: 30% (structure is king)
- On-Chain/Nansen: 25% (smart money follows structure)
- TA Ensemble: 25% (confirmation)
- Telegram Alpha: 10% (sentiment/confluence)
- Risk/Levels: 10% (execution quality)

Final confidence = weighted average adjusted by mentor synthesis.

Output clean, actionable signals. The user is not a professional trader - make it crystal clear.
Output ONLY valid JSON, no additional text."""


class Orchestrator(BaseAgent):
    """Main orchestrator that coordinates all specialist agents."""

    def __init__(self):
        super().__init__(
            name="Orchestrator",
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT
        )
        # Initialize all specialist agents
        self.wyckoff = WyckoffAgent()
        self.nansen = NansenAgent()
        self.telegram = TelegramAgent()
        # Initialize ta_ensemble subagents
        self.weekly_subagent = WeeklySubagent()
        self.daily_subagent = DailySubagent()
        self.fourhour_subagent = FourHourSubagent()
        self.ta_mentor = TAMentor()
        self.risk = RiskAgent()
        # Direct Anthropic client for Mentor synthesis call
        self.mentor_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def get_merged_watchlist(self) -> list[str]:
        """Get merged watchlist: settings symbols + recent Telegram signal symbols.

        Deduplication: uppercase all symbols, use dict.fromkeys() to preserve order
        while removing duplicates (settings symbols first, then Telegram additions).
        """
        base_symbols = [s.upper().strip() for s in settings.WATCHLIST]
        telegram_symbols = get_recent_signal_symbols(hours=72)

        # Merge with dedup — settings symbols take priority in ordering
        merged = list(dict.fromkeys(base_symbols + telegram_symbols))
        return merged

    def analyze(self, symbol: str, context: dict) -> dict:
        """Required by BaseAgent - delegates to analyze_symbol."""
        return self.analyze_symbol(symbol, context)

    def analyze_symbol(self, symbol: str, market_data: dict) -> OrchestratorOutput:
        """Run full analysis pipeline for a single symbol."""

        # 1. Get self-learning context (past similar patterns)
        past_patterns = get_similar_patterns(symbol=symbol, limit=5)
        wyckoff_phase_stats = None

        # 2. Run all specialist agents in sequence
        # (In production, these could be parallelized)

        # Wyckoff Analysis
        wyckoff_result = self.wyckoff.analyze(symbol, market_data)

        # Get stats for this Wyckoff phase if identified
        if wyckoff_result.get('composite_analysis', {}).get('overall_phase'):
            phase = wyckoff_result['composite_analysis']['overall_phase']
            wyckoff_phase_stats = get_pattern_stats('wyckoff_phase', {'phase': phase})

        # Nansen On-Chain Analysis
        nansen_result = self.nansen.analyze(symbol, market_data)

        # Telegram Alpha Scan
        telegram_result = self.telegram.analyze(symbol, market_data)

        # TA Ensemble Multi-Timeframe Analysis
        # Run all 3 timeframe subagents
        weekly_result = self.weekly_subagent.analyze(symbol, market_data)
        daily_result = self.daily_subagent.analyze(symbol, market_data)
        fourhour_result = self.fourhour_subagent.analyze(symbol, market_data)

        # Synthesize with TA Mentor
        ta_result = self.ta_mentor.synthesize(weekly_result, daily_result, fourhour_result)

        # Determine bias for risk/levels agent
        wyckoff_bias = wyckoff_result.get('composite_analysis', {}).get('overall_bias', 'neutral')
        ta_bias = ta_result.get('unified_signal', {}).get('bias', 'neutral')

        # Risk/Levels Calculation
        risk_context = {
            **market_data,
            'wyckoff_data': wyckoff_result,
            'ta_data': ta_result,
            'suggested_bias': wyckoff_bias if wyckoff_bias != 'neutral' else ta_bias,
            'open_position_count': market_data.get('open_position_count', 0),
            'account_size': market_data.get('account_size'),
        }
        risk_result = self.risk.analyze(symbol, risk_context)

        # 3. Build agent context for Mentor synthesis
        agent_context = self._build_mentor_context(
            symbol=symbol,
            wyckoff=wyckoff_result,
            nansen=nansen_result,
            telegram=telegram_result,
            ta=ta_result,
            risk=risk_result,
            past_patterns=past_patterns,
            wyckoff_stats=wyckoff_phase_stats,
        )

        # 4. Mentor synthesis — direct Anthropic SDK call
        mentor_output = self._call_mentor(symbol, agent_context, risk_result)

        # 5. Log high-conviction signals to Obsidian vault
        if mentor_output.confidence and mentor_output.confidence > 75:
            self._log_to_obsidian(mentor_output)

        # 6. Record to SignalJournal
        signal_id = self._record_to_journal_v2(mentor_output, wyckoff_result, nansen_result,
                                                telegram_result, ta_result, risk_result)
        mentor_output.signal_id = signal_id

        return mentor_output

    def _build_mentor_context(self, symbol, wyckoff, nansen, telegram, ta, risk, past_patterns, wyckoff_stats):
        """Build structured context string for Mentor SDK call."""
        context = f"""## Symbol: {symbol}

### Wyckoff Analysis
Phase: {wyckoff.get('composite_analysis', {}).get('overall_phase', 'Unknown')}
Bias: {wyckoff.get('composite_analysis', {}).get('overall_bias', 'neutral')}
Confluence Score: {wyckoff.get('composite_analysis', {}).get('confluence_score', 'N/A')}
Notes: {wyckoff.get('composite_analysis', {}).get('notes', 'N/A')}

### On-Chain (Nansen)
Overall Bias: {nansen.overall_signal.bias}
Confidence: {nansen.overall_signal.confidence}
Key Insights: {', '.join(nansen.overall_signal.key_insights) if nansen.overall_signal.key_insights else 'None'}
Signal Ratio: {nansen.signal_count_bullish} bullish / {nansen.signal_count_bearish} bearish

### TA Ensemble
Unified Bias: {ta.get('unified_signal', {}).get('bias', 'N/A')}
Confidence: {ta.get('overall', {}).get('confidence', 'N/A')}
Summary: {ta.get('overall', {}).get('notes', 'N/A')}

### Telegram Alpha
Sentiment: {telegram.overall_sentiment}
Confidence: {telegram.confidence}
Signals Found: {telegram.signals_found}
Confluence: {telegram.confluence_count}
Reasoning: {telegram.reasoning}

### Risk Assessment
Direction: {risk.trade_direction}
Approved: {risk.approved}
Rejection Reasons: {risk.rejection_reasons if risk.rejection_reasons else 'None'}
Entry Zone: {risk.entry_zone.low} - {risk.entry_zone.high} (ideal: {risk.entry_zone.ideal})
Stop Loss: {risk.stop_loss.price} ({risk.stop_loss.type})
TP1: {risk.take_profits.tp1.price if risk.take_profits.tp1 else 'N/A'} (R:R {risk.risk_reward.to_tp1})
TP2: {risk.take_profits.tp2.price if risk.take_profits.tp2 else 'N/A'} (R:R {risk.risk_reward.to_tp2 if risk.risk_reward.to_tp2 else 'N/A'})
3 Laws: {risk.three_laws_check.overall}

### Self-Learning Context
"""
        if past_patterns:
            wins = sum(1 for p in past_patterns if p.get('outcome') == 'win')
            total = len(past_patterns)
            context += f"Past similar signals: {wins}/{total} wins\n"
        if wyckoff_stats:
            context += f"Phase stats: {wyckoff_stats.get('pattern_type')}: {wyckoff_stats.get('win_rate', 0):.0%} win rate\n"
        if not past_patterns and not wyckoff_stats:
            context += "No historical patterns available.\n"

        return context

    def _call_mentor(self, symbol: str, agent_context: str, risk: RiskOutput) -> OrchestratorOutput:
        """Call Anthropic SDK for Mentor synthesis — the centrepiece of v0.5.

        Uses settings.MENTOR_MODEL (claude-opus-4-6) at temperature 0.2.
        Reads all agent outputs and produces the final OrchestratorOutput.
        """
        mentor_system = """You are the Titan Terminal Mentor — a seasoned trading strategist who synthesizes multi-agent analysis into a final trading decision.

You receive outputs from 5 specialist agents: Wyckoff (structure), Nansen (on-chain), TA Ensemble (technicals), Telegram Alpha (sentiment), and Risk (levels/sizing).

Your job:
1. Read ALL agent outputs carefully
2. Identify confluence and conflicts between agents
3. Produce a final directional call: BULLISH, BEARISH, or NO SIGNAL
4. Set a confidence level (0-100) reflecting the strength of confluence
5. Determine the suggested action: Long Spot, Long Hyperliquid, Short Hyperliquid, or Avoid
6. Provide FULL reasoning — do not summarize or truncate. Explain what each agent found and how you weigh the evidence.

You weight the specialists:
- Wyckoff: 30% (structure is king)
- On-Chain/Nansen: 25% (smart money follows structure)
- TA Ensemble: 25% (confirmation)
- Telegram Alpha: 10% (sentiment/confluence)
- Risk/Levels: 10% (execution quality)

If the Risk agent rejected the trade (approved=false), you MUST set suggested_action to Avoid regardless of other signals.

Output ONLY valid JSON matching this exact schema — no markdown, no extra text:
{
    "direction": "BULLISH" | "BEARISH" | "NO SIGNAL",
    "confidence": <int 0-100>,
    "suggested_action": "Long Spot" | "Long Hyperliquid" | "Short Hyperliquid" | "Avoid",
    "accumulation_score": <int 0-100>,
    "distribution_score": <int 0-100>,
    "reasoning": "<FULL reasoning text — multiple paragraphs OK, do not truncate>"
}"""

        user_prompt = f"""Analyze {symbol} and produce your final trading decision.

{agent_context}

Remember: Output ONLY valid JSON. reasoning MUST be complete — capture your full analysis."""

        response = self.mentor_client.messages.create(
            model=settings.MENTOR_MODEL,
            max_tokens=4000,
            temperature=0.2,
            system=mentor_system,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse the Mentor response
        response_text = response.content[0].text
        try:
            mentor_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                mentor_data = json.loads(json_match.group())
            else:
                # Fallback — Mentor response was not valid JSON
                mentor_data = {
                    "direction": "NO SIGNAL",
                    "confidence": 0,
                    "suggested_action": "Avoid",
                    "accumulation_score": 50,
                    "distribution_score": 50,
                    "reasoning": f"Mentor response could not be parsed: {response_text[:500]}"
                }

        # Build OrchestratorOutput from Mentor response + risk data
        output = OrchestratorOutput(
            symbol=symbol,
            timestamp=datetime.now(),
            direction=mentor_data.get("direction", "NO SIGNAL"),
            confidence=max(0, min(100, mentor_data.get("confidence", 0))),
            suggested_action=mentor_data.get("suggested_action", "Avoid"),
            accumulation_score=max(0, min(100, mentor_data.get("accumulation_score", 50))),
            distribution_score=max(0, min(100, mentor_data.get("distribution_score", 50))),
            reasoning=mentor_data.get("reasoning", ""),
            # Carry forward from risk agent
            entry_zone=EntryZoneSimple(
                low=risk.entry_zone.low,
                high=risk.entry_zone.high,
                ideal=risk.entry_zone.ideal
            ) if risk.entry_zone else None,
            stop_loss=risk.stop_loss.price if risk.stop_loss else None,
            tp1=risk.take_profits.tp1.price if risk.take_profits and risk.take_profits.tp1 else None,
            tp2=risk.take_profits.tp2.price if risk.take_profits and risk.take_profits.tp2 else None,
            risk_reward=risk.risk_reward.to_tp1 if risk.risk_reward else None,
            three_laws_check=ThreeLawsCheckSimple(
                law_1_risk=risk.three_laws_check.law_1_risk,
                law_2_rr=risk.three_laws_check.law_2_rr,
                law_3_positions=risk.three_laws_check.law_3_positions,
                overall=risk.three_laws_check.overall
            ) if risk.three_laws_check else None,
        )
        return output

    def _log_to_obsidian(self, output: OrchestratorOutput) -> None:
        """Log high-conviction signal to Obsidian vault in plain English.

        Per user decision: signals with confidence > 75 logged to
        agents/orchestrator/session-notes.md
        """
        import os
        from pathlib import Path

        vault_base = Path(settings.NANSEN_VAULT_PATH).parent.parent  # Up from agents/nansen to vault root
        obsidian_path = vault_base / "agents" / "orchestrator" / "session-notes.md"

        try:
            os.makedirs(obsidian_path.parent, exist_ok=True)

            entry = f"""
---

### {output.symbol} — {output.timestamp.strftime('%Y-%m-%d %H:%M')}

**Direction:** {output.direction} | **Confidence:** {output.confidence}% | **Action:** {output.suggested_action}

**Entry Zone:** {output.entry_zone.low if output.entry_zone else 'N/A'} - {output.entry_zone.high if output.entry_zone else 'N/A'}
**Stop Loss:** {output.stop_loss or 'N/A'} | **TP1:** {output.tp1 or 'N/A'} | **TP2:** {output.tp2 or 'N/A'} | **R:R:** {output.risk_reward or 'N/A'}

**Reasoning:**
{output.reasoning or 'No reasoning provided.'}

"""
            with open(obsidian_path, 'a') as f:
                f.write(entry)

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to log to Obsidian vault: {e}")

    def _record_to_journal_v2(self, output: OrchestratorOutput, wyckoff, nansen, telegram, ta, risk) -> int:
        """Record signal to SignalJournal for self-learning."""
        journal_data = {
            'symbol': output.symbol,
            'timestamp': output.timestamp.isoformat(),
            'timeframe': 'D',
            'accumulation_score': output.accumulation_score,
            'distribution_score': output.distribution_score,
            'confidence': output.confidence,
            'wyckoff_phase': output.wyckoff_phase,
            'wyckoff_notes': output.wyckoff_summary,
            'suggested_action': output.suggested_action,
            'entry_zone_low': output.entry_zone.low if output.entry_zone else None,
            'entry_zone_high': output.entry_zone.high if output.entry_zone else None,
            'stop_loss': output.stop_loss,
            'tp1': output.tp1,
            'tp2': output.tp2,
            'risk_reward': output.risk_reward,
            'nansen_data': json.dumps(nansen.model_dump(mode='json')),
            'telegram_data': json.dumps(telegram.model_dump(mode='json')),
            'wyckoff_data': json.dumps(wyckoff),
            'ta_data': json.dumps(ta),
            'risk_data': json.dumps(risk.model_dump(mode='json')),
            'mentor_critique': json.dumps({"reasoning": output.reasoning}),
            'batch_id': str(uuid.uuid4())[:8]
        }
        return record_signal(journal_data)

    def run_morning_batch(self, market_data_fetcher, symbols: list = None) -> list:
        """Run morning batch analysis for all symbols.

        Args:
            market_data_fetcher: Callable that takes symbol and returns market data dict
            symbols: Optional override list. If None, uses merged watchlist.
        """
        if symbols is None:
            symbols = self.get_merged_watchlist()

        results = []
        for symbol in symbols:
            try:
                # Fetch market data for symbol
                market_data = market_data_fetcher(symbol)

                # Run full analysis
                signal = self.analyze_symbol(symbol, market_data)
                results.append(signal)

            except Exception as e:
                results.append({
                    'symbol': symbol,
                    'error': str(e),
                    'suggested_action': 'Avoid'
                })

        # Sort by confidence (highest first), filter out Avoid unless all are Avoid
        # Use _get_field() because results can be OrchestratorOutput (attr) or error dict (.get())
        actionable = [r for r in results if _get_field(r, 'suggested_action') != 'Avoid']
        if actionable:
            results = sorted(actionable, key=lambda x: _get_field(x, 'confidence', 0), reverse=True)
        else:
            results = sorted(results, key=lambda x: _get_field(x, 'confidence', 0), reverse=True)

        # Limit to top 8-20
        return results[:20]

    def chat(self, user_message: str, context: Optional[dict] = None) -> str:
        """Handle ad-hoc chat queries."""

        # Check for outcome recording
        if 'mark' in user_message.lower() and ('win' in user_message.lower() or 'loss' in user_message.lower()):
            return self._handle_outcome_recording(user_message)

        # Regular chat/analysis query
        prompt = f"""User query: {user_message}

Context: {json.dumps(context) if context else 'No additional context'}

Respond helpfully. If they're asking about a specific token, provide brief analysis.
If they're asking about the market, give an overview.
Keep responses concise and actionable."""

        return self._call_claude(prompt, max_tokens=1000)

    def _handle_outcome_recording(self, message: str) -> str:
        """Parse and record trade outcome from chat."""
        # Simple parsing - could be improved
        from ..db import update_outcome, get_recent_signals

        # Try to extract symbol, outcome, and PnL
        words = message.upper().split()
        symbol = None
        outcome = None
        pnl = None

        for word in words:
            if word in HYPERLIQUID_PERPS:
                symbol = word
            if 'WIN' in word:
                outcome = 'win'
            if 'LOSS' in word:
                outcome = 'loss'

        # Extract PnL percentage
        import re
        pnl_match = re.search(r'[+-]?\d+\.?\d*%?', message)
        if pnl_match:
            pnl_str = pnl_match.group().replace('%', '')
            try:
                pnl = float(pnl_str)
            except ValueError:
                pass

        if symbol and outcome:
            # Find most recent signal for this symbol
            recent = get_recent_signals(limit=50)
            for sig in recent:
                if sig.get('symbol') == symbol and not sig.get('outcome'):
                    update_outcome(sig['id'], outcome, pnl)
                    return f"Recorded: {symbol} {outcome}" + (f" {pnl}%" if pnl else "") + ". Self-learning updated."

        return "Couldn't parse outcome. Try: 'mark SOL as win +15%' or 'mark BTC as loss -3%'"
