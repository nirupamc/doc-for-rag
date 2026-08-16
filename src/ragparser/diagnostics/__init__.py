"""Diagnostics for RagParser — extraction, layout, structure summary.

Read-only analyzer that produces an ExtractionReport from a parsed Document.
Does not modify the document.

Typical usage:

    from ragparser.diagnostics import analyze_document
    from ragparser.parser import DocumentParser

    parser = DocumentParser()
    doc = parser.parse("example.pdf")
    report = analyze_document(doc)
    print(report.status)
    print(report.status_reasons)
"""

from ragparser.ir import Document

from .analyzer import analyze_document
from .models import ExtractionReport, ReportStatus, StatusReason

__all__ = [
    "analyze_document",
    "ExtractionReport",
    "ReportStatus",
    "StatusReason",
]