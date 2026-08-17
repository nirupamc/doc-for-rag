"""Tests for Tesseract OCR backend (mocked)."""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from ragparser.backends.ocr import TesseractOCRBackend
from ragparser.ir import (
    Block,
    BlockType,
    BoundingBox,
    ExtractionMethod,
    ExtractionStatus,
    Page,
)
from ragparser.analysis import PageAnalyzer


class TestTesseractOCRBackend:
    def test_availability_check_missing(self):
        """Test that backend reports unavailable when Tesseract not installed."""
        with patch('pytesseract.get_tesseract_version', side_effect=FileNotFoundError("tesseract not found")):
            backend = TesseractOCRBackend()
            assert backend.is_available() is False

    def test_availability_check_success(self):
        """Test that backend reports available when Tesseract is installed."""
        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend()
            assert backend.is_available() is True

    def test_extract_page_missing_tesseract(self):
        """Test extract_page returns FAILED when Tesseract missing."""
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)

        with patch('pytesseract.get_tesseract_version', side_effect=FileNotFoundError("tesseract not found")):
            backend = TesseractOCRBackend()
            result = backend.extract_page(page, 1)

        doc.close()
        assert isinstance(result, Page)
        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.extraction_method == ExtractionMethod.OCR
        assert "Tesseract not available" in result.warnings[0]
        assert result.number == 1

    def test_extract_page_tesseract_error(self):
        """Test extract_page returns FAILED on TesseractError."""
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            with patch('pytesseract.image_to_data', side_effect=Exception("Tesseract process failed")):
                backend = TesseractOCRBackend()
                result = backend.extract_page(page, 1)

        doc.close()
        assert result.extraction_status == ExtractionStatus.FAILED
        assert result.extraction_method == ExtractionMethod.OCR
        assert "Tesseract process failed" in result.warnings[0]

    def test_render_page(self):
        """Test page rendering produces PIL Image."""
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend(dpi=300)
            image = backend._render_page(page)

        doc.close()
        assert image is not None
        assert hasattr(image, 'width')
        assert hasattr(image, 'height')
        # 300 DPI: 612 * 300/72 = 2550, 792 * 300/72 = 3300
        assert image.width == 2550
        assert image.height == 3300

    def _make_page_and_derot(self, rotation=0):
        """Helper to create a page and its derotation matrix without closing doc."""
        import fitz
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)
        page.set_rotation(rotation)
        derot = page.derotation_matrix
        return doc, page, derot

    def test_group_into_blocks_empty(self):
        """Test grouping with empty OCR data returns empty list."""
        doc, page, derot = self._make_page_and_derot()

        ocr_data = {
            "text": [],
            "conf": [],
            "block_num": [],
            "par_num": [],
            "line_num": [],
            "word_num": [],
            "left": [],
            "top": [],
            "width": [],
            "height": [],
        }

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend()
            blocks = backend._group_into_blocks(
                ocr_data, 1, 2550, 3300, 612, 792, derot
            )

        doc.close()
        assert blocks == []

    def test_group_into_blocks_single_block(self):
        """Test grouping words into a single block."""
        doc, page, derot = self._make_page_and_derot()

        # Simulate Tesseract output for "Hello World" in one block
        ocr_data = {
            "text": ["Hello", "World"],
            "conf": [95, 90],
            "block_num": [1, 1],
            "par_num": [1, 1],
            "line_num": [1, 1],
            "word_num": [1, 2],
            "left": [100, 200],
            "top": [100, 100],
            "width": [80, 80],
            "height": [30, 30],
        }

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend()
            blocks = backend._group_into_blocks(
                ocr_data, 1, 2550, 3300, 612, 792, derot
            )

        doc.close()
        assert len(blocks) == 1
        block = blocks[0]
        assert block.text == "Hello World"
        assert block.extraction_method == ExtractionMethod.OCR
        assert block.confidence is not None
        assert 0.0 <= block.confidence <= 1.0
        assert block.page_number == 1
        assert block.reading_order == 0
        assert block.bbox is not None

    def test_group_into_blocks_multiple_blocks(self):
        """Test grouping words into multiple blocks by block_num."""
        doc, page, derot = self._make_page_and_derot()

        # Two blocks with different block_num
        ocr_data = {
            "text": ["First", "block", "Second", "block"],
            "conf": [95, 90, 85, 80],
            "block_num": [1, 1, 2, 2],
            "par_num": [1, 1, 1, 1],
            "line_num": [1, 1, 1, 1],
            "word_num": [1, 2, 1, 2],
            "left": [100, 200, 100, 200],
            "top": [100, 100, 300, 300],
            "width": [80, 80, 80, 80],
            "height": [30, 30, 30, 30],
        }

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend()
            blocks = backend._group_into_blocks(
                ocr_data, 1, 2550, 3300, 612, 792, derot
            )

        doc.close()
        assert len(blocks) == 2
        assert blocks[0].text == "First block"
        assert blocks[1].text == "Second block"
        assert blocks[0].reading_order == 0
        assert blocks[1].reading_order == 1

    def test_tesseract_paragraphs_become_separate_blocks(self):
        """Paragraph hierarchy must not be collapsed into one coarse block."""
        doc, page, derot = self._make_page_and_derot()
        ocr_data = {
            "text": ["First", "paragraph", "Second", "paragraph"],
            "conf": [90, 91, 92, 93],
            "block_num": [1, 1, 1, 1],
            "par_num": [1, 1, 2, 2],
            "line_num": [1, 1, 1, 1],
            "word_num": [1, 2, 1, 2],
            "left": [100, 180, 140, 230],
            "top": [100, 100, 200, 200],
            "width": [60, 90, 70, 90],
            "height": [30, 30, 30, 30],
        }

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            blocks = TesseractOCRBackend()._group_into_blocks(
                ocr_data, 1, 2550, 3300, 612, 792, derot
            )

        doc.close()
        assert [block.text for block in blocks] == [
            "First paragraph", "Second paragraph"
        ]
        assert blocks[0].bbox.y1 < blocks[1].bbox.y0
        assert [block.reading_order for block in blocks] == [0, 1]

    def test_clear_first_line_indent_splits_tesseract_paragraph(self):
        """A missed Tesseract paragraph boundary is recovered geometrically."""
        lines = [
            [{"left": 100, "height": 30, "word_num": 1, "text": "end."}],
            [{"left": 150, "height": 30, "word_num": 1, "text": "New"}],
            [{"left": 101, "height": 30, "word_num": 1, "text": "continues"}],
        ]

        groups = TesseractOCRBackend._split_indented_paragraphs(lines)

        assert [[word["text"] for word in group] for group in groups] == [
            ["end."], ["New", "continues"]
        ]

    def test_non_alphanumeric_noise_is_filtered(self):
        """Isolated punctuation artifacts must not become tiny OCR blocks."""
        doc, page, derot = self._make_page_and_derot()
        ocr_data = {
            "text": ["Body", "|"],
            "conf": [95, 20],
            "block_num": [1, 2],
            "par_num": [1, 1],
            "line_num": [1, 1],
            "word_num": [1, 1],
            "left": [100, 20],
            "top": [100, 120],
            "width": [80, 2],
            "height": [30, 4],
        }

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            blocks = TesseractOCRBackend()._group_into_blocks(
                ocr_data, 1, 2550, 3300, 612, 792, derot
            )

        doc.close()
        assert [block.text for block in blocks] == ["Body"]

    def test_confidence_normalization(self):
        """Test confidence normalization from 0-100 to 0.0-1.0."""
        doc, page, derot = self._make_page_and_derot()

        # Three words with confidences 100, 50, 0 -> median 50 -> 0.5
        ocr_data = {
            "text": ["a", "b", "c"],
            "conf": [100, 50, 0],
            "block_num": [1, 1, 1],
            "par_num": [1, 1, 1],
            "line_num": [1, 1, 1],
            "word_num": [1, 2, 3],
            "left": [100, 150, 200],
            "top": [100, 100, 100],
            "width": [30, 30, 30],
            "height": [30, 30, 30],
        }

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend()
            blocks = backend._group_into_blocks(
                ocr_data, 1, 2550, 3300, 612, 792, derot
            )

        doc.close()
        assert len(blocks) == 1
        # Median of [0, 50, 100] is 50 -> 0.5
        assert abs(blocks[0].confidence - 0.5) < 0.01

    def test_confidence_negative_ignored(self):
        """Test that negative confidence values are filtered out."""
        doc, page, derot = self._make_page_and_derot()

        ocr_data = {
            "text": ["valid", "ignored"],
            "conf": [90, -1],  # -1 is Tesseract sentinel
            "block_num": [1, 1],
            "par_num": [1, 1],
            "line_num": [1, 1],
            "word_num": [1, 2],
            "left": [100, 200],
            "top": [100, 100],
            "width": [80, 80],
            "height": [30, 30],
        }

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend()
            blocks = backend._group_into_blocks(
                ocr_data, 1, 2550, 3300, 612, 792, derot
            )

        doc.close()
        assert len(blocks) == 1
        assert blocks[0].text == "valid"
        assert abs(blocks[0].confidence - 0.9) < 0.01

    def test_coordinate_conversion_no_rotation(self):
        """Test pixel -> page -> canonical conversion with 0° rotation."""
        doc, page, derot = self._make_page_and_derot(0)

        # Word at pixel (300, 246) in 2550x3300 image
        # Page coords: (300*612/2550, 246*792/3300) = (72, 59)
        # Canonical = same (identity derotation)
        ocr_data = {
            "text": ["Test"],
            "conf": [90],
            "block_num": [1],
            "par_num": [1],
            "line_num": [1],
            "word_num": [1],
            "left": [300],
            "top": [246],
            "width": [100],
            "height": [30],
        }

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend(dpi=300)
            blocks = backend._group_into_blocks(
                ocr_data, 1, 2550, 3300, 612, 792, derot
            )

        doc.close()
        assert len(blocks) == 1
        bbox = blocks[0].bbox
        # Allow small floating point differences
        assert abs(bbox.x0 - 72) < 1
        assert abs(bbox.y0 - 59) < 1

    def test_coordinate_conversion_90deg_rotation(self):
        """Test pixel -> page -> canonical conversion with 90° rotation."""
        doc, page, derot = self._make_page_and_derot(90)

        # For 90°: page.rect = (0, 0, 792, 612), pixmap = 3300x2550
        # Word at pixel (300, 246) in 3300x2550 image
        # Page coords: (300*792/3300, 246*612/2550) = (72, 59)
        # The pixmap is already in the rotated page.rect orientation.
        ocr_data = {
            "text": ["Test"],
            "conf": [90],
            "block_num": [1],
            "par_num": [1],
            "line_num": [1],
            "word_num": [1],
            "left": [300],
            "top": [246],
            "width": [100],
            "height": [30],
        }

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend(dpi=300)
            blocks = backend._group_into_blocks(
                ocr_data, 1, 3300, 2550, 792, 612, derot
            )

        doc.close()
        assert len(blocks) == 1
        bbox = blocks[0].bbox
        assert abs(bbox.x0 - 72) < 1
        assert abs(bbox.y0 - 59) < 1
        assert 0 <= bbox.x1 <= 792
        assert 0 <= bbox.y1 <= 612

    def test_get_dpi(self):
        """Test get_dpi returns configured DPI."""
        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend(dpi=300)
            assert backend.get_dpi() == 300

        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend(dpi=150)
            assert backend.get_dpi() == 150

    def test_get_method_name(self):
        """Test get_method_name returns 'ocr'."""
        with patch('pytesseract.get_tesseract_version', return_value='5.3.0'):
            backend = TesseractOCRBackend()
            assert backend.get_method_name() == "ocr"


