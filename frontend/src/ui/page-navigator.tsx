/* PageNavigator — Scrollable sidebar showing page summaries.

 * For every page shows compact information:
 *   Page N
 *   CLASSIFICATION
 *   STATUS
 *
 * Clicking a page updates the selected page in the inspector.
 * Highlighted block (from PDF overlay) is visually indicated.
 */

"use client"

export interface PageNavigatorProps {
  pages: { number: number; classification: string; extraction_status: string }[]
  selected: number
  onSelect: (pageNumber: number) => void
  highlightedBlock?: number | null
}

export function PageNavigator({ pages, selected, onSelect, highlightedBlock }: PageNavigatorProps) {
  return (
    <nav aria-label="Page index">
      <div className="border-b border-[var(--phosphor-dim)] px-2 py-2">
        <p className="tech-label">Page index</p>
        <p className="font-terminal text-sm text-[var(--phosphor-dim)]">{String(pages.length).padStart(3, "0")}::ENTRIES</p>
      </div>
      {pages.map((page) => {
        const isSelected = page.number === selected
        const isHighlighted = highlightedBlock === page.number
        return (
          <button
            key={page.number}
            onClick={() => onSelect(page.number)}
            className={`relative grid w-full grid-cols-[38px_1fr] border-b border-[var(--phosphor-very-dim)] px-2 py-1.5 text-left transition-colors
              ${isSelected ? "bg-[var(--phosphor)] text-[var(--crt-black)] before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:bg-[var(--phosphor-bright)]" : "text-[var(--phosphor-dim)] hover:bg-[var(--phosphor-very-dim)] hover:text-[var(--phosphor)]"}
              ${isHighlighted ? "text-[var(--phosphor-bright)]" : ""}`}
            aria-selected={isSelected}
            aria-label={`Page ${page.number}`}
            tabIndex={isSelected ? 0 : -1}
          >
            <span className="font-terminal text-xl leading-none">
              {String(page.number).padStart(3, "0")}
            </span>
            <span className="font-interface space-y-0.5 text-[8px] font-medium uppercase leading-none tracking-[.08em]">
              <span className="block">{page.classification === "native" ? "NAT" : page.classification === "ocr_required" ? "OCR" : page.classification.slice(0, 3)}</span>
              <span className={`block ${isSelected ? "text-[var(--bg)]" : page.extraction_status === "success" ? "text-[var(--text)]" : "text-[var(--red)]"}`}>{page.extraction_status === "success" ? "PASS" : "ERR"}</span>
            </span>
            {isHighlighted && (
              <span className="sr-only">highlighted</span>
            )}
          </button>
        )
      })}
    </nav>
  )
}
