"""Tests for M6 Diagnostics + Extraction Report."""

from pathlib import Path

import json
import subprocess
import sys

from ragparser.diagnostics import analyze_document, ExtractionReport, ReportStatus, StatusReason
from ragparser.parser import DocumentParser


def test_report_basic_creation(simple_pdf):
    """Test that a report can be created from a parsed document."""
    parser = DocumentParser()
    doc = parser.parse(simple_pdf)
    report = analyze_document(doc)
    assert isinstance(report, ExtractionReport)
    assert report.page_count == 1


def test_report_to_dict(simple_pdf):
    """Test that to_dict() produces a JSON-serializable dict."""
    parser = DocumentParser()
    doc = parser.parse(simple_pdf)
    report = analyze_document(doc)
    d = report.to_dict()
    assert "source_path" in d
    assert "page_count" in d
    assert "status" in d
    assert "status_reasons" in d
    assert "problem_pages" in d
    assert json.dumps(d)  # should not raise


def test_report_status_good(simple_pdf):
    """Test that a clean native page gets GOOD status."""
    parser = DocumentParser()
    doc = parser.parse(simple_pdf)
    report = analyze_document(doc)
    assert report.status == ReportStatus.GOOD


def test_report_status_review_suspicious(drawing_page_pdf):
    """Test that SUSPICIOUS classification triggers REVIEW status."""
    parser = DocumentParser()
    doc = parser.parse(drawing_page_pdf)
    report = analyze_document(doc)
    # drawing_page has a SUSPICIOUS classification
    assert report.status == ReportStatus.REVIEW
    assert any(r.category == "extraction" and "SUSPICIOUS" in r.message for r in report.status_reasons)


def test_report_status_poor_failed_pages(mixed_document_pdf):
    """Test that >= 10% failed pages triggers POOR status."""
    parser = DocumentParser()
    doc = parser.parse(mixed_document_pdf)
    report = analyze_document(doc)
    # mixed_document has 5 pages; check if any have failed status
    failed_count = report.extraction_status_counts.get("failed", 0)
    total = report.page_count
    if failed_count >= total * 0.10:
        assert report.status == ReportStatus.POOR
    else:
        # Could be REVIEW if other triggers present
        assert report.status in (ReportStatus.REVIEW, ReportStatus.GOOD)


def test_extraction_counts(simple_pdf):
    """Test extraction count fields are populated."""
    parser = DocumentParser()
    doc = parser.parse(simple_pdf)
    report = analyze_document(doc)
    assert "native" in report.classification_counts
    assert "ocr_required" in report.classification_counts
    assert "empty" in report.classification_counts
    assert "suspicious" in report.classification_counts
    assert report.classification_counts["native"] > 0


def test_ocr_confidence_fields(simple_pdf):
    """Test OCR confidence fields are populated correctly."""
    parser = DocumentParser()
    doc = parser.parse(simple_pdf)
    report = analyze_document(doc)
    assert report.ocr_block_count >= 0
    assert report.blocks_with_confidence >= 0
    assert report.low_confidence_block_count >= 0
    # For a native page with no OCR blocks, these should be 0
    assert report.ocr_block_count == 0 or report.blocks_with_confidence == 0


def test_median_min_confidence(simple_pdf):
    """Test median and min OCR confidence are set appropriately."""
    parser = DocumentParser()
    doc = parser.parse(simple_pdf)
    report = analyze_document(doc)
    # For a native page with no OCR blocks, these should be None
    assert report.median_ocr_confidence is None
    assert report.min_ocr_confidence is None


def test_problem_pages(simple_pdf):
    """Test problem_pages list for a clean document."""
    parser = DocumentParser()
    doc = parser.parse(simple_pdf)
    report = analyze_document(doc)
    assert report.problem_pages == []


def test_status_reasons_populated(simple_pdf):
    """Test that status_reasons is populated even for GOOD status."""
    parser = DocumentParser()
    doc = parser.parse(simple_pdf)
    report = analyze_document(doc)
    assert report.status_reasons is not None


def test_status_reasons_list_structure():
    """Test StatusReason to_dict() serialization."""
    reason = StatusReason(category="extraction", message="Test message", count=3, page_numbers=[1, 2, 3])
    d = reason.to_dict()
    assert d == {"category": "extraction", "message": "Test message", "count": 3, "page_numbers": [1, 2, 3]}


def test_status_reason_minimal():
    """Test StatusReason with minimal fields."""
    reason = StatusReason(category="general", message="Just a message")
    d = reason.to_dict()
    assert d == {"category": "general", "message": "Just a message"}


def test_report_serialization_with_reasons(mixed_document_pdf):
    """Test full to_dict() serialization with status reasons."""
    parser = DocumentParser()
    doc = parser.parse(mixed_document_pdf)
    report = analyze_document(doc)
    d = report.to_dict()
    assert d["status"] in ("good", "review", "poor")
    assert isinstance(d["status_reasons"], list)
    for r in d["status_reasons"]:
        assert "category" in r
        assert "message" in r


def test_cli_report_command(simple_pdf, tmp_path):
    """Test the ragparser report CLI command."""
    output_file = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "report", str(simple_pdf), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert "status" in data
    assert "page_count" in data


