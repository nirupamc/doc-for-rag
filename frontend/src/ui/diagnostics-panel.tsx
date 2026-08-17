"use client"

import type { ExtractionReport } from "@/lib/api"

export function DiagnosticsPanel({ report }: { report: ExtractionReport }) {
  return (
    <section>
      <header className="mb-4 flex items-end justify-between border-b border-[var(--phosphor-dim)] pb-2">
        <div><p className="tech-label">Machine report // 04</p><h3 className="tech-heading mt-1 text-3xl">Extraction diagnostics</h3></div>
        <span className={`font-display text-4xl leading-none ${tone(report.status)}`}>{report.status.toUpperCase()}</span>
      </header>
      <DiagnosticGroup title="Extraction">
        <Metric label="Native" value={report.extraction_method_counts.native ?? 0} />
        <Metric label="OCR" value={report.extraction_method_counts.ocr ?? 0} />
        <Metric label="Failed pages" value={report.extraction_status_counts.failed ?? 0} warning={(report.extraction_status_counts.failed ?? 0) > 0} />
      </DiagnosticGroup>
      <DiagnosticGroup title="OCR signal">
        <Metric label="Blocks" value={report.ocr_block_count} />
        <Metric label="Confidence samples" value={report.blocks_with_confidence} />
        <Metric label="Median confidence" value={report.median_ocr_confidence?.toFixed(2) ?? "—"} />
        <Metric label="Minimum confidence" value={report.min_ocr_confidence?.toFixed(2) ?? "—"} />
        <Metric label="Low confidence" value={report.low_confidence_block_count} warning={report.low_confidence_block_count > 0} />
      </DiagnosticGroup>
      <DiagnosticGroup title="Layout / structure">
        <Metric label="Single column" value={report.layout_mode_counts.single_column ?? 0} />
        <Metric label="Two column" value={report.layout_mode_counts.two_column ?? 0} />
        <Metric label="Uncertain" value={report.layout_mode_counts.uncertain ?? 0} warning={(report.layout_mode_counts.uncertain ?? 0) > 0} />
        <Metric label="Paragraph" value={report.block_role_counts.paragraph ?? 0} />
        <Metric label="Heading" value={report.block_role_counts.heading ?? 0} />
        <Metric label="Unknown" value={report.block_role_counts.unknown ?? 0} />
      </DiagnosticGroup>

      {report.status_reasons.length > 0 && <div className="section-rule mt-4 pt-3"><p className="tech-label mb-2">Status reasons</p><ul className="space-y-1 font-terminal text-base leading-tight">{report.status_reasons.map((reason, index) => <li key={index}><span className="text-[var(--amber)]">{reason.category.toUpperCase()}::</span>{reason.message}{reason.page_numbers?.length ? ` [P${reason.page_numbers.join("/P")}]` : ""}</li>)}</ul></div>}
      {report.warnings.length > 0 && <div className="section-rule mt-4 pt-3"><p className="tech-label mb-2 text-[var(--amber)]">Warning register</p><ul className="font-terminal text-base text-[var(--amber)]">{report.warnings.map((warning, index) => <li key={index}>WARN::P{String(warning.page).padStart(3, "0")}::{warning.message}</li>)}</ul></div>}
      <p className={`mt-4 border-l-2 px-3 py-1 font-terminal text-lg uppercase ${report.problem_pages.length ? "border-[var(--amber)] bg-[var(--warning-bg)] text-[var(--amber)]" : "border-[var(--text)] bg-[var(--good-bg)] text-[var(--text-strong)]"}`}>{report.problem_pages.length ? `Review required // ${report.problem_pages.length} page(s)` : "System::no critical anomalies detected"}</p>
    </section>
  )
}

function DiagnosticGroup({ title, children }: { title: string; children: React.ReactNode }) { return <div className="mb-3"><p className="tech-label mb-1">{title}</p><dl className="border-y border-[var(--phosphor-very-dim)] py-1">{children}</dl></div> }
function Metric({ label, value, warning = false }: { label: string; value: number | string; warning?: boolean }) { return <div className="flex justify-between font-terminal text-lg leading-tight"><dt className="text-[var(--phosphor-dim)]">{label.toUpperCase()}</dt><dd className={warning ? "text-[var(--amber)]" : "text-[var(--phosphor)]"}>{typeof value === "number" ? String(value).padStart(3, "0") : value}</dd></div> }
function tone(status: string) { return status === "good" ? "text-[var(--phosphor-bright)]" : status === "review" ? "text-[var(--amber)]" : "text-[var(--red)]" }
