"use client"

import type { PageData } from "@/lib/api"

interface PageInspectorProps {
  page: PageData
  highlightedBlock: number | null
  selectedBlock: number | null
  onBlockHover: (readingOrder: number | null) => void
  onBlockSelect: (readingOrder: number | null) => void
}

export function PageInspector({ page, highlightedBlock, selectedBlock, onBlockHover, onBlockSelect }: PageInspectorProps) {
  return (
    <section className="flex h-full flex-col">
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--phosphor-dim)] px-3 py-2">
        <h3 className="tech-heading text-xl">Page // {String(page.number).padStart(3, "0")}</h3>
        <p className="font-terminal text-sm uppercase text-[var(--phosphor-dim)]">
          {page.classification.replaceAll("_", " ")} · {page.extraction_method}/{page.extraction_status}
        </p>
      </header>
      {page.warnings.length > 0 && (
        <ul className="border-b border-[var(--amber)] bg-[var(--warning-bg)] px-3 py-2 font-terminal text-base text-[var(--amber)]">
          {page.warnings.map((warning) => <li key={warning}>WARN // {warning}</li>)}
        </ul>
      )}
      <div className="flex items-center justify-between border-b border-[var(--phosphor-dim)] px-3 py-2">
        <h4 className="tech-label">Block register</h4>
        <span className="font-display text-2xl">{String(page.blocks.length).padStart(3, "0")}</span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
        {page.blocks.map((block) => {
          const highlighted = highlightedBlock === block.reading_order
          const selected = selectedBlock === block.reading_order
          const confidence = block.confidence == null ? "—" : `${(block.confidence * 100).toFixed(0)}%`
          return (
            <button
              type="button"
              key={`${page.number}:${block.reading_order}`}
              className={`w-full border-b px-3 py-2 text-left transition-colors ${selected ? "border-[var(--text-strong)] bg-[var(--selected-bg)] shadow-[inset_3px_0_0_var(--text)]" : highlighted ? "border-[var(--text)] bg-[var(--hover-bg)]" : "border-[var(--border-subtle)] hover:bg-[var(--hover-bg)]"}`}
              onMouseEnter={() => onBlockHover(block.reading_order)}
              onMouseLeave={() => onBlockHover(null)}
              onClick={() => onBlockSelect(selected ? null : block.reading_order)}
            >
              <span className="font-interface flex items-center justify-between text-[9px] font-semibold uppercase tracking-[.1em]">
                <strong>Block::{String(page.number).padStart(3, "0")}.{String(block.reading_order + 1).padStart(2, "0")} · {block.role}</strong>
                <span className={selected ? "text-[var(--phosphor-bright)]" : "text-[var(--phosphor-dim)]"}>{selected ? "SELECTED" : confidence}</span>
              </span>
              <span className="mt-1.5 block whitespace-pre-wrap break-words font-terminal text-base leading-tight text-[var(--phosphor)]">{truncate(block.text, 180)}</span>
              {selected && (
                <span className="mt-2 grid grid-cols-2 border-t border-[var(--phosphor-very-dim)] pt-1 font-terminal text-sm text-[var(--phosphor-dim)]">
                  <span>X0 {block.bbox.x0.toFixed(1)} &nbsp; Y0 {block.bbox.y0.toFixed(1)}</span>
                  <span>X1 {block.bbox.x1.toFixed(1)} &nbsp; Y1 {block.bbox.y1.toFixed(1)}</span>
                </span>
              )}
            </button>
          )
        })}
        {page.blocks.length === 0 && <p className="tech-label p-4">No blocks extracted</p>}
      </div>
    </section>
  )
}

function truncate(text: string, length: number) { return text.length > length ? `${text.slice(0, length)}…` : text }