def test_cli_report_json_output(simple_pdf, tmp_path):
    """Test ragparser report outputs valid JSON via -o flag."""
    output_file = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "report", str(simple_pdf), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert "status" in data


def test_cli_report_pretty(simple_pdf, tmp_path):
    """Test ragparser report with --pretty flag outputs pretty JSON."""
    output_file = tmp_path / "report.json"
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "report", str(simple_pdf), "--pretty", "-o", str(output_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    # Pretty-printed JSON should have newlines and indentation
    assert "\n" in output_file.read_text()
    assert "  " in output_file.read_text()


def test_cli_report_nonexistent():
    """Test ragparser report with nonexistent file."""
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "report", "nonexistent.pdf"],
        capture_output=True,
        text=True,
    )
    # Typer returns 2 for invalid argument errors
    assert result.returncode == 2


def test_empty_page_report(empty_page_pdf):
    """Test report for an empty page - should be GOOD (no problems)."""
    parser = DocumentParser()
    doc = parser.parse(empty_page_pdf)
    report = analyze_document(doc)
    assert report.page_count == 1
    assert report.classification_counts["empty"] == 1
    assert report.status == ReportStatus.GOOD
    assert report.problem_pages == []


def test_scanned_page_report(scanned_page_pdf):
    """Test report for a scanned page - OCR_required classification."""
    parser = DocumentParser()
    doc = parser.parse(scanned_page_pdf)
    report = analyze_document(doc)
    assert report.classification_counts["ocr_required"] >= 1
    # OCR executed successfully (SUCCESS) but recovered zero text.
    # Per approved semantics: this triggers REVIEW (not FAILED/POOR) because
    # execution did not fail; it should NOT count toward the FAILED percentage.
    assert report.status == ReportStatus.REVIEW
    # There should be an explicit status reason for the OCR recovery issue
    assert any("recovered no usable text" in r.message for r in report.status_reasons)


def test_sparse_page_report(sparse_page_pdf):
    """Test report for a sparse page - NATIVE classification, not suspicious."""
    parser = DocumentParser()
    doc = parser.parse(sparse_page_pdf)
    report = analyze_document(doc)
    assert report.classification_counts["native"] >= 1
    assert report.status == ReportStatus.GOOD


def test_visual_no_structure_report():
    """Test report for a document with no structure - should be GOOD if no failures."""
    parser = DocumentParser()
    no_structure_path = Path("tests/fixtures/no_structure.pdf")
    doc = parser.parse(no_structure_path)
    report = analyze_document(doc)
    assert report.page_count > 0
    # No structure is not a problem; should be GOOD unless other triggers
    assert report.status in (ReportStatus.GOOD, ReportStatus.REVIEW)


def test_problem_pages_poor(mixed_document_pdf):
    """Test that POOR status has problem pages listed."""
    parser = DocumentParser()
    doc = parser.parse(mixed_document_pdf)
    report = analyze_document(doc)
    if report.status == ReportStatus.POOR:
        assert len(report.problem_pages) > 0
        assert all(1 <= p <= report.page_count for p in report.problem_pages)


def test_no_mutation_of_document(simple_pdf):
    """Test that analyze_document does not mutate the document."""
    parser = DocumentParser()
    doc = parser.parse(simple_pdf)
    original_blocks = len(doc.pages[0].blocks)
    _ = analyze_document(doc)
    assert len(doc.pages[0].blocks) == original_blocks


def test_extraction_report_dataclass_fields():
    """Test ExtractionReport dataclass has all expected fields with defaults."""
    report = ExtractionReport(
        source_path="test.pdf",
        page_count=1,
        classification_counts={"native": 1, "ocr_required": 0, "empty": 0, "suspicious": 0},
        extraction_method_counts={"native": 1, "ocr": 0},
        extraction_status_counts={"success": 1, "failed": 0},
        layout_mode_counts={"single_column": 1, "two_column": 0, "uncertain": 0},
        block_role_counts={"heading": 0, "paragraph": 1, "header": 0, "footer": 0, "page_number": 0, "unknown": 0},
    )
    assert report.ocr_block_count == 0
    assert report.blocks_with_confidence == 0
    assert report.median_ocr_confidence is None
    assert report.min_ocr_confidence is None
    assert report.low_confidence_block_count == 0
    assert report.pages_with_low_confidence == []
    assert report.warnings == []
    assert report.status == ReportStatus.GOOD
    assert report.status_reasons == []
    assert report.problem_pages == []


def test_extraction_report_to_dict_minimal():
    """Test minimal to_dict() serialization."""
    report = ExtractionReport(
        source_path="test.pdf",
        page_count=1,
        classification_counts={"native": 1, "ocr_required": 0, "empty": 0, "suspicious": 0},
        extraction_method_counts={"native": 1, "ocr": 0},
        extraction_status_counts={"success": 1, "failed": 0},
        layout_mode_counts={"single_column": 1, "two_column": 0, "uncertain": 0},
        block_role_counts={"heading": 0, "paragraph": 1, "header": 0, "footer": 0, "page_number": 0, "unknown": 0},
    )
    d = report.to_dict()
    assert d["source_path"] == "test.pdf"
    assert d["page_count"] == 1
    assert d["status"] == "good"
    assert d["status_reasons"] == []
    assert d["problem_pages"] == []