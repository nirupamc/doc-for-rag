"""Backend protocols for document extraction."""

from typing import Protocol
from ragparser.ir import Page


class BackendProtocol(Protocol):
    """Protocol for extraction backends."""

    def extract_page(self, page: "fitz.Page", page_number: int) -> Page:
        """
        Extract content from a single page.

        Args:
            page: PyMuPDF page object
            page_number: 1-indexed page number

        Returns:
            Page with extracted blocks
        """
        ...

    def get_method_name(self) -> str:
        """Return the extraction method identifier."""
        ...


class OCRBackend(Protocol):
    """Protocol for OCR extraction backends."""

    def extract_page(self, page: "fitz.Page", page_number: int) -> Page:
        """
        Extract text from a page via OCR.

        Args:
            page: PyMuPDF page object
            page_number: 1-indexed page number

        Returns:
            Page with OCR-extracted blocks, extraction_status, extraction_method
        """
        ...

    def get_method_name(self) -> str:
        """Return 'ocr'."""
        ...

    def is_available(self) -> bool:
        """Check if OCR backend is installed and functional."""
        ...

    def get_dpi(self) -> int:
        """Return the DPI used for page rendering."""
        ...