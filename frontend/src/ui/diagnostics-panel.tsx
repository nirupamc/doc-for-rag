/* DiagnosticsPanel — Inspect the ExtractionReport.

 * Shows:
 *   - overall status
 *   - status reasons
 *   - problem pages
 *   - warnings
 *   - OCR diagnostics
 *   - layout counts
 *   - structure counts
 */

"use client"

import { ExtractionReport } from "@/lib/api"

export interface DiagnosticsPanelProps {
  report: ExtractionReport
}

export function DiagnosticsPanel({ report }: DiagnosticsPanelProps) {
  const statusLabels: Record<string, string> = {
    good: "GOOD",
    review: "REVIEW",
    poor: "POOR",
  }

  const statusClass: Record<string, string> = {
    good: "bg-green-100 text-green-800",
    review: "bg-yellow-100 text-yellow-800",
    poor: "bg-red-100 text-red-800",
  }

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm text-muted-foreground">Overall status</p>
        <span className={`inline-block px-2 py-1 rounded text-sm font-medium ${statusClass[report.status]}`}>
          {statusLabels[report.status]}
        </span>
      </div>

      {report.status_reasons.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">Status reasons</p>
          <ul className="list-disc list-inside text-sm">
            {report.status_reasons.map((reason, i) => (
              <li key={i} className="mb-1">
                <strong>{reason.category.toUpperCase()}:</strong> {reason.message}{" "}
                {reason.count !== null && reason.count > 0 && (
                  <span className="ml-2">
                    ({reason.count} page{s:1}{
                      reason.page_numbers &&
                      reason.page_numbers.length > 0
                        ? ` pages ${reason.page_numbers.map((p) => `#${p}`).join(", ")}`)
                        : ""
                    })
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <p className="text-sm text-muted-foreground">Problem pages</p>
        {report.problem_pages.length > 0 ? (
          <span>
            {report.problem_pages.map((p, i) => (
              <span key={p} className="mr-1">
                #{p}
              </span>
            ))}
          </span>
        ) : (
          <span className="text-muted-foreground">None</span>
        )}
      </div>

      {report.warnings.length > 0 && (
        <div>
          <p className="text-sm text-muted-foreground">Warnings</p>
          <ul className="list-disc list-inside text-sm">
            {report.warnings.map((w, i) => (
              <li key={i}>{w.message}</li>
            ))}
          </ul>
        </div>
      )}

      {/* OCR diagnostics */}
      <div>
        <p className="text-sm text-muted-foreground">OCR diagnostics</p>
        <dl className="grid grid-cols-2 gap-2 text-sm">
          <dt>OCR blocks</dt>
          <dd>{report.ocr_block_count}</dd>
          <dt>Blocks with confidence</dt>
          <dd>{report.blocks_with_confidence}</dd>
          <dt>Median confidence</dt>
          <dd>{report.median_ocr_confidence?.toFixed(2) ?? "N/A"}</dd>
          <dt>Min confidence</dt>
          <dd>{report.min_ocr_confidence?.toFixed(2) ?? "N/A"}</dd>
          <dt>Low confidence blocks</dt>
          <dd>{report.low_confidence_block_count}</dd>
          <dt>Pages with low confidence</dt>
          <dd>
            {report.pages_with_low_confidence.length > 0
              ? report.pages_with_low_confidence.map((p) => `#${p}`).join(", ")
              : "None"}
          </dd>
        </dl>
      </div>

      {/* Layout counts */}
      <div>
        <p className="text-sm text-muted-foreground">Layout mode counts</p>
        <dl className="grid grid-cols-3 gap-2 text-xs">
          <dt>Single column</dt>
          <dd>{report.layout_mode_counts.single_column}</dd>
          <dt>Two column</dt>
          <dd>{report.layout_mode_counts.two_column}</dd>
          <dt>Uncertain</dt>
          <dd>{report.layout_mode_counts.uncertain}</dd>
        </dl>
      </div>

      {/* Block role counts */}
      <div>
        <p className="text-sm text-muted-foreground">Block role counts</p>
        <dl className="grid grid-cols-6 gap-1 text-xxs">
          <dt>unknown</dt>
          <dd>{report.block_role_counts.unknown}</dd>
          <dt>heading</dt>
          <dd>{report.block_role_counts.heading}</dd>
          <dt>paragraph</dt>
          <dd>{report.block_role_counts.paragraph}</dd>
          <dt>header</dt>
          <dd>{report.block_role_counts.header}</dd>
          <dt>footer</dt>
          <dd>{report.block_role_counts.footer}</dd>
          <dt>page_number</dt>
          <dd>{report.block_role_counts.page_number}</dd>
        </dl>
      </div>
    </div>
  )
}