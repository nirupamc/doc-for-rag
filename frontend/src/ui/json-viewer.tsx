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
  data: string
  copyLabel?: string
}

export function JsonViewer({ title, data, copyLabel = "Copy JSON" }: JsonViewerProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(data)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea")
      textarea.value = data
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand("copy")
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const parsed = typeof data === "object" ? JSON.stringify(data, null, 2) : data

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h4 className="font-medium">{title}</h4>
        <button
          onClick={handleCopy}
          className="text-sm text-primary-600 hover:text-primary-800"
          title="Copy JSON"
          aria-label="Copy JSON">
          {copied ? "Copied!" : copyLabel}
        </button>
      </div>

      <div
        className`
          bg-muted-100 rounded rounded-border p-3 max-h-[400px] overflow-auto text-sm
        `
      >
        <pre className="whitespace-pre-wrap">{parsed}</pre>
      </div>

      {copied && (
        <p className="text-xs text-success">Copied to clipboard</p>
      )}
    </div>
  )
}