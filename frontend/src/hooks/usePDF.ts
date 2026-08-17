"use client"

import { useEffect, useState } from "react"

export function usePDF(file: File | null): string | null {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)

  useEffect(() => {
    if (!file) {
      setPdfUrl(null)
      return
    }

    const nextUrl = URL.createObjectURL(file)
    setPdfUrl(nextUrl)

    return () => {
      URL.revokeObjectURL(nextUrl)
    }
  }, [file])

  return pdfUrl
}
