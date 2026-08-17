"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { Document, Page, pdfjs } from "react-pdf"
import type { PDFDocumentProxy } from "pdfjs-dist"
import { usePDF } from "@/hooks/usePDF"
import type { BlockData, PageData } from "@/lib/api"

pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.js"

interface PDFViewerProps {
  file: File
  selectedPage: number
  parsedPage: PageData
  showBboxes: boolean
  showLabels: boolean
  highlightedBlock: number | null
  selectedBlock: number | null
  onBlockHover: (readingOrder: number | null) => void
  onBlockSelect: (readingOrder: number | null) => void
}

export function PDFViewer({
  file,
  selectedPage,
  parsedPage,
  showBboxes,
  showLabels,
  highlightedBlock,
  selectedBlock,
  onBlockHover,
  onBlockSelect,
}: PDFViewerProps) {
  const pdfUrl = usePDF(file)
  const containerRef = useRef<HTMLDivElement>(null)
  const pageRef = useRef<HTMLDivElement>(null)
  const [containerWidth, setContainerWidth] = useState(0)
  const [renderedSize, setRenderedSize] = useState({ width: 0, height: 0 })
  const [pageCount, setPageCount] = useState(0)
  const [zoom, setZoom] = useState(1)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const element = containerRef.current
    if (!element) return
    const updateWidth = () => setContainerWidth(element.clientWidth)
    updateWidth()
    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width ?? element.clientWidth
      setContainerWidth(width)
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [pdfUrl])

  useEffect(() => {
    setZoom(1)
    setError(null)
  }, [file, selectedPage])

  const measureCanvas = useCallback(() => {
    const canvas = pageRef.current?.querySelector("canvas")
    if (canvas) {
      setRenderedSize({ width: canvas.clientWidth, height: canvas.clientHeight })
    }
  }, [])

  const handleDocumentLoad = (pdf: PDFDocumentProxy) => {
    setPageCount(pdf.numPages)
    setError(null)
  }

  const pageWidth = Math.max(1, containerWidth * zoom)
  const scaleX = parsedPage.width > 0 ? renderedSize.width / parsedPage.width : 0
  const scaleY = parsedPage.height > 0 ? renderedSize.height / parsedPage.height : 0

  if (!pdfUrl) return <p className="tech-label">Preparing local PDF…</p>

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2 border-y border-[var(--phosphor-dim)] bg-[var(--crt-panel)] px-2 py-1">
        <span className="font-terminal text-base uppercase text-[var(--phosphor)]">Source::page {String(selectedPage).padStart(3, "0")}{pageCount ? ` / ${String(pageCount).padStart(3, "0")}` : ""} &nbsp; View::{Math.round(zoom * 100)}</span>
        <div className="flex gap-px bg-[var(--phosphor-dim)]">
          <button type="button" onClick={() => setZoom(1)} className="tech-button border-0">Fit Width</button>
          <button type="button" onClick={() => setZoom((value) => Math.max(0.5, value - 0.1))} className="tech-button border-0 px-3" aria-label="Zoom out">−</button>
          <button type="button" onClick={() => setZoom((value) => Math.min(3, value + 0.1))} className="tech-button border-0 px-3" aria-label="Zoom in">+</button>
        </div>
      </div>

      {error && <p className="border-l-2 border-[var(--red)] bg-[var(--error-bg)] p-3 font-terminal text-base text-[var(--red)]">PDF::ERROR // {error}. Parsed data remains available in the inspector.</p>}

      <div ref={containerRef} className="pdf-stage relative min-h-[620px] overflow-auto border border-[var(--border-subtle)] bg-[var(--viewer-bg)] p-4 shadow-[inset_0_0_40px_rgba(0,0,0,.8)]">
        <Document
          file={pdfUrl}
          onLoadSuccess={handleDocumentLoad}
          onLoadError={(cause) => setError(cause.message)}
          loading={<p className="tech-label p-6">Loading PDF preview…</p>}
          error={<p className="p-6 font-mono text-xs text-[var(--red)]">Unable to render the PDF preview.</p>}
        >
          <div ref={pageRef} className="relative z-[10000] mx-auto w-fit" style={{ minHeight: renderedSize.height || undefined }}>
            <span className="absolute -left-2 -top-2 h-4 w-4 border-l border-t border-[var(--phosphor-dim)]" aria-hidden="true" />
            <span className="absolute -right-2 -top-2 h-4 w-4 border-r border-t border-[var(--phosphor-dim)]" aria-hidden="true" />
            <Page
              pageNumber={selectedPage}
              width={pageWidth}
              renderAnnotationLayer={false}
              renderTextLayer={false}
              onRenderSuccess={measureCanvas}
              onRenderError={(cause) => setError(cause.message)}
            />
            {renderedSize.width > 0 && renderedSize.height > 0 && (showBboxes || showLabels) && (
              <svg
                className="absolute left-0 top-0"
                width={renderedSize.width}
                height={renderedSize.height}
                viewBox={`0 0 ${renderedSize.width} ${renderedSize.height}`}
                aria-label="Parsed block overlays"
              >
                <title>Parsed block overlays</title>
                {parsedPage.blocks.map((block) => (
                  <BlockOverlay
                    key={`${parsedPage.number}:${block.reading_order}`}
                    block={block}
                    scaleX={scaleX}
                    scaleY={scaleY}
                    showBox={showBboxes}
                    showLabel={showLabels}
                    highlighted={highlightedBlock === block.reading_order}
                    selected={selectedBlock === block.reading_order}
                    onHover={onBlockHover}
                    onSelect={onBlockSelect}
                  />
                ))}
              </svg>
            )}
          </div>
        </Document>
      </div>
    </div>
  )
}

