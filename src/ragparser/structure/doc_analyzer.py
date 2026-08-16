"""
Document-level structure analysis — cross-page furniture detection.

Runs AFTER PageStructureAnalyzer (page-level HEADING/PARAGRAPH).

Responsibilities:
- HEADER: exact repeated running header across >= 3 pages
- FOOTER: exact repeated running footer across >= 3 pages
- PAGE_NUMBER: sequential pagination pattern with position + progression

Precedence (document-level > page-level):
    HEADER / FOOTER / PAGE_NUMBER
        >
HEADING / PARAGRAPH / UNKNOWN

Document-level furniture must NOT arbitrarily overwrite one another.
Once a block is confidently PAGE_NUMBER, HEADER must not later turn it into HEADER, etc.
"""

from ragparser.ir import BlockRole, Page


class DocumentStructureAnalyzer:
    """
    Document-level structure analysis using cross-page evidence.

    Assigns HEADER, FOOTER, or PAGE_NUMBER roles based on repeated
    patterns observed across multiple pages. Operates after
    PageStructureAnalyzer has assigned page-level roles.

    Does NOT modify block text, bbox, or any provenance fields.
    Only assigns or overwrites the `role` field when cross-page
    evidence is strong enough.
    """

    def __init__(self, min_pages_for_furniture: int = 3) -> None:
        self._min_pages_for_furniture = min_pages_for_furniture

    def analyze_document(self, pages: list[Page]) -> None:
        """
        Analyze all pages and assign document-level furniture roles.

        Must be called after PageStructureAnalyzer has run (page-level
        roles are already set). Mutates pages in-place.

        Architecture:
            PageStructureAnalyzer   ↓ HEADING / PARAGRAPH
            DocumentStructureAnalyzer ↓ HEADER / FOOTER / PAGE_NUMBER
        """
        if not pages:
            return

        # Stage 1: Detect PAGE_NUMBER candidates
        self._detect_page_numbers(pages)

        # Stage 2: Detect HEADERS (after page numbers, so PAGE_NUMBER
        # does not overwrite HEADER when evidence is strong enough)
        self._detect_headers(pages)

        # Stage 3: Detect FOOTERS (after headers, preserving existing
        # PAGE_NUMBER assignments where possible)
        self._detect_footers(pages)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text for cross-page comparison: trim + collapse whitespace."""
        return ' '.join(text.strip().split())

    @staticmethod
    def _extract_number_candidate(text: str) -> str | None:
        """Extract a pure number candidate from text.

        Handles forms: "42", "- 42 -", "Page 42"
        Returns just the numeric part, or None.
        """
        import re

        stripped = text.strip()

        # "42"
        if stripped.isdigit():
            return stripped

        # "Page 42"
        m = re.match(r'^Page\s+(\d+)$', stripped, re.IGNORECASE)
        if m:
            return m.group(1)

        # "- 42 -" or "42 -" etc.
        m = re.match(r'^(-?\d+)\s*-\s*$', stripped)
        if m:
            return m.group(1)

        # "42 of 100"
        m = re.match(r'^(\d+)\s+of\s+\d+$', stripped, re.IGNORECASE)
        if m:
            return m.group(1)

        # digit sequence at start
        m = re.match(r'^(\d+)\s', stripped)
        if m:
            return m.group(1)

        return None

    # ------------------------------------------------------------------
    # Stage 1 — Page numbers
    # ------------------------------------------------------------------

    def _detect_page_numbers(self, pages: list[Page]) -> None:
        """Detect PAGE_NUMBER blocks using conservative algorithm."""

        candidates = []  # (page_number, block, normalized_text, y_center, x_center, int_val)

        for page in pages:
            for block in page.blocks:
                # Only consider blocks not already assigned a higher-precedence furniture role
                if block.role == BlockRole.HEADER:
                    continue
                if block.role == BlockRole.FOOTER:
                    continue

                if not block.bbox or not page.height:
                    continue

                y_center = (block.bbox.y0 + block.bbox.y1) / 2
                # Page number at top margin (top 10%)
                is_top_margin = y_center < page.height * 0.10
                # Page number at bottom margin (bottom 10%)
                is_bottom_margin = y_center > page.height * 0.90

                if not (is_top_margin or is_bottom_margin):
                    continue

                # Page number should not span full width (body content typically does)
                width_pct = (block.bbox.x1 - block.bbox.x0) / page.width
                if width_pct > 0.70:
                    continue

                normalized = self._normalize_text(block.text)
                num_str = self._extract_number_candidate(normalized)
                if num_str is None:
                    continue

                try:
                    int_val = int(num_str)
                except ValueError:
                    continue

                x_center = (block.bbox.x0 + block.bbox.x1) / 2
                candidates.append((page.number, block, normalized, y_center, x_center, int_val))

        if not candidates:
            return

        # Group candidates by extracted integer value
        by_number = {}
        for page_num, block, norm_text, y_center, x_center, val in candidates:
            if val not in by_number:
                by_number[val] = []
            by_number[val].append((page_num, block, norm_text, y_center, x_center))

        # For each number, check:
        # 1. Appears across >= min_pages_for_furniture pages
        # 2. Consistent horizontal position (CV < 0.15)
        # 3. Plausible numeric progression (strictly increasing)
        for num_val, appearances in by_number.items():
            if len(appearances) < self._min_pages_for_furniture:
                continue

            # Sort by page number
            appearances.sort(key=lambda a: a[0])

            # Check horizontal consistency
            x_centers = [a[4] for a in appearances]
            x_mean = sum(x_centers) / len(x_centers)
            x_std = (sum((x - x_mean) ** 2 for x in x_centers) / len(x_centers)) ** 0.5
            x_cv = x_std / x_mean if x_mean > 0 else float('inf')

            if x_cv >= 0.15:
                continue

            # Check numeric progression (must be strictly increasing)
            page_nums = [a[0] for a in appearances]
            is_progression = all(
                later > earlier
                for earlier, later in zip(page_nums, page_nums[1:])
            )

            if not is_progression:
                continue

            # Confirmed page number pattern — assign to all appearances
            # PAGE_NUMBER has highest precedence; only set if not already HEADER
            for page_num, block, norm_text, y_center, x_center in appearances:
                if block.role != BlockRole.HEADER:
                    block.role = BlockRole.PAGE_NUMBER

    # ------------------------------------------------------------------
    # Stage 2 — Headers
    # ------------------------------------------------------------------

    def _detect_headers(self, pages: list[Page]) -> None:
        """Detect exact repeated running headers across >= 3 pages."""

        candidates = []  # (page_number, block, normalized_text, y_center, x_center)

        for page in pages:
            for block in page.blocks:
                # Skip if already assigned as PAGE_NUMBER (higher precedence)
                if block.role == BlockRole.PAGE_NUMBER:
                    continue

                if not block.bbox or not page.height:
                    continue

                y_center = (block.bbox.y0 + block.bbox.y1) / 2
                # Header is in top margin (top 15% of page)
                margin_threshold = page.height * 0.15
                if y_center >= margin_threshold:
                    continue

                text = block.text.strip()
                if not text:
                    continue

                normalized = self._normalize_text(text)

                # Skip if text is too short to be a meaningful header
                if len(normalized) < 3:
                    continue

                # Skip if text looks like a page number
                if self._extract_number_candidate(normalized):
                    continue

                x_center = (block.bbox.x0 + block.bbox.x1) / 2
                candidates.append((page.number, block, normalized, y_center, x_center))

        if not candidates:
            return

        # Group by normalized text
        by_text = {}
        for page_num, block, norm_text, y_center, x_center in candidates:
            if norm_text not in by_text:
                by_text[norm_text] = []
            # Store 5-element tuple: (page_num, block, norm_text, y_center, x_center)
            by_text[norm_text].append((page.number, block, norm_text, y_center, x_center))

        # For each text pattern, check:
        # 1. Appears across >= min_pages_for_furniture pages
        # 2. Similar top position across pages (CV < 0.10)
        # 3. Same/directional horizontal position (CV < 0.20)
        for norm_text, appearances in by_text.items():
            if len(appearances) < self._min_pages_for_furniture:
                continue

            # Sort by page number
            appearances.sort(key=lambda a: a[0])

            # Check similar top position: y_center should be consistent
            y_centers = [a[3] for a in appearances]
            y_mean = sum(y_centers) / len(y_centers)
            y_std = (sum((y - y_mean) ** 2 for y in y_centers) / len(y_centers)) ** 0.5
            y_cv = y_std / y_mean if y_mean > 0 else float('inf')

            # Vertical CV must be < 0.10 (10%) for header consistency
            if y_cv >= 0.10:
                continue

            # Check horizontal position consistency
            x_centers = [a[4] for a in appearances]
            x_mean = sum(x_centers) / len(x_centers)
            x_std = (sum((x - x_mean) ** 2 for x in x_centers) / len(x_centers)) ** 0.5
            x_cv = x_std / x_mean if x_mean > 0 else float('inf')

            # Horizontal CV must be < 0.20 for reasonable consistency
            if x_cv >= 0.20:
                continue

            # Confirmed header pattern — assign to all appearances
            # HEADER has highest precedence; only set if not already PAGE_NUMBER
            for page_num, block, norm_text, y_center, x_center in appearances:
                if block.role != BlockRole.PAGE_NUMBER:
                    block.role = BlockRole.HEADER

    # ------------------------------------------------------------------
    # Stage 3 — Footers
    # ------------------------------------------------------------------

    def _detect_footers(self, pages: list[Page]) -> None:
        """Detect exact repeated running footers across >= 3 pages."""

        candidates = []  # (page_number, block, normalized_text, y_center, x_center)

        for page in pages:
            for block in page.blocks:
                # Skip if already assigned as PAGE_NUMBER (highest precedence)
                if block.role == BlockRole.PAGE_NUMBER:
                    continue

                if not block.bbox or not page.height:
                    continue

                y_center = (block.bbox.y0 + block.bbox.y1) / 2
                # Footer is in bottom margin (bottom 15% of page)
                margin_threshold = page.height * 0.85
                if y_center <= margin_threshold:
                    continue

                text = block.text.strip()
                if not text:
                    continue

                normalized = self._normalize_text(text)

                # Skip if text looks like a page number
                if self._extract_number_candidate(normalized):
                    continue

                x_center = (block.bbox.x0 + block.bbox.x1) / 2
                candidates.append((page.number, block, normalized, y_center, x_center))

        if not candidates:
            return

        # Group by normalized text
        by_text = {}
        for page_num, block, norm_text, y_center, x_center in candidates:
            if norm_text not in by_text:
                by_text[norm_text] = []
            # Store 5-element tuple matching unpack below
            by_text[norm_text].append((page.number, block, norm_text, y_center, x_center))

        # For each text pattern, check:
        # 1. Appears across >= min_pages_for_furniture pages
        # 2. Similar bottom position across pages (CV < 0.10)
        # 3. Same/directional horizontal position (CV < 0.20)
        for norm_text, appearances in by_text.items():
            if len(appearances) < self._min_pages_for_furniture:
                continue

            # Sort by page number
            appearances.sort(key=lambda a: a[0])

            # Check similar bottom position: y_center should be consistent
            y_centers = [a[3] for a in appearances]
            y_mean = sum(y_centers) / len(y_centers)
            y_std = (sum((y - y_mean) ** 2 for y in y_centers) / len(y_centers)) ** 0.5
            y_cv = y_std / y_mean if y_mean > 0 else float('inf')

            # Vertical CV must be < 0.10 (10%) for footer consistency
            if y_cv >= 0.10:
                continue

            # Check horizontal position consistency
            x_centers = [a[4] for a in appearances]
            x_mean = sum(x_centers) / len(x_centers)
            x_std = (sum((x - x_mean) ** 2 for x in x_centers) / len(x_centers)) ** 0.5
            x_cv = x_std / x_mean if x_mean > 0 else float('inf')

            # Horizontal CV must be < 0.20 for reasonable consistency
            if x_cv >= 0.20:
                continue

            # Confirmed footer pattern — assign to all appearances
            # FOOTER has highest precedence among remaining roles
            # but must not overwrite an already-confirmed PAGE_NUMBER
            for page_num, block, norm_text, y_center, x_center in appearances:
                if block.role != BlockRole.PAGE_NUMBER:
                    block.role = BlockRole.FOOTER