"use client"

import { WhaleAlert } from "@/lib/api"
import { cn } from "@/lib/utils"

interface WhaleAlertPanelProps {
  alerts: WhaleAlert[] | null
}

const alertIcons = {
  whale_buy: '🐋',
  whale_sell: '🔴',
  fresh_wallet: '✨',
  smart_accumulation: '🧠',
}

const alertColors = {
  whale_buy: 'border-green-500/30 bg-green-500/5',
  whale_sell: 'border-red-500/30 bg-red-500/5',
  fresh_wallet: 'border-blue-500/30 bg-blue-500/5',
  smart_accumulation: 'border-purple-500/30 bg-purple-500/5',
}

const severityDot = {
  high: 'bg-red-500',
  medium: 'bg-yellow-500',
  low: 'bg-zinc-500',
}

export function WhaleAlertPanel({ alerts }: WhaleAlertPanelProps) {
  if (!alerts || alerts.length === 0) {
    return null
  }

  const formatAmount = (value: number) => {
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`
    if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`
    return `$${value.toLocaleString()}`
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm flex items-center gap-2">
          <span className="text-lg">🚨</span>
          Whale Alerts
        </h3>
        <span className="text-xs text-zinc-500">{alerts.length} active</span>
      </div>

      <div className="space-y-2">
        {alerts.map((alert, index) => (
          <div
            key={index}
            className={cn(
              "flex items-center gap-3 p-2 rounded border transition-colors hover:bg-zinc-800/50",
              alertColors[alert.alert_type]
            )}
          >
            {/* Severity indicator */}
            <div className={cn("w-2 h-2 rounded-full flex-shrink-0", severityDot[alert.severity])} />

            {/* Icon */}
            <span className="text-lg flex-shrink-0">{alertIcons[alert.alert_type]}</span>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono font-medium text-sm">{alert.symbol}</span>
                <span className="text-xs text-zinc-400 truncate">{alert.description}</span>
              </div>
            </div>

            {/* Amount & Time */}
            <div className="text-right flex-shrink-0">
              <div className="font-mono text-sm font-medium">
                {formatAmount(alert.amount_usd)}
              </div>
              <div className="text-xs text-zinc-500">{formatTime(alert.timestamp)}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
