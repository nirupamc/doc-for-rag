/* StatusBadge — Small inline status indicator.
 * 
 * Props:
 *   status: "good" | "review" | "poor"
 *   size: "sm" | "md" (default)
 */

"use client"

import { ReactNode } from "react"

export interface StatusBadgeProps {
  status: "good" | "review" | "poor"
  size?: "sm" | "md"
  asChild?: boolean
}

export function StatusBadge({
  status,
  size = "md",
  asChild = false,
}: StatusBadgeProps) {
  const labels: Record<string, { className: string; title: string }> = {
    good: {
      className: "bg-green-100 text-green-800",
      title: "GOOD — No significant issues detected",
    },
    review: {
      className: "bg-yellow-100 text-yellow-800",
      title: "REVIEW — Document requires attention",
    },
    poor: {
      className: "bg-red-100 text-red-800",
      title: "POOR — Significant extraction problems",
    },
  }

  const label = labels[status]
  const sizeClasses = size === "sm"
    ? "h-6 w-6 text-xs px-2 rounded"
    : "h-8 w-8 text-sm px-3 rounded"

  if (asChild) {
    return <span className={label.className} title={label.title} />
  }

  return (
    <span
      className={`${sizeClasses} inline-flex items-center rounded`}
      title={label.title}
    >
      {status.toUpperCase()}
    </span>
  )
}