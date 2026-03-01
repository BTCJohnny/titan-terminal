"use client"

import { useEffect, useState, useCallback } from "react"
import { Badge } from "@/components/ui/badge"
import { SymbolSidebar } from "@/components/symbol-sidebar"
import { SignalDetailPanel } from "@/components/signal-detail-panel"
import { NansenSignalCards } from "@/components/nansen-signal-cards"
import { getMorningReport, checkHealth } from "@/lib/api"
import type { AnalyzeResponse, MorningReportResponse } from "@/lib/types"
import { cn } from "@/lib/utils"

export default function Home() {
  const [report, setReport] = useState<MorningReportResponse | null>(null)
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)
  const [selectedSignal, setSelectedSignal] = useState<AnalyzeResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [backendStatus, setBackendStatus] = useState<{ ok: boolean; message: string } | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const fetchReport = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    const health = await checkHealth()
    setBackendStatus(health)

    if (!health.ok) {
      setError(`Backend unavailable: ${health.message}`)
      setIsLoading(false)
      return
    }

    try {
      const data = await getMorningReport()
      setReport(data)
      setLastRefresh(new Date())
      // Auto-select first signal (highest confidence)
      const firstSignal = data.signals.length > 0
        ? [...data.signals].sort((a, b) => b.confidence - a.confidence)[0]
        : null
      setSelectedSignal(firstSignal ?? null)
      setSelectedSymbol(firstSignal?.symbol ?? null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch morning report")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchReport()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-zinc-50 overflow-hidden">
      {/* Header — full width */}
      <header className="flex-none border-b border-zinc-800 px-5 py-2.5 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-tight">Titan Terminal</h1>
          <p className="text-xs text-zinc-500">Smart Money Intelligence</p>
        </div>
        <div className="flex items-center gap-3">
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
        </div>
      </header>

      {/* Three-column body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — symbol list */}
        <aside className="w-[280px] border-r border-zinc-800 flex flex-col overflow-hidden flex-none">
          <SymbolSidebar
            signals={report?.signals ?? []}
            selectedSymbol={selectedSymbol}
            isLoading={isLoading}
            onSelectSymbol={(symbol) => {
              setSelectedSymbol(symbol)
              const match = report?.signals.find((s) => s.symbol === symbol) ?? null
              setSelectedSignal(match)
            }}
            onRunReport={fetchReport}
          />
        </aside>

        {/* Center — signal detail */}
        <main className="flex-1 overflow-y-auto p-4 space-y-4">
          {!selectedSignal && !isLoading && (
            <div className="text-zinc-500 text-sm text-center mt-20">
              Select a symbol from the left sidebar
            </div>
          )}
          {isLoading && (
            <div className="flex items-center justify-center mt-20">
              <div className="text-center">
                <div className="animate-spin w-8 h-8 border-2 border-zinc-700 border-t-zinc-300 rounded-full mx-auto mb-4" />
                <p className="text-zinc-400 text-sm">Running morning report...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="p-4 bg-red-950/50 border border-red-800/50 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}
          {selectedSignal && !isLoading && (
            <>
              <SignalDetailPanel signal={selectedSignal} />
              <NansenSignalCards nansenSummary={selectedSignal.nansen_summary} />
            </>
          )}
        </main>

        {/* Right sidebar — chat (Plan 23-03) */}
        <aside className="w-[320px] border-l border-zinc-800 flex flex-col overflow-hidden flex-none">
          <div className="p-4 text-zinc-600 text-xs">Chat coming soon</div>
        </aside>
      </div>
    </div>
  )
}
