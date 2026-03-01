"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { AnalyzeResponse } from "@/lib/types"

interface SignalDetailPanelProps {
  signal: AnalyzeResponse
}

function formatPrice(value: number | null): string {
  if (value === null) return "—"
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })
}

function formatRR(value: number | null): string {
  if (value === null) return "—"
  return value.toFixed(2)
}

export function SignalDetailPanel({ signal }: SignalDetailPanelProps) {
  const {
    symbol,
    direction,
    confidence,
    suggested_action,
    entry_zone,
    stop_loss,
    tp1,
    tp2,
    risk_reward,
    wyckoff_phase,
    three_laws_check,
    reasoning,
    ta_summary,
  } = signal

  // Direction badge classes
  const directionClass =
    direction === "BULLISH"
      ? "bg-green-500/20 text-green-400 border border-green-500/30"
      : direction === "BEARISH"
      ? "bg-red-500/20 text-red-400 border border-red-500/30"
      : "bg-zinc-700/30 text-zinc-400 border border-zinc-600/30"

  const directionLabel = direction ?? "NO SIGNAL"

  // Suggested action badge classes
  const actionClass =
    suggested_action === "Long Spot" || suggested_action === "Long Hyperliquid"
      ? "bg-green-500/20 text-green-400 border border-green-500/30"
      : suggested_action === "Short Hyperliquid"
      ? "bg-red-500/20 text-red-400 border border-red-500/30"
      : "bg-zinc-700/30 text-zinc-400 border border-zinc-600/30"

  // Confidence bar colour
  const confidenceBarClass =
    confidence >= 70
      ? "bg-green-500"
      : confidence >= 50
      ? "bg-yellow-500"
      : "bg-red-500"

  // R:R colour
  const rrClass =
    risk_reward === null
      ? "text-zinc-400"
      : risk_reward >= 3
      ? "text-green-400"
      : risk_reward >= 2
      ? "text-yellow-400"
      : "text-red-400"

  // Three Laws badge helper
  function lawBadgeClass(value: string): string {
    if (value === "pass") return "border-green-500/40 text-green-400 bg-green-500/10"
    if (value === "fail") return "border-red-500/40 text-red-400 bg-red-500/10"
    // check_current_positions
    return "border-yellow-500/40 text-yellow-400 bg-yellow-500/10"
  }

  function overallBadgeClass(value: string): string {
    if (value === "approved") return "border-green-500/40 text-green-400 bg-green-500/10"
    if (value === "rejected") return "border-red-500/40 text-red-400 bg-red-500/10"
    return "border-yellow-500/40 text-yellow-400 bg-yellow-500/10"
  }

  return (
    <div className="space-y-4 w-full">

      {/* Section 1 — Header card */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardContent className="p-4">
          {/* Symbol + badges row */}
          <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
            <h2 className="text-2xl font-bold text-zinc-50">{symbol}</h2>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-semibold uppercase",
                  directionClass
                )}
              >
                {directionLabel}
              </span>
              <span
                className={cn(
                  "inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-semibold",
                  actionClass
                )}
              >
                {suggested_action}
              </span>
            </div>
          </div>

          {/* Confidence bar */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-zinc-400 uppercase tracking-wide">Confluence Score</span>
              <span className="text-sm font-mono font-bold text-zinc-200">{confidence}%</span>
            </div>
            <div className="w-full h-3 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all", confidenceBarClass)}
                style={{ width: `${confidence}%` }}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section 2 — Trade parameters */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardContent className="p-4">
          <div className="grid grid-cols-2 gap-4">

            {/* Entry Zone */}
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Entry Zone</p>
              <p className="font-mono text-sm text-zinc-200">
                {formatPrice(entry_zone?.low ?? null)} – {formatPrice(entry_zone?.ideal ?? null)} – {formatPrice(entry_zone?.high ?? null)}
              </p>
            </div>

            {/* Wyckoff Phase */}
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Wyckoff</p>
              <p className="text-sm text-zinc-400 italic">
                {wyckoff_phase ?? "—"}
              </p>
            </div>

            {/* Stop Loss */}
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Stop Loss</p>
              <p className="font-mono text-sm text-red-400">{formatPrice(stop_loss)}</p>
            </div>

            {/* R:R */}
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">R:R Ratio</p>
              <p className={cn("font-mono text-sm font-semibold", rrClass)}>{formatRR(risk_reward)}</p>
            </div>

            {/* TP1 */}
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">TP1</p>
              <p className="font-mono text-sm text-green-400">{formatPrice(tp1)}</p>
            </div>

            {/* TP2 */}
            <div>
              <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">TP2</p>
              <p className="font-mono text-sm text-green-400">{formatPrice(tp2)}</p>
            </div>

          </div>
        </CardContent>
      </Card>

      {/* Section 3 — Three Laws Check */}
      {three_laws_check !== null && (
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-xs text-zinc-500 uppercase tracking-wide mb-3">Three Laws Check</p>
            <div className="flex flex-wrap gap-2">
              <Badge
                variant="outline"
                className={cn("text-xs font-medium", lawBadgeClass(three_laws_check.law_1_risk))}
              >
                Law 1 (2% Risk): {three_laws_check.law_1_risk}
              </Badge>
              <Badge
                variant="outline"
                className={cn("text-xs font-medium", lawBadgeClass(three_laws_check.law_2_rr))}
              >
                Law 2 (R:R): {three_laws_check.law_2_rr}
              </Badge>
              <Badge
                variant="outline"
                className={cn(
                  "text-xs font-medium",
                  lawBadgeClass(three_laws_check.law_3_positions)
                )}
              >
                Law 3 (Positions):{" "}
                {three_laws_check.law_3_positions === "check_current_positions"
                  ? "check positions"
                  : three_laws_check.law_3_positions}
              </Badge>
              <Badge
                variant="outline"
                className={cn("text-xs font-semibold", overallBadgeClass(three_laws_check.overall))}
              >
                Overall: {three_laws_check.overall}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Section 4 — Reasoning */}
      {reasoning !== null && (
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-sm text-zinc-400 mb-2">Mentor Reasoning</p>
            <div className="max-h-48 overflow-y-auto bg-zinc-950/50 rounded p-3 text-sm text-zinc-200 whitespace-pre-wrap leading-relaxed">
              {reasoning}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Section 5 — TA Summary */}
      {ta_summary !== null && (
        <Card className="bg-zinc-900 border-zinc-800">
          <CardContent className="p-4">
            <p className="text-sm text-zinc-400 mb-1">TA Summary</p>
            <p className="text-sm text-zinc-300 italic">{ta_summary}</p>
          </CardContent>
        </Card>
      )}

    </div>
  )
}
