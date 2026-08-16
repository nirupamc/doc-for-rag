/* PageNavigator — Scrollable sidebar showing page summaries.

 * For every page shows compact information:
 *   Page N
 *   CLASSIFICATION
 *   STATUS
 *
 * Clicking a page updates the selected page in the inspector.
 */

"use client"

import { useState } from "react"

export interface PageNavigatorProps {
  pages: { number: number; classification: string; extraction_status: string }[]
  selected: number
  onSelect: (pageNumber: number) => void
}

export function PageNavigator({ pages, selected, onSelect }: PageNavigatorProps) {
  return (
    <div className="space-y-1">
      {pages.map((page) => {
        const isSelected = page.number === selected
        return (
          <button
            key={page.number}
            onClick={() => onSelect(page.number)}
            className={`
              w-full flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
              ${isSelected ? "bg-primary-100 text-primary-900" : "text-muted-foreground hover:bg-muted-hover"}
            `}
            aria-selected={isSelected}
            role="button"
            tabIndex={isSelected ? 0 : -1}
          >
            <span>
              Page {page.number}{" "}
              <span className="ml-1">
                {page.classification.toUpperCase()}
              </span>
            </span>
            <span className="text-xs">{page.extraction_status.toUpperCase()}</span>
          </button>
        )
      })}
    </div>
  )
}