"use client"

import { useEffect, useState, useCallback } from "react"
import { SignalCard } from "@/components/signal-card"
import { Chat } from "@/components/chat"
import { StatsCard } from "@/components/stats-card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { getMorningReport, getStats, checkHealth, MorningReport, Stats } from "@/lib/api"

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

    // Health check first
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
  }, [fetchData])

  const handleDeepDive = (symbol: string) => {
    // For MVP, just log. In production, this would open a modal with full report
    console.log(`Deep dive: ${symbol}`)
    alert(`Deep dive for ${symbol} - Full report coming in Phase 1`)
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      {/* Header */}
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="flex items-center justify-between max-w-[1800px] mx-auto">
          <div>
            <h1 className="text-2xl font-bold">Titan Terminal</h1>
            <p className="text-sm text-zinc-400">Multi-Agent Trading Intelligence</p>
          </div>
          <div className="flex items-center gap-4">
            {backendStatus && (
              <Badge variant={backendStatus.ok ? "default" : "destructive"}>
                {backendStatus.ok ? "Backend Connected" : "Backend Unreachable"}
              </Badge>
            )}
            {lastRefresh && (
              <span className="text-xs text-zinc-500">
                Last refresh: {lastRefresh.toLocaleTimeString()}
              </span>
            )}
            <Button
              onClick={() => fetchData(true)}
              disabled={isLoading}
              variant="outline"
            >
              {isLoading ? "Refreshing..." : "Refresh"}
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex max-w-[1800px] mx-auto">
        {/* Signals Grid */}
        <div className="flex-1 p-6">
          {/* Market Summary */}
          {report?.market_summary && (
            <div className="mb-6 p-4 bg-zinc-900 rounded-lg border border-zinc-800">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="outline">Market Overview</Badge>
                <span className="text-xs text-zinc-500">{report.timestamp}</span>
              </div>
              <p className="text-sm">{report.market_summary}</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="mb-6 p-4 bg-red-950 border border-red-800 rounded-lg">
              <p className="text-red-400">{error}</p>
              <p className="text-xs text-red-500 mt-2">
                Make sure the backend is running: uvicorn src.backend.api.main:app --reload
              </p>
            </div>
          )}

          {/* Loading State */}
          {isLoading && !report && (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="animate-spin w-8 h-8 border-2 border-zinc-700 border-t-zinc-300 rounded-full mx-auto mb-4" />
                <p className="text-zinc-400">Running morning analysis...</p>
                <p className="text-xs text-zinc-500 mt-2">This may take a moment</p>
              </div>
            </div>
          )}

          {/* Signals Grid */}
          {report && report.signals.length > 0 && (
            <>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">
                  Top Signals
                  <span className="text-sm text-zinc-400 ml-2">
                    ({report.signals.length} tokens)
                  </span>
                </h2>
                <Badge variant="secondary">Batch: {report.batch_id}</Badge>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {report.signals.map((signal, index) => (
                  <SignalCard
                    key={signal.symbol}
                    signal={signal}
                    rank={index + 1}
                    onDeepDive={handleDeepDive}
                  />
                ))}
              </div>
            </>
          )}

          {/* Empty State */}
          {report && report.signals.length === 0 && (
            <div className="text-center py-20">
              <p className="text-zinc-400">No actionable signals found.</p>
              <p className="text-xs text-zinc-500 mt-2">
                Try refreshing or check back later.
              </p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <aside className="w-96 border-l border-zinc-800 flex flex-col h-[calc(100vh-73px)]">
          {/* Stats */}
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
