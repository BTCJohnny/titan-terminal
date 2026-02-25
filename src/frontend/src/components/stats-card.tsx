"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Stats } from "@/lib/api"

interface StatsCardProps {
  stats: Stats | null
}

export function StatsCard({ stats }: StatsCardProps) {
  if (!stats) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Self-Learning Stats</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-zinc-500 text-sm">Loading...</div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Self-Learning Stats</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-zinc-400">Total Signals</div>
            <div className="text-2xl font-bold">{stats.total_signals}</div>
          </div>
          <div>
            <div className="text-xs text-zinc-400">Closed Trades</div>
            <div className="text-2xl font-bold">{stats.total_closed_trades}</div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-zinc-400">Win Rate</span>
            <span className={`text-lg font-bold ${stats.win_rate >= 50 ? "text-green-400" : "text-red-400"}`}>
              {stats.win_rate}%
            </span>
          </div>
          <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${stats.win_rate >= 50 ? "bg-green-500" : "bg-red-500"}`}
              style={{ width: `${stats.win_rate}%` }}
            />
          </div>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm text-zinc-400">Avg P&L</span>
          <span className={`text-lg font-bold ${stats.avg_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
            {stats.avg_pnl >= 0 ? "+" : ""}{stats.avg_pnl}%
          </span>
        </div>

        {stats.outcomes && Object.keys(stats.outcomes).length > 0 && (
          <div className="text-xs text-zinc-500 pt-2 border-t border-zinc-800">
            Wins: {stats.outcomes.win || 0} | Losses: {stats.outcomes.loss || 0} | Breakeven: {stats.outcomes.breakeven || 0}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
