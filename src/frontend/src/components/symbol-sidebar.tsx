"use client"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { AnalyzeResponse, Direction } from "@/lib/types"

interface SymbolSidebarProps {
  signals: AnalyzeResponse[]
  selectedSymbol: string | null
  isLoading: boolean
  onSelectSymbol: (symbol: string) => void
  onRunReport: () => void
}

function directionStyle(direction: Direction | null | undefined) {
  switch (direction) {
    case "BULLISH":
      return "bg-green-500/20 text-green-400 border-green-500/30"
    case "BEARISH":
      return "bg-red-500/20 text-red-400 border-red-500/30"
    default:
      return "bg-zinc-700/30 text-zinc-400 border-zinc-600/30"
  }
}

function directionLabel(direction: Direction | null | undefined): string {
  return direction ?? "NO SIGNAL"
}

function confidenceBarColor(confidence: number): string {
  if (confidence >= 70) return "bg-green-500"
  if (confidence >= 50) return "bg-yellow-500"
  return "bg-red-500"
}

export function SymbolSidebar({
  signals,
  selectedSymbol,
  isLoading,
  onSelectSymbol,
  onRunReport,
}: SymbolSidebarProps) {
  const sorted = [...signals].sort((a, b) => b.confidence - a.confidence)

  return (
    <div className="flex flex-col h-full">
      {/* Run Report button */}
      <div className="p-3 border-b border-zinc-800">
        <Button
          onClick={onRunReport}
          disabled={isLoading}
          size="sm"
          className="w-full text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700"
          variant="outline"
        >
          {isLoading ? "Running..." : "Run Morning Report"}
        </Button>
      </div>

      {/* Symbol list */}
      <div className="flex-1 overflow-y-auto">
        {/* Loading skeleton */}
        {isLoading && signals.length === 0 && (
          <div className="p-3 space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="animate-pulse space-y-2 p-2">
                <div className="h-4 bg-zinc-800 rounded w-2/3" />
                <div className="h-3 bg-zinc-800 rounded w-1/2" />
                <div className="h-1.5 bg-zinc-800 rounded w-full" />
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && signals.length === 0 && (
          <div className="p-4 text-center text-zinc-500 text-xs mt-8">
            No report data. Click Run Morning Report.
          </div>
        )}

        {/* Signal rows */}
        {sorted.map((signal) => {
          const isSelected = signal.symbol === selectedSymbol
          return (
            <button
              key={signal.symbol}
              onClick={() => onSelectSymbol(signal.symbol)}
              className={cn(
                "w-full text-left px-3 py-2.5 border-b border-zinc-800/50 transition-colors",
                isSelected
                  ? "bg-zinc-800"
                  : "hover:bg-zinc-800/50"
              )}
            >
              {/* Row header: symbol + direction badge */}
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-sm text-zinc-100">
                  {signal.symbol}
                </span>
                <Badge
                  variant="outline"
                  className={cn("text-xs border", directionStyle(signal.direction))}
                >
                  {directionLabel(signal.direction)}
                </Badge>
              </div>

              {/* Confidence bar */}
              <div className="flex items-center gap-2 mb-1">
                <div className="flex-1 h-1.5 bg-zinc-700 rounded-full overflow-hidden">
                  <div
                    className={cn("h-full rounded-full", confidenceBarColor(signal.confidence))}
                    style={{ width: `${signal.confidence}%` }}
                  />
                </div>
                <span className="font-mono text-sm text-zinc-300 tabular-nums w-10 text-right">
                  {signal.confidence}%
                </span>
              </div>

              {/* Suggested action */}
              <div className="text-xs text-zinc-400">
                {signal.suggested_action}
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
