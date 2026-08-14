"""Tests for page analysis: signals, classification, analyzer, router, integration."""

import pytest
from ragparser.analysis import (
    PageSignals,
    PageClassification,
    ClassificationResult,
    classify,
    PageAnalyzer,
    ExtractionRouter,
    ExtractionStrategy,
)
from ragparser.ir import (
    PageClassification as IRPageClassification,
    ExtractionMethod,
    ExtractionStatus,
)
from ragparser.parser import DocumentParser


class TestPageSignals:
    def test_defaults(self):
        signals = PageSignals()
        assert signals.native_char_count == 0
        assert signals.image_count == 0
        assert signals.has_native_text is False
        assert signals.has_images is False
        assert signals.has_drawings is False

    def test_post_init_sets_derived_booleans(self):
        signals = PageSignals(
            native_char_count=10,
            image_count=1,
            drawing_count=2,
            page_width=612,
            page_height=792,
        )
        assert signals.has_native_text is True
        assert signals.has_images is True
        assert signals.has_drawings is True
        assert signals.page_area == 612 * 792

    def test_to_dict_from_dict_roundtrip(self):
        signals = PageSignals(
            native_char_count=100,
            native_block_count=3,
            native_text_sample="Hello",
            image_count=2,
            largest_image_coverage=0.5,
            summed_image_area_ratio=0.6,
            drawing_count=1,
            drawing_coverage_ratio=0.1,
            page_width=612,
            page_height=792,
        )
        data = signals.to_dict()
        restored = PageSignals.from_dict(data)
        assert restored.native_char_count == 100
        assert restored.largest_image_coverage == 0.5


class TestClassification:
    def test_classify_empty(self):
        signals = PageSignals(page_width=612, page_height=792)
        result = classify(signals)
        assert result.classification == PageClassification.EMPTY
        assert "No native text, images, or vector graphics" in result.reason

    def test_classify_ocr_required(self):
        signals = PageSignals(
            native_char_count=0,
            image_count=1,
            largest_image_coverage=0.9,
            page_width=612,
            page_height=792,
        )
        result = classify(signals)
        assert result.classification == PageClassification.OCR_REQUIRED
        assert "No native text" in result.reason
        assert "90.0%" in result.reason

    def test_classify_ocr_required_small_image_suspicious(self):
        signals = PageSignals(
            native_char_count=0,
            image_count=1,
            largest_image_coverage=0.1,
            page_width=612,
            page_height=792,
        )
        result = classify(signals)
        assert result.classification == PageClassification.SUSPICIOUS
        assert "small image" in result.reason

    def test_classify_native_substantial_text(self):
        signals = PageSignals(
            native_char_count=100,
            largest_image_coverage=0.1,
            page_width=612,
            page_height=792,
        )
        result = classify(signals)
        assert result.classification == PageClassification.NATIVE
        assert "Native text" in result.reason

    def test_classify_native_text_with_incidental_images(self):
        signals = PageSignals(
            native_char_count=50,
            largest_image_coverage=0.2,
            page_width=612,
            page_height=792,
        )
        result = classify(signals)
        assert result.classification == PageClassification.NATIVE

    def test_classify_suspicious_text_with_large_image(self):
        signals = PageSignals(
            native_char_count=42,
            largest_image_coverage=0.9,
            page_width=612,
            page_height=792,
        )
        result = classify(signals)
        assert result.classification == PageClassification.SUSPICIOUS
        assert "large image covers" in result.reason

    def test_classify_suspicious_garbled_text(self):
        # Heuristic only catches U+FFFD replacement character.
        # PyMuPDF may render as middle dots (U+00B7) instead.
        # This test documents the current limitation.
        signals = PageSignals(
            native_char_count=20,
            native_text_sample="\uFFFD\uFFFD\uFFFD \uFFFD",
            largest_image_coverage=0.0,
            page_width=612,
            page_height=792,
        )
        result = classify(signals)
        assert result.classification == PageClassification.SUSPICIOUS
        assert "replacement char" in result.reason.lower()

    def test_classify_middle_dots_not_suspicious(self):
        """Middle dots (U+00B7) from PyMuPDF rendering are NOT caught by heuristic."""
        signals = PageSignals(
            native_char_count=12,
            native_text_sample="\u00B7\u00B7\u00B7 \u00B7\u00B7",
            largest_image_coverage=0.0,
            page_width=612,
            page_height=792,
        )
        result = classify(signals)
        # Not suspicious - middle dots pass through as native text
        assert result.classification == PageClassification.NATIVE

    def test_classify_sparse_text_alone_not_suspicious(self):
        """Sparse text alone should NOT be suspicious (legitimate title pages, etc.)."""
        signals = PageSignals(
            native_char_count=5,
            largest_image_coverage=0.0,
            page_width=612,
            page_height=792,
        )
        result = classify(signals)
        # Sparse text with no image -> NATIVE (not suspicious)
        assert result.classification == PageClassification.NATIVE

    def test_classify_drawings_only(self):
        signals = PageSignals(
            drawing_count=2,
            drawing_coverage_ratio=0.5,
            page_width=612,
            page_height=792,
        )
        result = classify(signals)
        assert result.classification == PageClassification.SUSPICIOUS
        assert "Vector graphics" in result.reason

    def test_classification_result_contains_signals(self):
        signals = PageSignals(native_char_count=10, page_width=612, page_height=792)
        result = classify(signals)
        assert result.signals is signals
        assert isinstance(result.reason, str)
        assert len(result.reason) > 0


