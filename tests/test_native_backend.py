"""Tests for native PDF extraction backend."""

import pytest
from ragparser.backends.native import DocumentLoader, NativeExtractor
from ragparser.ir import BlockType, ExtractionMethod


class TestDocumentLoader:
    def test_open_close(self, simple_pdf):
        loader = DocumentLoader(str(simple_pdf))
        loader.open()
        assert loader.doc is not None
        assert loader.page_count == 1
        loader.close()
        assert loader._doc is None

    def test_context_manager(self, simple_pdf):
        with DocumentLoader(str(simple_pdf)) as loader:
            assert loader.page_count == 1
        # Should be closed after context

    def test_page_count(self, simple_pdf, two_page_pdf):
        with DocumentLoader(str(simple_pdf)) as loader:
            assert loader.page_count == 1
        with DocumentLoader(str(two_page_pdf)) as loader:
            assert loader.page_count == 2

    def test_metadata(self, simple_pdf):
        with DocumentLoader(str(simple_pdf)) as loader:
            meta = loader.metadata
            assert isinstance(meta, dict)

    def test_get_page(self, simple_pdf):
        with DocumentLoader(str(simple_pdf)) as loader:
            page = loader.get_page(0)
            assert page is not None
            assert page.number == 0  # 0-indexed

    def test_iter_pages(self, two_page_pdf):
        with DocumentLoader(str(two_page_pdf)) as loader:
            pages = list(loader.iter_pages())
            assert len(pages) == 2
            assert pages[0][0] == 1  # 1-indexed page number
            assert pages[1][0] == 2

    def test_invalid_path_raises(self, nonexistent_pdf):
        loader = DocumentLoader(str(nonexistent_pdf))
        with pytest.raises(ValueError, match="Failed to open document"):
            loader.open()

    def test_property_without_open_raises(self):
        loader = DocumentLoader("dummy.pdf")
        with pytest.raises(RuntimeError, match="Document not opened"):
            _ = loader.doc


class TestNativeExtractor:
    def test_extract_page(self, simple_pdf):
        with DocumentLoader(str(simple_pdf)) as loader:
            page = loader.get_page(0)
            extractor = NativeExtractor()
            ir_page = extractor.extract_page(page, 1)

        assert ir_page.number == 1
        assert ir_page.width == 612
        assert ir_page.height == 792
        assert len(ir_page.blocks) > 0

    def test_block_properties(self, simple_pdf):
        with DocumentLoader(str(simple_pdf)) as loader:
            page = loader.get_page(0)
            extractor = NativeExtractor()
            ir_page = extractor.extract_page(page, 1)

        block = ir_page.blocks[0]
        assert block.type == BlockType.TEXT
        assert block.extraction_method == ExtractionMethod.NATIVE
        assert block.page_number == 1
        assert block.reading_order == 0
        assert block.confidence is None
        assert block.bbox is not None
        assert block.bbox.x0 >= 0
        assert block.bbox.y0 >= 0
        assert block.bbox.x1 <= ir_page.width
        assert block.bbox.y1 <= ir_page.height

    def test_text_content(self, simple_pdf):
        with DocumentLoader(str(simple_pdf)) as loader:
            page = loader.get_page(0)
            extractor = NativeExtractor()
            ir_page = extractor.extract_page(page, 1)

        full_text = " ".join(b.text for b in ir_page.blocks)
        assert "Hello" in full_text
        assert "World" in full_text
        assert "test PDF" in full_text

    def test_reading_order_sequential(self, simple_pdf):
        with DocumentLoader(str(simple_pdf)) as loader:
            page = loader.get_page(0)
            extractor = NativeExtractor()
            ir_page = extractor.extract_page(page, 1)

        for i, block in enumerate(ir_page.blocks):
            assert block.reading_order == i

    def test_method_name(self):
        extractor = NativeExtractor()
        assert extractor.get_method_name() == "native"

    def test_multi_page(self, two_page_pdf):
        with DocumentLoader(str(two_page_pdf)) as loader:
            extractor = NativeExtractor()
            for page_num, page in loader.iter_pages():
                ir_page = extractor.extract_page(page, page_num)
                assert ir_page.number == page_num
                assert len(ir_page.blocks) > 0

    def test_rotation_preserved(self, simple_pdf):
        with DocumentLoader(str(simple_pdf)) as loader:
            page = loader.get_page(0)
            rotation = page.rotation
            extractor = NativeExtractor()
            ir_page = extractor.extract_page(page, 1)

        assert ir_page.rotation == rotation


class TestParserIntegration:
    def test_parse_simple_pdf(self, simple_pdf):
        from ragparser.parser import DocumentParser

        parser = DocumentParser()
        doc = parser.parse(simple_pdf)

        assert doc.source_path == str(simple_pdf)
        assert doc.page_count == 1
        assert len(doc.pages) == 1
        assert doc.pages[0].number == 1

    def test_parse_two_page_pdf(self, two_page_pdf):
        from ragparser.parser import DocumentParser

        parser = DocumentParser()
        doc = parser.parse(two_page_pdf)

        assert doc.page_count == 2
        assert len(doc.pages) == 2
        assert doc.pages[0].number == 1
        assert doc.pages[1].number == 2

    def test_page_metadata_preserved(self, simple_pdf):
        from ragparser.parser import DocumentParser

        parser = DocumentParser()
        doc = parser.parse(simple_pdf)

        page = doc.pages[0]
        assert page.width > 0
        assert page.height > 0
        assert page.rotation in (0, 90, 180, 270)

    def test_invalid_input_raises(self):
        from ragparser.parser import DocumentParser

        parser = DocumentParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.pdf")

    def test_metadata_included(self, simple_pdf):
        from ragparser.parser import DocumentParser

        parser = DocumentParser()
        doc = parser.parse(simple_pdf)

        assert isinstance(doc.metadata, dict)