"""Native PDF extraction backend using PyMuPDF."""

import fitz
from ragparser.ir import (
    Block,
    BlockType,
    BoundingBox,
    ExtractionMethod,
    Page,
)
from ragparser.backends.base import BackendProtocol


class DocumentLoader:
    """
    Responsible for document lifecycle and metadata.

    - Opens/closes document
    - Validates input
    - Exposes document metadata
    - Provides access to pages
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._doc: fitz.Document | None = None

    def open(self) -> None:
        """Open the document."""
        try:
            self._doc = fitz.open(self._path)
        except Exception as e:
            raise ValueError(f"Failed to open document: {e}") from e

    def close(self) -> None:
        """Close the document."""
        if self._doc:
            self._doc.close()
            self._doc = None

    def __enter__(self) -> "DocumentLoader":
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @property
    def doc(self) -> fitz.Document:
        if self._doc is None:
            raise RuntimeError("Document not opened. Call open() or use context manager.")
        return self._doc

    @property
    def page_count(self) -> int:
        return self.doc.page_count

    @property
    def metadata(self) -> dict:
        return self.doc.metadata

    def get_page(self, index: int) -> fitz.Page:
        """Get a page by 0-based index."""
        return self.doc[index]

    def iter_pages(self):
        """Iterate over all pages with 1-indexed page numbers."""
        for i in range(self.page_count):
            yield i + 1, self.doc[i]


class NativeExtractor:
    """
    Extracts native text blocks from a PyMuPDF page.

    Responsibilities:
    - Receives a page
    - Extracts native text blocks
    - Preserves positional information in canonical coordinates
    - Produces IR Page with blocks
    """

    def __init__(self) -> None:
        self._method = ExtractionMethod.NATIVE

    def extract_page(self, page: fitz.Page, page_number: int) -> Page:
        """
        Extract text blocks from a page.

        Args:
            page: PyMuPDF page object
            page_number: 1-indexed page number

        Returns:
            Page with extracted blocks in reading order
        """
        blocks = []
        reading_order = 0

        # Get page dimensions in points
        page_rect = page.rect
        page_width = page_rect.width
        page_height = page_rect.height

        # Extract text blocks using PyMuPDF's get_text("dict")
        # This returns blocks in reading order (top-to-bottom, left-to-right)
        text_dict = page.get_text("dict")

        for block_dict in text_dict.get("blocks", []):
            if block_dict["type"] != 0:  # 0 = text block
                continue

            block_text = ""
            block_bbox = None

            # Aggregate text from lines/spans
            for line in block_dict.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span["text"]
                if block_text and not block_text.endswith("\n"):
                    block_text += "\n"

            block_text = block_text.rstrip("\n")

            if not block_text.strip():
                continue

            # Convert PyMuPDF bbox (x0, y0, x1, y1) to canonical BoundingBox
            # PyMuPDF uses same convention: top-left origin, points, x right, y down
            bbox = block_dict["bbox"]
            block_bbox = BoundingBox(
                x0=bbox[0],
                y0=bbox[1],
                x1=bbox[2],
                y1=bbox[3],
            )

            block = Block(
                type=BlockType.TEXT,
                text=block_text,
                bbox=block_bbox,
                extraction_method=self._method,
                page_number=page_number,
                reading_order=reading_order,
            )
            blocks.append(block)
            reading_order += 1

        return Page(
            number=page_number,
            width=page_width,
            height=page_height,
            blocks=blocks,
            rotation=page.rotation,
        )

    def get_method_name(self) -> str:
        return "native"