"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Signal } from "@/lib/api"
import { cn } from "@/lib/utils"

interface SignalCardProps {
  signal: Signal
  onDeepDive?: (symbol: string) => void
  rank: number
}

export function SignalCard({ signal, onDeepDive, rank }: SignalCardProps) {
  const isAccumulation = (signal.accumulation_score ?? 0) > (signal.distribution_score ?? 0)
  const score = isAccumulation ? signal.accumulation_score : signal.distribution_score
  const scoreType = isAccumulation ? "Accumulation" : "Distribution"

  const actionColor = {
    "Long Spot": "success",
    "Long Hyperliquid": "success",
    "Short Hyperliquid": "destructive",
    "Avoid": "secondary",
  } as const

  const mentorBadge = {
    approve: "success",
    caution: "warning",
    reject: "destructive",
  } as const

  return (
    <Card className="relative overflow-hidden">
      {/* Rank indicator */}
      <div className="absolute top-0 left-0 w-8 h-8 bg-zinc-800 flex items-center justify-center text-sm font-bold">
        #{rank}
      </div>

      <CardHeader className="pl-12">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">{signal.symbol}</CardTitle>
          <Badge variant={actionColor[signal.suggested_action as keyof typeof actionColor] || "secondary"}>
            {signal.suggested_action}
          </Badge>
        </div>
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          <span>{signal.wyckoff_phase || "—"}</span>
          {signal.mentor_verdict && (
            <Badge variant={mentorBadge[signal.mentor_verdict as keyof typeof mentorBadge] || "secondary"} className="text-xs">
              Mentor: {signal.mentor_verdict}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Score Display */}
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="text-xs text-zinc-400 mb-1">{scoreType} Score</div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full",
                    isAccumulation ? "bg-green-500" : "bg-red-500"
                  )}
                  style={{ width: `${score ?? 0}%` }}
                />
              </div>
              <span className="text-sm font-mono">{score ?? "—"}</span>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-zinc-400">Confidence</div>
            <div className="text-lg font-bold">{signal.confidence}%</div>
          </div>
        </div>

        {/* Trading Levels */}
        {signal.entry_zone && (
          <div className="grid grid-cols-4 gap-2 text-sm">
            <div>
              <div className="text-xs text-zinc-400">Entry</div>
              <div className="font-mono">
                {signal.entry_zone.low?.toFixed(2)} - {signal.entry_zone.high?.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-xs text-zinc-400">Stop</div>
              <div className="font-mono text-red-400">{signal.stop_loss?.toFixed(2) ?? "—"}</div>
            </div>
            <div>
              <div className="text-xs text-zinc-400">TP1</div>
              <div className="font-mono text-green-400">{signal.tp1?.toFixed(2) ?? "—"}</div>
            </div>
            <div>
              <div className="text-xs text-zinc-400">TP2</div>
              <div className="font-mono text-green-400">{signal.tp2?.toFixed(2) ?? "—"}</div>
            </div>
          </div>
        )}

        {/* Risk/Reward */}
        {signal.risk_reward && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-zinc-400">R:R Ratio</span>
            <span className={cn(
              "font-mono",
              signal.risk_reward >= 2 ? "text-green-400" : "text-yellow-400"
            )}>
              {signal.risk_reward.toFixed(2)}:1
            </span>
          </div>
        )}

        {/* Learning Context */}
        {signal.learning_context && (
          <div className="text-xs text-zinc-500 italic">
            {signal.learning_context}
          </div>
        )}

        {/* Mentor Concerns */}
        {signal.mentor_concerns && signal.mentor_concerns.length > 0 && (
          <div className="text-xs text-yellow-500">
            <span className="font-semibold">Watch:</span> {signal.mentor_concerns.join(", ")}
          </div>
        )}

        {/* Deep Dive Button */}
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => onDeepDive?.(signal.symbol)}
        >
          Deep Dive
        </Button>
      </CardContent>
    </Card>
  )
}
