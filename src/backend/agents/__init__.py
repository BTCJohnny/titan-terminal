"""Multi-agent system for Titan Terminal."""
from .base import BaseAgent
from .wyckoff import WyckoffAgent
from .nansen_agent import NansenAgent
from .telegram_agent import TelegramAgent
from .ta_ensemble import WeeklySubagent, DailySubagent, FourHourSubagent, TAMentor
from .risk_agent import RiskAgent
from .mentor import MentorCriticAgent
from .orchestrator import Orchestrator
from .nansen_mcp import (
    fetch_exchange_flows,
    fetch_smart_money,
    fetch_whale_activity,
    fetch_top_pnl,
    fetch_fresh_wallets,
    fetch_funding_rate,
    MCPSignalResult,
)

__all__ = [
    'BaseAgent',
    'WyckoffAgent',
    'NansenAgent',
    'TelegramAgent',
    'WeeklySubagent',
    'DailySubagent',
    'FourHourSubagent',
    'TAMentor',
    'RiskAgent',
    'MentorCriticAgent',
    'Orchestrator',
    'fetch_exchange_flows',
    'fetch_smart_money',
    'fetch_whale_activity',
    'fetch_top_pnl',
    'fetch_fresh_wallets',
    'fetch_funding_rate',
    'MCPSignalResult',
]
