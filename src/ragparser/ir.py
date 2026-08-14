"""
Canonical Intermediate Representation (IR) for RagParser.

Bounding Box Convention (canonical):
------------------------------------
- Origin: top-left of the page
- X increases to the right
- Y increases downward
- Units: PDF points (1/72 inch)
- x0, y0: top-left corner
- x1, y1: bottom-right corner

Backends are responsible for converting their native coordinate
representations into this canonical convention. The IR must never
leak backend-specific coordinate behavior.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class BlockType(Enum):
    """Type of content block."""
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"


class ExtractionMethod(Enum):
    """Method used to extract the block."""
    NATIVE = "native"
    OCR = "ocr"


@dataclass(slots=True)
class BoundingBox:
    """
    Canonical bounding box in PDF points.

    Convention:
        origin = top-left
        x increases to the right
        y increases downward
        units = PDF points
        x0, y0 = top-left
        x1, y1 = bottom-right

    All coordinates are absolute page coordinates (not normalized).
    """
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if self.x1 < self.x0:
            raise ValueError("x1 must be >= x0")
        if self.y1 < self.y0:
            raise ValueError("y1 must be >= y0")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    def to_dict(self) -> dict:
        return {
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BoundingBox":
        return cls(
            x0=data["x0"],
            y0=data["y0"],
            x1=data["x1"],
            y1=data["y1"],
        )


@dataclass(slots=True)
class Block:
    """
    A content block within a page.

    Provenance fields:
        - page_number: source page (1-indexed)
        - extraction_method: how this block was extracted
        - bbox: position in canonical coordinates
        - reading_order: sequential order on page (0 = unknown/not set)
    """
    type: BlockType = BlockType.TEXT
    text: str = ""
    bbox: Optional[BoundingBox] = None
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE
    confidence: Optional[float] = None
    page_number: int = 0
    reading_order: int = 0

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "text": self.text,
            "bbox": self.bbox.to_dict() if self.bbox else None,
            "extraction_method": self.extraction_method.value,
            "confidence": self.confidence,
            "page_number": self.page_number,
            "reading_order": self.reading_order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Block":
        bbox = BoundingBox.from_dict(data["bbox"]) if data.get("bbox") else None
        return cls(
            type=BlockType(data["type"]),
            text=data["text"],
            bbox=bbox,
            extraction_method=ExtractionMethod(data["extraction_method"]),
            confidence=data.get("confidence"),
            page_number=data["page_number"],
            reading_order=data.get("reading_order", 0),
        )


@dataclass(slots=True)
class Page:
    """
    A single document page.

    Attributes:
        number: 1-indexed page number
        width: page width in PDF points
        height: page height in PDF points
        blocks: content blocks on this page
        rotation: page rotation in degrees (0, 90, 180, 270)
    """
    number: int
    width: float
    height: float
    blocks: list[Block] = field(default_factory=list)
    rotation: int = 0

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "width": self.width,
            "height": self.height,
            "blocks": [b.to_dict() for b in self.blocks],
            "rotation": self.rotation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Page":
        return cls(
            number=data["number"],
            width=data["width"],
            height=data["height"],
            blocks=[Block.from_dict(b) for b in data.get("blocks", [])],
            rotation=data.get("rotation", 0),
        )


@dataclass(slots=True)
class Document:
    """
    Parsed document representation.

    Attributes:
        source_path: path to source document
        page_count: total number of pages
        pages: list of pages
        metadata: document-level metadata (title, author, etc.)
        warnings: non-fatal diagnostics from extraction
    """
    source_path: str
    page_count: int
    pages: list[Page] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "page_count": self.page_count,
            "pages": [p.to_dict() for p in self.pages],
            "metadata": self.metadata,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        return cls(
            source_path=data["source_path"],
            page_count=data["page_count"],
            pages=[Page.from_dict(p) for p in data.get("pages", [])],
            metadata=data.get("metadata", {}),
            warnings=data.get("warnings", []),
        )