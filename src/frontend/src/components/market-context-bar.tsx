"use client"

import { MarketContext } from "@/lib/api"
import { cn } from "@/lib/utils"

interface MarketContextBarProps {
  context: MarketContext | null
}

export function MarketContextBar({ context }: MarketContextBarProps) {
  if (!context) {
    return (
      <div className="bg-zinc-900/50 border-b border-zinc-800 px-6 py-3">
        <div className="flex items-center gap-8 max-w-[1800px] mx-auto">
          <div className="animate-pulse flex gap-8">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="h-4 w-24 bg-zinc-800 rounded" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  const moodColor = {
    greed: 'text-green-400',
    fear: 'text-red-400',
    neutral: 'text-yellow-400',
  }

  const fundingLabel = {
    long_heavy: { text: 'Longs Crowded', color: 'text-red-400' },
    short_heavy: { text: 'Shorts Crowded', color: 'text-green-400' },
    neutral: { text: 'Balanced', color: 'text-zinc-400' },
  }

  const formatMoney = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`
    return `$${value.toLocaleString()}`
  }

  return (
    <div className="bg-zinc-900/50 border-b border-zinc-800 px-6 py-2">
      <div className="flex items-center justify-between max-w-[1800px] mx-auto">
        <div className="flex items-center gap-6 text-sm">
          {/* BTC Price */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">BTC</span>
            <span className="font-mono font-medium">${context.btc_price.toLocaleString()}</span>
            <span className={cn(
              "font-mono text-xs",
              context.btc_24h_change >= 0 ? "text-green-400" : "text-red-400"
            )}>
              {context.btc_24h_change >= 0 ? '+' : ''}{context.btc_24h_change}%
            </span>
          </div>

          <div className="h-4 w-px bg-zinc-700" />

          {/* BTC Dominance */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">DOM</span>
            <span className="font-mono">{context.btc_dominance}%</span>
          </div>

          <div className="h-4 w-px bg-zinc-700" />

          {/* Total Market Cap */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">MCap</span>
            <span className="font-mono">{formatMoney(context.total_market_cap)}</span>
          </div>

          <div className="h-4 w-px bg-zinc-700" />

          {/* Funding */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">Funding</span>
            <span className={cn("font-medium", fundingLabel[context.funding_skew].color)}>
              {fundingLabel[context.funding_skew].text}
            </span>
          </div>
        </div>

        {/* Mood Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-zinc-500 text-sm">Market Mood</span>
            <div className="flex items-center gap-2">
              <div className="w-24 h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all",
                    context.mood_score > 60 ? "bg-green-500" :
                    context.mood_score < 40 ? "bg-red-500" : "bg-yellow-500"
                  )}
                  style={{ width: `${context.mood_score}%` }}
                />
              </div>
              <span className={cn("font-medium text-sm capitalize", moodColor[context.overall_mood])}>
                {context.overall_mood} ({context.mood_score})
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