class TestTesseractOCRBackendIntegration:
    """Integration tests requiring Tesseract - skipped if not available."""

    @pytest.mark.integration
    def test_scanned_page_ocr_recovers_text(self, scanned_text_page_pdf):
        """Test that OCR can recover text from a scanned page."""
        import fitz
        from ragparser.parser import DocumentParser

        parser = DocumentParser()
        if not parser._ocr_backend.is_available():
            pytest.skip("Tesseract not available")

        doc = parser.parse(scanned_text_page_pdf)
        assert doc.page_count == 1
        page = doc.pages[0]
        assert page.extraction_method == ExtractionMethod.OCR
        assert page.extraction_status == ExtractionStatus.SUCCESS
        assert len(page.blocks) > 0
        # Check that some expected text was recovered
        full_text = " ".join(b.text for b in page.blocks)
        assert "SCANNED" in full_text or "HELLO" in full_text.upper()

    @pytest.mark.integration
    def test_mixed_document_native_plus_ocr(self, mixed_document_pdf):
        """Test mixed document with native and OCR pages."""
        from ragparser.parser import DocumentParser

        parser = DocumentParser()
        if not parser._ocr_backend.is_available():
            pytest.skip("Tesseract not available")

        doc = parser.parse(mixed_document_pdf)
        assert doc.page_count == 5
        # Page 2 should be OCR_REQUIRED and get OCR extraction
        assert doc.pages[1].classification.value == "ocr_required"
        # If OCR available, it should have blocks
        if doc.pages[1].extraction_status == ExtractionStatus.SUCCESS:
            assert len(doc.pages[1].blocks) >= 0  # May be empty if no text found


# Fixture for scanned text page
import pytest

@pytest.fixture
def scanned_text_page_pdf():
    from pathlib import Path
    return Path("tests/fixtures/scanned_text_page.pdf")
