"""Route handlers for the RagParser Web API."""

import io
import tempfile
import os
import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse

from ragparser.parser import DocumentParser
from ragparser.diagnostics import analyze_document
from ragparser.web.schemas import (
    HealthResponse,
    ParseResponse,
    ErrorResponse,
    ParseRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["ragparser"])

# Development file size limit: 25 MB
MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MB


def _validate_upload(
    filename: str,
    content_type: str | None,
    file_bytes: bytes,
) -> None:
    """Validate uploaded file. Raises HTTPException on failure."""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing filename",
        )

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {filename}. Only PDF is accepted.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {len(file_bytes)} bytes. Maximum {MAX_FILE_BYTES // (1024 * 1024)} MB.",
        )

    # PyMuPDF validation: write to temp file then open (fitz.open requires a path)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        document = fitz.open(tmp_path)
        if document.page_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded PDF has no pages.",
            )
        document.close()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or malformed PDF: {exc}",
        ) from exc
    finally:
        # Clean up temp validation file immediately after check
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check() -> HealthResponse:
    """Return API health status and Tesseract availability."""
    from ragparser.backends.ocr import TesseractOCRBackend

    ocr_backend = TesseractOCRBackend()
    tesseract_available = ocr_backend.is_available()

    return HealthResponse(
        status="ok",
        tesseract_available=bool(tesseract_available),
    )


@router.post(
    "/parse",
    response_model=ParseResponse,
    summary="Parse a PDF document",
)
async def parse_document(
    file: UploadFile = File(
        ...,
        description="PDF file to parse",
    ),
) -> ParseResponse:
    """
    Parse an uploaded PDF and return the canonical Document IR + ExtractionReport.

    Processing flow:
    - Upload validation (filename, extension, size, content type, PyMuPDF check)
    - Temporary file (cleaned up after response)
    - DocumentParser.parse() → Document IR
    - DiagnosticsAnalyzer → ExtractionReport
    - Serialize and return
    """
    # Read file bytes early for validation
    file_bytes = await file.read()

    # Validate upload
    _validate_upload(filename=file.filename or "", content_type=file.content_type, file_bytes=file_bytes)

    temp_path: str | None = None
    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            temp_path = tmp.name

        # Parse with DocumentParser
        parser = DocumentParser()
        doc = parser.parse(temp_path)

        # Generate diagnostics report
        report = analyze_document(doc)

        # Serialize using canonical to_dict()
        return ParseResponse(
            document=doc.to_dict(),
            report=report.to_dict(),
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as exc:
        # Unexpected server failure - log and return 500
        logger.exception("Unexpected error during PDF parsing")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the PDF.",
        ) from exc
    finally:
        # Always clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass  # Best effort cleanup