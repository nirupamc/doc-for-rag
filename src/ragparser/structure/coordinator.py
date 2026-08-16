"""
Structure analysis coordinator — orchestrates page-level and document-level
structure analysis with explicit role precedence.

Pipeline order:
    extraction
    ↓
    layout
    ↓
    PageStructureAnalyzer           (page-level: HEADING / PARAGRAPH)
    ↓
    DocumentStructureAnalyzer       (document-level: HEADER / FOOTER / PAGE_NUMBER)
    ↓
    final structured IR

Precedence (document-level > page-level):
    HEADER / FOOTER / PAGE_NUMBER
        >
HEADING / PARAGRAPH / UNKNOWN

Key invariant: document-level furniture roles must NOT arbitrarily overwrite
one another. Once a block is confidently PAGE_NUMBER, HEADER detection must
not later turn it into HEADER, etc.
"""

from ragparser.layout import LayoutAnalyzer, LayoutMode, LayoutResult
from ragparser.structure.page_analyzer import PageStructureAnalyzer
from ragparser.structure.doc_analyzer import DocumentStructureAnalyzer


def run_structure_analysis(pages: list) -> None:
    """Run page-level then document-level structure analysis in order.

    Must be called after layout analysis has been completed on all pages.

    Args:
        pages: list of Page IR objects (mutated in-place)
        layout_results: list of LayoutResult from LayoutAnalyzer, one per page
    """
    # Stage 1: Page-level structure (HEADING / PARAGRAPH)
    page_analyzer = PageStructureAnalyzer()
    for i, page in enumerate(pages):
        # Each page already has blocks from extraction+layout
        # PageStructureAnalyzer assigns HEADING/PARAGRAPH roles
        page_analyzer.analyze_page(page)

    # Stage 2: Document-level structure (HEADER / FOOTER / PAGE_NUMBER)
    doc_analyzer = DocumentStructureAnalyzer(min_pages_for_furniture=3)
    doc_analyzer.analyze_document(pages)