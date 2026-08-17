"""
Page classification logic.

Pure functions: signals -> classification.
No I/O, no PyMuPDF dependencies.
"""

from dataclasses import dataclass
from typing import Optional
from ragparser.ir import PageClassification
from ragparser.analysis.signals import PageSignals


@dataclass(slots=True)
class ClassificationResult:
    """Result of page classification with explanation."""
    classification: PageClassification
    reason: str
    signals: PageSignals  # attached for explainability


def classify(signals: PageSignals) -> ClassificationResult:
    """
    Classify a page based on observable signals.

    Conservative rules:
    - EMPTY: truly nothing observable
    - OCR_REQUIRED: no native text, large image dominates page
    - NATIVE: substantial native text, images incidental
    - SUSPICIOUS: ambiguous cases (text + large image, sparse text + image,
      drawings only, garbled text) — defer to M3 hybrid extraction
    """
    # 1. EMPTY — truly nothing observable
    if not signals.has_native_text and not signals.has_images and not signals.has_drawings:
        return ClassificationResult(
            PageClassification.EMPTY,
            "No native text, images, or vector graphics detected.",
            signals
        )

    # 2. OCR_REQUIRED — no native text, large image dominates
    if not signals.has_native_text and signals.has_images:
        if signals.largest_image_coverage >= 0.5:
            return ClassificationResult(
                PageClassification.OCR_REQUIRED,
                f"No native text; largest image covers {signals.largest_image_coverage:.1%} of page.",
                signals
            )
        else:
            return ClassificationResult(
                PageClassification.SUSPICIOUS,
                f"No native text; only small image ({signals.largest_image_coverage:.1%} coverage).",
                signals
            )

    # 3. Has native text — evaluate conservatively
    if signals.has_native_text:
        suspicious_reason = _check_suspicious_text(signals)
        if suspicious_reason:
            return ClassificationResult(
                PageClassification.SUSPICIOUS,
                suspicious_reason,
                signals
            )

        # Substantial text + incidental images -> NATIVE
        if signals.largest_image_coverage < 0.3 and signals.native_char_count >= 50:
            return ClassificationResult(
                PageClassification.NATIVE,
                f"Native text ({signals.native_char_count} chars); images incidental ({signals.largest_image_coverage:.1%}).",
                signals
            )

        # Text present but large image dominates -> SUSPICIOUS (not HYBRID yet)
        if signals.largest_image_coverage >= 0.5:
            return ClassificationResult(
                PageClassification.SUSPICIOUS,
                f"Native text ({signals.native_char_count} chars) but large image covers {signals.largest_image_coverage:.1%} — may need OCR.",
                signals
            )

        # Default: text exists, images small -> NATIVE
        return ClassificationResult(
            PageClassification.NATIVE,
            f"Native text ({signals.native_char_count} chars); images present ({signals.largest_image_coverage:.1%}).",
            signals
        )

    # 4. Drawings only (no text, no images)
    if signals.has_drawings:
        return ClassificationResult(
            PageClassification.SUSPICIOUS,
            f"Vector graphics only ({signals.drawing_count} drawings); no extractable text or images.",
            signals
        )

    # Fallback
    return ClassificationResult(
        PageClassification.SUSPICIOUS,
        "Unable to confidently classify page.",
        signals
    )


def _check_suspicious_text(signals: PageSignals) -> Optional[str]:
    """
    Limited conservative heuristics for suspicious text.

    NOT robust garbled-text detection — only catches obvious cases.
    Real pathological PDFs should become benchmark documents in later milestones.
    """
    text = signals.native_text_sample
    if not text:
        return None

    # Replacement character ratio (limited heuristic)
    repl_count = text.count('\uFFFD')
    if repl_count > 0 and repl_count / len(text) > 0.3:
        return f"High replacement char ratio ({repl_count}/{len(text)}) — text layer may be corrupted."

    # Extreme sparsity on normal-sized page is NOT suspicious alone.
    # Legitimate pages can have very little text (titles, dividers, dedications).
    # Sparse text + dominant image is handled in the main classifier.

    return None