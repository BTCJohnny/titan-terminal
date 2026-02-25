"""Orchestrator - Main brain that coordinates all specialist agents."""
import json
from datetime import datetime
from typing import Optional
import uuid

from .base import BaseAgent
from .wyckoff import WyckoffAgent
from .nansen import NansenAgent
from .telegram import TelegramAgent
from .ta_ensemble import TAEnsembleAgent
from .risk_levels import RiskLevelsAgent
from .mentor import MentorCriticAgent
from ..db import record_signal, get_similar_patterns, get_pattern_stats
from ..config import config

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

Final confidence = weighted average adjusted by mentor critique.

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
        self.ta_ensemble = TAEnsembleAgent()
        self.risk_levels = RiskLevelsAgent()
        self.mentor = MentorCriticAgent()

    def analyze(self, symbol: str, context: dict) -> dict:
        """Required by BaseAgent - delegates to analyze_symbol."""
        return self.analyze_symbol(symbol, context)

    def analyze_symbol(self, symbol: str, market_data: dict) -> dict:
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

        # TA Ensemble Analysis
        ta_result = self.ta_ensemble.analyze(symbol, market_data)

        # Determine bias for risk/levels agent
        wyckoff_bias = wyckoff_result.get('composite_analysis', {}).get('overall_bias', 'neutral')
        ta_bias = ta_result.get('overall', {}).get('bias', 'neutral')

        # Risk/Levels Calculation
        risk_context = {
            **market_data,
            'wyckoff_data': wyckoff_result,
            'ta_data': ta_result,
            'suggested_bias': wyckoff_bias if wyckoff_bias != 'neutral' else ta_bias
        }
        risk_result = self.risk_levels.analyze(symbol, risk_context)

        # 3. Synthesize all results
        synthesis = self._synthesize_results(
            symbol=symbol,
            wyckoff=wyckoff_result,
            nansen=nansen_result,
            telegram=telegram_result,
            ta=ta_result,
            risk=risk_result,
            past_patterns=past_patterns,
            wyckoff_stats=wyckoff_phase_stats
        )

        # 4. Get mentor critique
        mentor_critique = self.mentor.critique(synthesis)

        # 5. Apply mentor adjustment
        final_signal = self._apply_mentor_adjustment(synthesis, mentor_critique)

        # 6. Record to SignalJournal for self-learning
        signal_id = self._record_to_journal(final_signal, wyckoff_result, nansen_result,
                                            telegram_result, ta_result, risk_result,
                                            mentor_critique)
        final_signal['signal_id'] = signal_id

        return final_signal

    def _synthesize_results(self, symbol: str, wyckoff: dict, nansen: dict,
                           telegram: dict, ta: dict, risk: dict,
                           past_patterns: list, wyckoff_stats: Optional[dict]) -> dict:
        """Synthesize all specialist outputs into a unified signal."""

        # Extract key data points
        wyckoff_composite = wyckoff.get('composite_analysis', {})
        nansen_overall = nansen.get('overall_signal', {})
        ta_overall = ta.get('overall', {})
        risk_verdict = risk.get('final_verdict', {})

        # Calculate accumulation/distribution score
        wyckoff_bias = wyckoff_composite.get('overall_bias', 'neutral')
        nansen_bias = nansen_overall.get('bias', 'neutral')
        ta_bias = ta_overall.get('bias', 'neutral')

        acc_score, dist_score = self._calculate_acc_dist_scores(
            wyckoff_bias, nansen_bias, ta_bias,
            wyckoff_composite.get('confluence_score', 50),
            nansen_overall.get('confidence', 50),
            ta_overall.get('confidence', 50)
        )

        # Determine suggested action
        suggested_action = self._determine_action(
            wyckoff_bias, risk_verdict.get('action', 'avoid'),
            acc_score, dist_score
        )

        # Calculate confidence (weighted average)
        confidence = self._calculate_confidence(
            wyckoff_composite.get('confluence_score', 50),
            nansen_overall.get('confidence', 50),
            ta_overall.get('confidence', 50),
            telegram.get('confidence', 0),
            risk_verdict.get('confidence', 50)
        )

        # Build self-learning context
        learning_context = ""
        if past_patterns:
            wins = sum(1 for p in past_patterns if p.get('outcome') == 'win')
            total = len(past_patterns)
            learning_context = f"Past similar signals: {wins}/{total} wins"
        if wyckoff_stats:
            learning_context += f" | {wyckoff_stats.get('pattern_type')}: {wyckoff_stats.get('win_rate', 0):.0%} win rate"

        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'accumulation_score': acc_score,
            'distribution_score': dist_score,
            'confidence': confidence,
            'suggested_action': suggested_action,
            'wyckoff_phase': wyckoff_composite.get('overall_phase'),
            'wyckoff_summary': wyckoff_composite.get('notes'),
            'nansen_summary': nansen_overall.get('key_insights', []),
            'ta_summary': ta_overall.get('notes'),
            'telegram_signals': telegram.get('relevant_signals', []),
            'entry_zone': risk.get('entry_zone', {}),
            'stop_loss': risk.get('stop_loss', {}).get('price'),
            'tp1': risk.get('take_profits', {}).get('tp1', {}).get('price'),
            'tp2': risk.get('take_profits', {}).get('tp2', {}).get('price'),
            'risk_reward': risk.get('risk_reward', {}).get('to_tp1'),
            'three_laws_check': risk.get('three_laws_check', {}),
            'learning_context': learning_context,
            'key_levels': ta.get('key_levels', {})
        }

    def _calculate_acc_dist_scores(self, wyckoff_bias: str, nansen_bias: str,
                                   ta_bias: str, wyckoff_conf: int,
                                   nansen_conf: int, ta_conf: int) -> tuple:
        """Calculate accumulation and distribution scores."""

        def bias_to_score(bias: str) -> tuple:
            if bias == 'accumulation' or bias == 'bullish':
                return (1, 0)
            elif bias == 'distribution' or bias == 'bearish':
                return (0, 1)
            return (0.5, 0.5)

        # Weight biases
        w_acc, w_dist = 0, 0

        # Wyckoff (30%)
        acc, dist = bias_to_score(wyckoff_bias)
        w_acc += acc * 0.3 * wyckoff_conf
        w_dist += dist * 0.3 * wyckoff_conf

        # Nansen (25%)
        acc, dist = bias_to_score(nansen_bias)
        w_acc += acc * 0.25 * nansen_conf
        w_dist += dist * 0.25 * nansen_conf

        # TA (25%)
        acc, dist = bias_to_score(ta_bias)
        w_acc += acc * 0.25 * ta_conf
        w_dist += dist * 0.25 * ta_conf

        # Normalize to 0-100
        total = w_acc + w_dist
        if total > 0:
            acc_score = int((w_acc / total) * 100)
            dist_score = int((w_dist / total) * 100)
        else:
            acc_score, dist_score = 50, 50

        return acc_score, dist_score

    def _determine_action(self, wyckoff_bias: str, risk_action: str,
                         acc_score: int, dist_score: int) -> str:
        """Determine suggested trading action."""

        if risk_action == 'avoid':
            return 'Avoid'

        if acc_score > 65:
            if risk_action == 'long_perp':
                return 'Long Hyperliquid'
            return 'Long Spot'
        elif dist_score > 65:
            return 'Short Hyperliquid'
        else:
            return 'Avoid'

    def _calculate_confidence(self, wyckoff: int, nansen: int, ta: int,
                             telegram: int, risk: int) -> int:
        """Calculate weighted confidence score."""
        # Weights: Wyckoff 30%, Nansen 25%, TA 25%, Telegram 10%, Risk 10%
        weighted = (
            wyckoff * 0.30 +
            nansen * 0.25 +
            ta * 0.25 +
            telegram * 0.10 +
            risk * 0.10
        )
        return int(weighted)

    def _apply_mentor_adjustment(self, signal: dict, critique: dict) -> dict:
        """Apply mentor's confidence adjustment and add critique."""

        adjustment = critique.get('confidence_adjustment', 0)
        signal['confidence'] = max(0, min(100, signal['confidence'] + adjustment))
        signal['mentor_verdict'] = critique.get('verdict')
        signal['mentor_concerns'] = critique.get('concerns', [])
        signal['mentor_notes'] = critique.get('mentor_notes')

        # If mentor rejects, change action to Avoid
        if critique.get('verdict') == 'reject':
            signal['suggested_action'] = 'Avoid'
            signal['confidence'] = min(signal['confidence'], 30)

        return signal

    def _record_to_journal(self, signal: dict, wyckoff: dict, nansen: dict,
                          telegram: dict, ta: dict, risk: dict,
                          mentor: dict) -> int:
        """Record signal to SignalJournal for self-learning."""

        journal_data = {
            'symbol': signal['symbol'],
            'timestamp': signal['timestamp'],
            'timeframe': 'D',  # Primary timeframe
            'accumulation_score': signal.get('accumulation_score'),
            'distribution_score': signal.get('distribution_score'),
            'confidence': signal['confidence'],
            'wyckoff_phase': signal.get('wyckoff_phase'),
            'wyckoff_notes': signal.get('wyckoff_summary'),
            'suggested_action': signal['suggested_action'],
            'entry_zone_low': signal.get('entry_zone', {}).get('low'),
            'entry_zone_high': signal.get('entry_zone', {}).get('high'),
            'stop_loss': signal.get('stop_loss'),
            'tp1': signal.get('tp1'),
            'tp2': signal.get('tp2'),
            'risk_reward': signal.get('risk_reward'),
            'nansen_data': json.dumps(nansen),
            'telegram_data': json.dumps(telegram),
            'wyckoff_data': json.dumps(wyckoff),
            'ta_data': json.dumps(ta),
            'risk_data': json.dumps(risk),
            'mentor_critique': json.dumps(mentor),
            'batch_id': str(uuid.uuid4())[:8]
        }

        return record_signal(journal_data)

    def run_morning_batch(self, symbols: list, market_data_fetcher) -> list:
        """Run morning batch analysis for all symbols."""

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
        actionable = [r for r in results if r.get('suggested_action') != 'Avoid']
        if actionable:
            results = sorted(actionable, key=lambda x: x.get('confidence', 0), reverse=True)
        else:
            results = sorted(results, key=lambda x: x.get('confidence', 0), reverse=True)

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
            if word in config.HYPERLIQUID_PERPS:
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
