"use client"

import { useState, useRef, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { sendChat } from "@/lib/api"
import type { AnalyzeResponse } from "@/lib/types"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: string
}

interface ChatPanelProps {
  selectedSignal: AnalyzeResponse | null
}

export function ChatPanel({ selectedSignal }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const result = await sendChat(userMessage.content)
      const assistantMessage: Message = {
        role: "assistant",
        content: result.response,
        timestamp: result.timestamp,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      const errorMessage: Message = {
        role: "assistant",
        content: err instanceof Error ? `Error: ${err.message}` : "Something went wrong. Please try again.",
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleOpenClaude = () => {
    const context = selectedSignal
      ? `Signal: ${selectedSignal.symbol} | Direction: ${selectedSignal.direction ?? "N/A"} | Confidence: ${selectedSignal.confidence}% | Action: ${selectedSignal.suggested_action} | Entry: ${selectedSignal.entry_zone?.low ?? "—"}-${selectedSignal.entry_zone?.high ?? "—"} | Stop: ${selectedSignal.stop_loss ?? "—"} | TP1: ${selectedSignal.tp1 ?? "—"} | TP2: ${selectedSignal.tp2 ?? "—"} | R:R: ${selectedSignal.risk_reward ?? "—"} | Reasoning: ${selectedSignal.reasoning ?? "N/A"}`
      : "No signal selected. Please run Morning Report first."
    navigator.clipboard.writeText(context).catch(() => {})
    window.open("https://claude.ai", "_blank")
  }

  return (
    <div className="h-full flex flex-col">
      {/* Panel header */}
      <div className="flex-none border-b border-zinc-800 px-4 py-3">
        <h2 className="text-sm font-semibold text-zinc-100">Titan Chat</h2>
        <p className="text-xs text-zinc-500 mt-0.5">Ask about signals</p>
      </div>

      {/* Open in Claude.ai button */}
      <div className="flex-none px-3 py-2 border-b border-zinc-800">
        <Button
          variant="outline"
          size="sm"
          className="w-full text-xs border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
          onClick={handleOpenClaude}
        >
          Open in Claude.ai
        </Button>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <p className="text-zinc-500 text-sm text-center mt-4">
            Ask about any signal or market setup
          </p>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={cn(
              "p-3 rounded-lg text-sm",
              message.role === "user"
                ? "bg-zinc-800 ml-8 text-zinc-100"
                : "bg-zinc-900 mr-8 border border-zinc-800 text-zinc-200"
            )}
          >
            {message.content}
          </div>
        ))}

        {isLoading && (
          <div className="bg-zinc-900 mr-8 border border-zinc-800 p-3 rounded-lg text-sm text-zinc-400">
            <span className="inline-flex gap-1">
              <span className="animate-pulse">.</span>
              <span className="animate-pulse [animation-delay:0.2s]">.</span>
              <span className="animate-pulse [animation-delay:0.4s]">.</span>
            </span>
            <span className="ml-1">Thinking</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <form
        onSubmit={handleSubmit}
        className="flex-none border-t border-zinc-800 p-3 flex gap-2"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything..."
          className="flex-1 bg-zinc-900 border-zinc-700 text-zinc-100 placeholder-zinc-500 text-sm"
          disabled={isLoading}
        />
        <Button
          type="submit"
          size="sm"
          disabled={isLoading || !input.trim()}
          className="bg-zinc-700 hover:bg-zinc-600 text-zinc-100 text-xs"
        >
          Send
        </Button>
      </form>
    </div>
  )
}