class TestPageAnalyzer:
    def test_analyze_clean_native(self, simple_pdf):
        import fitz
        doc = fitz.open(str(simple_pdf))
        page = doc[0]
        analyzer = PageAnalyzer()
        result = analyzer.analyze_page(page, 1)
        doc.close()

        assert result.classification == PageClassification.NATIVE
        assert result.signals.native_char_count > 0
        assert result.signals.image_count == 0

    def test_analyze_empty_page(self, empty_page_pdf):
        import fitz
        doc = fitz.open(str(empty_page_pdf))
        page = doc[0]
        analyzer = PageAnalyzer()
        result = analyzer.analyze_page(page, 1)
        doc.close()

        assert result.classification == PageClassification.EMPTY
        assert result.signals.native_char_count == 0
        assert result.signals.image_count == 0

    def test_analyze_scanned_page(self, scanned_page_pdf):
        import fitz
        doc = fitz.open(str(scanned_page_pdf))
        page = doc[0]
        analyzer = PageAnalyzer()
        result = analyzer.analyze_page(page, 1)
        doc.close()

        assert result.classification == PageClassification.OCR_REQUIRED
        assert result.signals.native_char_count == 0
        assert result.signals.image_count == 1
        assert result.signals.largest_image_coverage >= 0.5

    def test_analyze_mixed_page(self, mixed_page_pdf):
        import fitz
        doc = fitz.open(str(mixed_page_pdf))
        page = doc[0]
        analyzer = PageAnalyzer()
        result = analyzer.analyze_page(page, 1)
        doc.close()

        assert result.classification == PageClassification.NATIVE
        assert result.signals.native_char_count > 0
        assert result.signals.image_count == 1
        assert result.signals.largest_image_coverage < 0.3

    def test_analyze_garbled_page(self, garbled_page_pdf):
        import fitz
        doc = fitz.open(str(garbled_page_pdf))
        page = doc[0]
        analyzer = PageAnalyzer()
        result = analyzer.analyze_page(page, 1)
        doc.close()

        # Note: PyMuPDF renders replacement chars as middle dots (U+00B7),
        # not U+FFFD, so the replacement-char heuristic doesn't trigger.
        # This is a known limitation of the M2 conservative heuristic.
        # The page has native text (middle dots) but no images -> NATIVE.
        assert result.classification == PageClassification.NATIVE
        assert result.signals.native_char_count > 0

    def test_analyze_sparse_page(self, sparse_page_pdf):
        import fitz
        doc = fitz.open(str(sparse_page_pdf))
        page = doc[0]
        analyzer = PageAnalyzer()
        result = analyzer.analyze_page(page, 1)
        doc.close()

        # Sparse text alone -> NATIVE (not suspicious)
        assert result.classification == PageClassification.NATIVE
        assert result.signals.native_char_count == 1

    def test_analyze_drawing_page(self, drawing_page_pdf):
        import fitz
        doc = fitz.open(str(drawing_page_pdf))
        page = doc[0]
        analyzer = PageAnalyzer()
        result = analyzer.analyze_page(page, 1)
        doc.close()

        assert result.classification == PageClassification.SUSPICIOUS
        assert result.signals.drawing_count > 0

    def test_analyze_text_with_large_image(self, text_with_large_image_pdf):
        import fitz
        doc = fitz.open(str(text_with_large_image_pdf))
        page = doc[0]
        analyzer = PageAnalyzer()
        result = analyzer.analyze_page(page, 1)
        doc.close()

        assert result.classification == PageClassification.SUSPICIOUS
        assert result.signals.native_char_count > 0
        assert result.signals.largest_image_coverage >= 0.5


