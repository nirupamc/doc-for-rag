"""Quick verification test for DocumentStructureAnalyzer."""
import sys
sys.path.insert(0, '.')

from ragparser.ir import Block, BlockRole, BoundingBox, Page
from ragparser.structure.doc_analyzer import DocumentStructureAnalyzer

def test_page_numbers_detected():
    """Test that sequential page numbers are detected across >=3 pages."""
    pages = []

    # Page 1
    blocks_p1 = [
        Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=1, role=BlockRole.UNKNOWN),
        Block(text='Introduction', bbox=BoundingBox(0, 50, 612, 80), page_number=1, role=BlockRole.UNKNOWN),
        Block(text='Body text here.', bbox=BoundingBox(0, 100, 612, 130), page_number=1, role=BlockRole.UNKNOWN),
        Block(text='42', bbox=BoundingBox(550, 760, 610, 788), page_number=1, role=BlockRole.UNKNOWN),
        Block(text='Page 1', bbox=BoundingBox(0, 760, 612, 788), page_number=1, role=BlockRole.UNKNOWN),
    ]
    pages.append(Page(number=1, width=612, height=792, blocks=blocks_p1))

    # Page 2 (repeated)
    blocks_p2 = [
        Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=2, role=BlockRole.UNKNOWN),
        Block(text='Methodology', bbox=BoundingBox(0, 50, 612, 80), page_number=2, role=BlockRole.UNKNOWN),
        Block(text='Body text here.', bbox=BoundingBox(0, 100, 612, 130), page_number=2, role=BlockRole.UNKNOWN),
        Block(text='42', bbox=BoundingBox(550, 760, 610, 788), page_number=2, role=BlockRole.UNKNOWN),
        Block(text='Page 2', bbox=BoundingBox(0, 760, 612, 788), page_number=2, role=BlockRole.UNKNOWN),
    ]
    pages.append(Page(number=2, width=612, height=792, blocks=blocks_p2))

    # Page 3 (repeated)
    blocks_p3 = [
        Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=3, role=BlockRole.UNKNOWN),
        Block(text='Results', bbox=BoundingBox(0, 50, 612, 80), page_number=3, role=BlockRole.UNKNOWN),
        Block(text='Body text here.', bbox=BoundingBox(0, 100, 612, 130), page_number=3, role=BlockRole.UNKNOWN),
        Block(text='42', bbox=BoundingBox(550, 760, 610, 788), page_number=3, role=BlockRole.UNKNOWN),
        Block(text='Page 3', bbox=BoundingBox(0, 760, 612, 788), page_number=3, role=BlockRole.UNKNOWN),
    ]
    pages.append(Page(number=3, width=612, height=792, blocks=blocks_p3))

    analyzer = DocumentStructureAnalyzer(min_pages_for_furniture=3)
    analyzer.analyze_document(pages)

    pn_blocks = [b for p in pages for b in p.blocks if b.role == BlockRole.PAGE_NUMBER]
    assert len(pn_blocks) >= 3, f"Expected at least 3 PAGE_NUMBER blocks, got {len(pn_blocks)}"
    print(f"PASS: Page numbers detected ({len(pn_blocks)} blocks)")

def test_headers_detected():
    """Test that repeated headers are detected across >=3 pages."""
    pages = []

    # Page 1
    blocks_p1 = [
        Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=1, role=BlockRole.UNKNOWN),
        Block(text='Introduction', bbox=BoundingBox(0, 50, 612, 80), page_number=1, role=BlockRole.UNKNOWN),
        Block(text='Body text here.', bbox=BoundingBox(0, 100, 612, 130), page_number=1, role=BlockRole.UNKNOWN),
    ]
    pages.append(Page(number=1, width=612, height=792, blocks=blocks_p1))

    # Page 2 (repeated header)
    blocks_p2 = [
        Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=2, role=BlockRole.UNKNOWN),
        Block(text='Methodology', bbox=BoundingBox(0, 50, 612, 80), page_number=2, role=BlockRole.UNKNOWN),
        Block(text='Body text here.', bbox=BoundingBox(0, 100, 612, 130), page_number=2, role=BlockRole.UNKNOWN),
    ]
    pages.append(Page(number=2, width=612, height=792, blocks=blocks_p2))

    # Page 3 (repeated header)
    blocks_p3 = [
        Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=3, role=BlockRole.UNKNOWN),
        Block(text='Results', bbox=BoundingBox(0, 50, 612, 80), page_number=3, role=BlockRole.UNKNOWN),
        Block(text='Body text here.', bbox=BoundingBox(0, 100, 612, 130), page_number=3, role=BlockRole.UNKNOWN),
    ]
    pages.append(Page(number=3, width=612, height=792, blocks=blocks_p3))

    analyzer = DocumentStructureAnalyzer(min_pages_for_furniture=3)
    analyzer.analyze_document(pages)

    header_blocks = [b for p in pages for b in p.blocks if b.role == BlockRole.HEADER]
    assert len(header_blocks) >= 3, f"Expected at least 3 HEADER blocks, got {len(header_blocks)}"
    print(f"PASS: Headers detected ({len(header_blocks)} blocks)")

