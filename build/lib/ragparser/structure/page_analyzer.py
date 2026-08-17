"""
Page-level structure analysis — deterministic heading detection.

Pure functions: evidence -> heading decision.
No pseudo-confidence; deterministic rule with explicit evidence.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from ragparser.ir import Block, BlockRole, Page
from ragparser.structure.signals import BlockStructureSignal


@dataclass(slots=True)
class HeadingEvidence:
    """Explicit evidence for heading classification."""
    font_size_ratio: Optional[float] = None  # block / body median
    is_bold: Optional[bool] = None
    line_count: int = 0
    char_count: int = 0
    isolation_ratio: float = 0.0  # vertical gap / page height
    is_all_caps: bool = False
    reasons: List[str] = field(default_factory=list)


class PageStructureAnalyzer:
    """
    Deterministic heading detection using explicit evidence and a documented rule.

    Rule: A block is HEADING if ALL of:
      (1) line_count <= 2 AND char_count <= 120
      (2) At least TWO of:
          - font_size_ratio >= 1.3 (native only)
          - is_bold == True (native only)
          - isolation_ratio >= 0.03 (vertical gap >= 3% page height)
          - is_all_caps == True (weak, only with other signals)

    Otherwise: PARAGRAPH.

    No pseudo-confidence; deterministic rule with explicit evidence.
    """

    def __init__(
        self,
        min_font_size_ratio: float = 1.3,
        max_heading_line_count: int = 2,
        max_heading_char_count: int = 120,
        min_isolation_ratio: float = 0.03,
    ) -> None:
        self._min_font_size_ratio = min_font_size_ratio
        self._max_line_count = max_heading_line_count
        self._max_char_count = max_heading_char_count
        self._min_isolation_ratio = min_isolation_ratio

    def analyze_page(self, page: "Page") -> "Page":
        """Mutate page blocks: assign HEADING role where detected."""
        if not page.blocks:
            return page

        # Estimate body font size from native blocks with font info
        body_font_size = self._estimate_body_font_size(page)

        for block in page.blocks:
            if block.role != BlockRole.UNKNOWN:
                continue  # Already labeled (e.g., from layout)

            evidence = self._collect_evidence(block, page, body_font_size)
            if self._is_heading(evidence):
                block.role = BlockRole.HEADING
            else:
                block.role = BlockRole.PARAGRAPH

        return page

    def _estimate_body_font_size(self, page) -> Optional[float]:
        """Estimate body font size from native blocks with font info."""
        sizes = []
        for block in page.blocks:
            if block.font_size and block.role == BlockRole.UNKNOWN:
                sizes.append(block.font_size)
        if not sizes:
            return None
        sizes.sort()
        return sizes[len(sizes) // 2]

    def _collect_evidence(self, block, page, body_font_size: Optional[float]):
        ev = HeadingEvidence()
        ev.line_count = block.text.count('\n') + 1
        ev.char_count = len(block.text.strip())

        # Font size ratio (native only)
        if block.font_size and body_font_size:
            ev.font_size_ratio = block.font_size / body_font_size

        # Bold
        ev.is_bold = block.is_bold

        # Isolation
        ev.isolation_ratio = self._compute_isolation(block, page)

        # All caps
        text = block.text.strip()
        ev.is_all_caps = text.isupper() and len(text) > 3

        # Build reasons
        if ev.font_size_ratio and ev.font_size_ratio >= 1.3:
            ev.reasons.append(f"font_size_ratio={ev.font_size_ratio:.2f}")
        if ev.is_bold:
            ev.reasons.append("bold")
        if ev.isolation_ratio >= 0.03:
            ev.reasons.append(f"isolation={ev.isolation_ratio:.2f}")
        if ev.is_all_caps:
            ev.reasons.append("all_caps")
        if ev.line_count <= 2:
            ev.reasons.append(f"lines={ev.line_count}")
        if ev.char_count <= 120:
            ev.reasons.append(f"chars={ev.char_count}")

        return ev

    def _is_heading(self, ev) -> bool:
        # Gate 1: short block
        if ev.line_count > 2 or ev.char_count > 120:
            return False

        # Gate 2: at least two strong signals
        signals = 0
        if ev.font_size_ratio and ev.font_size_ratio >= 1.3:
            signals += 1
        if ev.is_bold:
            signals += 1
        if ev.isolation_ratio >= 0.03:
            signals += 1
        # all_caps is weak, only counts with another signal

        return signals >= 2

    def _compute_isolation(self, block, page) -> float:
        if not block.bbox or page.height <= 0:
            return 0.0
        min_gap = float('inf')
        found_other = False
        for other in page.blocks:
            if other is block or not other.bbox:
                continue
            found_other = True
            gap = min(abs(other.bbox.y0 - block.bbox.y1), abs(other.bbox.y1 - block.bbox.y0))
            if gap < min_gap:
                min_gap = gap
        if not found_other:
            return 0.0
        return min_gap / page.height