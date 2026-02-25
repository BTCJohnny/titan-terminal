/**
 * API client for Titan Terminal backend
 */

// Force fallback if env var not picked up (Next.js client-side quirk)
// Backend runs on port 8001 by default
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

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
 * Health check - test backend connectivity AND /api/* CORS
 */
export async function checkHealth(): Promise<{ ok: boolean; message: string }> {
  // Test root endpoint first
  const rootUrl = `${API_BASE}/`
  console.log("[Titan API] Health check (root):", rootUrl)
  try {
    const rootRes = await fetch(rootUrl, { method: "GET" })
    if (!rootRes.ok) {
      return { ok: false, message: `Backend returned ${rootRes.status}` }
    }
    const rootData = await rootRes.json()
    console.log("[Titan API] Root OK:", rootData)

    // Test /api/* endpoint to verify CORS on API routes
    const apiUrl = `${API_BASE}/api/health-test`
    console.log("[Titan API] Health check (api):", apiUrl)
    const apiRes = await fetch(apiUrl, { method: "GET" })
    if (!apiRes.ok) {
      return { ok: false, message: `API routes returned ${apiRes.status}` }
    }
    const apiData = await apiRes.json()
    console.log("[Titan API] API health-test OK:", apiData)

    return { ok: true, message: `Connected: ${rootData.service} v${rootData.version}` }
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
