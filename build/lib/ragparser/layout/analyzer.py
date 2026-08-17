"""
Layout analyzer — geometric block ordering.

Pure functions: signals -> reading order.
No I/O, no PyMuPDF dependencies.
Non-fatal validation with fallback.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple
import math

from ragparser.ir import Page, LayoutMode
from ragparser.layout.signals import LayoutSignals, BlockGeometry


class ColumnRole(Enum):
    """Geometric role in two-column layout."""
    FULL_WIDTH_TOP = "full_width_top"
    FULL_WIDTH_BOTTOM = "full_width_bottom"
    LEFT_COLUMN = "left_column"
    RIGHT_COLUMN = "right_column"


@dataclass(slots=True)
class LayoutResult:
    """Result of layout analysis."""
    layout_mode: LayoutMode
    resolved_order: List[int]      # indices into page.blocks (final reading order)
    input_order: List[int]         # original extraction order (for debugging)
    reason: str
    signals: LayoutSignals
    column_roles: Optional[Dict[int, str]] = None  # block_id -> ColumnRole value


class LayoutAnalyzer:
    """
    Analyzes geometric block layout and assigns reading order.

    Single responsibility: geometry -> order.
    Does NOT care about extraction method (native vs OCR).
    Does NOT crash on invalid geometry -- warns and falls back.
    """

    def __init__(
        self,
        row_tolerance_pct: float = 0.02,           # 2% of page height
        column_gap_threshold_pct: float = 0.15,     # 15% of page width
        min_column_span_pct: float = 0.30,          # 30% of page height
        min_column_overlap_pct: float = 0.20,       # 20% of page height
        full_width_threshold_pct: float = 0.70,     # 70% of page width
    ) -> None:
        # Configurable thresholds (documented as experimental hypotheses)
        self._row_tolerance_pct = row_tolerance_pct
        self._column_gap_threshold_pct = column_gap_threshold_pct
        self._min_column_span_pct = min_column_span_pct
        self._min_column_overlap_pct = min_column_overlap_pct
        self._full_width_threshold_pct = full_width_threshold_pct

    def analyze_page(self, page: Page) -> LayoutResult:
        """Analyze a page's blocks and return reading order."""
        # Preserve input order for debugging
        input_order = list(range(len(page.blocks)))

        # Handle edge cases
        if not page.blocks:
            return LayoutResult(
                layout_mode=LayoutMode.SINGLE_COLUMN,
                resolved_order=[],
                input_order=[],
                reason="No blocks to order",
                signals=LayoutSignals(page_width=page.width, page_height=page.height, block_count=0, blocks=[]),
            )

        if len(page.blocks) == 1:
            signals = self._collect_signals(page)
            return LayoutResult(
                layout_mode=LayoutMode.SINGLE_COLUMN,
                resolved_order=[0],
                input_order=[0],
                reason="Single block",
                signals=signals,
            )

        # Collect and validate signals
        signals, valid_indices = self._collect_and_validate_signals(page)

        if not signals.has_blocks:
            # All blocks had invalid geometry
            return LayoutResult(
                layout_mode=LayoutMode.UNCERTAIN,
                resolved_order=input_order,  # preserve extraction order as fallback
                input_order=input_order,
                reason="All blocks have invalid geometry; preserving extraction order",
                signals=signals,
            )

        # If some blocks invalid, we'll order valid ones and append invalid at end
        invalid_indices = [i for i in range(len(page.blocks)) if i not in valid_indices]

        # Detect layout mode
        layout_mode, column_roles = self._detect_columns(signals)

        if layout_mode == LayoutMode.UNCERTAIN:
            resolved_valid = self._fallback_order(signals)
            reason = "Layout ambiguous; using conservative top-to-bottom fallback."
        elif layout_mode == LayoutMode.SINGLE_COLUMN:
            resolved_valid = self._single_column_order(signals)
            reason = "Single column; top-to-bottom with row clustering."
        elif layout_mode == LayoutMode.TWO_COLUMN:
            resolved_valid = self._two_column_order(signals, column_roles)
            reason = "Two columns detected; full-width top, then left column, then right column, then full-width bottom."

        # Combine: valid blocks in resolved order, then invalid blocks in input order
        resolved_order = resolved_valid + invalid_indices

        return LayoutResult(
            layout_mode=layout_mode,
            resolved_order=resolved_order,
            input_order=input_order,
            reason=reason,
            signals=signals,
            column_roles=column_roles,
        )

    def _collect_and_validate_signals(self, page: Page) -> Tuple[LayoutSignals, List[int]]:
        """Collect geometry and validate each block's bbox."""
        blocks = []
        valid_indices = []

        for i, block in enumerate(page.blocks):
            if block.bbox is None:
                # No geometry -- mark invalid
                continue

            b = block.bbox
            warnings = []

            # Validate coordinates
            if not (math.isfinite(b.x0) and math.isfinite(b.y0) and
                    math.isfinite(b.x1) and math.isfinite(b.y1)):
                warnings.append(f"Block {i}: non-finite coordinates")
            elif b.x1 < b.x0 or b.y1 < b.y0:
                warnings.append(f"Block {i}: x1<x0 or y1<y0")
            elif b.width <= 0 or b.height <= 0:
                warnings.append(f"Block {i}: zero/negative size")
            elif (b.x0 < -100 or b.y0 < -100 or
                  b.x1 > page.width + 100 or b.y1 > page.height + 100):
                warnings.append(f"Block {i}: extreme out-of-page coordinates")

            if warnings:
                # Add to page warnings for visibility
                if not hasattr(page, 'warnings'):
                    page.warnings = []
                page.warnings.extend(warnings)
                continue

            blocks.append(BlockGeometry.from_block(block, i))
            valid_indices.append(i)

        signals = LayoutSignals(
            page_width=page.width,
            page_height=page.height,
            block_count=len(blocks),
            blocks=blocks,
        )
        return signals, valid_indices

    def _detect_columns(self, signals: LayoutSignals) -> Tuple[LayoutMode, Optional[Dict[int, str]]]:
        """Conservative two-column detection with full-width top/bottom handling."""
        if signals.block_count < 4:
            return LayoutMode.SINGLE_COLUMN, None

        # Find horizontal clusters using center_x
        centers_x = sorted(b.center_x for b in signals.blocks)

        # Find largest gap between adjacent centers
        max_gap = 0
        gap_index = -1
        for i in range(len(centers_x) - 1):
            gap = centers_x[i + 1] - centers_x[i]
            if gap > max_gap:
                max_gap = gap
                gap_index = i

        # Gap must be significant
        if max_gap / signals.page_width < self._column_gap_threshold_pct:
            return LayoutMode.SINGLE_COLUMN, None

        # Split point
        split_x = (centers_x[gap_index] + centers_x[gap_index + 1]) / 2

        # First, classify all blocks as full-width or column
        column_roles = {}
        full_width_blocks = []
        column_candidates = []  # (block, is_left)

        for b in signals.blocks:
            block_width_pct = b.width / signals.page_width

            if block_width_pct >= self._full_width_threshold_pct:
                # Full-width block - defer top/bottom classification
                column_roles[b.block_id] = "full_width_deferred"
                full_width_blocks.append(b)
            elif b.center_x <= signals.page_width / 2:
                # Heuristic: use page center as rough split for initial classification
                column_roles[b.block_id] = "left_column"
                column_candidates.append((b, True))
            else:
                column_roles[b.block_id] = "right_column"
                column_candidates.append((b, False))

        # If no clear full-width blocks, try refined split
        if not full_width_blocks:
            split_x = (centers_x[gap_index] + centers_x[gap_index + 1]) / 2
            column_candidates = []
            for b in signals.blocks:
                if b.center_x <= split_x:
                    column_roles[b.block_id] = "left_column"
                    column_candidates.append((b, True))
                else:
                    column_roles[b.block_id] = "right_column"
                    column_candidates.append((b, False))
        else:
            # Re-classify non-full-width using the gap split
            for b in signals.blocks:
                if column_roles.get(b.block_id) == "full_width_deferred":
                    continue
                if b.center_x <= split_x:
                    column_roles[b.block_id] = "left_column"
                    column_candidates.append((b, True))
                else:
                    column_roles[b.block_id] = "right_column"
                    column_candidates.append((b, False))

        left_blocks = [b for b, is_left in column_candidates if is_left]
        right_blocks = [b for b, is_left in column_candidates if not is_left]

        # Validate column structure
        if len(left_blocks) < 2 or len(right_blocks) < 2:
            return LayoutMode.SINGLE_COLUMN, None

        # Check vertical span of each column
        left_span = max(b.y1 for b in left_blocks) - min(b.y0 for b in left_blocks)
        right_span = max(b.y1 for b in right_blocks) - min(b.y0 for b in right_blocks)

        if (left_span < self._min_column_span_pct * signals.page_height or
            right_span < self._min_column_span_pct * signals.page_height):
            return LayoutMode.SINGLE_COLUMN, None

        # Check vertical overlap
        left_y_min = min(b.y0 for b in left_blocks)
        left_y_max = max(b.y1 for b in left_blocks)
        right_y_min = min(b.y0 for b in right_blocks)
        right_y_max = max(b.y1 for b in right_blocks)

        overlap = min(left_y_max, right_y_max) - max(left_y_min, right_y_min)
        if overlap < self._min_column_overlap_pct * signals.page_height:
            return LayoutMode.SINGLE_COLUMN, None

        # Now classify full-width blocks as TOP or BOTTOM relative to column span
        column_y_min = min(left_y_min, right_y_min)
        column_y_max = max(left_y_max, right_y_max)
        column_center_y = (column_y_min + column_y_max) / 2

        for b in signals.blocks:
            if column_roles.get(b.block_id) == "full_width_deferred":
                if b.center_y <= column_center_y:
                    column_roles[b.block_id] = "full_width_top"
                else:
                    column_roles[b.block_id] = "full_width_bottom"

        # Check if any full-width block is ambiguously inside column region
        for b in signals.blocks:
            role = column_roles.get(b.block_id, "")
            if role.startswith("full_width"):
                if b.y0 < column_y_max and b.y1 > column_y_min:
                    # Full-width block overlaps column vertical span -- ambiguous
                    return LayoutMode.UNCERTAIN, None

        return LayoutMode.TWO_COLUMN, column_roles

    def _single_column_order(self, signals: LayoutSignals) -> List[int]:
        """Top-to-bottom with row clustering."""
        blocks = signals.blocks[:]
        row_tolerance = self._row_tolerance_pct * signals.page_height

        blocks.sort(key=lambda b: b.y0)

        rows = []
        if not blocks:
            return []

        current_row = [blocks[0]]
        for b in blocks[1:]:
            row_y0 = min(rb.y0 for rb in current_row)
            row_y1 = max(rb.y1 for rb in current_row)
            if b.y0 <= row_y1 + row_tolerance and b.y1 >= row_y0 - row_tolerance:
                current_row.append(b)
            else:
                rows.append(current_row)
                current_row = [b]
        rows.append(current_row)

        # Within each row, sort left-to-right
        reading_order = []
        for row in rows:
            row.sort(key=lambda b: b.x0)
            reading_order.extend([b.block_id for b in row])

        return reading_order

    def _two_column_order(self, signals: LayoutSignals, column_roles: Dict[int, str]) -> List[int]:
        """Full-width top, then left column top-to-bottom, then right column top-to-bottom, then full-width bottom."""
        full_width_top = [b for b in signals.blocks if column_roles.get(b.block_id) == "full_width_top"]
        full_width_bottom = [b for b in signals.blocks if column_roles.get(b.block_id) == "full_width_bottom"]
        left = [b for b in signals.blocks if column_roles.get(b.block_id) == "left_column"]
        right = [b for b in signals.blocks if column_roles.get(b.block_id) == "right_column"]

        def column_order(blocks):
            if not blocks:
                return []
            blocks.sort(key=lambda b: b.y0)
            row_tolerance = self._row_tolerance_pct * signals.page_height
            rows = []
            current_row = [blocks[0]]
            for b in blocks[1:]:
                row_y0 = min(rb.y0 for rb in current_row)
                row_y1 = max(rb.y1 for rb in current_row)
                if b.y0 <= row_y1 + row_tolerance and b.y1 >= row_y0 - row_tolerance:
                    current_row.append(b)
                else:
                    rows.append(current_row)
                    current_row = [b]
            rows.append(current_row)
            order = []
            for row in rows:
                row.sort(key=lambda b: b.x0)
                order.extend([b.block_id for b in row])
            return order

        # Order: full-width top, left column, right column, full-width bottom
        order = []
        order.extend(column_order(full_width_top))
        order.extend(column_order(left))
        order.extend(column_order(right))
        order.extend(column_order(full_width_bottom))
        return order

    def _fallback_order(self, signals: LayoutSignals) -> List[int]:
        """Conservative y-then-x sort for UNCERTAIN layouts."""
        blocks = sorted(signals.blocks, key=lambda b: (b.y0, b.x0))
        return [b.block_id for b in blocks]

    def _collect_signals(self, page: Page) -> LayoutSignals:
        """Collect observable geometry from valid blocks only."""
        blocks = []
        for i, block in enumerate(page.blocks):
            if block.bbox is None:
                continue
            try:
                blocks.append(BlockGeometry.from_block(block, i))
            except ValueError:
                continue
        return LayoutSignals(
            page_width=page.width,
            page_height=page.height,
            block_count=len(blocks),
            blocks=blocks,
        )