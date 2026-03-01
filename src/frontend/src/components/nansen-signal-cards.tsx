"use client"

import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface NansenSignalCardsProps {
  nansenSummary: string[] | null
}

const SIGNAL_LABELS = [
  "Smart Money Flows",
  "Exchange Flows",
  "On-Chain Holdings",
  "Buy/Sell Pressure",
  "Top PnL Wallets",
]

type NansenDirection = "bullish" | "bearish" | "neutral"

function detectDirection(text: string): NansenDirection {
  const lower = text.toLowerCase()
  if (
    lower.includes("bullish") ||
    lower.includes("accumulating") ||
    lower.includes("outflow") ||
    lower.includes("positive")
  ) {
    return "bullish"
  }
  if (
    lower.includes("bearish") ||
    lower.includes("distributing") ||
    lower.includes("inflow") ||
    lower.includes("negative")
  ) {
    return "bearish"
  }
  return "neutral"
}

function directionBadgeClass(direction: NansenDirection): string {
  if (direction === "bullish") return "text-green-400 bg-green-500/10 border border-green-500/30"
  if (direction === "bearish") return "text-red-400 bg-red-500/10 border border-red-500/30"
  return "text-zinc-400 bg-zinc-700/20 border border-zinc-600/30"
}

export function NansenSignalCards({ nansenSummary }: NansenSignalCardsProps) {
  if (!nansenSummary || nansenSummary.length === 0) return null

  const entries = nansenSummary.slice(0, 5)

  return (
    <div>
      <p className="text-sm font-semibold text-zinc-400 mb-3 uppercase tracking-wide">
        On-Chain Intelligence
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {entries.map((summary, index) => {
          const direction = detectDirection(summary)
          const label = SIGNAL_LABELS[index] ?? `Signal ${index + 1}`
          const isAnomalous = direction === "bearish"

          return (
            <Card
              key={index}
              className={cn(
                "bg-zinc-900 border-zinc-800",
                isAnomalous && "border-amber-500/50"
              )}
            >
              <CardContent className="p-4">
                {/* Title + direction badge */}
                <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
                  <p className="text-sm font-semibold text-zinc-200">{label}</p>
                  <span
                    className={cn(
                      "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold uppercase",
                      directionBadgeClass(direction)
                    )}
                  >
                    {direction}
                  </span>
                </div>
                {/* Summary text */}
                <p className="text-sm text-zinc-300">{summary}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
