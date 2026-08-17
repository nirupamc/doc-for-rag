"use client"

import { useRef, useState, type ChangeEvent, type DragEvent } from "react"
import { parseDocument, type ParseResponse } from "@/lib/api"
import { StatusBadge } from "@/ui/status-badge"

type UploadState = "IDLE" | "UPLOADING" | "PROCESSING" | "SUCCESS" | "ERROR"

export interface UploadPanelProps {
  onParseSuccess: (response: ParseResponse, file: File) => void
}

const MAX_BYTES = 25 * 1024 * 1024

export function UploadPanel({ onParseSuccess }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [state, setState] = useState<UploadState>("IDLE")
  const [error, setError] = useState<string | null>(null)

  const selectFile = (selected?: File) => {
    if (!selected) return
    if (selected.type !== "application/pdf" && !selected.name.toLowerCase().endsWith(".pdf")) {
      setFile(null)
      setState("ERROR")
      setError("Unsupported file type: only PDF is accepted.")
      return
    }
    if (selected.size > MAX_BYTES) {
      setFile(null)
      setState("ERROR")
      setError("File too large. The local development limit is 25 MB.")
      return
    }
    setFile(selected)
    setState("IDLE")
    setError(null)
  }

  const handleInput = (event: ChangeEvent<HTMLInputElement>) => {
    selectFile(event.target.files?.[0])
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    selectFile(event.dataTransfer.files[0])
  }

  const handleParse = async () => {
    if (!file) return
    const formData = new FormData()
    formData.append("file", file, file.name)

    try {
      setError(null)
      setState("UPLOADING")
      const request = parseDocument(formData)
      setState("PROCESSING")
      const response = await request
      setState("SUCCESS")
      onParseSuccess(response, file)
    } catch (caught: unknown) {
      setState("ERROR")
      setError(caught instanceof Error ? caught.message : "Unexpected parsing failure")
    }
  }

  const clear = () => {
    setFile(null)
    setState("IDLE")
    setError(null)
    if (inputRef.current) inputRef.current.value = ""
  }

  const busy = state === "UPLOADING" || state === "PROCESSING"

  return (
    <section className="mx-auto flex min-h-[calc(100vh-130px)] max-w-5xl items-center justify-center py-12">
      <div className="relative w-full max-w-2xl border-y border-[var(--border)] bg-[var(--surface-raised)] px-6 py-10 md:px-12">
        <span className="absolute left-0 top-0 h-4 w-4 border-l border-t border-[var(--phosphor)]" aria-hidden="true" />
        <span className="absolute right-0 top-0 h-4 w-4 border-r border-t border-[var(--phosphor)]" aria-hidden="true" />
        <p className="tech-label mb-5">Document intake // channel 01</p>
        <h2 className="tech-heading mb-2 text-5xl">{busy ? "Document analysis" : "No document loaded"}</h2>
        <p className="font-terminal mb-6 text-lg text-[var(--phosphor-dim)]">SYSTEM READY // AWAITING INPUT<span className="cursor-blink">_</span></p>
        <div
          className="group cursor-pointer border border-dashed border-[var(--phosphor-dim)] bg-[var(--crt-panel)] px-6 py-14 text-center transition-colors hover:border-[var(--phosphor)] hover:bg-[var(--phosphor-very-dim)]"
          onClick={() => inputRef.current?.click()}
          onDragOver={(event) => event.preventDefault()}
          onDrop={handleDrop}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") inputRef.current?.click()
          }}
        >
          <p className="font-interface text-sm font-semibold uppercase tracking-[.12em] text-[var(--phosphor)]">[ Insert document ]</p>
          <p className="tech-label mt-3">PDF / Max 25 MB</p>
          <span className="tech-button mt-6 inline-block group-hover:border-[var(--phosphor-bright)]">Select file</span>
        </div>
        <input ref={inputRef} type="file" accept="application/pdf,.pdf" onChange={handleInput} hidden />

        {file && (
          <div className="mt-5 space-y-4 border-t border-[var(--phosphor-very-dim)] pt-4">
            <div className="flex items-center gap-3 font-terminal text-lg text-[var(--phosphor-bright)]">
              <StatusBadge status="good" size="sm" />
              <span className="text-sm">{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={handleParse}
                className="tech-button tech-button-primary disabled:cursor-wait disabled:opacity-50"
              >
                {busy ? "Processing document…" : "Parse PDF"}
              </button>
              <button type="button" disabled={busy} onClick={clear} className="tech-button">
                Remove
              </button>
            </div>
          </div>
        )}

        <p className="tech-label mt-5" aria-live="polite">Intake state // {state}</p>
        {busy && <div className="mt-3 border-l border-[var(--phosphor)] pl-3 font-terminal text-base text-[var(--phosphor-dim)]"><p>&gt; DOCUMENT RECEIVED</p><p>&gt; EXTRACTION ENGINE ACTIVE</p><p className="text-[var(--phosphor)]">&gt; BUILDING DOCUMENT MODEL<span className="cursor-blink">_</span></p></div>}
        {error && <p className="mt-3 border-l-2 border-[var(--red)] bg-[var(--error-bg)] p-3 font-terminal text-base text-[var(--red)]">ERR:: {error}</p>}
        {!file && !error && <p className="mt-3 font-terminal text-base uppercase text-[var(--phosphor-dim)]">&gt; Awaiting source document.</p>}
      </div>
    </section>
  )
}
