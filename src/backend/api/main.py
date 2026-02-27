"""FastAPI backend for Titan Terminal."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from ..agents import Orchestrator
from ..tools.market_data import get_market_data_fetcher
from ..db import init_db, get_recent_signals, update_outcome, get_connection
from ..config.constants import HYPERLIQUID_PERPS

# Initialize FastAPI app
app = FastAPI(
    title="Titan Terminal API",
    description="Multi-agent crypto trading intelligence",
    version="0.1.0"
)

# CORS for Next.js frontend - permissive for dev, tighten in production
# Using allow_credentials=False with "*" origins for maximum compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    response: str
    timestamp: str


class OutcomeRequest(BaseModel):
    signal_id: int
    outcome: str  # 'win', 'loss', 'breakeven', 'skipped'
    pnl: Optional[float] = None
    notes: Optional[str] = None


class WhaleAlert(BaseModel):
    symbol: str
    alert_type: str  # 'whale_buy', 'whale_sell', 'fresh_wallet', 'smart_accumulation'
    amount_usd: float
    description: str
    timestamp: str
    severity: str  # 'high', 'medium', 'low'


class MarketContext(BaseModel):
    btc_dominance: float
    btc_price: float
    btc_24h_change: float
    total_market_cap: float
    funding_skew: str  # 'long_heavy', 'short_heavy', 'neutral'
    overall_mood: str  # 'greed', 'fear', 'neutral'
    mood_score: int  # 0-100 fear/greed index


class Signal(BaseModel):
    symbol: str
    accumulation_score: Optional[int] = None
    distribution_score: Optional[int] = None
    confidence: int
    suggested_action: str
    wyckoff_phase: Optional[str] = None
    entry_zone: Optional[dict] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    risk_reward: Optional[float] = None
    mentor_verdict: Optional[str] = None
    mentor_concerns: Optional[List[str]] = None
    learning_context: Optional[str] = None
    signal_id: Optional[int] = None
    # New smart money fields
    unusual_activity_score: Optional[int] = None  # 0-100
    smart_flow_usd: Optional[float] = None  # Net smart money flow
    whale_count: Optional[int] = None  # Whales trading this
    fresh_wallets: Optional[int] = None  # New wallets accumulating
    narrative: Optional[str] = None  # "Why this matters" explanation
    price_24h_change: Optional[float] = None
    volume_24h: Optional[float] = None
    sparkline: Optional[List[float]] = None  # 24h price data for mini chart


class MorningReportResponse(BaseModel):
    timestamp: str
    batch_id: str
    signals: List[Signal]
    market_summary: Optional[str] = None
    market_context: Optional[MarketContext] = None
    whale_alerts: Optional[List[WhaleAlert]] = None


# Lazy-loaded orchestrator
_orchestrator = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Titan Terminal API", "version": "0.1.0"}


@app.get("/api/health-test")
async def api_health_test():
    """Simple /api/* health check - no DB, no external calls."""
    return {"status": "ok", "path": "/api/health-test", "cors": "enabled"}


@app.get("/api/morning-report", response_model=MorningReportResponse)
async def get_morning_report(refresh: bool = False):
    """
    Get the morning report with ranked trading signals.

    - If refresh=True or no cached report exists, runs full analysis
    - Returns cached report otherwise
    """
    orchestrator = get_orchestrator()
    fetcher = get_market_data_fetcher()

    # Check for cached report (within last 15 minutes)
    if not refresh:
        cached = _get_cached_report()
        if cached:
            return cached

    # Run full morning batch
    try:
        signals = orchestrator.run_morning_batch(
            symbols=HYPERLIQUID_PERPS[:10],  # Start with top 10 for MVP
            market_data_fetcher=fetcher.fetch
        )

        cleaned_signals = [_clean_signal(s) for s in signals if not s.get('error')]

        response = MorningReportResponse(
            timestamp=datetime.now().isoformat(),
            batch_id=signals[0].get('batch_id', 'unknown') if signals else 'empty',
            signals=[Signal(**s) for s in cleaned_signals],
            market_summary=_generate_market_summary(signals),
            market_context=MarketContext(**_generate_market_context()),
            whale_alerts=[WhaleAlert(**a) for a in _generate_whale_alerts(signals)]
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@app.get("/api/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    """
    Analyze a specific symbol on demand.
    """
    orchestrator = get_orchestrator()
    fetcher = get_market_data_fetcher()

    try:
        market_data = fetcher.fetch(symbol.upper())
        signal = orchestrator.analyze_symbol(symbol.upper(), market_data)
        return Signal(**_clean_signal(signal))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing {symbol}: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for ad-hoc queries.

    Examples:
    - "analyze SOL"
    - "how's the market?"
    - "mark SOL as win +18%"
    """
    orchestrator = get_orchestrator()

    try:
        response = orchestrator.chat(request.message, request.context)
        return ChatResponse(
            response=response,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/api/outcome")
async def record_outcome(request: OutcomeRequest):
    """
    Record trade outcome for self-learning.
    """
    try:
        update_outcome(
            signal_id=request.signal_id,
            outcome=request.outcome,
            pnl=request.pnl,
            notes=request.notes
        )
        return {"status": "ok", "message": f"Outcome recorded for signal {request.signal_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording outcome: {str(e)}")


@app.get("/api/history")
async def get_signal_history(limit: int = 20):
    """
    Get recent signal history from journal.
    """
    try:
        signals = get_recent_signals(limit=limit)
        return {"signals": signals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """
    Get self-learning statistics.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total signals
    cursor.execute("SELECT COUNT(*) as total FROM signal_journal")
    total = cursor.fetchone()['total']

    # Outcomes
    cursor.execute("""
        SELECT outcome, COUNT(*) as count
        FROM signal_journal
        WHERE outcome IS NOT NULL
        GROUP BY outcome
    """)
    outcomes = {row['outcome']: row['count'] for row in cursor.fetchall()}

    # Win rate
    wins = outcomes.get('win', 0)
    losses = outcomes.get('loss', 0)
    total_closed = wins + losses
    win_rate = wins / total_closed if total_closed > 0 else 0

    # Average PnL
    cursor.execute("""
        SELECT AVG(outcome_pnl) as avg_pnl
        FROM signal_journal
        WHERE outcome_pnl IS NOT NULL
    """)
    avg_pnl = cursor.fetchone()['avg_pnl'] or 0

    conn.close()

    return {
        "total_signals": total,
        "outcomes": outcomes,
        "win_rate": round(win_rate * 100, 1),
        "avg_pnl": round(avg_pnl, 2),
        "total_closed_trades": total_closed
    }


def _get_cached_report():
    """Check for a recent cached report."""
    # For MVP, we don't cache - always fresh
    # In production, could use Redis or file-based cache
    return None


def _clean_signal(signal: dict) -> dict:
    """Clean signal dict for Pydantic model with enhanced smart money data."""
    import random

    symbol = signal.get('symbol', '')
    confidence = signal.get('confidence', 0)
    acc_score = signal.get('accumulation_score', 50)

    # Generate smart money metrics (simulated for MVP, will be real data in production)
    unusual_score = min(100, int(confidence * 0.8 + random.randint(0, 30)))
    is_bullish = acc_score > 50

    # Generate narrative based on signal data
    narrative = _generate_narrative(signal)

    # Generate sparkline (24 data points for 24h)
    base = 100
    sparkline = []
    for i in range(24):
        change = random.uniform(-2, 2.5) if is_bullish else random.uniform(-2.5, 2)
        base = base * (1 + change/100)
        sparkline.append(round(base, 2))

    return {
        'symbol': symbol,
        'accumulation_score': signal.get('accumulation_score'),
        'distribution_score': signal.get('distribution_score'),
        'confidence': confidence,
        'suggested_action': signal.get('suggested_action', 'Avoid'),
        'wyckoff_phase': signal.get('wyckoff_phase'),
        'entry_zone': signal.get('entry_zone'),
        'stop_loss': signal.get('stop_loss'),
        'tp1': signal.get('tp1'),
        'tp2': signal.get('tp2'),
        'risk_reward': signal.get('risk_reward'),
        'mentor_verdict': signal.get('mentor_verdict'),
        'mentor_concerns': signal.get('mentor_concerns'),
        'learning_context': signal.get('learning_context'),
        'signal_id': signal.get('signal_id'),
        # Enhanced smart money fields
        'unusual_activity_score': unusual_score,
        'smart_flow_usd': round(random.uniform(500000, 15000000) * (1 if is_bullish else -1), 0),
        'whale_count': random.randint(2, 12) if unusual_score > 50 else random.randint(0, 3),
        'fresh_wallets': random.randint(50, 500) if is_bullish else random.randint(10, 100),
        'narrative': narrative,
        'price_24h_change': round(random.uniform(-8, 12) if is_bullish else random.uniform(-12, 5), 2),
        'volume_24h': round(random.uniform(10000000, 500000000), 0),
        'sparkline': sparkline,
    }


def _generate_narrative(signal: dict) -> str:
    """Generate a 'Why this matters' narrative for the signal."""
    symbol = signal.get('symbol', 'Token')
    phase = signal.get('wyckoff_phase', '')
    acc = signal.get('accumulation_score', 50)
    dist = signal.get('distribution_score', 50)
    confidence = signal.get('confidence', 50)

    narratives = []

    if acc > 70:
        narratives.append(f"Strong accumulation detected with smart money flowing in")
    elif dist > 70:
        narratives.append(f"Distribution underway as whales reduce positions")

    if phase:
        phase_narratives = {
            'accumulation': "Wyckoff accumulation phase suggests institutional buying",
            'markup': "In markup phase - trend continuation likely",
            'distribution': "Distribution phase - consider taking profits",
            'markdown': "Markdown phase - avoid longs, potential short opportunity",
            'spring': "Spring pattern detected - potential reversal setup",
            'upthrust': "Upthrust pattern - watch for breakdown",
        }
        if phase.lower() in phase_narratives:
            narratives.append(phase_narratives[phase.lower()])

    if confidence > 75:
        narratives.append("High confluence across multiple indicators")
    elif confidence < 40:
        narratives.append("Low conviction setup - wait for confirmation")

    return ". ".join(narratives) if narratives else f"{symbol} showing mixed signals - monitor for clarity"


def _generate_market_context() -> dict:
    """Generate market context data."""
    import random

    # Simulated market data (will be real API calls in production)
    mood_score = random.randint(25, 75)
    if mood_score > 60:
        mood = 'greed'
    elif mood_score < 40:
        mood = 'fear'
    else:
        mood = 'neutral'

    funding = random.choice(['long_heavy', 'short_heavy', 'neutral'])

    return {
        'btc_dominance': round(random.uniform(52, 58), 1),
        'btc_price': round(random.uniform(85000, 105000), 0),
        'btc_24h_change': round(random.uniform(-5, 7), 2),
        'total_market_cap': round(random.uniform(2.8, 3.5) * 1e12, 0),
        'funding_skew': funding,
        'overall_mood': mood,
        'mood_score': mood_score,
    }


def _generate_whale_alerts(signals: list) -> list:
    """Generate whale alerts based on signals."""
    import random

    alerts = []
    alert_types = [
        ('whale_buy', 'Whale accumulated', 'high'),
        ('whale_sell', 'Whale distribution detected', 'high'),
        ('fresh_wallet', 'Fresh wallets clustering', 'medium'),
        ('smart_accumulation', 'Smart money inflow', 'medium'),
    ]

    # Generate 3-6 alerts from top signals
    for signal in signals[:6]:
        if random.random() > 0.4:  # 60% chance of alert
            symbol = signal.get('symbol', 'BTC')
            alert_type, desc_prefix, severity = random.choice(alert_types)
            amount = random.uniform(1000000, 25000000)

            alerts.append({
                'symbol': symbol,
                'alert_type': alert_type,
                'amount_usd': round(amount, 0),
                'description': f"{desc_prefix} ${amount/1e6:.1f}M in {symbol}",
                'timestamp': datetime.now().isoformat(),
                'severity': severity,
            })

    # Sort by amount
    alerts.sort(key=lambda x: x['amount_usd'], reverse=True)
    return alerts[:5]  # Max 5 alerts


def _generate_market_summary(signals: list) -> str:
    """Generate a brief market summary from signals."""
    if not signals:
        return "No actionable signals found."

    bullish = sum(1 for s in signals if s.get('accumulation_score', 0) > 60)
    bearish = sum(1 for s in signals if s.get('distribution_score', 0) > 60)

    if bullish > bearish:
        sentiment = "Accumulation signals dominate"
    elif bearish > bullish:
        sentiment = "Distribution signals dominate"
    else:
        sentiment = "Mixed signals"

    top = signals[0] if signals else None
    top_note = f"Top pick: {top.get('symbol')} ({top.get('confidence')}% confidence)" if top else ""

    return f"{sentiment}. {top_note}"
