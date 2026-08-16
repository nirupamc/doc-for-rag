"""Data models for ExtractionReport and status determination."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Set, Optional

from ragparser.ir import Document, PageClassification, ExtractionMethod, ExtractionStatus, LayoutMode, BlockRole


class ReportStatus(Enum):
    """Overall document status derived from visible conditions."""
    GOOD = "good"
    REVIEW = "review"
    POOR = "poor"


@dataclass
class StatusReason:
    """A rule that contributed to the overall status."""
    category: str  # e.g. "extraction", "layout", "ocr", "structure", "general"
    message: str
    # Number of pages affected, if applicable
    count: Optional[int] = None
    # Page numbers affected, if applicable
    page_numbers: Optional[List[int]] = None

    def to_dict(self) -> dict:
        d: dict = {"category": self.category, "message": self.message}
        if self.count is not None:
            d["count"] = self.count
        if self.page_numbers is not None:
            d["page_numbers"] = self.page_numbers
        return d


@dataclass
class ExtractionReport:
    """Minimal extraction report produced from a Document IR."""

    source_path: str
    page_count: int

    # Extraction classification counts
    classification_counts: Dict[str, int]  # "native", "ocr_required", "empty", "suspicious"

    # Extraction method counts (actual method used)
    extraction_method_counts: Dict[str, int]  # "native", "ocr"

    # Extraction status counts
    extraction_status_counts: Dict[str, int]  # "success", "failed"

    # Layout mode counts
    layout_mode_counts: Dict[str, int]  # "single_column", "two_column", "uncertain"

    # Block role counts
    block_role_counts: Dict[str, int]  # "heading", "paragraph", "header", "footer", "page_number", "unknown"

    # OCR diagnostics
    ocr_block_count: int = 0
    blocks_with_confidence: int = 0
    median_ocr_confidence: Optional[float] = None
    min_ocr_confidence: Optional[float] = None
    low_confidence_block_count: int = 0
    pages_with_low_confidence: List[int] = field(default_factory=list)

    # Warnings
    warnings: List[dict] = field(default_factory=list)

    # Overall status and reasons
    status: ReportStatus = ReportStatus.GOOD
    status_reasons: List[StatusReason] = field(default_factory=list)

    # Problem pages
    problem_pages: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to JSON-serializable dict."""
        return {
            "source_path": self.source_path,
            "page_count": self.page_count,
            "classification_counts": self.classification_counts,
            "extraction_method_counts": self.extraction_method_counts,
            "extraction_status_counts": self.extraction_status_counts,
            "layout_mode_counts": self.layout_mode_counts,
            "block_role_counts": self.block_role_counts,
            "ocr_block_count": self.ocr_block_count,
            "blocks_with_confidence": self.blocks_with_confidence,
            "median_ocr_confidence": self.median_ocr_confidence,
            "min_ocr_confidence": self.min_ocr_confidence,
            "low_confidence_block_count": self.low_confidence_block_count,
            "pages_with_low_confidence": self.pages_with_low_confidence,
            "warnings": self.warnings,
            "status": self.status.value,
            "status_reasons": [r.to_dict() for r in self.status_reasons],
            "problem_pages": self.problem_pages,
        }