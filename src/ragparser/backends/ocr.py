"""
Tesseract OCR backend using pytesseract.

Responsibilities:
- Verify Tesseract executable availability
- Render PDF page to image at configured DPI
- Run Tesseract OCR with detailed output (DICT)
- Group words into geometric blocks using Tesseract's block_num hierarchy
- Convert pixel coordinates to canonical PDF points via derotation_matrix
- Normalize confidence to 0.0-1.0
- Produce canonical RagParser Page IR
"""

import pytesseract
from PIL import Image
import fitz

from ragparser.ir import (
    Block,
    BlockType,
    BoundingBox,
    ExtractionMethod,
    ExtractionStatus,
    Page,
)
from ragparser.backends.base import OCRBackend


class TesseractOCRBackend:
    """
    Tesseract OCR backend using pytesseract.

    Uses Tesseract's built-in layout hierarchy (block_num, par_num, line_num)
    for geometric block grouping. Does not attempt semantic paragraph
    reconstruction (headings, headers, footers) — that belongs to later stages.
    """

    def __init__(self, dpi: int = 300, language: str = "eng") -> None:
        self._dpi = dpi
        self._language = language
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if tesseract executable is in PATH."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        return self._available

    def get_dpi(self) -> int:
        return self._dpi

    def get_method_name(self) -> str:
        return "ocr"

    def extract_page(self, page: "fitz.Page", page_number: int) -> Page:
        if not self._available:
            return self._failed_page(
                page,
                page_number,
                "Tesseract not available. Install tesseract-ocr and ensure it's in PATH."
            )

        try:
            # 1. Render page to PIL Image at configured DPI
            image = self._render_page(page)

            # 2. Run Tesseract with detailed output
            ocr_data = pytesseract.image_to_data(
                image,
                lang=self._language,
                output_type=pytesseract.Output.DICT,
            )

            # 3. Group words into blocks and convert coordinates
            blocks = self._group_into_blocks(
                ocr_data,
                page_number,
                image.width,
                image.height,
                page.rect.width,
                page.rect.height,
                page.derotation_matrix,
            )

            ir_page = Page(
                number=page_number,
                width=page.rect.width,
                height=page.rect.height,
                blocks=blocks,
                rotation=page.rotation,
            )
            ir_page.extraction_status = ExtractionStatus.SUCCESS
            ir_page.extraction_method = ExtractionMethod.OCR

            if not blocks:
                ir_page.warnings = [
                    "OCR completed successfully but recovered no usable text."
                ]

            return ir_page

        except pytesseract.TesseractError as e:
            return self._failed_page(page, page_number, f"TesseractError: {e}")
        except Exception as e:
            return self._failed_page(page, page_number, f"{type(e).__name__}: {e}")

    def _render_page(self, page: "fitz.Page") -> Image.Image:
        """Render PDF page to PIL Image at configured DPI."""
        zoom = self._dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    def _group_into_blocks(
        self,
        ocr_data: dict,
        page_number: int,
        img_w: int,
        img_h: int,
        page_w: float,
        page_h: float,
        derotation_matrix: fitz.Matrix,
    ) -> list[Block]:
        """
        Group Tesseract words into geometric blocks by block_num.

        Uses Tesseract's hierarchy: block_num -> par_num -> line_num -> word_num.
        Produces coarse text regions with bbox, text, confidence.
        """
        # Filter valid word entries (level=5, text non-empty, conf >= 0)
        words = []
        for i in range(len(ocr_data["text"])):
            text = ocr_data["text"][i].strip()
            conf = ocr_data["conf"][i]
            if text and conf >= 0:
                words.append({
                    "block_num": ocr_data["block_num"][i],
                    "par_num": ocr_data["par_num"][i],
                    "line_num": ocr_data["line_num"][i],
                    "word_num": ocr_data["word_num"][i],
                    "text": text,
                    "conf": conf,
                    "left": ocr_data["left"][i],
                    "top": ocr_data["top"][i],
                    "width": ocr_data["width"][i],
                    "height": ocr_data["height"][i],
                })

        if not words:
            return []

        # Group by block_num
        blocks_by_num = {}
        for w in words:
            bn = w["block_num"]
            if bn not in blocks_by_num:
                blocks_by_num[bn] = []
            blocks_by_num[bn].append(w)

        # Sort block_nums for reading order
        sorted_block_nums = sorted(blocks_by_num.keys())

        # Convert each block
        ir_blocks = []
        for reading_order, bn in enumerate(sorted_block_nums):
            block_words = blocks_by_num[bn]

            # Sort words by reading order within block
            block_words.sort(key=lambda w: (w["par_num"], w["line_num"], w["word_num"]))

            # Concatenate text
            text_parts = [w["text"] for w in block_words]
            block_text = " ".join(text_parts)

            # Compute block bbox = union of word bboxes (in pixel coords)
            min_left = min(w["left"] for w in block_words)
            min_top = min(w["top"] for w in block_words)
            max_right = max(w["left"] + w["width"] for w in block_words)
            max_bottom = max(w["top"] + w["height"] for w in block_words)

            # Convert pixel bbox -> page points -> canonical points
            # Step 1: pixels -> page points (using page.rect which matches rendered image)
            page_x0 = min_left * page_w / img_w
            page_y0 = min_top * page_h / img_h
            page_x1 = max_right * page_w / img_w
            page_y1 = max_bottom * page_h / img_h

            # Step 2: page points -> canonical points (apply derotation_matrix)
            corners_page = [
                fitz.Point(page_x0, page_y0),
                fitz.Point(page_x1, page_y0),
                fitz.Point(page_x0, page_y1),
                fitz.Point(page_x1, page_y1),
            ]
            corners_canon = [c * derotation_matrix for c in corners_page]
            xs = [c.x for c in corners_canon]
            ys = [c.y for c in corners_canon]
            canonical_bbox = BoundingBox(
                x0=min(xs),
                y0=min(ys),
                x1=max(xs),
                y1=max(ys),
            )

            # Block confidence = median of word confidences, normalized to 0.0-1.0
            confs = [w["conf"] for w in block_words]
            confs.sort()
            median_conf = confs[len(confs) // 2] / 100.0

            ir_blocks.append(Block(
                type=BlockType.TEXT,
                text=block_text,
                bbox=canonical_bbox,
                extraction_method=ExtractionMethod.OCR,
                confidence=median_conf,
                page_number=page_number,
                reading_order=reading_order,
            ))

        return ir_blocks

    def _failed_page(self, page: "fitz.Page", page_number: int, reason: str) -> Page:
        ir_page = Page(
            number=page_number,
            width=page.rect.width,
            height=page.rect.height,
            blocks=[],
            rotation=page.rotation,
        )
        ir_page.extraction_status = ExtractionStatus.FAILED
        ir_page.extraction_method = ExtractionMethod.OCR
        ir_page.warnings = [f"OCR failed [{reason}]"]
        return ir_page