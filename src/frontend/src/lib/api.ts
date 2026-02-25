/**
 * API client for Titan Terminal backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface Signal {
  symbol: string
  accumulation_score: number | null
  distribution_score: number | null
  confidence: number
  suggested_action: string
  wyckoff_phase: string | null
  entry_zone: { low: number; high: number; ideal: number } | null
  stop_loss: number | null
  tp1: number | null
  tp2: number | null
  risk_reward: number | null
  mentor_verdict: string | null
  mentor_concerns: string[] | null
  learning_context: string | null
  signal_id: number | null
}

export interface MorningReport {
  timestamp: string
  batch_id: string
  signals: Signal[]
  market_summary: string | null
}

export interface ChatResponse {
  response: string
  timestamp: string
}

export interface Stats {
  total_signals: number
  outcomes: Record<string, number>
  win_rate: number
  avg_pnl: number
  total_closed_trades: number
}

export async function getMorningReport(refresh: boolean = false): Promise<MorningReport> {
  const res = await fetch(`${API_BASE}/api/morning-report?refresh=${refresh}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch morning report: ${res.statusText}`)
  }
  return res.json()
}

export async function analyzeSymbol(symbol: string): Promise<Signal> {
  const res = await fetch(`${API_BASE}/api/analyze/${symbol}`)
  if (!res.ok) {
    throw new Error(`Failed to analyze ${symbol}: ${res.statusText}`)
  }
  return res.json()
}

export async function sendChat(message: string, context?: Record<string, unknown>): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, context }),
  })
  if (!res.ok) {
    throw new Error(`Chat error: ${res.statusText}`)
  }
  return res.json()
}

export async function recordOutcome(
  signalId: number,
  outcome: string,
  pnl?: number,
  notes?: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/outcome`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      signal_id: signalId,
      outcome,
      pnl,
      notes,
    }),
  })
  if (!res.ok) {
    throw new Error(`Failed to record outcome: ${res.statusText}`)
  }
}

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/api/stats`)
  if (!res.ok) {
    throw new Error(`Failed to fetch stats: ${res.statusText}`)
  }
  return res.json()
}

export async function getHistory(limit: number = 20): Promise<{ signals: Signal[] }> {
  const res = await fetch(`${API_BASE}/api/history?limit=${limit}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch history: ${res.statusText}`)
  }
  return res.json()
}
