"use client"

import { useState, useRef, useEffect } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { sendChat } from "@/lib/api"
import { cn } from "@/lib/utils"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: string
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput("")
    setIsLoading(true)

    try {
      const response = await sendChat(input)
      const assistantMessage: Message = {
        role: "assistant",
        content: response.response,
        timestamp: response.timestamp,
      }
      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Unknown error"}`,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="p-4 border-b border-zinc-800">
        <h2 className="font-semibold">Chat</h2>
        <p className="text-xs text-zinc-400">Ask about any token or the market</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-zinc-500 text-sm">
            <p>Try:</p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>&quot;analyze SOL&quot;</li>
              <li>&quot;how&apos;s the market?&quot;</li>
              <li>&quot;mark BTC as win +12%&quot;</li>
            </ul>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={cn(
              "p-3 rounded-lg text-sm",
              message.role === "user"
                ? "bg-zinc-800 ml-8"
                : "bg-zinc-900 mr-8 border border-zinc-800"
            )}
          >
            <div className="text-xs text-zinc-500 mb-1">
              {message.role === "user" ? "You" : "Titan"}
            </div>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        ))}

        {isLoading && (
          <div className="bg-zinc-900 p-3 rounded-lg mr-8 border border-zinc-800 text-sm">
            <div className="text-xs text-zinc-500 mb-1">Titan</div>
            <div className="flex items-center gap-1">
              <span className="animate-pulse">Thinking</span>
              <span className="animate-bounce">.</span>
              <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>.</span>
              <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>.</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-zinc-800">
        <div className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything..."
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </Button>
        </div>
      </form>
    </div>
  )
}
