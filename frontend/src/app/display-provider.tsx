"use client"

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react"

export type DisplayTheme = "crt" | "mono"

interface DisplayContextValue {
  theme: DisplayTheme
  crtEffects: boolean
  setTheme: (theme: DisplayTheme) => void
  setCrtEffects: (enabled: boolean) => void
}

const THEME_KEY = "ragparser.display.theme"
const EFFECTS_KEY = "ragparser.display.crtEffects"

const DisplayContext = createContext<DisplayContextValue | null>(null)

export function DisplayProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<DisplayTheme>("crt")
  const [crtEffects, setCrtEffects] = useState(true)
  const [preferencesLoaded, setPreferencesLoaded] = useState(false)

  useEffect(() => {
    const savedTheme = window.localStorage.getItem(THEME_KEY)
    const savedEffects = window.localStorage.getItem(EFFECTS_KEY)

    if (savedTheme === "crt" || savedTheme === "mono") setTheme(savedTheme)
    if (savedEffects === "true" || savedEffects === "false") setCrtEffects(savedEffects === "true")
    setPreferencesLoaded(true)
  }, [])

  useEffect(() => {
    const root = document.documentElement
    root.dataset.theme = theme
    root.dataset.crtEffects = String(theme === "crt" && crtEffects)

    if (preferencesLoaded) {
      window.localStorage.setItem(THEME_KEY, theme)
      window.localStorage.setItem(EFFECTS_KEY, String(crtEffects))
    }
  }, [theme, crtEffects, preferencesLoaded])

  const value = useMemo(
    () => ({ theme, crtEffects, setTheme, setCrtEffects }),
    [theme, crtEffects],
  )

  return <DisplayContext.Provider value={value}>{children}</DisplayContext.Provider>
}

export function useDisplay() {
  const context = useContext(DisplayContext)
  if (!context) throw new Error("useDisplay must be used within DisplayProvider")
  return context
}

