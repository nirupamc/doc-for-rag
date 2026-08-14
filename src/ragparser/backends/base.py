"""Backend protocol for document extraction."""

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