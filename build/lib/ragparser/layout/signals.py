"""
Layout analysis signals — observable geometric facts about blocks on a page.

These are raw measurements with NO interpretation.
Classification logic lives in analyzer.py.
"""

from dataclasses import dataclass
from typing import List, Optional
from ragparser.ir import Block, BoundingBox


@dataclass(slots=True)
class BlockGeometry:
    """Observable geometry for a single block."""
    block_id: int
    x0: float
    y0: float
    x1: float
    y1: float
    width: float
    height: float
    area: float
    center_x: float
    center_y: float

    @classmethod
    def from_block(cls, block: Block, block_id: int) -> "BlockGeometry":
        if block.bbox is None:
            raise ValueError("Block has no bbox")
        b = block.bbox
        return cls(
            block_id=block_id,
            x0=b.x0,
            y0=b.y0,
            x1=b.x1,
            y1=b.y1,
            width=b.width,
            height=b.height,
            area=b.width * b.height,
            center_x=(b.x0 + b.x1) / 2,
            center_y=(b.y0 + b.y1) / 2,
        )


@dataclass(slots=True)
class LayoutSignals:
    """Observable geometric facts about blocks on a page."""
    page_width: float
    page_height: float
    block_count: int
    blocks: List["BlockGeometry"]

    # Derived
    has_blocks: bool = False
    single_block: bool = False

    def __post_init__(self) -> None:
        self.has_blocks = self.block_count > 0
        self.single_block = self.block_count == 1