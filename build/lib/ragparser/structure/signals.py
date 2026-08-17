"""
Structure analysis signals — observable facts for structure classification.

These are raw measurements with NO interpretation.
Classification logic lives in page_analyzer.py and doc_analyzer.py.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from ragparser.ir import Block, BoundingBox, BlockRole


@dataclass(slots=True)
class BlockStructureSignal:
    """Observable facts about a block for structure analysis."""
    block_id: int
    text: str
    normalized_text: str  # trimmed, whitespace collapsed
    bbox: BoundingBox
    reading_order: int
    role: BlockRole  # current role (from heading detection)
    font_size: Optional[float]
    font_name: Optional[str]
    is_bold: Optional[bool]
    line_count: int
    char_count: int
    # Geometric
    relative_y_top: float      # y0 / page_height (0.0-1.0)
    relative_y_bottom: float   # y1 / page_height
    relative_x_center: float   # center_x / page_width
    width_pct: float           # width / page_width
    height_pct: float          # height / page_height
    # Page geometry
    page_width: float
    page_height: float


@dataclass(slots=True)
class PageStructureSignals:
    """Observable structure facts for a single page."""
    page_number: int
    blocks: List[BlockStructureSignal]


def normalize_text(text: str) -> str:
    """Normalize text for comparison: trim, collapse whitespace."""
    return ' '.join(text.strip().split())