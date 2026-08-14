"""Backend package for RagParser extraction backends."""

from ragparser.backends.base import BackendProtocol, OCRBackend
from ragparser.backends.native import NativeExtractor
from ragparser.backends.ocr import TesseractOCRBackend

__all__ = [
    "BackendProtocol",
    "OCRBackend",
    "NativeExtractor",
    "TesseractOCRBackend",
]