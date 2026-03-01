"""FastAPI backend for Titan Terminal."""
import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..agents import Orchestrator
from ..tools.market_data import get_market_data_fetcher
from ..db import init_db, init_snapshot_tables, get_recent_signals, update_outcome, get_connection
from ..models.orchestrator_output import OrchestratorOutput
from ..config.settings import settings

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
    init_snapshot_tables()


# Request/Response models
class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    response: str
    timestamp: str


class OutcomeRequest(BaseModel):
    signal_id: int
    outcome: str  # 'win', 'loss', 'breakeven', 'skipped'
    pnl: Optional[float] = None
    notes: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """Single-symbol analysis response — serialized OrchestratorOutput."""
    symbol: str
    signal_id: Optional[int] = None
    timestamp: str
    direction: Optional[str] = None  # BULLISH/BEARISH/NO SIGNAL
    confidence: int
    suggested_action: str
    accumulation_score: int
    distribution_score: int
    reasoning: Optional[str] = None
    entry_zone: Optional[dict] = None  # {low, high, ideal}
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    risk_reward: Optional[float] = None
    three_laws_check: Optional[dict] = None
    wyckoff_phase: Optional[str] = None
    nansen_summary: Optional[list] = None
    ta_summary: Optional[str] = None


class MorningReportResponse(BaseModel):
    """Morning report: ranked list of AnalyzeResponse items."""
    timestamp: str
    count: int
    signals: List[AnalyzeResponse]


# Lazy-loaded orchestrator
_orchestrator = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


# Lazy-loaded Anthropic client for chat
_chat_client = None


def get_chat_client() -> anthropic.Anthropic:
    global _chat_client
    if _chat_client is None:
        _chat_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _chat_client


def _build_chat_context() -> str:
    """Build signal context string from recent morning batch data.

    Fetches recent signals from journal. If no recent signals, returns a
    minimal context note prompting the user to run /morning-report first.
    """
    recent = get_recent_signals(limit=10)
    if not recent:
        return "No recent analysis data available. Suggest running /morning-report first."

    context_parts = ["## Recent Signal Data\n"]
    for sig in recent[:5]:
        context_parts.append(
            f"**{sig.get('symbol', '?')}** — "
            f"Action: {sig.get('suggested_action', 'N/A')}, "
            f"Confidence: {sig.get('confidence', 'N/A')}%, "
            f"Direction: {sig.get('direction', 'N/A')}, "
            f"Entry: {sig.get('entry_zone_low', 'N/A')}-{sig.get('entry_zone_high', 'N/A')}, "
            f"Stop: {sig.get('stop_loss', 'N/A')}, "
            f"TP1: {sig.get('tp1', 'N/A')}, TP2: {sig.get('tp2', 'N/A')}, "
            f"R:R: {sig.get('risk_reward', 'N/A')}"
        )

    return "\n".join(context_parts)


def _serialize_output(output: OrchestratorOutput) -> dict:
    """Convert OrchestratorOutput to API response dict."""
    return {
        "symbol": output.symbol,
        "signal_id": output.signal_id,
        "timestamp": output.timestamp.isoformat(),
        "direction": output.direction,
        "confidence": output.confidence,
        "suggested_action": output.suggested_action,
        "accumulation_score": output.accumulation_score,
        "distribution_score": output.distribution_score,
        "reasoning": output.reasoning,
        "entry_zone": output.entry_zone.model_dump() if output.entry_zone else None,
        "stop_loss": output.stop_loss,
        "tp1": output.tp1,
        "tp2": output.tp2,
        "risk_reward": output.risk_reward,
        "three_laws_check": output.three_laws_check.model_dump() if output.three_laws_check else None,
        "wyckoff_phase": output.wyckoff_phase,
        "nansen_summary": output.nansen_summary,
        "ta_summary": output.ta_summary,
    }


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Titan Terminal API", "version": "0.1.0"}


@app.get("/api/health-test")
async def api_health_test():
    """Simple /api/* health check - no DB, no external calls."""
    return {"status": "ok", "path": "/api/health-test", "cors": "enabled"}


