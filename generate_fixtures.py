"""Generate deterministic M5 fixtures using PyMuPDF."""

import fitz
from pathlib import Path

OUTPUT_DIR = Path("tests/fixtures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_structured_doc():
    """Create a document with repeated header, heading, body, page numbers, footer."""
    doc = fitz.open()

    # Page size: 612 x 792 = Letter (points)
    doc = fitz.open()

    # ===== PAGE 1 =====
    page1 = doc.new_page(width=612, height=792)

    # Header (repeated across pages) - use default font
    page1.insert_text((72, 72), "Report Header")

    # Heading (larger font to trigger heading detection)
    page1.insert_text((72, 120), "Introduction", fontsize=18)

    # Body paragraphs
    page1.insert_text((72, 160), "This is the first paragraph of the introduction on page 1.")
    y = 180
    for i in range(3):
        page1.insert_text((72, y), f"This is body paragraph {i+1} on page 1.")
        y += 30

    # Page number at bottom margin
    page1.insert_text((550, 750), "1")

    # Footer (repeated across pages)
    page1.insert_text((72, 760), "Confidential")

    # ===== PAGE 2 =====
    page2 = doc.new_page(width=612, height=792)

    # Header (same text, same position)
    page2.insert_text((72, 72), "Report Header")

    # Different heading
    page2.insert_text((72, 120), "Methodology", fontsize=18)

    # Body
    page2.insert_text((72, 160), "This is the methodology section on page 2.")
    y = 190
    for i in range(2):
        page2.insert_text((72, y), f"Supporting detail {i+1} on page 2.")
        y += 30

    # Page number (sequential)
    page2.insert_text((550, 750), "2")

    # Footer (same text)
    page2.insert_text((72, 760), "Confidential")

    # ===== PAGE 3 =====
    page3 = doc.new_page(width=612, height=792)

    # Header (same text, same position)
    page3.insert_text((72, 72), "Report Header")

    # Different heading
    page3.insert_text((72, 120), "Results", fontsize=18)

    # Body
    page3.insert_text((72, 160), "This is the results section on page 3.")
    y = 190
    for i in range(2):
        page3.insert_text((72, y), f"Analysis point {i+1} on page 3.")
        y += 30

    # Page number (sequential)
    page3.insert_text((550, 750), "3")

    # Footer (same text)
    page3.insert_text((72, 760), "Confidential")

    doc.save(str(OUTPUT_DIR / "structured_doc.pdf"))
    doc.close()
    print("Created structured_doc.pdf")


def create_no_structure_doc():
    """Create a document where structure detection should fail (negative test)."""
    doc = fitz.open()

    # Page 1
    page1 = doc.new_page(width=612, height=792)

    # varying top text (no repeated header)
    page1.insert_text((72, 50), "Chapter 1: Getting Started")
    page1.insert_text((72, 90), "Welcome to the document")

    # Body paragraphs
    page1.insert_text((72, 130), "This is the first paragraph of content on page 1. It discusses various topics.")
    page1.insert_text((72, 160), "The second paragraph continues the discussion with more detailed information.")

    # Page 2
    page2 = doc.new_page(width=612, height=792)

    # Different varying top text
    page2.insert_text((72, 50), "Chapter 2: Advanced Topics")
    page2.insert_text((72, 90), "Deep dive into advanced concepts")

    # Body paragraphs (different content)
    page2.insert_text((72, 130), "This chapter covers advanced topics in detail. The material is technical in nature.")
    page2.insert_text((72, 160), "Readers should have prior knowledge of the subject matter before proceeding.")

    # Page 3
    page3 = doc.new_page(width=612, height=792)

    # Yet different top text
    page3.insert_text((72, 50), "Appendix A: References")
    page3.insert_text((72, 90), "Bibliography of sources")

    # Body paragraphs
    page3.insert_text((72, 130), "This appendix lists references cited throughout the document.")
    page3.insert_text((72, 160), "See the main text for citations and further reading.")

    # Numbers inside body text (should NOT become PAGE_NUMBER)
    page3.insert_text((300, 400), "The answer is 42")

    doc.save(str(OUTPUT_DIR / "no_structure.pdf"))
    doc.close()
    print("Created no_structure.pdf")


if __name__ == "__main__":
    create_structured_doc()
    create_no_structure_doc()
    print("\nAll fixtures created successfully!")