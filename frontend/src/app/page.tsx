"use client"

import { useEffect, useState } from "react"
import { DocumentWorkspace } from "@/app/workspace"
import { UploadPanel } from "@/app/uploader"
import {
  checkHealth,
  type HealthResponse,
  type ParseResponse,
} from "@/lib/api"
import { StatusBadge } from "@/ui/status-badge"
import { useDisplay } from "@/app/display-provider"

export default function HomePage() {
  const { theme, crtEffects, setTheme, setCrtEffects } = useDisplay()
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthError, setHealthError] = useState(false)
  const [result, setResult] = useState<ParseResponse | null>(null)
  const [pdfFile, setPdfFile] = useState<File | null>(null)

  useEffect(() => {
    let active = true

    checkHealth()
      .then((response) => {
        if (active) setHealth(response)
      })
      .catch((error: unknown) => {
        console.debug("Backend health check failed", error)
        if (active) setHealthError(true)
      })

    return () => {
      active = false
    }
  }, [])

  const reset = () => {
    setResult(null)
    setPdfFile(null)
  }

  return (
    <main className="crt-grid min-h-screen px-2 py-2 md:px-4">
      <header className="system-header mb-2 flex min-h-16 flex-wrap items-center justify-between gap-4 border border-[var(--border)] bg-[var(--surface-raised)] px-4 py-2">
        <div className="flex items-center gap-3">
          <div className="brand-rail h-10 w-[3px] bg-[var(--text)]" aria-hidden="true" />
          <div>
            <h1 className="tech-heading text-3xl">RagParser</h1>
            <p className="font-interface text-[9px] uppercase tracking-[.17em] text-[var(--phosphor-dim)]">Document normalization terminal</p>
            <p className="font-terminal text-xs uppercase text-[var(--phosphor-dim)]">Structural extraction / OCR / layout analysis</p>
          </div>
        </div>
        <div className="ml-auto grid grid-cols-[auto_auto] gap-x-3 gap-y-0 font-terminal text-sm uppercase leading-tight">
          {health ? (
            <>
              <span className="phosphor-dot mt-1.5" aria-hidden="true" /><span className="text-[var(--phosphor-bright)]">Core::online</span>
              <span className="text-[var(--phosphor-dim)]">API::ready</span><span className={health.tesseract_available ? "text-[var(--phosphor)]" : "text-[var(--amber)]"}>{health.tesseract_available ? "OCR::ready" : "OCR::unavailable"}</span>
              <span className="sr-only"><StatusBadge status={health.tesseract_available ? "good" : "review"} size="sm" /></span>
            </>
          ) : healthError ? (
            <><span className="h-1.5 w-1.5 bg-[var(--red)]" /><span className="text-[var(--red)]">Core::offline</span><span className="text-[var(--phosphor-dim)]">API::unavailable</span></>
          ) : (
            <><span className="cursor-blink h-1.5 w-1.5 bg-[var(--phosphor)]" /><span>Core::handshake</span></>
          )}
        </div>
        <DisplayControls theme={theme} crtEffects={crtEffects} onTheme={setTheme} onEffects={setCrtEffects} />
      </header>

      {result && pdfFile ? (
        <DocumentWorkspace
          document={result.document}
          report={result.report}
          file={pdfFile}
          onReset={reset}
        />
      ) : (
        <UploadPanel
          onParseSuccess={(response, file) => {
            setResult(response)
            setPdfFile(file)
          }}
        />
      )}
      <div className="mt-2 flex justify-between border-t border-[var(--phosphor-very-dim)] pt-1 font-terminal text-xs uppercase text-[var(--phosphor-dim)]"><span>RGP//SYS.01</span><span>LOCAL WORKSTATION</span></div>
    </main>
  )
}

function DisplayControls({ theme, crtEffects, onTheme, onEffects }: {
  theme: "crt" | "mono"
  crtEffects: boolean
  onTheme: (theme: "crt" | "mono") => void
  onEffects: (enabled: boolean) => void
}) {
  return (
    <div className="display-controls border-l border-[var(--border)] pl-3 font-interface text-[9px] font-semibold uppercase tracking-[.1em]" aria-label="Display settings">
      <div className="grid grid-cols-[58px_auto] items-center gap-1">
        <span className="text-[var(--text-muted)]">Display //</span>
        <span className="flex gap-px bg-[var(--border)]">
          <DisplayButton active={theme === "crt"} label="CRT" onClick={() => onTheme("crt")} />
          <DisplayButton active={theme === "mono"} label="Mono" onClick={() => onTheme("mono")} />
        </span>
      </div>
      {theme === "crt" && (
        <div className="mt-1 grid grid-cols-[58px_auto] items-center gap-1">
          <span className="text-[var(--text-muted)]">CRT FX //</span>
          <span className="flex gap-px bg-[var(--border)]">
            <DisplayButton active={crtEffects} label="On" onClick={() => onEffects(true)} />
            <DisplayButton active={!crtEffects} label="Off" onClick={() => onEffects(false)} />
          </span>
        </div>
      )}
    </div>
  )
}

function DisplayButton({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) {
  return <button type="button" aria-pressed={active} onClick={onClick} className={`display-button px-2 py-1 ${active ? "is-active" : ""}`}>{label}</button>
}
