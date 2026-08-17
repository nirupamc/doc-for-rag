"use client"

import { useEffect, useState } from "react"
import type { DocumentData, ExtractionReport } from "@/lib/api"
import { DiagnosticsPanel } from "@/ui/diagnostics-panel"
import { JsonViewer } from "@/ui/json-viewer"
import { PageInspector } from "@/ui/page-inspector"
import { PageNavigator } from "@/ui/page-navigator"
import { PDFViewer } from "@/ui/pdf-viewer"
import { StatusBadge } from "@/ui/status-badge"

interface DocumentWorkspaceProps {
  document: DocumentData
  report: ExtractionReport
  file: File
  onReset: () => void
}

export function DocumentWorkspace({ document, report, file, onReset }: DocumentWorkspaceProps) {
  const [selectedPage, setSelectedPage] = useState(1)
  const [view, setView] = useState<"summary" | "inspector">("summary")
  const [showBlocks, setShowBlocks] = useState(true)
  const [showLabels, setShowLabels] = useState(true)
  const [highlightedBlock, setHighlightedBlock] = useState<number | null>(null)
  const [selectedBlock, setSelectedBlock] = useState<number | null>(null)

  useEffect(() => {
    setSelectedPage(1)
    setView("summary")
    setHighlightedBlock(null)
    setSelectedBlock(null)
  }, [document])

  const page = document.pages.find((item) => item.number === selectedPage) ?? document.pages[0]
  const selectPage = (pageNumber: number) => {
    setSelectedPage(pageNumber)
    setHighlightedBlock(null)
    setSelectedBlock(null)
    setView("inspector")
  }

  return (
    <section className="space-y-3">
      <div className="tech-panel flex flex-wrap items-center justify-between gap-3 px-3 py-2">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="tech-heading text-2xl">Document // active</h2>
            <StatusBadge status={report.status} size="sm" />
          </div>
          <p className="mt-1 font-terminal text-base uppercase text-[var(--phosphor-dim)]">
            {file.name} · {document.page_count} {document.page_count === 1 ? "page" : "pages"}
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => setView(view === "summary" ? "inspector" : "summary")} className="tech-button">
            {view === "summary" ? "[ Inspect pages ]" : "[ System report ]"}
          </button>
          <button type="button" onClick={onReset} className="tech-button tech-button-primary">
            [ Load new document ]
          </button>
        </div>
      </div>

      {view === "summary" ? (
        <div className="grid gap-px border border-[var(--phosphor-dim)] bg-[var(--phosphor-dim)] lg:grid-cols-[1fr_1fr_1.25fr]">
          <div className="grid grid-cols-3 gap-px bg-[var(--phosphor-dim)] lg:col-span-3"><SummaryCard label="Pages" value={document.page_count} /><SummaryCard label="Successful" value={report.extraction_status_counts.success} /><SummaryCard label="Problem pages" value={report.problem_pages.length} /></div>
          <SummaryModule title="Extraction" rows={[["Native", report.extraction_method_counts.native ?? 0], ["OCR", report.extraction_method_counts.ocr ?? 0], ["Failed", report.extraction_status_counts.failed ?? 0]]} />
          <SummaryModule title="Layout" rows={[["Single", report.layout_mode_counts.single_column ?? 0], ["Double", report.layout_mode_counts.two_column ?? 0], ["Uncertain", report.layout_mode_counts.uncertain ?? 0]]} />
          <SummaryModule title="Structure" rows={[["Header", report.block_role_counts.header ?? 0], ["Heading", report.block_role_counts.heading ?? 0], ["Paragraph", report.block_role_counts.paragraph ?? 0], ["Footer", report.block_role_counts.footer ?? 0]]} />
          <div className="bg-[var(--crt-panel)] p-4 lg:col-span-3">
            <p className="tech-label mb-2">System report</p><p className={`border-l-2 px-3 py-1 font-terminal text-lg uppercase ${report.problem_pages.length ? "border-[var(--amber)] text-[var(--amber)]" : "border-[var(--phosphor)] text-[var(--phosphor-bright)]"}`}>{report.problem_pages.length ? `Review required // ${report.problem_pages.length} problem pages` : "No critical anomalies detected"}</p>
          </div>
          <div className="bg-[var(--crt-panel)] p-4 lg:col-span-3">
            <h3 className="tech-label mb-3">Page index</h3>
            <PageNavigator pages={document.pages} selected={selectedPage} onSelect={selectPage} />
          </div>
        </div>
      ) : page ? (
        <div className="grid grid-cols-1 gap-px border border-[var(--phosphor-dim)] bg-[var(--phosphor-dim)] xl:grid-cols-[142px_minmax(0,1fr)_350px]">
          <aside className="max-h-[calc(100vh-150px)] overflow-auto bg-[var(--crt-panel)]">
            <PageNavigator pages={document.pages} selected={selectedPage} onSelect={selectPage} />
          </aside>
          <div className="min-w-0 space-y-2 bg-[var(--surface-deep)] p-2">
            <div className="flex flex-wrap items-center gap-1 border-y border-[var(--phosphor-very-dim)] bg-[var(--crt-panel)] p-1">
              <TerminalToggle checked={showBlocks} onChange={setShowBlocks} label="Show Blocks" />
              <TerminalToggle checked={showLabels} onChange={setShowLabels} label="Show Labels" />
              <span className="tech-label ml-auto pr-2">Overlay::linked</span>
            </div>
            <PDFViewer
              file={file}
              selectedPage={selectedPage}
              parsedPage={page}
              showBboxes={showBlocks}
              showLabels={showLabels}
              highlightedBlock={highlightedBlock}
              selectedBlock={selectedBlock}
              onBlockHover={setHighlightedBlock}
              onBlockSelect={setSelectedBlock}
            />
          </div>
          <div className="bg-[var(--crt-panel)]">
            <PageInspector
              page={page}
              highlightedBlock={highlightedBlock}
              selectedBlock={selectedBlock}
              onBlockHover={setHighlightedBlock}
              onBlockSelect={setSelectedBlock}
              showBboxes={showBlocks}
            />
          </div>
        </div>
      ) : (
        <p className="border border-[var(--amber)] bg-[var(--warning-bg)] p-4 font-terminal text-[var(--amber)]">WARN:: The parser returned no pages.</p>
      )}

      <div className="grid grid-cols-1 gap-px border border-[var(--phosphor-dim)] bg-[var(--phosphor-dim)] lg:grid-cols-2">
        <div className="bg-[var(--crt-panel)] p-5"><DiagnosticsPanel report={report} /></div>
        <div className="space-y-px bg-[var(--phosphor-dim)]">
          <div className="bg-[var(--crt-panel)] p-5"><JsonViewer title="Document JSON" data={document} copyLabel="Copy document JSON" /></div>
          <div className="bg-[var(--crt-panel)] p-5"><JsonViewer title="Extraction Report JSON" data={report} copyLabel="Copy report JSON" /></div>
        </div>
      </div>
      <footer className="sticky bottom-0 z-20 flex flex-wrap gap-x-4 border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-1 font-terminal text-sm uppercase text-[var(--text-muted)]">
        <span>DOC::{String(document.page_count).padStart(3, "0")}P</span>
        <span>BLOCKS::{String((report.block_role_counts.paragraph ?? 0) + (report.block_role_counts.heading ?? 0) + (report.block_role_counts.header ?? 0) + (report.block_role_counts.footer ?? 0) + (report.block_role_counts.page_number ?? 0) + (report.block_role_counts.unknown ?? 0)).padStart(3, "0")}</span>
        <span>OCR::{String(report.ocr_block_count).padStart(3, "0")}</span>
        <span>WARN::{String(report.warnings.length).padStart(3, "0")}</span>
        <span className={report.status === "good" ? "text-[var(--phosphor)]" : report.status === "review" ? "text-[var(--amber)]" : "text-[var(--red)]"}>STATUS::{report.status.toUpperCase()}</span>
      </footer>
    </section>
  )
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return <div className="bg-[var(--crt-panel)] p-4"><p className="tech-label">{label}</p><p className="font-display mt-1 text-5xl leading-none text-[var(--phosphor-bright)]">{String(value).padStart(3, "0")}</p></div>
}

