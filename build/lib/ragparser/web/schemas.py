"""Pydantic models for the RagParser Web API request/response."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, Field


class ParseResponse(BaseModel):
    """Response wrapper for POST /parse output."""

    document: Dict[str, Any] = Field(
        description="Canonical Document IR serialization (to_dict output)"
    )
    report: Dict[str, Any] = Field(
        description="ExtractionReport serialization (to_dict output)"
    )


class HealthResponse(BaseModel):
    """Response wrapper for GET /health output."""

    status: str = Field(description="Overall API status", pattern=r"^(ok|error)$")
    tesseract_available: bool = Field(
        description="Whether Tesseract OCR backend is available"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str = Field(description="Human-readable error message")
    code: str = Field(description="Error type/classification")


class ParseRequest(BaseModel):
    """Request model for POST /parse (validated by FastAPI multipart handling)."""

    pass  # No body fields; the file is uploaded via multipart/form-data "file" field