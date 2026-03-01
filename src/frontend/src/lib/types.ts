/**
 * Titan Terminal — shared TypeScript types
 * Matches Phase 22 FastAPI backend response models exactly.
 */

export interface EntryZone {
  low: number | null
  high: number | null
  ideal: number | null
}

export interface ThreeLawsCheck {
  law_1_risk: "pass" | "fail"
  law_2_rr: "pass" | "fail"
  law_3_positions: "pass" | "fail"
  overall: "approved" | "rejected" | "caution"
}

export type Direction = "BULLISH" | "BEARISH" | "NO SIGNAL"
export type SuggestedAction = "Long Spot" | "Long Hyperliquid" | "Short Hyperliquid" | "Avoid"

export interface AnalyzeResponse {
  symbol: string
  signal_id: number | null
  timestamp: string
  direction: Direction | null
  confidence: number          // 0-100
  suggested_action: SuggestedAction
  accumulation_score: number
  distribution_score: number
  reasoning: string | null
  entry_zone: EntryZone | null
  stop_loss: number | null
  tp1: number | null
  tp2: number | null
  risk_reward: number | null
  three_laws_check: ThreeLawsCheck | null
  wyckoff_phase: string | null
  nansen_summary: string[] | null
  ta_summary: string | null
}

export interface MorningReportResponse {
  timestamp: string
  count: number
  signals: AnalyzeResponse[]
}

export interface ChatRequest {
  question: string
}

export interface ChatResponse {
  response: string
  timestamp: string
}
