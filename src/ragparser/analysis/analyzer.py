"""
Page analysis — cheap inspection to collect signals and classify.

Performs lightweight page inspection (get_text, get_images, get_drawings)
without building full IR blocks. Avoids duplicate full extraction where possible.

Note: get_text("dict") still performs PyMuPDF text processing internally.
M2 accepts this small duplication; profile before optimizing.
"""

import fitz
from ragparser.analysis.signals import PageSignals
from ragparser.analysis.classifier import ClassificationResult, classify


class PageAnalyzer:
    """
    Analyzes a page to produce signals and classification.

    Responsibilities:
    - Cheap page inspection (text, images, drawings)
    - Signal collection
    - Classification via classifier module
    """

    def __init__(self) -> None:
        self._max_text_sample = 200

    def analyze_page(self, page: fitz.Page, page_number: int) -> ClassificationResult:
        """
        Analyze a single page.

        Args:
            page: PyMuPDF page object
            page_number: 1-indexed page number

        Returns:
            ClassificationResult with classification, reason, and signals
        """
        signals = self._collect_signals(page)
        return classify(signals)

    def _collect_signals(self, page: fitz.Page) -> PageSignals:
        """Collect observable signals from a page."""
        # Page geometry
        page_width = page.rect.width
        page_height = page.rect.height

        # Native text signals
        text_dict = page.get_text("dict")
        native_char_count = 0
        native_block_count = 0
        text_sample_parts = []

        for block_dict in text_dict.get("blocks", []):
            if block_dict["type"] != 0:  # 0 = text block
                continue
            native_block_count += 1
            for line in block_dict.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if text:
                        native_char_count += len(text)
                        if len("".join(text_sample_parts)) < self._max_text_sample:
                            text_sample_parts.append(text)

        native_text_sample = "".join(text_sample_parts)[:self._max_text_sample]

        # Image signals
        image_count, largest_image_coverage, summed_image_area_ratio = self._collect_image_signals(page)

        # Drawing signals
        drawing_count, drawing_coverage_ratio = self._collect_drawing_signals(page)

        return PageSignals(
            native_char_count=native_char_count,
            native_block_count=native_block_count,
            native_text_sample=native_text_sample,
            image_count=image_count,
            largest_image_coverage=largest_image_coverage,
            summed_image_area_ratio=summed_image_area_ratio,
            drawing_count=drawing_count,
            drawing_coverage_ratio=drawing_coverage_ratio,
            page_width=page_width,
            page_height=page_height,
        )

    def _collect_image_signals(self, page: fitz.Page) -> tuple[int, float, float]:
        """
        Collect image signals.

        Returns:
            (image_count, largest_image_coverage, summed_image_area_ratio)

        Note: summed_image_area_ratio may exceed 1.0 if images overlap (capped at 1.0).
              largest_image_coverage is more reliable for scanned-page detection.
        """
        page_area = page.rect.width * page.rect.height
        if page_area == 0:
            return 0, 0.0, 0.0

        images = page.get_images()
        if not images:
            return 0, 0.0, 0.0

        largest = 0.0
        total = 0.0
        for img in images:
            xref = img[0]
            for r in page.get_image_rects(xref):
                area = r.width * r.height
                total += area
                if area > largest:
                    largest = area

        return (
            len(images),
            min(largest / page_area, 1.0),
            min(total / page_area, 1.0),
        )

    def _collect_drawing_signals(self, page: fitz.Page) -> tuple[int, float]:
        """
        Collect vector graphics (drawing) signals.

        Returns:
            (drawing_count, drawing_coverage_ratio)
        """
        page_area = page.rect.width * page.rect.height
        if page_area == 0:
            return 0, 0.0

        drawings = page.get_drawings()
        if not drawings:
            return 0, 0.0

        # Sum drawing bounding rect areas (approximate)
        total_area = sum(d["rect"].width * d["rect"].height for d in drawings)
        return len(drawings), min(total_area / page_area, 1.0)