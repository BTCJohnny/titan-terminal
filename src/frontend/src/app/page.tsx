"use client"

import { useEffect, useState, useCallback } from "react"
import { RichSignalCard } from "@/components/rich-signal-card"
import { MarketContextBar } from "@/components/market-context-bar"
import { WhaleAlertPanel } from "@/components/whale-alert-panel"
import { Chat } from "@/components/chat"
import { StatsCard } from "@/components/stats-card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { getMorningReport, getStats, checkHealth, MorningReport, Stats } from "@/lib/api"
import { cn } from "@/lib/utils"

export default function Home() {
  const [report, setReport] = useState<MorningReport | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [backendStatus, setBackendStatus] = useState<{ ok: boolean; message: string } | null>(null)

  const fetchData = useCallback(async (refresh: boolean = false) => {
    setIsLoading(true)
    setError(null)

    const health = await checkHealth()
    setBackendStatus(health)

    if (!health.ok) {
      setError(health.message)
      setIsLoading(false)
      return
    }

    try {
      const [reportData, statsData] = await Promise.all([
        getMorningReport(refresh),
        getStats(),
      ])
      setReport(reportData)
      setStats(statsData)
      setLastRefresh(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()

    // Keyboard shortcuts
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'r' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        fetchData(true)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [fetchData])

  const handleDeepDive = (symbol: string) => {
    console.log(`Deep dive: ${symbol}`)
    alert(`Deep dive for ${symbol} - Full report coming in Phase 1`)
  }

  // Filter signals to only show unusual activity
  const actionableSignals = report?.signals.filter(s =>
    s.suggested_action !== 'Avoid' ||
    (s.unusual_activity_score && s.unusual_activity_score > 60)
  ) || []

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      {/* Header */}
      <header className="border-b border-zinc-800 px-6 py-3">
        <div className="flex items-center justify-between max-w-[1800px] mx-auto">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-xl font-bold tracking-tight">Titan Terminal</h1>
              <p className="text-xs text-zinc-500">Smart Money Intelligence</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {backendStatus && (
              <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  backendStatus.ok
                    ? "border-green-500/30 text-green-400"
                    : "border-red-500/30 text-red-400"
                )}
              >
                {backendStatus.ok ? "● Connected" : "● Offline"}
              </Badge>
            )}
            {lastRefresh && (
              <span className="text-xs text-zinc-600">
                {lastRefresh.toLocaleTimeString()}
              </span>
            )}
            <Button
              onClick={() => fetchData(true)}
              disabled={isLoading}
              size="sm"
              variant="outline"
              className="text-xs"
            >
              {isLoading ? "Loading..." : "Refresh (⌘R)"}
            </Button>
          </div>
        </div>
      </header>

      {/* Market Context Bar */}
      <MarketContextBar context={report?.market_context ?? null} />

      {/* Main Content */}
      <main className="flex max-w-[1800px] mx-auto">
        {/* Main Panel */}
        <div className="flex-1 p-4 space-y-4">
          {/* Error State */}
          {error && (
            <div className="p-4 bg-red-950/50 border border-red-800/50 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Loading State */}
          {isLoading && !report && (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="animate-spin w-8 h-8 border-2 border-zinc-700 border-t-zinc-300 rounded-full mx-auto mb-4" />
                <p className="text-zinc-400 text-sm">Analyzing markets...</p>
                <p className="text-xs text-zinc-600 mt-1">Running smart money detection</p>
              </div>
            </div>
          )}

          {/* Whale Alerts */}
          {report?.whale_alerts && report.whale_alerts.length > 0 && (
            <WhaleAlertPanel alerts={report.whale_alerts} />
          )}

          {/* Smart Money Leaderboard */}
          {actionableSignals.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-zinc-300">
                  Smart Money Leaderboard
                  <span className="text-zinc-600 font-normal ml-2">
                    {actionableSignals.length} tokens with unusual activity
                  </span>
                </h2>
                {report && (
                  <Badge variant="outline" className="text-xs text-zinc-500">
                    Batch: {report.batch_id}
                  </Badge>
                )}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-3">
                {actionableSignals.map((signal, index) => (
                  <RichSignalCard
                    key={signal.symbol}
                    signal={signal}
                    rank={index + 1}
                    onDeepDive={handleDeepDive}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {report && actionableSignals.length === 0 && !isLoading && (
            <div className="text-center py-16 bg-zinc-900/30 rounded-lg border border-zinc-800">
              <div className="text-4xl mb-4">🔍</div>
              <p className="text-zinc-400">No unusual activity detected</p>
              <p className="text-xs text-zinc-600 mt-2">
                Markets are quiet. Check back later or refresh for new data.
              </p>
              <Button
                onClick={() => fetchData(true)}
                size="sm"
                variant="outline"
                className="mt-4"
              >
                Scan Again
              </Button>
            </div>
          )}

          {/* Market Summary */}
          {report?.market_summary && (
            <div className="text-xs text-zinc-500 text-center py-2">
              {report.market_summary}
            </div>
          )}
        </div>

        {/* Right Sidebar */}
        <aside className="w-80 border-l border-zinc-800 flex flex-col h-[calc(100vh-110px)]">
          {/* Self-Learning Stats */}
          <div className="p-4 border-b border-zinc-800">
            <StatsCard stats={stats} />
          </div>

          {/* Chat */}
          <div className="flex-1 overflow-hidden">
            <Chat />
          </div>
        </aside>
      </main>
    </div>
  )
}
