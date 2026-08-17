"""
Extraction router — maps page classification to extraction strategy.
"""

from enum import Enum
from ragparser.analysis.classifier import ClassificationResult
from ragparser.ir import PageClassification


class ExtractionStrategy(Enum):
    """Extraction strategy for a page."""
    NATIVE = "native"
    OCR_REQUIRED = "ocr_required"
    EMPTY = "empty"
    SUSPICIOUS = "suspicious"


class ExtractionRouter:
    """
    Routes page classification to extraction strategy.

    M2: OCR_REQUIRED returns placeholder (OCR implemented in M3).
    """

    def route(self, classification: ClassificationResult) -> ExtractionStrategy:
        """Map classification to extraction strategy."""
        cls = classification.classification

        if cls == PageClassification.NATIVE:
            return ExtractionStrategy.NATIVE
        elif cls == PageClassification.OCR_REQUIRED:
            return ExtractionStrategy.OCR_REQUIRED
        elif cls == PageClassification.EMPTY:
            return ExtractionStrategy.EMPTY
        elif cls == PageClassification.SUSPICIOUS:
            return ExtractionStrategy.SUSPICIOUS
        else:
            return ExtractionStrategy.SUSPICIOUS

    def get_strategy_name(self, strategy: ExtractionStrategy) -> str:
        """Human-readable strategy name."""
        return strategy.value