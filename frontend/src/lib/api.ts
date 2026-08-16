/**
 * API client for RagParser FastAPI backend.
 * 
 * Base URL configured via environment variable with local development fallback.
 * 
 * Usage:
 *   const health = await checkHealth()
 *   const result = await parseDocument(formData)
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_RAGPARSER_API_URL || "http://127.0.0.1:8000"

const debug = (msg: string, ...args: unknown[]) => {
  if (import.meta.env.DEV) {
    console.debug(`[ragparser-frontend] ${msg}`, ...args)
  }
}

export interface HealthResponse {
  status: "ok"
  tesseract_available: boolean
}

export interface BlockData {
  type: "text" | "image"
  text: string
  bbox: {
    x0: number
    y0: number
    x1: number
    y1: number
  }
  extraction_method: "native" | "ocr"
  confidence?: number | null
  page_number: number
  reading_order: number
  role: "unknown" | "heading" | "paragraph" | "header" | "footer" | "page_number"
  font_name?: string | null
  font_size?: number | null
  is_bold?: boolean | null
}

export interface PageData {
  number: number
  width: number
  height: number
  blocks: BlockData[]
  rotation: number
  classification: "native" | "ocr_required" | "empty" | "suspicious"
  classification_reason: string
  extraction_status: "success" | "failed"
  extraction_method: "native" | "ocr"
  layout_mode: "single_column" | "two_column" | "uncertain"
  layout_reason: string
  warnings: string[]
}

export interface DocumentData {
  source_path: string
  page_count: number
  pages: PageData[]
  metadata: {
    format: string
    title: string
    author: string
    subject: string
    keywords: string
    creator: string
    producer: string
    creationDate: string
    modDate: string
    trapped: string
    encryption: null | unknown
  }
  warnings: string[]
}

export interface ExtractionReport {
  source_path: string
  page_count: number
  classification_counts: {
    native: number
    ocr_required: number
    empty: number
    suspicious: number
  }
  extraction_method_counts: {
    native: number
    ocr: number
  }
  extraction_status_counts: {
    success: number
    failed: number
  }
  layout_mode_counts: {
    single_column: number
    two_column: number
    uncertain: number
  }
  block_role_counts: {
    unknown: number
    heading: number
    paragraph: number
    header: number
    footer: number
    page_number: number
    unknown: number
  }
  ocr_block_count: number
  blocks_with_confidence: number
  median_ocr_confidence: number | null
  min_ocr_confidence: number | null
  low_confidence_block_count: number
  pages_with_low_confidence: number[]
  warnings: { page: number; message: string }[]
  status: "good" | "review" | "poor"
  status_reasons: {
    category: "extraction" | "layout" | "ocr" | "structure" | "general"
    message: string
    count?: number | null
    page_numbers?: number[] | null
  }[]
  problem_pages: number[]
}

export interface ParseResponse {
  document: DocumentData
  report: ExtractionReport
}

export interface CheckHealthResponse {
  status: "ok"
  tesseract_available: boolean
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/v1/health`, {
    cache: "no-store",
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(
      `Health check failed: ${res.status} ${res.statusText} – ${text}`
    )
  }

  const data = (await res.json()) as CheckHealthResponse
  debug(`checkHealth: status=${data.status}, tesseract_available=${data.tesseract_available}`)
  return {
    status: data.status,
    tesseract_available: data.tesseract_available,
  }
}

export async function parseDocument(formData: FormData): Promise<ParseResponse> {
  const res = await fetch(`${API_BASE_URL}/v1/parse`, {
    method: "POST",
    body: formData,
    cache: "no-store",
  })

  if (!res.ok) {
    const text = await res.text()
    // Try to extract a human-readable message from the backend error
    let detail = `Request failed: ${res.status} ${res.statusText}`
    try {
      const errJson = JSON.parse(text)
      detail = errJson.detail || detail
    } catch {
      // not JSON – keep the generic message
    }
    throw new Error(detail)
  }

  const data = (await res.json()) as ParseResponse
  debug(
    `parseDocument: doc.pages=${data.document.pages.length}, report.status=${data.report.status}`
  )
  return data
}

export async function resetState(): Promise<void> {
  // In the server-side; the client just clears local state.
  // No-op on the client; kept for API compatibility.
  debug("resetState called (client-side clear recommended)")
}