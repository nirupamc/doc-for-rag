/* JsonViewer — Simple formatted JSON viewer with copy functionality.

 * Props:
 *   title: heading title
 *   data: JSON string or object
 *   copyLabel: button label for copy action
 */

"use client"

import { useState } from "react"

export interface JsonViewerProps {
  title: string
  data: unknown
  copyLabel?: string
}

export function JsonViewer({ title, data, copyLabel = "Copy JSON" }: JsonViewerProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(parsed)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea")
      textarea.value = parsed
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand("copy")
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const parsed = typeof data === "string" ? data : JSON.stringify(data, null, 2)

  return (
    <section>
      <div className="mb-2 flex items-center justify-between border-b border-[var(--phosphor-dim)] pb-2">
        <div><p className="tech-label">Data dump // read only</p><h4 className="font-interface mt-1 text-xs font-semibold uppercase tracking-[.1em]">{title}</h4></div>
        <button
          onClick={handleCopy}
          className="tech-button"
          title="Copy JSON"
          aria-label={copyLabel}>
          {copied ? "Copied!" : copyLabel}
        </button>
      </div>

      <div className="max-h-[360px] overflow-auto border border-[var(--border-subtle)] bg-[var(--surface-deep)] p-3">
        <pre className="whitespace-pre-wrap font-terminal text-base leading-tight text-[var(--phosphor)]">{parsed}</pre>
      </div>

      {copied && (
        <p className="tech-label mt-2 text-[var(--phosphor-bright)]">Buffer::copied</p>
      )}
    </section>
  )
}
