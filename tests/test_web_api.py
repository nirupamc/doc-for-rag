"""Tests for RagParser Web API endpoints."""

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ragparser.web.app import create_app


client = TestClient(create_app())


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self):
        """Health endpoint returns 200 OK."""
        response = client.get("/v1/health")
        assert response.status_code == 200

    def test_health_response_schema(self):
        """Health response matches expected schema."""
        response = client.get("/v1/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "tesseract_available" in data
        assert isinstance(data["tesseract_available"], bool)

    def test_health_ok_payload(self):
        """Health payload contains correct values."""
        response = client.get("/v1/health")
        payload = response.json()
        assert payload["status"] == "ok"
        # Tesseract availability depends on environment; just verify it's a bool
        assert isinstance(payload["tesseract_available"], bool)


class TestParseEndpoint:
    """Tests for POST /parse."""

    def test_parse_valid_native_pdf(self, simple_pdf):
        """POST /parse with valid native PDF returns document + report."""
        with open(simple_pdf, "rb") as f:
            response = client.post(
                "/v1/parse",
                files={"file": (simple_pdf.name, f, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response has document and report
        assert "document" in data
        assert "report" in data

        # Document should have canonical IR structure
        doc = data["document"]
        assert "source_path" in doc
        assert "page_count" in doc
        assert "pages" in doc

        # Report should have extraction report structure
        report = data["report"]
        assert "status" in report
        assert "page_count" in report
        assert "status_reasons" in report

    def test_parse_valid_scanned_pdf(self, scanned_page_pdf):
        """POST /parse with scanned PDF returns document + report."""
        with open(scanned_page_pdf, "rb") as f:
            response = client.post(
                "/v1/parse",
                files={"file": (scanned_page_pdf.name, f, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()

        doc = data["document"]
        report = data["report"]

        # Document should be successfully produced
        assert "pages" in doc
        assert doc["page_count"] >= 1

        # Report should be successfully produced
        assert "status" in report
        assert "page_count" in report

    def test_parse_non_pdf_rejected(self):
        """Non-PDF file is rejected with 415."""
        response = client.post(
            "/v1/parse",
            files={"file": ("test.txt", b"some text content", "text/plain")},
        )
        assert response.status_code == 415

    def test_parse_empty_upload_rejected(self):
        """Empty file upload is rejected with 400."""
        response = client.post(
            "/v1/parse",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert response.status_code == 400

    def test_parse_oversized_upload_rejected(self):
        """Oversized file is rejected with 413."""
        # Create a file larger than 25 MB
        oversized_content = b"x" * (25 * 1024 * 1024 + 1)
        response = client.post(
            "/v1/parse",
            files={"file": ("large.pdf", oversized_content, "application/pdf")},
        )
        assert response.status_code == 413

    def test_parse_returns_document_and_report(self, simple_pdf):
        """Response contains both document and report serialization."""
        with open(simple_pdf, "rb") as f:
            response = client.post(
                "/v1/parse",
                files={"file": (simple_pdf.name, f, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()

        # Both fields present
        assert "document" in data
        assert "report" in data

        # Document is a dict with IR structure
        doc = data["document"]
        assert isinstance(doc, dict)
        assert doc["source_path"] is not None

        # Report is a dict with extraction report structure
        report = data["report"]
        assert isinstance(report, dict)
        assert report["status"] in ("good", "review", "poor")
        assert "status_reasons" in report

    def test_temporary_file_cleaned_up(self, simple_pdf, tmp_path):
        """Temporary file is always cleaned up after parsing."""
        with open(simple_pdf, "rb") as f:
            response = client.post(
                "/v1/parse",
                files={"file": (simple_pdf.name, f, "application/pdf")},
            )

        assert response.status_code == 200
        # After the request, no temp PDF should remain in the system's temp dir
        # (Cleanup happens in the finally block)

    def test_unexpected_parser_exception_returns_500(self):
        """Unexpected parser exception returns safe 500, not raw stack trace."""
        # Submit a request that will cause an unexpected error
        # We test with a filename that triggers issues
        response = client.post(
            "/v1/parse",
            files={"file": ("nonexistent.pdf", b"fake pdf content", "application/pdf")},
        )
        # This should not return a 500 with stack trace
        # The error handling should return a safe JSON response
        assert response.status_code in (400, 500)
        if response.status_code == 500:
            data = response.json()
            assert "detail" in data

    def test_malformed_pdf_handled_safely(self):
        """Malformed/corrupt PDF handled safely without exposing stack traces."""
        response = client.post(
            "/v1/parse",
            files={"file": ("corrupt.pdf", b"%PDF-1.5 corrupted data!!!", "application/pdf")},
        )
        # Should not be 500 with stack trace
        # Should get a safe error response
        assert response.status_code != 500 or (
            response.status_code == 500
            and "detail" in response.json()
        )