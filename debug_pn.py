"""Debug script for page number detection."""
from ragparser.ir import Block, BlockRole, BoundingBox, Page
from ragparser.structure.doc_analyzer import DocumentStructureAnalyzer

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

# Page 2
blocks_p2 = [
    Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=2, role=BlockRole.UNKNOWN),
    Block(text='Methodology', bbox=BoundingBox(0, 50, 612, 80), page_number=2, role=BlockRole.UNKNOWN),
    Block(text='Body text here.', bbox=BoundingBox(0, 100, 612, 130), page_number=2, role=BlockRole.UNKNOWN),
    Block(text='42', bbox=BoundingBox(550, 760, 610, 788), page_number=2, role=BlockRole.UNKNOWN),
    Block(text='Page 2', bbox=BoundingBox(0, 760, 612, 788), page_number=2, role=BlockRole.UNKNOWN),
]
pages.append(Page(number=2, width=612, height=792, blocks=blocks_p2))

# Page 3
blocks_p3 = [
    Block(text='Report Header', bbox=BoundingBox(0, 0, 612, 30), page_number=3, role=BlockRole.UNKNOWN),
    Block(text='Results', bbox=BoundingBox(0, 50, 612, 80), page_number=3, role=BlockRole.UNKNOWN),
    Block(text='Body text here.', bbox=BoundingBox(0, 100, 612, 130), page_number=3, role=BlockRole.UNKNOWN),
    Block(text='42', bbox=BoundingBox(550, 760, 610, 788), page_number=3, role=BlockRole.UNKNOWN),
    Block(text='Page 3', bbox=BoundingBox(0, 760, 612, 788), page_number=3, role=BlockRole.UNKNOWN),
]
pages.append(Page(number=3, width=612, height=792, blocks=blocks_p3))

analyzer = DocumentStructureAnalyzer(min_pages_for_furniture=3)
analyzer._detect_page_numbers(pages)

for page in pages:
    for block in page.blocks:
        print(f'Page {page.number}: role={block.role.value}, text="{block.text}"')

pn_blocks = [b for p in pages for b in p.blocks if b.role == BlockRole.PAGE_NUMBER]
print(f'PAGE_NUMBER blocks: {len(pn_blocks)}')