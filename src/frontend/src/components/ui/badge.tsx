import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning"
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "border-transparent bg-zinc-50 text-zinc-900",
    secondary: "border-transparent bg-zinc-800 text-zinc-50",
    destructive: "border-transparent bg-red-500 text-zinc-50",
    outline: "text-zinc-50 border-zinc-700",
    success: "border-transparent bg-green-600 text-zinc-50",
    warning: "border-transparent bg-yellow-600 text-zinc-900",
  }

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-zinc-300 focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
