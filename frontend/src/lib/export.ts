/**
 * Client-side export serialization for parsed documents.
 *
 * The backend currently exposes only /v1/health and /v1/parse — there is no
 * export endpoint. These serializers deterministically transform the actual
 * parse response into Markdown / plain text / JSON on the client. If a
 * server-side export API is added later, swap the generators here without
 * touching the export workspace UI.
 */

import type { BlockData, DocumentData, PageData, ParseResponse } from "@/lib/api"

export type ExportFormat = "markdown" | "text" | "json"

export const EXPORT_FORMATS: { id: ExportFormat; label: string; description: string }[] = [
  { id: "markdown", label: "Markdown", description: "Role-aware headings and paragraphs" },
  { id: "text", label: "Plain Text", description: "Normalized reading-order text" },
  { id: "json", label: "JSON", description: "Canonical document + report payload" },
]

/* Body content excludes running headers, footers and page numbers. */
const BODY_ROLES = new Set(["heading", "paragraph", "unknown"])

export function orderedBlocks(page: PageData): BlockData[] {
  return [...page.blocks].sort((a, b) => a.reading_order - b.reading_order)
}

export function pageToCleanText(page: PageData): string {
  return orderedBlocks(page)
    .filter((block) => block.type === "text" && BODY_ROLES.has(block.role) && block.text.trim().length > 0)
    .map((block) => block.text.trim())
    .join("\n\n")
}

export function documentToCleanText(document: DocumentData): string {
  return document.pages
    .map(pageToCleanText)
    .filter((text) => text.length > 0)
    .join("\n\n")
}

export function pageToMarkdown(page: PageData): string {
  const parts: string[] = []
  for (const block of orderedBlocks(page)) {
    const text = block.text.trim()
    if (!text || block.type !== "text") continue
    if (block.role === "heading") parts.push(`## ${text}`)
    else if (BODY_ROLES.has(block.role)) parts.push(text)
  }
  return parts.join("\n\n")
}

export function documentToMarkdown(document: DocumentData): string {
  const title = document.metadata?.title?.trim()
  const body = document.pages
    .map(pageToMarkdown)
    .filter((text) => text.length > 0)
    .join("\n\n")
  if (!body) return title ? `# ${title}\n` : ""
  return title ? `# ${title}\n\n${body}\n` : `${body}\n`
}

export function responseToJson(response: ParseResponse): string {
  return `${JSON.stringify(response, null, 2)}\n`
}

export function generateExport(format: ExportFormat, response: ParseResponse): string {
  switch (format) {
    case "markdown":
      return documentToMarkdown(response.document)
    case "text":
      return `${documentToCleanText(response.document)}\n`
    case "json":
      return responseToJson(response)
  }
}

export function exportMimeType(format: ExportFormat): string {
  switch (format) {
    case "markdown":
      return "text/markdown;charset=utf-8"
    case "text":
      return "text/plain;charset=utf-8"
    case "json":
      return "application/json;charset=utf-8"
  }
}

export function exportExtension(format: ExportFormat): string {
  switch (format) {
    case "markdown":
      return "md"
    case "text":
      return "txt"
    case "json":
      return "json"
  }
}

export function baseFileName(fileName: string): string {
  const trimmed = fileName.trim()
  return trimmed.toLowerCase().endsWith(".pdf") ? trimmed.slice(0, -4) : trimmed || "document"
}

export function downloadExport(fileName: string, format: ExportFormat, content: string): void {
  const blob = new Blob([content], { type: exportMimeType(format) })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = `${baseFileName(fileName)}.${exportExtension(format)}`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}