class TestExtractionRouter:
    def test_route_native(self):
        router = ExtractionRouter()
        signals = PageSignals(native_char_count=100, page_width=612, page_height=792)
        result = classify(signals)
        strategy = router.route(result)
        assert strategy == ExtractionStrategy.NATIVE

    def test_route_ocr_required(self):
        router = ExtractionRouter()
        signals = PageSignals(native_char_count=0, image_count=1, largest_image_coverage=0.9, page_width=612, page_height=792)
        result = classify(signals)
        strategy = router.route(result)
        assert strategy == ExtractionStrategy.OCR_REQUIRED

    def test_route_empty(self):
        router = ExtractionRouter()
        signals = PageSignals(page_width=612, page_height=792)
        result = classify(signals)
        strategy = router.route(result)
        assert strategy == ExtractionStrategy.EMPTY

    def test_route_suspicious(self):
        router = ExtractionRouter()
        signals = PageSignals(drawing_count=1, page_width=612, page_height=792)
        result = classify(signals)
        strategy = router.route(result)
        assert strategy == ExtractionStrategy.SUSPICIOUS


class TestDocumentParserIntegration:
    def test_parse_clean_native(self, simple_pdf):
        parser = DocumentParser()
        doc = parser.parse(simple_pdf)
        assert doc.page_count == 1
        assert doc.pages[0].classification == IRPageClassification.NATIVE
        assert len(doc.pages[0].blocks) > 0

    def test_parse_empty_page(self, empty_page_pdf):
        parser = DocumentParser()
        doc = parser.parse(empty_page_pdf)
        assert doc.page_count == 1
        assert doc.pages[0].classification == IRPageClassification.EMPTY
        assert len(doc.pages[0].blocks) == 0

    def test_parse_scanned_page_ocr_failed(self, scanned_page_pdf):
        parser = DocumentParser()
        doc = parser.parse(scanned_page_pdf)
        assert doc.page_count == 1
        assert doc.pages[0].classification == IRPageClassification.OCR_REQUIRED
        assert doc.pages[0].extraction_method == ExtractionMethod.OCR
        assert doc.pages[0].extraction_status == ExtractionStatus.FAILED
        assert len(doc.pages[0].blocks) == 0
        assert "OCR failed" in doc.pages[0].warnings[0]
        assert "Tesseract not available" in doc.pages[0].warnings[0]

    def test_parse_mixed_page(self, mixed_page_pdf):
        parser = DocumentParser()
        doc = parser.parse(mixed_page_pdf)
        assert doc.page_count == 1
        assert doc.pages[0].classification == IRPageClassification.NATIVE
        assert len(doc.pages[0].blocks) > 0

    def test_parse_suspicious_warning(self, drawing_page_pdf):
        parser = DocumentParser()
        doc = parser.parse(drawing_page_pdf)
        assert doc.pages[0].classification == IRPageClassification.SUSPICIOUS
        assert "suspicious" in doc.pages[0].warnings[0].lower()

    def test_parse_mixed_document(self, mixed_document_pdf):
        parser = DocumentParser()
        doc = parser.parse(mixed_document_pdf)
        assert doc.page_count == 5
        # Page 1: native
        assert doc.pages[0].classification == IRPageClassification.NATIVE
        # Page 2: ocr_required
        assert doc.pages[1].classification == IRPageClassification.OCR_REQUIRED
        # Page 3: empty
        assert doc.pages[2].classification == IRPageClassification.EMPTY
        # Page 4: sparse -> native (not suspicious)
        assert doc.pages[3].classification == IRPageClassification.NATIVE
        # Page 5: text + large image -> suspicious
        assert doc.pages[4].classification == IRPageClassification.SUSPICIOUS

    def test_analyze_without_full_parse(self, mixed_document_pdf):
        parser = DocumentParser()
        analyses = parser.analyze(mixed_document_pdf)
        assert len(analyses) == 5
        assert analyses[0].classification == PageClassification.NATIVE
        assert analyses[1].classification == PageClassification.OCR_REQUIRED
        assert analyses[2].classification == PageClassification.EMPTY
        assert analyses[3].classification == PageClassification.NATIVE
        assert analyses[4].classification == PageClassification.SUSPICIOUS


class TestCLIAnalysis:
    def test_cli_info_shows_analysis(self, mixed_document_pdf):
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "ragparser.cli", "info", str(mixed_document_pdf)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        output = result.stdout
        assert "Classification: NATIVE" in output
        assert "Classification: OCR_REQUIRED" in output
        assert "Classification: EMPTY" in output
        assert "Classification: SUSPICIOUS" in output
        assert "Largest image coverage" in output
        assert "Native chars" in output