function SummaryModule({ title, rows }: { title: string; rows: Array<[string, number]> }) {
  return <section className="bg-[var(--crt-panel)] p-4"><h3 className="font-interface mb-3 border-b border-[var(--phosphor-very-dim)] pb-2 text-[10px] font-semibold uppercase tracking-[.14em]">{title}</h3><dl>{rows.map(([label, value]) => <div key={label} className="flex justify-between font-terminal text-lg leading-tight"><dt className="text-[var(--phosphor-dim)]">{label.toUpperCase()}</dt><dd>{String(value).padStart(3, "0")}</dd></div>)}</dl></section>
}

function TerminalToggle({ checked, onChange, label }: { checked: boolean; onChange: (value: boolean) => void; label: string }) {
  return <label className={`font-interface cursor-pointer border px-3 py-1.5 text-[9px] font-semibold uppercase tracking-[.1em] ${checked ? "border-[var(--text)] bg-[var(--selected-bg)] text-[var(--text-strong)]" : "border-[var(--border-subtle)] text-[var(--text-muted)]"}`}><input className="sr-only" type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} /><span className={`toggle-lamp mr-2 inline-block h-1.5 w-1.5 ${checked ? "bg-[var(--text)]" : "bg-[var(--border-subtle)]"}`} />{label}</label>
}
