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


class PageClassification(Enum):
    """Page-level extraction strategy classification."""
    NATIVE = "native"
    OCR_REQUIRED = "ocr_required"
    EMPTY = "empty"
    SUSPICIOUS = "suspicious"


class ExtractionStatus(Enum):
    """Result of extraction execution."""
    SUCCESS = "success"
    FAILED = "failed"


class LayoutMode(Enum):
    """Detected geometric layout mode for a page."""
    SINGLE_COLUMN = "single_column"
    TWO_COLUMN = "two_column"
    UNCERTAIN = "uncertain"


class BlockRole(Enum):
    """Semantic role of a content block."""
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    UNKNOWN = "unknown"


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
    Structure fields (M5):
        - role: semantic role of the block
        - font_name: font family name (native extraction only)
        - font_size: font size in points (native extraction only)
        - is_bold: whether text is predominantly bold (native extraction only)
    """
    type: BlockType = BlockType.TEXT
    text: str = ""
    bbox: Optional[BoundingBox] = None
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE
    confidence: Optional[float] = None
    page_number: int = 0
    reading_order: int = 0
    role: BlockRole = BlockRole.UNKNOWN
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    is_bold: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "text": self.text,
            "bbox": self.bbox.to_dict() if self.bbox else None,
            "extraction_method": self.extraction_method.value,
            "confidence": self.confidence,
            "page_number": self.page_number,
            "reading_order": self.reading_order,
            "role": self.role.value,
            "font_name": self.font_name,
            "font_size": self.font_size,
            "is_bold": self.is_bold,
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
            role=BlockRole(data.get("role", "unknown")),
            font_name=data.get("font_name"),
            font_size=data.get("font_size"),
            is_bold=data.get("is_bold"),
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
        classification: page extraction classification (provisional M2)
        classification_reason: human-readable classification explanation (provisional M2)
        extraction_status: result of extraction execution (M3)
        extraction_method: actual extraction method used (M3)
        layout_mode: detected geometric layout mode (provisional M4)
        layout_reason: human-readable layout explanation (provisional M4)
        warnings: non-fatal diagnostics from extraction
    """
    number: int
    width: float
    height: float
    blocks: list[Block] = field(default_factory=list)
    rotation: int = 0
    classification: Optional[PageClassification] = None
    classification_reason: Optional[str] = None
    extraction_status: Optional[ExtractionStatus] = None
    extraction_method: Optional[ExtractionMethod] = None
    layout_mode: Optional[LayoutMode] = None
    layout_reason: Optional[str] = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "width": self.width,
            "height": self.height,
            "blocks": [b.to_dict() for b in self.blocks],
            "rotation": self.rotation,
            "classification": self.classification.value if self.classification else None,
            "classification_reason": self.classification_reason,
            "extraction_status": self.extraction_status.value if self.extraction_status else None,
            "extraction_method": self.extraction_method.value if self.extraction_method else None,
            "layout_mode": self.layout_mode.value if self.layout_mode else None,
            "layout_reason": self.layout_reason,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Page":
        classification = None
        if data.get("classification"):
            classification = PageClassification(data["classification"])
        extraction_status = None
        if data.get("extraction_status"):
            extraction_status = ExtractionStatus(data["extraction_status"])
        extraction_method = None
        if data.get("extraction_method"):
            extraction_method = ExtractionMethod(data["extraction_method"])
        layout_mode = None
        if data.get("layout_mode"):
            layout_mode = LayoutMode(data["layout_mode"])
        return cls(
            number=data["number"],
            width=data["width"],
            height=data["height"],
            blocks=[Block.from_dict(b) for b in data.get("blocks", [])],
            rotation=data.get("rotation", 0),
            classification=classification,
            classification_reason=data.get("classification_reason"),
            extraction_status=extraction_status,
            extraction_method=extraction_method,
            layout_mode=layout_mode,
            layout_reason=data.get("layout_reason"),
            warnings=data.get("warnings", []),
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