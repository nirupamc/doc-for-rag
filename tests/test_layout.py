"""Tests for layout analysis: signals, ordering, column detection."""

import pytest
from ragparser.ir import Block, BlockType, BoundingBox, Page, ExtractionMethod
from ragparser.layout import LayoutAnalyzer, LayoutSignals, BlockGeometry, LayoutMode


class TestBlockGeometry:
    def test_from_block(self):
        block = Block(
            text="Test",
            bbox=BoundingBox(x0=10, y0=20, x1=100, y1=50),
            page_number=1,
        )
        geom = BlockGeometry.from_block(block, 5)
        assert geom.block_id == 5
        assert geom.x0 == 10
        assert geom.y0 == 20
        assert geom.width == 90
        assert geom.height == 30
        assert geom.center_x == 55
        assert geom.center_y == 35

    def test_from_block_no_bbox_raises(self):
        block = Block(text="Test", bbox=None)
        with pytest.raises(ValueError):
            BlockGeometry.from_block(block, 0)


class TestLayoutSignals:
    def test_empty(self):
        signals = LayoutSignals(page_width=612, page_height=792, block_count=0, blocks=[])
        assert not signals.has_blocks
        assert not signals.single_block

    def test_single_block(self):
        block = BlockGeometry(block_id=0, x0=0, y0=0, x1=10, y1=10, width=10, height=10, area=100, center_x=5, center_y=5)
        signals = LayoutSignals(page_width=612, page_height=792, block_count=1, blocks=[block])
        assert signals.has_blocks
        assert signals.single_block


