"use client"

import { useEffect, useMemo, useState } from "react"
import type { BlockData, DocumentData, ExtractionReport, PageData, ParseResponse } from "@/lib/api"
import {
  EXPORT_FORMATS,
  downloadExport,
  exportExtension,
  generateExport,
  orderedBlocks,
  pageToCleanText,
  type ExportFormat,
} from "@/lib/export"
import { DiagnosticsPanel } from "@/ui/diagnostics-panel"
import { JsonViewer } from "@/ui/json-viewer"
import { PageInspector } from "@/ui/page-inspector"
import { PageNavigator } from "@/ui/page-navigator"
import { PDFViewer } from "@/ui/pdf-viewer"
import { StatusBadge } from "@/ui/status-badge"

type WorkspaceView = "summary" | "inspector" | "export"

interface DocumentWorkspaceProps {
  document: DocumentData
  report: ExtractionReport
  file: File
  onReset: () => void
}

const pad3 = (value: number) => String(value).padStart(3, "0")

export function DocumentWorkspace({ document, report, file, onReset }: DocumentWorkspaceProps) {
  const [selectedPage, setSelectedPage] = useState(1)
  const [view, setView] = useState<WorkspaceView>("summary")
  const [showBlocks, setShowBlocks] = useState(false)
  const [showLabels, setShowLabels] = useState(false)
  const [highlightedBlock, setHighlightedBlock] = useState<number | null>(null)
  const [selectedBlock, setSelectedBlock] = useState<number | null>(null)
  const [summaryTab, setSummaryTab] = useState<"clean" | "structured">("clean")
  const [inspectorTab, setInspectorTab] = useState<"clean" | "blocks">("blocks")
  const [showSystemReport, setShowSystemReport] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [exportFormat, setExportFormat] = useState<ExportFormat>("markdown")

  useEffect(() => {
    setSelectedPage(1)
    setView("summary")
    setHighlightedBlock(null)
    setSelectedBlock(null)
    setShowSystemReport(false)
  }, [document])

  const response = useMemo<ParseResponse>(() => ({ document, report }), [document, report])
  const exportPreview = useMemo(() => generateExport(exportFormat, response), [exportFormat, response])

  const page = document.pages.find((item) => item.number === selectedPage) ?? document.pages[0]
  const selectPage = (pageNumber: number) => {
    setSelectedPage(pageNumber)
    setHighlightedBlock(null)
    setSelectedBlock(null)
    setView("inspector")
  }

  const totalBlocks = Object.values(report.block_role_counts).reduce((sum, value) => sum + (value ?? 0), 0)

  return (
    <section className="space-y-3">
      <div className="tech-panel border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2">
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
          <div className="flex items-center gap-2">
            <h2 className="tech-heading text-2xl">Document // active</h2>
            <StatusBadge status={report.status} size="sm" />
          </div>
          <div role="tablist" aria-label="Workspace mode" className="flex flex-wrap items-center gap-1">
            <span className="tech-label mr-1">Mode //</span>
            <ModeTab active={view === "summary"} label="01 Summary" onClick={() => setView("summary")} />
            <ModeTab active={view === "inspector"} label="02 Inspect" onClick={() => setView("inspector")} />
            <ModeTab active={view === "export"} label="03 Export" onClick={() => setView("export")} />
          </div>
          <button type="button" onClick={onReset} className="tech-button">
            Load new document
          </button>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-[var(--phosphor-very-dim)] pt-2 font-terminal text-base uppercase text-[var(--phosphor-dim)]">
          <span className="text-[var(--phosphor)]">File::{file.name}</span>
          <span>Pages::{pad3(document.page_count)}</span>
          <span>Native::{pad3(report.classification_counts.native ?? 0)}</span>
          <span>OCR::{pad3(report.classification_counts.ocr_required ?? 0)}</span>
          <span>Blocks::{pad3(totalBlocks)}</span>
        </div>
      </div>

      {view === "summary" && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-px border border-[var(--phosphor-dim)] bg-[var(--phosphor-dim)] md:grid-cols-4">
            <SummaryCard label="Pages" value={document.page_count} />
            <SummaryCard label="Successful" value={report.extraction_status_counts.success ?? 0} />
            <SummaryCard label="Problem pages" value={report.problem_pages.length} warn={report.problem_pages.length > 0} />
            <SummaryCard label="OCR blocks" value={report.ocr_block_count} />
          </div>

          <div className="border border-[var(--phosphor-dim)] bg-[var(--crt-panel)]">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--phosphor-dim)] px-3 py-2">
              <div className="flex flex-wrap items-center gap-1" role="tablist" aria-label="Summary content">
                <ModeTab active={summaryTab === "clean"} label="Clean" onClick={() => setSummaryTab("clean")} />
                <ModeTab active={summaryTab === "structured"} label="Structured" onClick={() => setSummaryTab("structured")} />
              </div>
              <button
                type="button"
                onClick={() => setShowSystemReport((value) => !value)}
                aria-expanded={showSystemReport}
                className={`tech-button ${showSystemReport ? "is-active" : ""}`}
              >
                {showSystemReport ? "[-] System report" : "[+] System report"}
              </button>
            </div>
            <div className="max-h-[62vh] overflow-auto p-4">
              {summaryTab === "clean" ? <CleanDocument pages={document.pages} /> : <StructuredDocument pages={document.pages} />}
            </div>
          </div>

          {showSystemReport && (
            <div className="grid grid-cols-1 gap-px border border-[var(--phosphor-dim)] bg-[var(--phosphor-dim)] lg:grid-cols-2">
              <div className="bg-[var(--crt-panel)] p-5"><DiagnosticsPanel report={report} /></div>
              <div className="space-y-px bg-[var(--phosphor-dim)]">
                <div className="bg-[var(--crt-panel)] p-5"><JsonViewer title="Document JSON" data={document} copyLabel="Copy document JSON" /></div>
                <div className="bg-[var(--crt-panel)] p-5"><JsonViewer title="Extraction Report JSON" data={report} copyLabel="Copy report JSON" /></div>
              </div>
            </div>
          )}
        </div>
      )}

      {view === "inspector" && page && (
        <div className="flex items-stretch border border-[var(--phosphor-dim)] bg-[var(--crt-panel)]">
          <aside className={`shrink-0 border-r border-[var(--phosphor-dim)] ${sidebarCollapsed ? "w-10" : "w-[160px]"}`}>
            <button
              type="button"
              onClick={() => setSidebarCollapsed((value) => !value)}
              aria-expanded={!sidebarCollapsed}
              className="tech-button w-full justify-between border-0"
            >
              {sidebarCollapsed ? "»" : "« Pages"}
            </button>
            <div className="max-h-[calc(100vh-190px)] overflow-auto">
              {sidebarCollapsed ? (
                document.pages.map((item) => (
                  <button
                    key={item.number}
                    type="button"
                    onClick={() => selectPage(item.number)}
                    aria-label={`Page ${item.number}`}
                    className={`block w-full border-b border-[var(--phosphor-very-dim)] px-1 py-2 text-center font-terminal text-base ${item.number === selectedPage ? "bg-[var(--phosphor)] text-[var(--crt-black)]" : "text-[var(--phosphor-dim)] hover:bg-[var(--phosphor-very-dim)] hover:text-[var(--phosphor)]"}`}
                  >
                    {item.number}
                  </button>
                ))
              ) : (
                <PageNavigator pages={document.pages} selected={selectedPage} onSelect={selectPage} />
              )}
            </div>
          </aside>

          <div className="grid min-w-0 flex-1 grid-cols-1 gap-px bg-[var(--phosphor-dim)] xl:grid-cols-2">
            <div className="min-w-0 space-y-2 bg-[var(--surface-deep)] p-2">
              <div className="flex flex-wrap items-center gap-1 border-y border-[var(--phosphor-very-dim)] bg-[var(--crt-panel)] p-1">
                <TerminalToggle checked={showBlocks} onChange={setShowBlocks} label="All Boxes" />
                <TerminalToggle checked={showLabels} onChange={setShowLabels} label="All Labels" />
                <span className="tech-label ml-auto pr-2">Boxes::hover/select</span>
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
            <div className="flex min-w-0 flex-col bg-[var(--crt-panel)]">
              <div className="flex items-center gap-1 border-b border-[var(--phosphor-dim)] p-1" role="tablist" aria-label="Inspection content">
                <ModeTab active={inspectorTab === "clean"} label="Clean" onClick={() => setInspectorTab("clean")} />
                <ModeTab active={inspectorTab === "blocks"} label="Blocks" onClick={() => setInspectorTab("blocks")} />
              </div>
              <div className="max-h-[calc(100vh-190px)] min-h-[420px] overflow-auto">
                {inspectorTab === "clean" ? (
                  <div className="p-4">
                    <p className="tech-label mb-3">Page {pad3(page.number)} // normalized text</p>
                    <p className="whitespace-pre-wrap break-words font-terminal text-lg leading-snug text-[var(--phosphor)]">
                      {pageToCleanText(page) || "No body text extracted on this page."}
                    </p>
                  </div>
                ) : (
                  <PageInspector
                    page={page}
                    highlightedBlock={highlightedBlock}
                    selectedBlock={selectedBlock}
                    onBlockHover={setHighlightedBlock}
                    onBlockSelect={setSelectedBlock}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {view === "inspector" && !page && (
        <p className="border border-[var(--amber)] bg-[var(--warning-bg)] p-4 font-terminal text-[var(--amber)]">WARN:: The parser returned no pages.</p>
      )}

      {view === "export" && (
        <div className="border border-[var(--phosphor-dim)] bg-[var(--crt-panel)]">
          <header className="border-b border-[var(--phosphor-dim)] px-4 py-3">
            <p className="tech-label">Output channel</p>
            <h3 className="tech-heading mt-1 text-2xl">Export document</h3>
          </header>
          <div className="space-y-4 p-4">
            <div className="flex flex-wrap items-center gap-1" role="tablist" aria-label="Export format">
              {EXPORT_FORMATS.map((format) => (
                <ModeTab
                  key={format.id}
                  active={exportFormat === format.id}
                  label={format.label}
                  onClick={() => setExportFormat(format.id)}
                />
              ))}
            </div>
            <p className="font-terminal text-base uppercase text-[var(--phosphor-dim)]">
              {EXPORT_FORMATS.find((format) => format.id === exportFormat)?.description} ·{" "}
              {exportPreview.length > 0 ? `${exportPreview.length.toLocaleString()} chars` : "No exportable content"}
            </p>
            <div className="max-h-[46vh] overflow-auto border border-[var(--border-subtle)] bg-[var(--surface-deep)] p-3">
              <pre className="whitespace-pre-wrap break-words font-terminal text-base leading-tight text-[var(--phosphor)]">
                {exportPreview || "The parsed document contains no exportable text."}
              </pre>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => downloadExport(file.name, exportFormat, exportPreview)}
                disabled={exportPreview.length === 0}
                className="tech-button-primary"
              >
                &gt; Download .{exportExtension(exportFormat)}
              </button>
              <p className="font-terminal text-sm uppercase text-[var(--phosphor-dim)]">
                Generated locally from the parse response
              </p>
            </div>
          </div>
        </div>
      )}

      <footer className="sticky bottom-0 z-20 flex flex-wrap gap-x-4 border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-1 font-terminal text-sm uppercase text-[var(--text-muted)]">
        <span>DOC::{pad3(document.page_count)}P</span>
        <span>BLOCKS::{pad3(totalBlocks)}</span>
        <span>OCR::{pad3(report.ocr_block_count)}</span>
        <span>WARN::{pad3(report.warnings.length)}</span>
        <span className={report.status === "good" ? "text-[var(--phosphor)]" : report.status === "review" ? "text-[var(--amber)]" : "text-[var(--red)]"}>STATUS::{report.status.toUpperCase()}</span>
      </footer>
    </section>
  )
}

function ModeTab({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return (
    <button type="button" role="tab" aria-selected={active} onClick={onClick} className={`tech-button ${active ? "is-active" : ""}`}>
      [ {label} ]
    </button>
  )
}

function CleanDocument({ pages }: { pages: PageData[] }) {
  const hasContent = pages.some((page) => pageToCleanText(page).length > 0)
  if (!hasContent) return <p className="tech-label">No body text extracted.</p>
  return (
    <div className="space-y-5">
      {pages.map((page) => {
        const text = pageToCleanText(page)
        if (!text) return null
        return (
          <section key={page.number}>
            <p className="mb-2 border-b border-[var(--phosphor-very-dim)] pb-1 font-terminal text-sm uppercase text-[var(--phosphor-dim)]">Page {pad3(page.number)}</p>
            <p className="whitespace-pre-wrap break-words font-terminal text-lg leading-snug text-[var(--phosphor)]">{text}</p>
          </section>
        )
      })}
    </div>
  )
}

const ROLE_TAGS: Record<BlockData["role"], string> = {
  heading: "HDG",
  paragraph: "PAR",
  header: "HDR",
  footer: "FTR",
  page_number: "PAG",
  unknown: "UNK",
}

function StructuredDocument({ pages }: { pages: PageData[] }) {
  return (
    <div className="space-y-5">
      {pages.map((page) => (
        <section key={page.number}>
          <p className="mb-2 border-b border-[var(--phosphor-very-dim)] pb-1 font-terminal text-sm uppercase text-[var(--phosphor-dim)]">
            Page {pad3(page.number)} // {orderedBlocks(page).length} blocks
          </p>
          <div className="space-y-2">
            {orderedBlocks(page).map((block) => (
              <div key={`${page.number}:${block.reading_order}`} className="grid grid-cols-[44px_minmax(0,1fr)] gap-2">
                <span className={`pt-0.5 font-interface text-[9px] font-semibold uppercase tracking-[.1em] ${block.role === "heading" ? "text-[var(--phosphor-bright)]" : block.role === "header" || block.role === "footer" || block.role === "page_number" ? "text-[var(--border)]" : "text-[var(--phosphor-dim)]"}`}>
                  {ROLE_TAGS[block.role] ?? "UNK"}
                </span>
                <p className={`whitespace-pre-wrap break-words font-terminal leading-snug ${block.role === "heading" ? "text-xl text-[var(--phosphor-bright)]" : block.role === "header" || block.role === "footer" || block.role === "page_number" ? "text-base text-[var(--phosphor-dim)]" : "text-lg text-[var(--phosphor)]"}`}>
                  {block.text.trim() || <span className="text-[var(--phosphor-dim)]">[empty]</span>}
                </p>
              </div>
            ))}
            {page.blocks.length === 0 && <p className="tech-label">No blocks extracted</p>}
          </div>
        </section>
      ))}
    </div>
  )
}

function SummaryCard({ label, value, warn = false }: { label: string; value: number; warn?: boolean }) {
  return (
    <div className="bg-[var(--crt-panel)] p-4">
      <p className="tech-label">{label}</p>
      <p className={`font-display mt-1 text-5xl leading-none ${warn ? "text-[var(--amber)]" : "text-[var(--phosphor-bright)]"}`}>{pad3(value)}</p>
    </div>
  )
}

function TerminalToggle({ checked, onChange, label }: { checked: boolean; onChange: (value: boolean) => void; label: string }) {
  return (
    <label className={`font-interface cursor-pointer border px-3 py-1.5 text-[9px] font-semibold uppercase tracking-[.1em] ${checked ? "border-[var(--text)] bg-[var(--selected-bg)] text-[var(--text-strong)]" : "border-[var(--border-subtle)] text-[var(--text-muted)]"}`}>
      <input className="sr-only" type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span className={`toggle-lamp mr-2 inline-block h-1.5 w-1.5 ${checked ? "bg-[var(--text)]" : "bg-[var(--border-subtle)]"}`} />
      {label}
    </label>
  )
}
