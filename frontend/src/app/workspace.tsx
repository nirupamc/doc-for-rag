/*
 * DocumentWorkspace — Post-parse document analysis interface.
 * 
 * Layout:
 *   Header with document metrics + status + reset
 *   Main area with two columns:
 *     - Page navigator (sidebar)
 *     - Page inspector (main)
 *   Footer with diagnostics + raw data
 */

"use client"

import { useState, useEffect } from "react"
import { DocumentData, ExtractionReport } from "@/lib/api"
import { StatusBadge } from "@/ui/status-badge"
import { PageNavigator } from "@/ui/page-navigator"
import { PageInspector } from "@/ui/page-inspector"
import { DiagnosticsPanel } from "@/ui/diagnostics-panel"
import { JsonViewer } from "@/ui/json-viewer"
import { LoadingState } from "@/ui/loading-state"
import { ErrorState } from "@/ui/error-state"

export function DocumentWorkspace({
  document,
  report,
}: {
  document: DocumentData
  report: ExtractionReport
}) {
  const [selectedPage, setSelectedPage] = useState(1)
  const [view, setView] = useState<"summary" | "inspector">("summary")
  const [isResetting, setIsResetting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset state when document changes
  useEffect(() => {
    setSelectedPage(1)
    setView("summary")
    setError(null)
  }, [document.page_count])

  const handleReset = async () => {
    setIsResetting(true)
    setError(null)
    // In a full app, we'd call a backend reset endpoint.
    // For M2, just clear local state.
    setTimeout(() => {
      setIsResetting(false)
      setView("summary")
    }, 800)
  }

  const statusLabel = {
    good: "GOOD",
    review: "REVIEW",
    poor: "POOR",
  }[report.status] || report.status

  return (
    <main className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left column: Page navigator + inspector */}
      <div className="lg:col-span-7 space-y-4">
        {view === "summary" ? (
          <DocumentSummary document={document} report={report} onSelect={setSelectedPage} />
        ) : (
          <>
            <PageNavigator
              pages={document.pages}
              selected={selectedPage}
              onSelect={setSelectedPage}
            />
            <PageInspector
              page={document.pages[selectedPage - 1] || { } as PageData}
              onReanalyse={handleReset}
            />
          </>
        )}
      </div>

      {/* Right column: Diagnostics + raw data */}
      <div className="lg:col-span-5 space-y-4">
        <DiagnosticsPanel report={report} />
        <JsonViewer
          title="Document JSON"
          data={JSON.stringify(document, null, 2)}
          copyLabel="Copy document JSON"
        />
        <JsonViewer
          title="Extraction Report JSON"
          data={JSON.stringify(report, null, 2)}
          copyLabel="Copy report JSON"
        />
      </div>
    </main>
  )
}

DocumentWorkspace.defaultProps = {
  document: {} as DocumentData,
  report: {} as ExtractionReport,
}