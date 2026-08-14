"""Tests for IR creation and serialization."""

import json
import pytest
from ragparser.ir import (
    Block,
    BlockType,
    BoundingBox,
    Document,
    ExtractionMethod,
    Page,
)


class TestBoundingBox:
    def test_creation(self):
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=50)
        assert bbox.x0 == 0
        assert bbox.y0 == 0
        assert bbox.x1 == 100
        assert bbox.y1 == 50
        assert bbox.width == 100
        assert bbox.height == 50

    def test_invalid_x1_raises(self):
        with pytest.raises(ValueError):
            BoundingBox(x0=100, y0=0, x1=50, y1=50)

    def test_invalid_y1_raises(self):
        with pytest.raises(ValueError):
            BoundingBox(x0=0, y0=50, x1=100, y1=0)

    def test_to_dict(self):
        bbox = BoundingBox(x0=10, y0=20, x1=110, y1=70)
        data = bbox.to_dict()
        assert data == {"x0": 10, "y0": 20, "x1": 110, "y1": 70}

    def test_from_dict(self):
        data = {"x0": 10, "y0": 20, "x1": 110, "y1": 70}
        bbox = BoundingBox.from_dict(data)
        assert bbox.x0 == 10
        assert bbox.y0 == 20
        assert bbox.x1 == 110
        assert bbox.y1 == 70


class TestBlock:
    def test_defaults(self):
        block = Block()
        assert block.type == BlockType.TEXT
        assert block.text == ""
        assert block.bbox is None
        assert block.extraction_method == ExtractionMethod.NATIVE
        assert block.confidence is None
        assert block.page_number == 0
        assert block.reading_order == 0

    def test_with_values(self):
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=50)
        block = Block(
            type=BlockType.TEXT,
            text="Hello",
            bbox=bbox,
            extraction_method=ExtractionMethod.NATIVE,
            confidence=0.95,
            page_number=1,
            reading_order=0,
        )
        assert block.text == "Hello"
        assert block.bbox == bbox
        assert block.confidence == 0.95

    def test_to_dict(self):
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=50)
        block = Block(text="Test", bbox=bbox, page_number=1)
        data = block.to_dict()
        assert data["type"] == "text"
        assert data["text"] == "Test"
        assert data["bbox"] == {"x0": 0, "y0": 0, "x1": 100, "y1": 50}
        assert data["page_number"] == 1

    def test_from_dict(self):
        data = {
            "type": "text",
            "text": "Test",
            "bbox": {"x0": 0, "y0": 0, "x1": 100, "y1": 50},
            "extraction_method": "native",
            "confidence": None,
            "page_number": 1,
            "reading_order": 0,
        }
        block = Block.from_dict(data)
        assert block.text == "Test"
        assert block.bbox is not None
        assert block.bbox.x0 == 0
        assert block.page_number == 1


class TestPage:
    def test_creation(self):
        page = Page(number=1, width=612, height=792)
        assert page.number == 1
        assert page.width == 612
        assert page.height == 792
        assert page.blocks == []
        assert page.rotation == 0

    def test_with_blocks(self):
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=50)
        block = Block(text="Test", bbox=bbox, page_number=1)
        page = Page(number=1, width=612, height=792, blocks=[block])
        assert len(page.blocks) == 1

    def test_to_dict(self):
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=50)
        block = Block(text="Test", bbox=bbox, page_number=1)
        page = Page(number=1, width=612, height=792, blocks=[block])
        data = page.to_dict()
        assert data["number"] == 1
        assert data["width"] == 612
        assert data["height"] == 792
        assert len(data["blocks"]) == 1

    def test_from_dict(self):
        data = {
            "number": 1,
            "width": 612,
            "height": 792,
            "blocks": [
                {
                    "type": "text",
                    "text": "Test",
                    "bbox": {"x0": 0, "y0": 0, "x1": 100, "y1": 50},
                    "extraction_method": "native",
                    "confidence": None,
                    "page_number": 1,
                    "reading_order": 0,
                }
            ],
            "rotation": 0,
        }
        page = Page.from_dict(data)
        assert page.number == 1
        assert len(page.blocks) == 1
        assert page.blocks[0].text == "Test"


class TestDocument:
    def test_creation(self):
        doc = Document(source_path="test.pdf", page_count=1)
        assert doc.source_path == "test.pdf"
        assert doc.page_count == 1
        assert doc.pages == []
        assert doc.metadata == {}
        assert doc.warnings == []

    def test_with_pages(self):
        page = Page(number=1, width=612, height=792)
        doc = Document(source_path="test.pdf", page_count=1, pages=[page])
        assert len(doc.pages) == 1

    def test_to_dict(self):
        page = Page(number=1, width=612, height=792)
        doc = Document(source_path="test.pdf", page_count=1, pages=[page], metadata={"author": "Test"})
        data = doc.to_dict()
        assert data["source_path"] == "test.pdf"
        assert data["page_count"] == 1
        assert data["metadata"]["author"] == "Test"

    def test_from_dict(self):
        data = {
            "source_path": "test.pdf",
            "page_count": 1,
            "pages": [
                {
                    "number": 1,
                    "width": 612,
                    "height": 792,
                    "blocks": [],
                    "rotation": 0,
                }
            ],
            "metadata": {"author": "Test"},
            "warnings": [],
        }
        doc = Document.from_dict(data)
        assert doc.source_path == "test.pdf"
        assert doc.page_count == 1
        assert doc.metadata["author"] == "Test"

    def test_roundtrip(self):
        """Test full serialization roundtrip."""
        bbox = BoundingBox(x0=72, y0=72, x1=200, y1=100)
        block = Block(
            type=BlockType.TEXT,
            text="Hello, World!",
            bbox=bbox,
            extraction_method=ExtractionMethod.NATIVE,
            page_number=1,
            reading_order=0,
        )
        page = Page(number=1, width=612, height=792, blocks=[block])
        doc = Document(
            source_path="test.pdf",
            page_count=1,
            pages=[page],
            metadata={"title": "Test"},
            warnings=[],
        )

        # Serialize to JSON and back
        json_str = json.dumps(doc.to_dict())
        data = json.loads(json_str)
        restored = Document.from_dict(data)

        assert restored.source_path == doc.source_path
        assert restored.page_count == doc.page_count
        assert restored.pages[0].number == doc.pages[0].number
        assert restored.pages[0].blocks[0].text == "Hello, World!"
        assert restored.pages[0].blocks[0].bbox.x0 == 72
        assert restored.metadata["title"] == "Test"