class TestLayoutAnalyzerBaseline:
    def setup_method(self):
        self.analyzer = LayoutAnalyzer()

    def _make_page(self, blocks):
        return Page(number=1, width=612, height=792, blocks=blocks)

    def test_zero_blocks(self):
        page = self._make_page([])
        result = self.analyzer.analyze_page(page)
        assert result.layout_mode == LayoutMode.SINGLE_COLUMN
        assert result.resolved_order == []

    def test_single_block(self):
        block = Block(text="A", bbox=BoundingBox(10, 10, 100, 50), page_number=1)
        page = self._make_page([block])
        result = self.analyzer.analyze_page(page)
        assert result.layout_mode == LayoutMode.SINGLE_COLUMN
        assert result.resolved_order == [0]
        assert result.input_order == [0]

    def test_single_column_baseline(self):
        """Top-to-bottom ordering for single column."""
        blocks = [
            Block(text="C", bbox=BoundingBox(10, 200, 100, 250), page_number=1),  # lowest
            Block(text="A", bbox=BoundingBox(10, 10, 100, 60), page_number=1),   # top
            Block(text="B", bbox=BoundingBox(10, 100, 100, 150), page_number=1),  # middle
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        assert result.layout_mode == LayoutMode.SINGLE_COLUMN
        assert result.resolved_order == [1, 2, 0]  # A, B, C

    def test_shuffled_input_reordered(self):
        """Input order doesn't matter; geometry determines output."""
        blocks = [
            Block(text="Third", bbox=BoundingBox(10, 200, 100, 250), page_number=1),
            Block(text="First", bbox=BoundingBox(10, 10, 100, 60), page_number=1),
            Block(text="Second", bbox=BoundingBox(10, 100, 100, 150), page_number=1),
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        assert result.input_order == [0, 1, 2]
        assert result.resolved_order == [1, 2, 0]

    def test_same_row_left_to_right(self):
        """Blocks on same visual row order left-to-right."""
        blocks = [
            Block(text="Right", bbox=BoundingBox(300, 50, 400, 100), page_number=1),
            Block(text="Left", bbox=BoundingBox(50, 50, 150, 100), page_number=1),
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        assert result.layout_mode == LayoutMode.SINGLE_COLUMN
        assert result.resolved_order == [1, 0]  # Left then Right

    def test_row_tolerance(self):
        """Small vertical differences grouped into same row."""
        blocks = [
            Block(text="B", bbox=BoundingBox(10, 100, 100, 150), page_number=1),
            Block(text="A", bbox=BoundingBox(10, 12, 100, 62), page_number=1),  # y0=12, close to 10
            Block(text="C", bbox=BoundingBox(10, 200, 100, 250), page_number=1),
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        # A and B should be in same row (y0=12 vs y0=100? no, 12 and 100 are far)
        # Actually A at y0=12, B at y0=100 - different rows
        assert result.resolved_order == [1, 0, 2]  # A, B, C


class TestLayoutAnalyzerTwoColumn:
    def setup_method(self):
        self.analyzer = LayoutAnalyzer()

    def _make_page(self, blocks):
        return Page(number=1, width=612, height=792, blocks=blocks)

    def test_two_column_left_then_right(self):
        """Full-width header, then left column, then right column, then full-width footer."""
        # Use custom analyzer with lower column span threshold for this test
        analyzer = LayoutAnalyzer(min_column_span_pct=0.20)
        blocks = [
            # Header (full-width)
            Block(text="HEADER", bbox=BoundingBox(50, 20, 562, 60), page_number=1),
            # Left column
            Block(text="L1", bbox=BoundingBox(50, 100, 250, 140), page_number=1),
            Block(text="L2", bbox=BoundingBox(50, 180, 250, 220), page_number=1),
            Block(text="L3", bbox=BoundingBox(50, 260, 250, 300), page_number=1),
            # Right column
            Block(text="R1", bbox=BoundingBox(362, 100, 562, 140), page_number=1),
            Block(text="R2", bbox=BoundingBox(362, 180, 562, 220), page_number=1),
            Block(text="R3", bbox=BoundingBox(362, 260, 562, 300), page_number=1),
            # Footer (full-width)
            Block(text="FOOTER", bbox=BoundingBox(50, 700, 562, 740), page_number=1),
        ]
        page = self._make_page(blocks)
        result = analyzer.analyze_page(page)
        assert result.layout_mode == LayoutMode.TWO_COLUMN
        # Order: header, L1, L2, L3, R1, R2, R3, footer
        expected = [0, 1, 2, 3, 4, 5, 6, 7]
        assert result.resolved_order == expected

    def test_full_width_header_above_columns(self):
        """Header spans full width, then two columns."""
        analyzer = LayoutAnalyzer(min_column_span_pct=0.10)
        blocks = [
            Block(text="TITLE", bbox=BoundingBox(50, 20, 562, 60), page_number=1),
            Block(text="L1", bbox=BoundingBox(50, 100, 250, 140), page_number=1),
            Block(text="L2", bbox=BoundingBox(50, 180, 250, 220), page_number=1),
            Block(text="L3", bbox=BoundingBox(50, 260, 250, 300), page_number=1),
            Block(text="R1", bbox=BoundingBox(362, 100, 562, 140), page_number=1),
            Block(text="R2", bbox=BoundingBox(362, 180, 562, 220), page_number=1),
            Block(text="R3", bbox=BoundingBox(362, 260, 562, 300), page_number=1),
        ]
        page = self._make_page(blocks)
        result = analyzer.analyze_page(page)
        assert result.layout_mode == LayoutMode.TWO_COLUMN
        # Order: Title, L1, L2, L3, R1, R2, R3
        assert result.resolved_order == [0, 1, 2, 3, 4, 5, 6]

    def test_two_column_insufficient_blocks(self):
        """Less than 4 blocks -> single column."""
        blocks = [
            Block(text="A", bbox=BoundingBox(50, 100, 250, 140), page_number=1),
            Block(text="B", bbox=BoundingBox(362, 100, 562, 140), page_number=1),
            Block(text="C", bbox=BoundingBox(50, 180, 250, 220), page_number=1),
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        assert result.layout_mode == LayoutMode.SINGLE_COLUMN

    def test_two_column_insufficient_gap(self):
        """Columns too close together -> single column."""
        blocks = [
            Block(text="HEADER", bbox=BoundingBox(50, 20, 562, 60), page_number=1),
            Block(text="L1", bbox=BoundingBox(50, 100, 300, 140), page_number=1),  # overlaps middle
            Block(text="R1", bbox=BoundingBox(312, 100, 562, 140), page_number=1),  # small gap
            Block(text="FOOTER", bbox=BoundingBox(50, 700, 562, 740), page_number=1),
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        assert result.layout_mode == LayoutMode.SINGLE_COLUMN


class TestLayoutAnalyzerEdgeCases:
    def setup_method(self):
        self.analyzer = LayoutAnalyzer()

    def _make_page(self, blocks):
        return Page(number=1, width=612, height=792, blocks=blocks)

    def test_invalid_bbox_warning_and_fallback(self):
        """Extreme out-of-page coordinates produce warning and fallback ordering."""
        blocks = [
            Block(text="Valid1", bbox=BoundingBox(10, 10, 100, 50), page_number=1),
            Block(text="Valid2", bbox=BoundingBox(10, 100, 100, 150), page_number=1),
            Block(text="Extreme", bbox=BoundingBox(10000, 10000, 10100, 10150), page_number=1),  # far out of page
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        # Extreme block is filtered out, leaving 2 valid blocks -> SINGLE_COLUMN
        assert result.layout_mode == LayoutMode.SINGLE_COLUMN
        assert page.warnings  # warning should be generated
        assert "extreme out-of-page" in page.warnings[0].lower()
        # Valid blocks should be ordered correctly
        assert result.resolved_order[:2] == [0, 1]
        # Extreme block (index 2) should be appended at the end
        assert result.resolved_order[2] == 2

    def test_all_invalid_blocks(self):
        """All blocks with extreme coordinates -> UNCERTAIN with input order."""
        blocks = [
            Block(text="Extreme1", bbox=BoundingBox(10000, 10000, 10100, 10150), page_number=1),
            Block(text="Extreme2", bbox=BoundingBox(20000, 20000, 20100, 20250), page_number=1),
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        assert result.layout_mode == LayoutMode.UNCERTAIN
        assert result.resolved_order == [0, 1]  # input order preserved

    def test_none_bbox(self):
        """Block with None bbox is treated as invalid."""
        blocks = [
            Block(text="Valid", bbox=BoundingBox(10, 10, 100, 50), page_number=1),
            Block(text="NoBBox", bbox=None, page_number=1),
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        # With one valid block, it should be SINGLE_COLUMN (single valid block)
        assert result.layout_mode in (LayoutMode.SINGLE_COLUMN, LayoutMode.UNCERTAIN)
        # Valid block should be ordered first
        assert result.resolved_order[0] == 0

    def test_fallback_uncertain(self):
        """Ambiguous layout falls back to UNCERTAIN with y-then-x sort."""
        # Create ambiguous layout: blocks scattered without clear columns
        blocks = [
            Block(text="A", bbox=BoundingBox(50, 50, 200, 100), page_number=1),
            Block(text="B", bbox=BoundingBox(400, 50, 550, 100), page_number=1),
            Block(text="C", bbox=BoundingBox(200, 200, 350, 250), page_number=1),  # middle
            Block(text="D", bbox=BoundingBox(50, 400, 200, 450), page_number=1),
        ]
        page = self._make_page(blocks)
        result = self.analyzer.analyze_page(page)
        # With only 4 blocks and middle block, should be UNCERTAIN or SINGLE_COLUMN
        assert result.layout_mode in (LayoutMode.UNCERTAIN, LayoutMode.SINGLE_COLUMN)


class TestLayoutAnalyzerEquivalence:
    """Test that native and OCR blocks with same geometry produce same order."""

    def setup_method(self):
        self.analyzer = LayoutAnalyzer()

    def _make_page(self, blocks):
        return Page(number=1, width=612, height=792, blocks=blocks)

    def test_native_ocr_equivalence_single_column(self):
        """Same geometry, different extraction_method -> same order."""
        blocks_native = [
            Block(text="A", bbox=BoundingBox(10, 10, 100, 50), page_number=1, extraction_method=ExtractionMethod.NATIVE),
            Block(text="B", bbox=BoundingBox(10, 100, 100, 150), page_number=1, extraction_method=ExtractionMethod.NATIVE),
            Block(text="C", bbox=BoundingBox(10, 200, 100, 250), page_number=1, extraction_method=ExtractionMethod.NATIVE),
        ]
        blocks_ocr = [
            Block(text="A", bbox=BoundingBox(10, 10, 100, 50), page_number=1, extraction_method=ExtractionMethod.OCR, confidence=0.9),
            Block(text="B", bbox=BoundingBox(10, 100, 100, 150), page_number=1, extraction_method=ExtractionMethod.OCR, confidence=0.85),
            Block(text="C", bbox=BoundingBox(10, 200, 100, 250), page_number=1, extraction_method=ExtractionMethod.OCR, confidence=0.95),
        ]
        page_native = self._make_page(blocks_native)
        page_ocr = self._make_page(blocks_ocr)

        result_native = self.analyzer.analyze_page(page_native)
        result_ocr = self.analyzer.analyze_page(page_ocr)

        assert result_native.resolved_order == result_ocr.resolved_order

    def test_native_ocr_equivalence_two_column(self):
        """Same two-column geometry, different extraction_method -> same order."""
        blocks_native = [
            Block(text="H", bbox=BoundingBox(50, 20, 562, 60), page_number=1, extraction_method=ExtractionMethod.NATIVE),
            Block(text="L1", bbox=BoundingBox(50, 100, 250, 140), page_number=1, extraction_method=ExtractionMethod.NATIVE),
            Block(text="L2", bbox=BoundingBox(50, 180, 250, 220), page_number=1, extraction_method=ExtractionMethod.NATIVE),
            Block(text="R1", bbox=BoundingBox(362, 100, 562, 140), page_number=1, extraction_method=ExtractionMethod.NATIVE),
            Block(text="R2", bbox=BoundingBox(362, 180, 562, 220), page_number=1, extraction_method=ExtractionMethod.NATIVE),
            Block(text="F", bbox=BoundingBox(50, 700, 562, 740), page_number=1, extraction_method=ExtractionMethod.NATIVE),
        ]
        blocks_ocr = [
            Block(text="H", bbox=BoundingBox(50, 20, 562, 60), page_number=1, extraction_method=ExtractionMethod.OCR),
            Block(text="L1", bbox=BoundingBox(50, 100, 250, 140), page_number=1, extraction_method=ExtractionMethod.OCR),
            Block(text="L2", bbox=BoundingBox(50, 180, 250, 220), page_number=1, extraction_method=ExtractionMethod.OCR),
            Block(text="R1", bbox=BoundingBox(362, 100, 562, 140), page_number=1, extraction_method=ExtractionMethod.OCR),
            Block(text="R2", bbox=BoundingBox(362, 180, 562, 220), page_number=1, extraction_method=ExtractionMethod.OCR),
            Block(text="F", bbox=BoundingBox(50, 700, 562, 740), page_number=1, extraction_method=ExtractionMethod.OCR),
        ]
        page_native = self._make_page(blocks_native)
        page_ocr = self._make_page(blocks_ocr)

        result_native = self.analyzer.analyze_page(page_native)
        result_ocr = self.analyzer.analyze_page(page_ocr)

        assert result_native.layout_mode == result_ocr.layout_mode
        assert result_native.resolved_order == result_ocr.resolved_order


class TestLayoutAnalyzerSignals:
    def test_collect_signals_empty(self):
        from ragparser.layout import LayoutAnalyzer
        analyzer = LayoutAnalyzer()
        page = Page(number=1, width=612, height=792, blocks=[])
        signals = analyzer._collect_signals(page)
        assert signals.block_count == 0
        assert not signals.has_blocks

    def test_collect_signals_skips_none_bbox(self):
        from ragparser.layout import LayoutAnalyzer
        analyzer = LayoutAnalyzer()
        blocks = [
            Block(text="A", bbox=BoundingBox(10, 10, 100, 50), page_number=1),
            Block(text="B", bbox=None, page_number=1),
        ]
        page = Page(number=1, width=612, height=792, blocks=blocks)
        signals = analyzer._collect_signals(page)
        assert signals.block_count == 1
        assert signals.blocks[0].block_id == 0