@app.get("/api/morning-report-mock", response_model=MorningReportResponse)
async def get_morning_report_mock():
    """Temporary mock endpoint to test dashboard UI flow."""
    mock_signals = [
        AnalyzeResponse(
            symbol="ETH", signal_id=1, timestamp=datetime.now().isoformat(),
            direction="BULLISH", confidence=82, suggested_action="Long Spot",
            accumulation_score=75, distribution_score=20,
            reasoning="Strong accumulation pattern with rising on-chain activity. Smart money wallets increasing ETH positions over the past 72 hours. Wyckoff Spring pattern forming at key support level with declining sell pressure.",
            entry_zone={"low": 3180.0, "high": 3350.0, "ideal": 3250.0},
            stop_loss=3050.0, tp1=3600.0, tp2=3900.0, risk_reward=3.2,
            three_laws_check={"law_1_risk": "pass", "law_2_rr": "pass", "law_3_positions": "pass", "overall": "approved"},
            wyckoff_phase="Spring",
            nansen_summary=[
                "Smart money wallets accumulating — 12 large wallets added 45K ETH in past 48h, bullish signal",
                "Exchange outflows accelerating — net 28K ETH withdrawn from exchanges, reducing sell-side supply",
                "Fresh wallet activity rising — 340 new wallets with >10 ETH created this week, accumulation phase",
                "Buy pressure dominant — top PnL traders 73% long, positive sentiment shift",
                "Whale activity bullish — 3 whale wallets moved 15K ETH to cold storage, long-term holding signal",
            ],
            ta_summary="RSI at 58 with bullish divergence on 4H. MACD crossover forming. Volume profile shows strong support at 3200.",
        ),
        AnalyzeResponse(
            symbol="BTC", signal_id=2, timestamp=datetime.now().isoformat(),
            direction="BEARISH", confidence=45, suggested_action="Avoid",
            accumulation_score=30, distribution_score=65,
            reasoning="Distribution pattern detected. Exchange inflows increasing while on-chain metrics show weakening demand. Risk/reward unfavorable at current levels.",
            entry_zone=None, stop_loss=None, tp1=None, tp2=None, risk_reward=None,
            three_laws_check={"law_1_risk": "fail", "law_2_rr": "fail", "law_3_positions": "check_current_positions", "overall": "rejected"},
            wyckoff_phase="Distribution",
            nansen_summary=[
                "Smart money reducing exposure — 8 large wallets sold 1200 BTC this week, bearish signal",
                "Exchange inflows rising — net 5400 BTC deposited to exchanges, increasing sell-side pressure",
                "On-chain holdings declining — long-term holder supply dropping for 3rd consecutive week",
                "Sell pressure dominant — top PnL traders 62% short, negative sentiment",
                "Whale activity mixed — some redistribution but no clear accumulation pattern",
            ],
            ta_summary="RSI at 42, trending down. Death cross forming on daily. Support at 58K under pressure.",
        ),
        AnalyzeResponse(
            symbol="SOL", signal_id=3, timestamp=datetime.now().isoformat(),
            direction="NO SIGNAL", confidence=55, suggested_action="Avoid",
            accumulation_score=50, distribution_score=45,
            reasoning="Neutral positioning. On-chain metrics are mixed with no clear directional bias. Wait for clearer setup before entering.",
            entry_zone={"low": 145.0, "high": 160.0, "ideal": 152.0},
            stop_loss=138.0, tp1=175.0, tp2=195.0, risk_reward=2.1,
            three_laws_check={"law_1_risk": "pass", "law_2_rr": "pass", "law_3_positions": "check_current_positions", "overall": "caution"},
            wyckoff_phase="Ranging",
            nansen_summary=[
                "Smart money neutral — no significant position changes detected",
                "Exchange flows balanced — roughly equal inflows and outflows this week",
                "Fresh wallet activity stable — no unusual patterns detected",
            ],
            ta_summary="Consolidating between 145-162. Bollinger bands tightening, breakout imminent but direction unclear.",
        ),
    ]
    return MorningReportResponse(
        timestamp=datetime.now().isoformat(),
        count=len(mock_signals),
        signals=mock_signals,
    )


@app.get("/api/morning-report", response_model=MorningReportResponse)
async def get_morning_report(symbols: str = None):
    """
    Get the morning report with ranked trading signals.

    Runs on-demand analysis via orchestrator.run_morning_batch() and returns
    top 3-5 opportunities ranked by confidence.

    Query params:
        symbols: Optional comma-separated symbol list (e.g. "ETH,BTC").
                 If omitted, uses full merged watchlist.
    """
    orchestrator = get_orchestrator()
    fetcher = get_market_data_fetcher()
    symbol_list = [s.strip().upper() for s in symbols.split(",")] if symbols else None

    try:
        results = orchestrator.run_morning_batch(market_data_fetcher=fetcher.fetch, symbols=symbol_list)

        # Filter to only valid OrchestratorOutput instances (skip error dicts)
        valid_outputs = [r for r in results if isinstance(r, OrchestratorOutput)]

        # Limit to top 5 results (already sorted by confidence in run_morning_batch)
        top_outputs = valid_outputs[:5]

        signals = [AnalyzeResponse(**_serialize_output(output)) for output in top_outputs]

        return MorningReportResponse(
            timestamp=datetime.now().isoformat(),
            count=len(signals),
            signals=signals,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


@app.get("/api/analyze/{symbol}", response_model=AnalyzeResponse)
async def analyze_symbol(symbol: str):
    """
    Analyze a specific symbol on demand.

    Runs orchestrator.analyze_symbol() for one symbol and returns a
    complete OrchestratorOutput.
    """
    orchestrator = get_orchestrator()
    fetcher = get_market_data_fetcher()

    try:
        market_data = fetcher.fetch(symbol.upper())
        output = orchestrator.analyze_symbol(symbol.upper(), market_data)
        return AnalyzeResponse(**_serialize_output(output))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing {symbol}: {str(e)}")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for natural language signal Q&A.

    Uses Anthropic SDK (settings.MODEL_NAME) to generate answers
    grounded in live signal/journal data.

    Examples:
    - "What's the best setup today?"
    - "How does SOL look?"
    - "Which symbol has the highest confidence?"
    """
    client = get_chat_client()
    signal_context = _build_chat_context()

    system_prompt = (
        "You are Titan Terminal's trading assistant. You answer questions about "
        "crypto trading signals, setups, and market analysis.\n\n"
        "You have access to recent signal analysis data (provided below). Use this "
        "data to ground your answers in real analysis — never make up numbers or signals.\n\n"
        "If the user asks about a specific symbol, reference the analysis data if available. "
        "If no data exists for that symbol, say so clearly.\n\n"
        "Keep answers concise, actionable, and clear. The user is learning to trade — "
        "explain reasoning, not just conclusions.\n\n"
        "## Signal Data\n"
        + signal_context
    )

    try:
        response = client.messages.create(
            model=settings.MODEL_NAME,
            max_tokens=1000,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": request.question}]
        )

        answer = response.content[0].text

        return ChatResponse(
            response=answer,
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
