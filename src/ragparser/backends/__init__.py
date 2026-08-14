"""Backend package for RagParser extraction backends."""

from ragparser.backends.base import BackendProtocol
from ragparser.backends.native import NativeExtractor

__all__ = [
    "BackendProtocol",
    "NativeExtractor",
]