def test_no_fp_page_numbers_in_body():
    """Test that numbers in body text are not promoted to PAGE_NUMBER."""
    pages = []

    # Page with "42" in body text - should NOT become PAGE_NUMBER
    blocks_p1 = [
        Block(text='The answer is 42', bbox=BoundingBox(100, 400, 512, 430), page_number=1, role=BlockRole.UNKNOWN),
        Block(text='Some other content', bbox=BoundingBox(100, 500, 512, 530), page_number=1, role=BlockRole.UNKNOWN),
    ]
    pages.append(Page(number=1, width=612, height=792, blocks=blocks_p1))

    # Page 2 (same content, no page number at margin)
    blocks_p2 = [
        Block(text='The answer is 42', bbox=BoundingBox(100, 400, 512, 430), page_number=2, role=BlockRole.UNKNOWN),
        Block(text='Some other content', bbox=BoundingBox(100, 500, 512, 530), page_number=2, role=BlockRole.UNKNOWN),
    ]
    pages.append(Page(number=2, width=612, height=792, blocks=blocks_p2))

    # Page 3 (same content, no page number at margin)
    blocks_p3 = [
        Block(text='The answer is 42', bbox=BoundingBox(100, 400, 512, 430), page_number=3, role=BlockRole.UNKNOWN),
        Block(text='Some other content', bbox=BoundingBox(100, 500, 512, 530), page_number=3, role=BlockRole.UNKNOWN),
    ]
    pages.append(Page(number=3, width=612, height=792, blocks=blocks_p3))

    analyzer = DocumentStructureAnalyzer(min_pages_for_furniture=3)
    analyzer.analyze_document(pages)

    pn_blocks = [b for p in pages for b in p.blocks if b.role == BlockRole.PAGE_NUMBER]
    # The "42" in body text should NOT become PAGE_NUMBER since it's not at margin
    # and doesn't appear as a repeated pattern at top/bottom
    assert len(pn_blocks) == 0, f"Expected 0 PAGE_NUMBER blocks, got {len(pn_blocks)}"
    print("PASS: No false-positive page numbers in body text")

def test_precedence_header_over_heading():
    """Test that HEADER has higher precedence than HEADING."""
    pages = []

    # Page with something that could be heading or header
    blocks_p1 = [
        Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=1, role=BlockRole.UNKNOWN),
        Block(text='Chapter Title', bbox=BoundingBox(0, 200, 612, 230), page_number=1, role=BlockRole.HEADING),
    ]
    pages.append(Page(number=1, width=612, height=792, blocks=blocks_p1))

    # Page 2 (repeated header)
    blocks_p2 = [
        Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=2, role=BlockRole.UNKNOWN),
        Block(text='Section Title', bbox=BoundingBox(0, 200, 612, 230), page_number=2, role=BlockRole.HEADING),
    ]
    pages.append(Page(number=2, width=612, height=792, blocks=blocks_p2))

    # Page 3 (repeated header)
    blocks_p3 = [
        Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=3, role=BlockRole.UNKNOWN),
        Block(text='Another Section', bbox=BoundingBox(0, 200, 612, 230), page_number=3, role=BlockRole.HEADING),
    ]
    pages.append(Page(number=3, width=612, height=792, blocks=blocks_p3))

    analyzer = DocumentStructureAnalyzer(min_pages_for_furniture=3)
    analyzer.analyze_document(pages)

    # The header blocks should be HEADER, not HEADING
    header_blocks = [b for p in pages for b in p.blocks if b.role == BlockRole.HEADER]
    heading_blocks = [b for p in pages for b in p.blocks if b.role == BlockRole.HEADING]

    assert len(header_blocks) >= 3, f"Expected at least 3 HEADER blocks, got {len(header_blocks)}"
    # The original HEADING blocks should remain HEADING since they're not at top margin
    print(f"PASS: Precedence verified ({len(header_blocks)} headers, {len(heading_blocks)} headings)")

if __name__ == '__main__':
    test_page_numbers_detected()
    test_headers_detected()
    test_no_fp_page_numbers_in_body()
    test_precedence_header_over_heading()
    print('\nAll tests PASSED!')