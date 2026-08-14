"""High-level DocumentParser API."""

from pathlib import Path
from ragparser.ir import Document
from ragparser.backends.native import DocumentLoader, NativeExtractor
from ragparser.analysis import PageAnalyzer, ExtractionRouter, ExtractionStrategy


class DocumentParser:
    """
    High-level document parsing API.

    Coordinates DocumentLoader, PageAnalyzer, ExtractionRouter,
    and extraction backends to produce a canonical Document IR.
    """

    def __init__(self) -> None:
        self._analyzer = PageAnalyzer()
        self._router = ExtractionRouter()
        self._native_extractor = NativeExtractor()

    def parse(self, path: str | Path) -> Document:
        """
        Parse a document and return the canonical IR.

        Performs per-page analysis and routes to appropriate extraction strategy.

        Args:
            path: Path to the document file

        Returns:
            Document IR with extracted content and page classifications

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
                # Analyze page (cheap inspection)
                analysis = self._analyzer.analyze_page(page, page_number)

                # Route to extraction strategy
                strategy = self._router.route(analysis)

                # Extract based on strategy
                ir_page = self._extract_page(page, page_number, strategy, analysis)

                doc.pages.append(ir_page)

            return doc

    def _extract_page(
        self,
        page: "fitz.Page",
        page_number: int,
        strategy: ExtractionStrategy,
        analysis,
    ) -> "Page":
        """Extract page content based on strategy."""
        from ragparser.ir import Page

        page_width = page.rect.width
        page_height = page.rect.height

        if strategy == ExtractionStrategy.NATIVE:
            # Full native extraction
            ir_page = self._native_extractor.extract_page(page, page_number)

        elif strategy == ExtractionStrategy.OCR_REQUIRED:
            # Placeholder for M3 OCR
            ir_page = Page(
                number=page_number,
                width=page_width,
                height=page_height,
                blocks=[],
            )
            ir_page.warnings = ["OCR required but not available in M2"]

        elif strategy == ExtractionStrategy.EMPTY:
            # No extraction needed
            ir_page = Page(
                number=page_number,
                width=page_width,
                height=page_height,
                blocks=[],
            )

        elif strategy == ExtractionStrategy.SUSPICIOUS:
            # Extract what we can, add warning
            ir_page = self._native_extractor.extract_page(page, page_number)
            ir_page.warnings = [f"Classification: suspicious — {analysis.reason}"]

        else:
            # Fallback
            ir_page = Page(
                number=page_number,
                width=page_width,
                height=page_height,
                blocks=[],
            )

        # Attach classification info to IR (provisional M2)
        ir_page.classification = analysis.classification
        ir_page.classification_reason = analysis.reason
        # Note: signals not attached to avoid IR bloat; available via analysis

        return ir_page

    def analyze(self, path: str | Path) -> list:
        """
        Analyze document pages without full extraction.

        Returns list of ClassificationResult for each page.
        Useful for CLI inspection without full parsing.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {path}")

        results = []
        with DocumentLoader(str(path)) as loader:
            for page_number, page in loader.iter_pages():
                analysis = self._analyzer.analyze_page(page, page_number)
                results.append(analysis)
        return results