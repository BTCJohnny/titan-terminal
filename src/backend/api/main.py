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
from ..config import config

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


class MorningReportResponse(BaseModel):
    timestamp: str
    batch_id: str
    signals: List[Signal]
    market_summary: Optional[str] = None


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
            symbols=config.HYPERLIQUID_PERPS[:10],  # Start with top 10 for MVP
            market_data_fetcher=fetcher.fetch
        )

        response = MorningReportResponse(
            timestamp=datetime.now().isoformat(),
            batch_id=signals[0].get('batch_id', 'unknown') if signals else 'empty',
            signals=[Signal(**_clean_signal(s)) for s in signals if not s.get('error')],
            market_summary=_generate_market_summary(signals)
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
    """Clean signal dict for Pydantic model."""
    return {
        'symbol': signal.get('symbol'),
        'accumulation_score': signal.get('accumulation_score'),
        'distribution_score': signal.get('distribution_score'),
        'confidence': signal.get('confidence', 0),
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
    }


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
