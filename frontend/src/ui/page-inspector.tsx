/* PageInspector — Detailed view of a single selected page.

 * Shows structured page information:
 *   - page number
 *   - classification
 *   - classification reason
 *   - extraction method
 *   - extraction status
 *   - layout mode
 *   - warnings
 *   - blocks ordered by reading_order
 *
 * For each block shows:
 *   - role
 *   - text (truncated)
 *   - extraction method
 *   - confidence (if OCR)
 *   - bbox in collapsible details
 */

"use client"

import { useState } from "react"

export interface PageInspectorProps {
  page: {
    number: number
    classification: string
    classification_reason: string
    extraction_method: string
    extraction_status: string
    layout_mode: string
    layout_reason: string
    warnings: string[]
    blocks: {
      type: string
      text: string
      bbox: { x0: number; y0: number; x1: number; y1: number }
      extraction_method: string
      confidence?: number | null
      reading_order: number
      role: string
    }[]
  }
  onReanalyse?: () => void
}

export function PageInspector({ page, onReanalyse }: PageInspectorProps) {
  const [showBboxes, setShowBboxes] = useState(false)

  const truncated = (text: string, len = 60) =>
    text.length > len ? `${text.slice(0, len)}…` : text

  return (
    <div className="p-5 rounded-lg border-border">
      <h3 className="font-semibold mb-3">Page {page.number}</h3>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-sm text-muted-foreground">Classification</p>
          <p className="font-medium">{page.classification.toUpperCase()}</p>
          <p className="text-xs text-muted-foreground">{page.classification_reason}</p>
        </div>
        <div>
          <p className="text-sm text-muted-foreground">Extraction</p>
          <p className="font-medium">
            {page.extraction_method.toUpperCase()}
            {" "}
            {page.extraction_status.toUpperCase()}
          </p>
          <p className="text-xs text-muted-foreground">{page.layout_mode.toUpperCase()}</p>
        </div>
      </div>

      {page.warnings.length > 0 && (
        <div className="mb-4 p-3 rounded rounded-border border-border">
          <p className="text-sm text-warning">Warnings:</p>
          <ul className="list-disc list-inside text-sm">
            {page.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {page.blocks.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-medium mb-2">Blocks ({page.blocks.length})</p>
          <div className="space-y-2">
            {page.blocks.map((block, i) => {
              const confDisplay = block.confidence !== null
                ? `${(block.confidence * 100).toFixed(0)}%`
                : "N/A"

              return (
                <div
                  key={i}
                  className`
                    p-3 rounded rounded-border border-border
                    ${block.reading_order === 0 ? "opacity-60" : ""}
                  `
                >
                  <div className="flex justify-between align-items-start">
                    <div>
                      <p className="font-medium">{block.role.toUpperCase()}</p>
                      <p className="text-xs text-muted-foreground">
                        {truncated(block.text, 50)}
                      </p>
                    </div>
                    <div className="text-right text-xs">
                      <span>{block.reading_order + 1}</span>
                      <span className="ml-1">/{page.blocks.length}</span>
                      <span className="text-primary-500 cursor-pointer">
                        {truncated(confDisplay, 4)}
                      </span>
                    </div>
                  </div>

                  {showBboxes && (
                    <div className="mt-1 text-caption text-muted-foreground">
                      bbox:{" "}
                      <span>{block.bbox.x0.toFixed(1)} , {block.bbox.y0.toFixed(1)}</span>
                      <span>{block.bbox.x1.toFixed(1)} , {block.bbox.y1.toFixed(1)}</span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {!page.blocks.length && (
        <p className="text-sm text-muted-foreground mb-2">
          No blocks extracted.
        </p>
      )}
    </div>
  )