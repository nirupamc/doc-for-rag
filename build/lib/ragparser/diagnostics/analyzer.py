"""Diagnostics analyzer — produces ExtractionReport from a Document."""

from collections import Counter
from typing import List, Dict, Set, Optional

from ragparser.ir import Document, Page, Block, BlockRole, ExtractionMethod, ExtractionStatus, LayoutMode, PageClassification

from .models import ExtractionReport, ReportStatus, StatusReason


def analyze_document(document: Document) -> ExtractionReport:
    """
    Produce an ExtractionReport from a parsed Document.

    Does NOT modify the document. All data are derived from what is already
    present in the IR.
    """
    report = _build_base_report(document)
    _add_ocr_diagnostics(report, document)
    _apply_policy(
        report,
        report.classification_counts,
        report.extraction_status_counts,
        report.layout_mode_counts,
        report.block_role_counts,
    )
    _add_warnings(report, document)
    _determine_status(report)
    return report


# ------------------------------------------------------------------
# Base report construction
# ------------------------------------------------------------------

def _build_base_report(document: Document) -> ExtractionReport:
    """Populate the report with counts from the document IR."""

    # Classification counts (page-level)
    classification_counts = Counter(
        p.classification.value if p.classification else "unknown"
        for p in document.pages
    )
    # Ensure all four known classes are present
    for cls in ("native", "ocr_required", "empty", "suspicious"):
        if cls not in classification_counts:
            classification_counts[cls] = 0

    # Extraction method counts (actual method used on blocks)
    method_counts = Counter(
        b.extraction_method.value for p in document.pages for b in p.blocks
    )

    # Extraction status counts
    status_counts = Counter(
        p.extraction_status.value if p.extraction_status else "unknown"
        for p in document.pages
    )
    for s in ("success", "failed"):
        if s not in status_counts:
            status_counts[s] = 0

    # Layout mode counts
    layout_counts = Counter(
        p.layout_mode.value if p.layout_mode else "unknown"
        for p in document.pages
    )
    for l in ("single_column", "two_column", "uncertain"):
        if l not in layout_counts:
            layout_counts[l] = 0

    # Block role counts
    role_counts = Counter(
        b.role.value for p in document.pages for b in p.blocks
    )
    for r in ("heading", "paragraph", "header", "footer", "page_number", "unknown"):
        if r not in role_counts:
            role_counts[r] = 0

    # OCR basics
    ocr_blocks = [b for p in document.pages for b in p.blocks if b.extraction_method == ExtractionMethod.OCR]
    ocr_block_count = len(ocr_blocks)
    blocks_with_conf = sum(1 for b in ocr_blocks if b.confidence is not None)

    conf_vals = [b.confidence for b in ocr_blocks if b.confidence is not None]
    median_conf: Optional[float] = None
    min_conf: Optional[float] = None
    if conf_vals:
        sorted_vals = sorted(conf_vals)
        n = len(sorted_vals)
        median_conf = sorted_vals[n // 2]
        min_conf = sorted_vals[0]

    # Low-confidence threshold: 0.5 (configurable conceptually)
    low_conf_count = sum(1 for c in conf_vals if c < 0.5) if conf_vals else 0

    # Pages with at least one low-confidence OCR block
    low_conf_pages: Set[int] = set()
    for b in ocr_blocks:
        if b.confidence is not None and b.confidence < 0.5:
            low_conf_pages.add(b.page_number)

    # Warnings collection
    all_warnings: List[dict] = []
    for p in document.pages:
        for w in p.warnings:
            all_warnings.append({"page": p.number, "message": w})

    return ExtractionReport(
        source_path=document.source_path,
        page_count=document.page_count,
        classification_counts=dict(classification_counts),
        extraction_method_counts=dict(method_counts),
        extraction_status_counts=dict(status_counts),
        layout_mode_counts=dict(layout_counts),
        block_role_counts=dict(role_counts),
        ocr_block_count=ocr_block_count,
        blocks_with_confidence=blocks_with_conf,
        median_ocr_confidence=median_conf,
        min_ocr_confidence=min_conf,
        low_confidence_block_count=low_conf_count,
        pages_with_low_confidence=sorted(low_conf_pages),
        warnings=all_warnings,
    )


# -----------------------------------------------------------------
# Policy: explicit GOOD / REVIEW / POOR thresholds
# -----------------------------------------------------------------

# POOR: failed extraction pages >= 10% of non-empty pages
# REVIEW: any failed page below the POOR threshold
#         any SUSPICIOUS page
#         any UNCERTAIN layout page
#         any low-confidence OCR warning
#         

_inconsistent_empty_skip = True  # Prototype 1: inconsistent EMPTY not auto-flagged

_POORED_THRESHOLD_RATIO = 0.10  # 10% of total pages


def _apply_policy(report: ExtractionReport, classification_counts: Dict[str, int],
                  extraction_status_counts: Dict[str, int],
                  layout_mode_counts: Dict[str, int],
                  block_role_counts: Dict[str, int]) -> None:
    """
    Apply Prototype 1 policy thresholds and set status/reasons.

    Takes counts (already extracted from the document) rather than the
    document itself, to keep the function pure and avoid circular references.
    """

    reasons: List[StatusReason] = []
    problem_pages: List[int] = []

    # --- POOR threshold: failed extraction >= 10% of total pages ---
    total_pages = sum(classification_counts.values()) if classification_counts else 0
    failed_pages = extraction_status_counts.get('failed', 0)

    if total_pages > 0 and failed_pages / total_pages >= _POORED_THRESHOLD_RATIO:
        reasons.append(
            StatusReason(
                category="extraction",
                message="Failed extraction pages >= 10% of total pages",
                count=failed_pages,
            )
        )
        problem_pages = list(range(1, total_pages + 1))

    # --- REVIEW triggers ---
    review_triggers: List[StatusReason] = []

    # Any failed page (below POOR threshold)
    failed_pages = extraction_status_counts.get('failed', 0)
    if failed_pages > 0:
        # If we're not already in POOR, this is a REVIEW trigger
        if not reasons:  # Not already POOR
            review_triggers.append(
                StatusReason(
                    category="extraction",
                    message=f"{failed_pages} page(s) failed extraction",
                    count=failed_pages,
                )
            )
        problem_pages = list(range(1, total_pages + 1)) if total_pages else []

    # Any SUSPICIOUS classification — only if not already POOR
    suspicious_count = classification_counts.get('suspicious', 0)
    if suspicious_count > 0 and not reasons:
        review_triggers.append(
            StatusReason(
                category="extraction",
                message=f"{suspicious_count} page(s) classified SUSPICIOUS",
                count=suspicious_count,
            )
        )

    # Any UNCERTAIN layout — only if not already POOR
    uncertain_count = layout_mode_counts.get('uncertain', 0)
    if uncertain_count > 0 and not reasons:
        review_triggers.append(
            StatusReason(
                category="layout",
                message=f"{uncertain_count} page(s) have uncertain layout",
                count=uncertain_count,
            )
        )
        if not problem_pages:
            problem_pages = list(range(1, total_pages + 1)) if total_pages else []

    # Any low-confidence OCR warning — only if not already POOR
    low_conf_count = report.low_confidence_block_count
    if low_conf_count > 0 and not reasons:
        review_triggers.append(
            StatusReason(
                category="ocr",
                message=f"{low_conf_count} block(s) have low OCR confidence",
                count=low_conf_count,
                page_numbers=report.pages_with_low_confidence,
            )
        )
        if not problem_pages:
            problem_pages = report.pages_with_low_confidence

    # OCR completed but recovered no usable text — REVIEW trigger.
    # Per approved semantics: SUCCESS when execution succeeds; this triggers
    # REVIEW (not FAILED/POOR) and signals the page is problematic without
    # counting toward the FAILED extraction percentage.
    ocr_no_text_pages = report.pages_with_low_confidence
    if ocr_no_text_pages and not reasons:
        review_triggers.append(
            StatusReason(
                category="ocr",
                message="OCR completed but recovered no usable text",
                count=len(ocr_no_text_pages),
                page_numbers=ocr_no_text_pages,
            )
        )
        if not problem_pages:
            problem_pages = ocr_no_text_pages

    # Store triggers on the report
    if review_triggers:
        report.status = ReportStatus.REVIEW
        # Combine POOR reasons and review triggers into status_reasons
        all_reasons = list(reasons)
        for r in review_triggers:
            if r not in all_reasons:
                all_reasons.append(r)
        report.status_reasons = all_reasons
    elif reasons:  # POOR was triggered
        report.status = ReportStatus.POOR
        report.status_reasons = reasons
    else:
        report.status = ReportStatus.GOOD
        report.status_reasons = []

    # Deduplicate and sort problem pages
    report.problem_pages = sorted(set(problem_pages))


# -----------------------------------------------------------------
# OCR diagnostics (already partially in base, but collect extra detail)
# -----------------------------------------------------------------

def _add_ocr_diagnostics(report: ExtractionReport, document: Document) -> None:
    """Add OCR-specific fields; no-op if no OCR blocks present."""
    # Track pages where OCR was attempted but recovered no usable text.
    # Per approved semantics: SUCCESS when execution succeeds even if zero text recovered;
    # this triggers REVIEW (not FAILED/POOR) and marks the page as problematic.
    ocr_failed_pages: List[int] = []
    for p in document.pages:
        if (p.extraction_status == ExtractionStatus.SUCCESS
                and p.extraction_method == ExtractionMethod.OCR
                and len(p.blocks) == 0):
            ocr_failed_pages.append(p.number)
    if ocr_failed_pages:
        report.ocr_block_count = 0  # already 0, but explicit for clarity
        report.pages_with_low_confidence = sorted(ocr_failed_pages)


# -----------------------------------------------------------------
# Warning aggregation
# -----------------------------------------------------------------

def _add_warnings(report: ExtractionReport, document: Document) -> None:
    """Aggregate warnings from page-level warnings; deduplicate."""

    # Already populated in base report from page.warnings.
    # Deduplicate by (page, message).
    seen: Set[tuple] = set()
    deduped: List[dict] = []
    for w in report.warnings:
        key = (w["page"], w["message"])
        if key not in seen:
            seen.add(key)
            deduped.append(w)
    report.warnings = deduped


# -----------------------------------------------------------------
# Status determination
# -----------------------------------------------------------------

def _determine_status(report: ExtractionReport) -> None:
    """Set report.status and ensure status_reasons is populated."""

    # If status_reasons already populated by _apply_policy, keep it.
    # Otherwise default to GOOD.
    if report.status_reasons:
        # status already determined by policy
        pass
    else:
        report.status = ReportStatus.GOOD