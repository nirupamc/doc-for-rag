"""High-level DocumentParser API."""

from pathlib import Path
from ragparser.ir import Document
from ragparser.backends.native import DocumentLoader, NativeExtractor


class DocumentParser:
    """
    High-level document parsing API.

    Coordinates DocumentLoader and extraction backends to produce
    a canonical Document IR.
    """

    def __init__(self) -> None:
        self._extractor = NativeExtractor()

    def parse(self, path: str | Path) -> Document:
        """
        Parse a document and return the canonical IR.

        Args:
            path: Path to the document file

        Returns:
            Document IR with extracted content

        Raises:
            ValueError: If document cannot be opened or parsed
            FileNotFoundError: If path does not exist
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")

        with DocumentLoader(str(path)) as loader:
            doc = Document(
                source_path=str(path),
                page_count=loader.page_count,
                metadata=loader.metadata,
            )

            for page_number, page in loader.iter_pages():
                ir_page = self._extractor.extract_page(page, page_number)
                doc.pages.append(ir_page)

            return doc