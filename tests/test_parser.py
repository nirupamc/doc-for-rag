"""Tests for DocumentParser API."""

from ragparser.parser import DocumentParser
from ragparser.ir import Document


class TestDocumentParser:
    def test_parser_creation(self):
        parser = DocumentParser()
        assert parser is not None

    def test_parse_returns_document(self, simple_pdf):
        parser = DocumentParser()
        doc = parser.parse(simple_pdf)
        assert isinstance(doc, Document)

    def test_parse_preserves_page_count(self, simple_pdf, two_page_pdf):
        parser = DocumentParser()
        doc1 = parser.parse(simple_pdf)
        doc2 = parser.parse(two_page_pdf)
        assert doc1.page_count == 1
        assert doc2.page_count == 2

    def test_parse_blocks_have_provenance(self, simple_pdf):
        parser = DocumentParser()
        doc = parser.parse(simple_pdf)
        block = doc.pages[0].blocks[0]
        assert block.page_number == 1
        assert block.extraction_method.value == "native"
        assert block.bbox is not None
        assert block.reading_order >= 0

    def test_warnings_list_exists(self, simple_pdf):
        parser = DocumentParser()
        doc = parser.parse(simple_pdf)
        assert isinstance(doc.warnings, list)

    def test_metadata_dict_exists(self, simple_pdf):
        parser = DocumentParser()
        doc = parser.parse(simple_pdf)
        assert isinstance(doc.metadata, dict)