"""
Page analysis signals — observable facts about a page.

These are raw measurements with NO interpretation.
Classification logic lives in classifier.py.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class PageSignals:
    """
    Observable page measurements — no interpretation.

    These are the raw facts that feed classification.
    All ratios are 0.0-1.0 for portability.
    """

    # Native text signals (observable)
    native_char_count: int = 0
    native_block_count: int = 0
    native_text_sample: str = ""  # first ~200 chars for inspection

    # Image signals (observable)
    image_count: int = 0
    largest_image_coverage: float = 0.0      # single largest image rect / page area
    summed_image_area_ratio: float = 0.0     # sum of all image rect areas / page area (may overlap)

    # Vector graphics signals (observable)
    drawing_count: int = 0
    drawing_coverage_ratio: float = 0.0

    # Page geometry
    page_width: float = 0.0
    page_height: float = 0.0
    page_area: float = 0.0

    # Derived observable booleans (directly from counts)
    has_native_text: bool = False      # native_char_count > 0
    has_images: bool = False           # image_count > 0
    has_drawings: bool = False         # drawing_count > 0

    def __post_init__(self) -> None:
        self.has_native_text = self.native_char_count > 0
        self.has_images = self.image_count > 0
        self.has_drawings = self.drawing_count > 0
        if self.page_width and self.page_height:
            self.page_area = self.page_width * self.page_height

    def to_dict(self) -> dict:
        return {
            "native_char_count": self.native_char_count,
            "native_block_count": self.native_block_count,
            "native_text_sample": self.native_text_sample,
            "image_count": self.image_count,
            "largest_image_coverage": self.largest_image_coverage,
            "summed_image_area_ratio": self.summed_image_area_ratio,
            "drawing_count": self.drawing_count,
            "drawing_coverage_ratio": self.drawing_coverage_ratio,
            "page_width": self.page_width,
            "page_height": self.page_height,
            "page_area": self.page_area,
            "has_native_text": self.has_native_text,
            "has_images": self.has_images,
            "has_drawings": self.has_drawings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PageSignals":
        return cls(
            native_char_count=data.get("native_char_count", 0),
            native_block_count=data.get("native_block_count", 0),
            native_text_sample=data.get("native_text_sample", ""),
            image_count=data.get("image_count", 0),
            largest_image_coverage=data.get("largest_image_coverage", 0.0),
            summed_image_area_ratio=data.get("summed_image_area_ratio", 0.0),
            drawing_count=data.get("drawing_count", 0),
            drawing_coverage_ratio=data.get("drawing_coverage_ratio", 0.0),
            page_width=data.get("page_width", 0.0),
            page_height=data.get("page_height", 0.0),
            page_area=data.get("page_area", 0.0),
            has_native_text=data.get("has_native_text", False),
            has_images=data.get("has_images", False),
            has_drawings=data.get("has_drawings", False),
        )