function BlockOverlay({
  block,
  scaleX,
  scaleY,
  showBox,
  showLabel,
  highlighted,
  selected,
  onHover,
  onSelect,
}: {
  block: BlockData
  scaleX: number
  scaleY: number
  showBox: boolean
  showLabel: boolean
  highlighted: boolean
  selected: boolean
  onHover: (readingOrder: number | null) => void
  onSelect: (readingOrder: number | null) => void
}) {
  const x = block.bbox.x0 * scaleX
  const y = block.bbox.y0 * scaleY
  const width = Math.max(0, (block.bbox.x1 - block.bbox.x0) * scaleX)
  const height = Math.max(0, (block.bbox.y1 - block.bbox.y0) * scaleY)
  const stroke = selected ? "var(--overlay-selected)" : highlighted ? "var(--overlay-hover)" : "var(--overlay)"

  return (
    <g
      className="cursor-pointer"
      onMouseEnter={() => onHover(block.reading_order)}
      onMouseLeave={() => onHover(null)}
      onClick={() => onSelect(selected ? null : block.reading_order)}
    >
      <rect x={x} y={y} width={width} height={height} fill="transparent" pointerEvents="all" />
      {showBox && <rect x={x} y={y} width={width} height={height} fill={selected ? "var(--overlay-fill)" : "none"} stroke={stroke} strokeWidth={selected || highlighted ? 2 : 1} style={selected ? { filter: "var(--overlay-glow)" } : undefined} pointerEvents="none" />}
      {showLabel && (
        <g pointerEvents="none">
          <rect x={x} y={Math.max(0, y - 13)} width={Math.max(42, block.role.length * 6)} height={13} fill="var(--overlay-label-bg)" stroke={stroke} strokeWidth="1" />
          <text x={x + 3} y={Math.max(10, y - 3)} fill={stroke} fontFamily="VT323, monospace" fontSize="10">{block.role.toUpperCase()}::{String(block.reading_order + 1).padStart(2, "0")}</text>
        </g>
      )}
    </g>
  )
}
