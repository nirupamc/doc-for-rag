/*
 * UploadPanel — Restrained PDF upload experience.
 * 
 * Features:
 *   - Drag-and-drop area
 *   - File picker button
 *   - PDF-only validation
 *   - Size limit messaging (25 MB)
 *   - File info display after selection
 *   - Parse action (does not auto-upload)
 */

"use client"

import { useState } from "react"
import { parseDocument } from "@/lib/api"
import { LoadingState } from "@/ui/loading-state"
import { ErrorState } from "@/ui/error-state"
import { StatusBadge } from "@/ui/status-badge"

export interface UploadPanelProps {
  onParseSuccess: (response: {
    document: { page_count: number; pages: any[] }
    report: { status: string }
  }) => void
  onReset: () => void
}

export function UploadPanel({ onParseSuccess, onReset }: UploadPanelProps) {
  const [file, setFile] = useState<File | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)
  const [fileSize, setFileSize] = useState<string | null>(null)
  const [isParsing, setIsParsing] = useState(false)
  const [parseError, setParseError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (!selected) return

    // PDF-only check
    if (!selected.name.toLowerCase().endsWith(".pdf")) {
      setParseError("Unsupported file type: only PDF is accepted.")
      setFile(null)
      return
    }

    // Size check (25 MB development limit)
    const maxBytes = 25 * 1024 * 1024
    if (selected.size > maxBytes) {
      setParseError(
        `File too large: ${selected.size} bytes. Maximum ${maxBytes / (1024 * 1024)} MB.`
      )
      setFile(null)
      return
    }

    setFile(selected)
    setFileName(selected.name)
    setFileSize(`${selected.size / 1024} KB`)
    setParseError(null)
  }

  const handleParse = async () => {
    if (!file) return

    setIsParsing(true)
    setParseError(null)

    const formData = new FormData()
    formData.append("file", file, file.name)

    try {
      const response = await parseDocument(formData)
      onParseSuccess({
        document: response.document,
        report: response.report,
      })
    } catch (err: any) {
      setParseError(err.message || "Unexpected parsing failure")
    } finally {
      setIsParsing(false)
    }
  }

  return (
    <section className="max-w-2xl mx-auto">
      <div className="border rounded-lg p-6 bg-card border-border">
        <h2 className="text-xl font-semibold mb-4">RagParser</h2>

        {/* Drag-and-drop area */}
        <div
          className="border-2 dashed border-border rounded-lg p-8 text-center cursor-pointer transition-colors hover:border-primary"
          onClick={() => (document.getElementById("file-input") as HTMLInputElement).click()}
          onDragOver={(e) => {
            e.preventDefault()
            ;(e.currentTarget as HTMLElement).style.borderColor = "var(--primary)"
          }}
          onDragLeave={(e) => {
            e.preventDefault()
            ;(e.currentTarget as HTMLElement).style.borderColor = "var(--border)"
          }}
        >
          <p className="text-sm text-muted-foreground mb-2">
            Drag a PDF here or {" "}
            <button type="button" className="underline underline-offset-2">
              browse
            </button>
          </p>
          <p className="text-xs text-muted-foreground">
            PDF only · Max {25} MB
          </p>
        </div>

        {/* File input (hidden) */}
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          onChange={(e) => handleChange(e)}
          style={{ display: "none" }}
        />

        {/* File info + parse button */}
        {file && (
          <div className="mt-4 flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <StatusBadge status="good" size="sm" />
              <span>
                {fileName || "selected file"} ({fileSize || "?"})
              </span>
            </div>

            <button
              disabled={isParsing}
              onClick={handleParse}
              className="btn-primary"
              aria-live="polite">
                {isParsing ? (
                  <LoadingState size="sm" className="mr-2" />
                  Analyzing document...
                ) : "Parse PDF"}
              </button>

              {/* Clear button */}
              <button
                onClick={() => {
                  setFile(null)
                  setFileName(null)
                  setFileSize(null)
                  setParseError(null)
                }
                className="text-sm text-muted-foreground"
                aria-label="Clear selection">
                Remove
              </button>
            </div>

            {/* Error state */}
            {parseError && (
              <ErrorState message={parseError} onRetry={() => {}} />
            )}
          </div>
        )}

        {/* Empty state */}
        {!file && !isParsing && (
          <p className="text-sm text-muted-foreground mb-4">
            Select a PDF to begin inspection.
          </p>
        )}
      </div>
    </section>
  )
}