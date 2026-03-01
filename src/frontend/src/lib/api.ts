/**
 * API client for Titan Terminal backend
 * Matches Phase 22 FastAPI endpoints exactly.
 */

import type { AnalyzeResponse, MorningReportResponse, ChatResponse } from "./types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

console.log("[Titan API] Base URL:", API_BASE)

/**
 * Health check — tests both GET / and GET /api/health-test (CORS on API routes)
 */
export async function checkHealth(): Promise<{ ok: boolean; message: string }> {
  const rootUrl = `${API_BASE}/`
  console.log("[Titan API] Health check (root):", rootUrl)
  try {
    const rootRes = await fetch(rootUrl, { method: "GET" })
    if (!rootRes.ok) {
      return { ok: false, message: `Backend returned ${rootRes.status}` }
    }
    const rootData = await rootRes.json()
    console.log("[Titan API] Root OK:", rootData)

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

/**
 * Fetch the morning report — always on-demand, no caching.
 * GET /api/morning-report
 */
export async function getMorningReport(symbols?: string[]): Promise<MorningReportResponse> {
  const params = symbols?.length ? `?symbols=${symbols.join(",")}` : ""
  const url = `${API_BASE}/api/morning-report${params}`
  console.log("[Titan API] Fetching morning report:", url)
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`Failed to fetch morning report: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

/**
 * Analyze a single symbol on demand.
 * GET /api/analyze/{symbol}
 */
export async function analyzeSymbol(symbol: string): Promise<AnalyzeResponse> {
  const url = `${API_BASE}/api/analyze/${encodeURIComponent(symbol)}`
  console.log("[Titan API] Analyzing symbol:", url)
  const res = await fetch(url)
  if (!res.ok) {
    throw new Error(`Failed to analyze ${symbol}: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

/**
 * Send a chat question to the backend.
 * POST /api/chat — body: {question: string}
 */
export async function sendChat(question: string): Promise<ChatResponse> {
  const url = `${API_BASE}/api/chat`
  console.log("[Titan API] Sending chat:", url)
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  })
  if (!res.ok) {
    throw new Error(`Chat error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}
