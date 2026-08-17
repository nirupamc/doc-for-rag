/* StatusBadge — Small inline status indicator.
 * 
 * Props:
 *   status: "good" | "review" | "poor"
 *   size: "sm" | "md" (default)
 */

"use client"

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
      className: "border-[var(--border)] bg-[var(--good-bg)] text-[var(--text-strong)]",
      title: "GOOD — No significant issues detected",
    },
    review: {
      className: "border-[var(--amber)] bg-[var(--warning-bg)] text-[var(--amber)]",
      title: "REVIEW — Document requires attention",
    },
    poor: {
      className: "border-[var(--red)] bg-[var(--error-bg)] text-[var(--red)]",
      title: "POOR — Significant extraction problems",
    },
  }

  const label = labels[status]
  const sizeClasses = size === "sm"
    ? "h-5 text-[9px] px-2"
    : "h-7 text-[10px] px-3"

  if (asChild) {
    return <span className={label.className} title={label.title} />
  }

  return (
    <span
      className={`${sizeClasses} ${label.className} font-interface inline-flex items-center justify-center border font-bold tracking-[.1em]`}
      title={label.title}
    >
      {status.toUpperCase()}
    </span>
  )
}
