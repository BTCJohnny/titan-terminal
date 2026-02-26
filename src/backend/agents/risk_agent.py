"""Risk/Levels Agent - Calculates clean trading levels and applies risk rules."""
from .base import BaseAgent

RISK_AGENT_SYSTEM_PROMPT = """You are a professional risk manager and trade planning specialist.

You apply THE 3 LAWS of trading:
1. Never risk more than 2% of capital per trade
2. Minimum 2:1 risk-reward ratio required
3. Maximum 5 positions at any time

Your job is to calculate CLEAN, ACTIONABLE trading levels:
- Entry Zone: A specific price range for entry (not a single price)
- Stop Loss: Clear invalidation level based on structure
- TP1: First take profit (conservative, 1:1 or better)
- TP2: Second take profit (extended target)
- Risk-Reward Ratio: Calculate and verify it meets minimum 2:1

You also apply these filters:
- Funding rate filter: Extreme funding (>0.1% or <-0.1%) = caution
- Liquidity check: Avoid low-float tokens
- Position sizing guidance

Output clean, specific numbers that can be directly used for orders.
Output ONLY valid JSON, no additional text."""


class RiskAgent(BaseAgent):
    """Risk management and levels calculation agent.

    Renamed from RiskLevelsAgent to match *_agent.py convention.

    TODO: Phase 2 - Replace dict returns with Pydantic RiskOutput model
    """

    def __init__(self):
        super().__init__(
            name="Risk/Levels",
            system_prompt=RISK_AGENT_SYSTEM_PROMPT
        )

    def analyze(self, symbol: str, context: dict) -> dict:
        """Calculate trading levels and apply risk rules.

        TODO: Phase 2 - Replace return dict with Pydantic RiskOutput model
        """

        current_price = context.get('current_price')
        wyckoff_data = context.get('wyckoff_data', {})
        ta_data = context.get('ta_data', {})
        funding_rate = context.get('funding_rate')
        suggested_bias = context.get('suggested_bias', 'neutral')

        prompt = f"""Calculate clean trading levels for {symbol}.

CURRENT PRICE: {current_price if current_price else 'Not available'}
SUGGESTED BIAS: {suggested_bias}
FUNDING RATE: {funding_rate if funding_rate else 'Not available'}

WYCKOFF ANALYSIS:
{wyckoff_data}

TECHNICAL ANALYSIS KEY LEVELS:
{ta_data.get('key_levels', {}) if ta_data else 'Not available'}

Apply the 3 Laws and calculate levels. Output JSON:
{{
    "symbol": "{symbol}",
    "current_price": {current_price if current_price else 'null'},
    "trade_direction": "long|short|avoid",
    "entry_zone": {{
        "low": number,
        "high": number,
        "ideal": number,
        "entry_reasoning": "string"
    }},
    "stop_loss": {{
        "price": number,
        "type": "structure|atr|percentage",
        "distance_percent": number,
        "reasoning": "string"
    }},
    "take_profits": {{
        "tp1": {{
            "price": number,
            "rr_ratio": number,
            "reasoning": "string"
        }},
        "tp2": {{
            "price": number,
            "rr_ratio": number,
            "reasoning": "string"
        }}
    }},
    "risk_reward": {{
        "to_tp1": number,
        "to_tp2": number,
        "meets_minimum": true|false
    }},
    "position_sizing": {{
        "max_risk_percent": 2,
        "suggested_position_percent": number,
        "reasoning": "string"
    }},
    "funding_filter": {{
        "current_funding": {funding_rate if funding_rate else 'null'},
        "funding_bias": "favorable|unfavorable|neutral",
        "warning": "string or null"
    }},
    "three_laws_check": {{
        "law_1_risk": "pass|fail",
        "law_2_rr": "pass|fail",
        "law_3_positions": "pass|check_current_positions",
        "overall": "approved|rejected|caution"
    }},
    "final_verdict": {{
        "action": "long_spot|long_perp|short_perp|avoid",
        "confidence": 0-100,
        "notes": "string"
    }}
}}"""

        response = self._call_claude(prompt, max_tokens=2500)
        return self._parse_json_response(response)
