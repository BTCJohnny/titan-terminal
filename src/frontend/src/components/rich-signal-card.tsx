"use client"

import { useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Signal } from "@/lib/api"
import { cn } from "@/lib/utils"

interface RichSignalCardProps {
  signal: Signal
  rank: number
  onDeepDive?: (symbol: string) => void
}

// Simple sparkline SVG component
function Sparkline({ data, positive }: { data: number[], positive: boolean }) {
  if (!data || data.length < 2) return null

  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1

  const width = 120
  const height = 32
  const padding = 2

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * (width - 2 * padding)
    const y = height - padding - ((value - min) / range) * (height - 2 * padding)
    return `${x},${y}`
  }).join(' ')

  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        fill="none"
        stroke={positive ? '#22c55e' : '#ef4444'}
        strokeWidth="1.5"
        points={points}
      />
      {/* End dot */}
      <circle
        cx={width - padding}
        cy={height - padding - ((data[data.length - 1] - min) / range) * (height - 2 * padding)}
        r="2"
        fill={positive ? '#22c55e' : '#ef4444'}
      />
    </svg>
  )
}

export function RichSignalCard({ signal, rank, onDeepDive }: RichSignalCardProps) {
  const [expanded, setExpanded] = useState(false)

  const isAccumulation = (signal.accumulation_score ?? 0) > (signal.distribution_score ?? 0)
  const accScore = signal.accumulation_score ?? 50
  const distScore = signal.distribution_score ?? 50
  const priceUp = (signal.price_24h_change ?? 0) >= 0

  const actionStyles: Record<string, string> = {
    "Long Spot": "bg-green-500/20 text-green-400 border-green-500/30",
    "Long Hyperliquid": "bg-green-500/20 text-green-400 border-green-500/30",
    "Short Hyperliquid": "bg-red-500/20 text-red-400 border-red-500/30",
    "Avoid": "bg-zinc-700/30 text-zinc-400 border-zinc-600/30",
  }

  const formatMoney = (value: number | null) => {
    if (!value) return '—'
    const absVal = Math.abs(value)
    if (absVal >= 1e6) return `${value >= 0 ? '+' : '-'}$${(absVal / 1e6).toFixed(1)}M`
    if (absVal >= 1e3) return `${value >= 0 ? '+' : '-'}$${(absVal / 1e3).toFixed(0)}K`
    return `$${value.toLocaleString()}`
  }

  const formatVolume = (value: number | null) => {
    if (!value) return '—'
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`
    if (value >= 1e6) return `$${(value / 1e6).toFixed(0)}M`
    return `$${value.toLocaleString()}`
  }

  return (
    <Card
      className={cn(
        "relative overflow-hidden transition-all cursor-pointer hover:border-zinc-600",
        isAccumulation ? "border-l-2 border-l-green-500" : "border-l-2 border-l-red-500"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Rank badge */}
      <div className="absolute top-2 left-2 w-6 h-6 rounded bg-zinc-800 flex items-center justify-center text-xs font-bold">
        {rank}
      </div>

      <CardContent className="p-4 pl-10">
        {/* Header Row */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold">{signal.symbol}</h3>
              <Badge className={cn("text-xs border", actionStyles[signal.suggested_action] || actionStyles["Avoid"])}>
                {signal.suggested_action}
              </Badge>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-zinc-500">{signal.wyckoff_phase || 'Analyzing'}</span>
              {signal.mentor_verdict && (
                <Badge variant="outline" className={cn(
                  "text-xs",
                  signal.mentor_verdict === 'approve' ? 'border-green-500/30 text-green-400' :
                  signal.mentor_verdict === 'caution' ? 'border-yellow-500/30 text-yellow-400' :
                  'border-red-500/30 text-red-400'
                )}>
                  {signal.mentor_verdict}
                </Badge>
              )}
            </div>
          </div>

          {/* Sparkline & Price */}
          <div className="text-right">
            {signal.sparkline && (
              <Sparkline data={signal.sparkline} positive={priceUp} />
            )}
            <div className={cn(
              "font-mono text-sm font-medium",
              priceUp ? "text-green-400" : "text-red-400"
            )}>
              {signal.price_24h_change !== null && (
                <>{priceUp ? '+' : ''}{signal.price_24h_change}%</>
              )}
            </div>
          </div>
        </div>

        {/* Acc/Dist Bar */}
        <div className="mb-3">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-green-400">Acc {accScore}</span>
            <span className="text-red-400">Dist {distScore}</span>
          </div>
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden flex">
            <div
              className="bg-green-500 transition-all"
              style={{ width: `${accScore}%` }}
            />
            <div
              className="bg-red-500 transition-all"
              style={{ width: `${distScore}%` }}
            />
          </div>
        </div>

        {/* Smart Money Stats Row */}
        <div className="grid grid-cols-4 gap-2 text-xs mb-3">
          <div>
            <div className="text-zinc-500">Activity</div>
            <div className={cn(
              "font-mono font-medium",
              (signal.unusual_activity_score ?? 0) > 70 ? "text-yellow-400" : "text-zinc-300"
            )}>
              {signal.unusual_activity_score ?? '—'}/100
            </div>
          </div>
          <div>
            <div className="text-zinc-500">Smart Flow</div>
            <div className={cn(
              "font-mono font-medium",
              (signal.smart_flow_usd ?? 0) > 0 ? "text-green-400" : "text-red-400"
            )}>
              {formatMoney(signal.smart_flow_usd)}
            </div>
          </div>
          <div>
            <div className="text-zinc-500">Whales</div>
            <div className="font-mono font-medium">{signal.whale_count ?? '—'}</div>
          </div>
          <div>
            <div className="text-zinc-500">New Wallets</div>
            <div className="font-mono font-medium">{signal.fresh_wallets ?? '—'}</div>
          </div>
        </div>

        {/* Confidence Bar */}
        <div className="flex items-center gap-3 mb-3">
          <span className="text-xs text-zinc-500">Confidence</span>
          <div className="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className={cn(
                "h-full rounded-full",
                signal.confidence >= 70 ? "bg-green-500" :
                signal.confidence >= 50 ? "bg-yellow-500" : "bg-red-500"
              )}
              style={{ width: `${signal.confidence}%` }}
            />
          </div>
          <span className="font-mono text-sm font-bold">{signal.confidence}%</span>
        </div>

        {/* Expanded Content */}
        {expanded && (
          <div className="border-t border-zinc-800 pt-3 mt-3 space-y-3 animate-in slide-in-from-top-2">
            {/* Trading Levels */}
            {signal.entry_zone && (
              <div className="grid grid-cols-5 gap-2 text-xs">
                <div>
                  <div className="text-zinc-500">Entry</div>
                  <div className="font-mono text-blue-400">
                    {signal.entry_zone.low?.toFixed(2)}-{signal.entry_zone.high?.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-zinc-500">Stop</div>
                  <div className="font-mono text-red-400">{signal.stop_loss?.toFixed(2) ?? '—'}</div>
                </div>
                <div>
                  <div className="text-zinc-500">TP1</div>
                  <div className="font-mono text-green-400">{signal.tp1?.toFixed(2) ?? '—'}</div>
                </div>
                <div>
                  <div className="text-zinc-500">TP2</div>
                  <div className="font-mono text-green-400">{signal.tp2?.toFixed(2) ?? '—'}</div>
                </div>
                <div>
                  <div className="text-zinc-500">R:R</div>
                  <div className={cn(
                    "font-mono font-medium",
                    (signal.risk_reward ?? 0) >= 2 ? "text-green-400" : "text-yellow-400"
                  )}>
                    {signal.risk_reward?.toFixed(1) ?? '—'}:1
                  </div>
                </div>
              </div>
            )}

            {/* Narrative */}
            {signal.narrative && (
              <div className="bg-zinc-800/50 rounded p-2">
                <div className="text-xs text-zinc-400 mb-1">Why this matters</div>
                <p className="text-sm text-zinc-200">{signal.narrative}</p>
              </div>
            )}

            {/* Mentor Concerns */}
            {signal.mentor_concerns && signal.mentor_concerns.length > 0 && (
              <div className="text-xs text-yellow-500/80">
                <span className="font-semibold">Watch:</span> {signal.mentor_concerns.join(", ")}
              </div>
            )}

            {/* Volume */}
            <div className="flex items-center justify-between text-xs text-zinc-500">
              <span>24h Volume: {formatVolume(signal.volume_24h)}</span>
              {signal.learning_context && (
                <span className="italic">{signal.learning_context}</span>
              )}
            </div>

            {/* Deep Dive Button */}
            <button
              className="w-full py-2 text-xs font-medium bg-zinc-800 hover:bg-zinc-700 rounded transition-colors"
              onClick={(e) => {
                e.stopPropagation()
                onDeepDive?.(signal.symbol)
              }}
            >
              Full Analysis →
            </button>
          </div>
        )}

        {/* Click hint */}
        {!expanded && (
          <div className="text-center text-xs text-zinc-600 mt-2">
            Click to expand
          </div>
        )}
      </CardContent>
    </Card>
  )
}
