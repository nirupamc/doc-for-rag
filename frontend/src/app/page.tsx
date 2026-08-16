/*
 * RagParser Frontend — Web M2
 * 
 * Main application page. Displays the upload interface when no document
 * has been parsed, and the document workspace after a successful parse.
 */

import { useState, useEffect } from "react"
import { checkHealth, parseDocument } from "@/lib/api"
import { StatusBadge } from "@/ui/status-badge"
import { ErrorState } from "@/ui/error-state"
import { LoadingState } from "@/ui/loading-state"

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [hasDocument, setHasDocument] = useState(false)
  const [isBackendAvailable, setBackendAvailable] = useState(false)

  // Check backend health on mount
  useEffect(() => {
    async function init() {
      try {
        const h = await checkHealth()
        setHealth(h)
        setBackendAvailable(h.tesseract_available)
      } catch (e) {
        // Backend unavailable – show indicator but don't block UI
        debug(`Backend health check failed: ${e}`)
        setHealth({ status: "ok", tesseract_available: false })
        setBackendAvailable(false)
      }
    }
    init()
  }, [])

  return (
    <main className="min-h-screen bg-background p-4 md:p-6">
      <header className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tighter">
          RagParser
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Inspect and normalize PDFs for reliable RAG ingestion.
        </p>
      </header>

      {health ? (
        <div className="mb-4 flex items-center gap-2">
          <StatusBadge status={health.tesseract_available ? "good" : "error"} />
          <span className="text-sm text-muted-foreground">
            {" "}
            {health.tesseract_available ? "Parser online" : "OCR unavailable"}
          {" "}
          }
        </div>
      ) : (
        <p className="text-sm text-error">Backend health check failed</p>
      )}

      {hasDocument ? (
        <DocumentWorkspace />
      ) : (
        <UploadPanel />
      )}
    </main>
  )
}