/**
 * API client for Titan Terminal backend
 */

// Force fallback if env var not picked up (Next.js client-side quirk)
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// Debug: log the API base URL on load
console.log("[Titan API] Base URL:", API_BASE)
console.log("[Titan API] Env var:", process.env.NEXT_PUBLIC_API_URL)

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

/**
 * Health check - test backend connectivity
 */
export async function checkHealth(): Promise<{ ok: boolean; message: string }> {
  const url = `${API_BASE}/`
  console.log("[Titan API] Health check:", url)
  try {
    const res = await fetch(url, { method: "GET" })
    if (res.ok) {
      const data = await res.json()
      return { ok: true, message: `Connected: ${data.service} v${data.version}` }
    }
    return { ok: false, message: `Backend returned ${res.status}` }
  } catch (err) {
    console.error("[Titan API] Health check failed:", err)
    return { ok: false, message: `Cannot reach backend at ${API_BASE}` }
  }
}

export async function getMorningReport(refresh: boolean = false): Promise<MorningReport> {
  const url = `${API_BASE}/api/morning-report?refresh=${refresh}`
  console.log("[Titan API] Fetching morning report:", url)
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`Failed to fetch morning report: ${res.statusText}`)
  }
  return res.json()
}

export async function analyzeSymbol(symbol: string): Promise<Signal> {
  const url = `${API_BASE}/api/analyze/${symbol}`
  console.log("[Titan API] Analyzing symbol:", url)
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`Failed to analyze ${symbol}: ${res.statusText}`)
  }
  return res.json()
}

export async function sendChat(message: string, context?: Record<string, unknown>): Promise<ChatResponse> {
  const url = `${API_BASE}/api/chat`
  console.log("[Titan API] Sending chat:", url)
  const res = await fetch(url, {
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
  const url = `${API_BASE}/api/outcome`
  console.log("[Titan API] Recording outcome:", url)
  const res = await fetch(url, {
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
  const url = `${API_BASE}/api/stats`
  console.log("[Titan API] Fetching stats:", url)
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`Failed to fetch stats: ${res.statusText}`)
  }
  return res.json()
}

export async function getHistory(limit: number = 20): Promise<{ signals: Signal[] }> {
  const url = `${API_BASE}/api/history?limit=${limit}`
  console.log("[Titan API] Fetching history:", url)
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`Failed to fetch history: ${res.statusText}`)
  }
  return res.json()
}
