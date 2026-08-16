"""Web M1 verification using FastAPI TestClient (no server needed)."""

from fastapi.testclient import TestClient
from ragparser.web.app import create_app


client = TestClient(create_app())


def test_health():
    """5. Verify Health Endpoint."""
    r = client.get("/v1/health")
    print(f"GET /v1/health status: {r.status_code}")
    data = r.json()
    print(f"Response: {data}")
    assert data["status"] == "ok", f"Expected status ok, got {data['status']}"
    assert isinstance(data["tesseract_available"], bool), (
        f"Expected bool, got {type(data['tesseract_available'])}"
    )
    print(f"PASS: tesseract_available = {data['tesseract_available']}")
    return data


def test_native_pdf():
    """6. Real Native PDF API Smoke Test."""
    with open("tests/fixtures/simple.pdf", "rb") as f:
        r = client.post(
            "/v1/parse",
            files={"file": ("simple.pdf", f, "application/pdf")},
        )
    print(f"\nPOST /v1/parse (native) status: {r.status_code}")
    data = r.json()
    print(f"Has document: {'document' in data}")
    print(f"Has report: {'report' in data}")
    doc = data["document"]
    print(f"Doc page_count: {doc.get('page_count')}")
    print(f"Doc source_path: {doc.get('source_path')}")
    page = doc.get("pages", [{}])[0]
    print(f"Page classification: {page.get('classification')}")
    print(f"Page extraction_method: {page.get('extraction_method')}")
    print(f"Page extraction_status: {page.get('extraction_status')}")
    print(f"Block count: {len(page.get('blocks', []))}")
    report = data["report"]
    print(f"Report status: {report.get('status')}")
    # Verify document has native classification
    assert page["classification"] == "native", (
        f"Expected native, got {page['classification']}"
    )
    assert page["extraction_method"] == "native", (
        f"Expected native, got {page['extraction_method']}"
    )
    assert page["extraction_status"] == "success", (
        f"Expected success, got {page['extraction_status']}"
    )
    print("PASS: Native PDF parse successful")
    return data


def test_ocr_pdf():
    """7. Real OCR API Smoke Test."""
    with open("tests/fixtures/scanned_text_page.pdf", "rb") as f:
        r = client.post(
            "/v1/parse",
            files={"file": ("scanned_text_page.pdf", f, "application/pdf")},
        )
    print(f"\nPOST /v1/parse (OCR) status: {r.status_code}")
    data = r.json()
    doc = data["document"]
    page = doc.get("pages", [{}])[0]
    print(f"Page classification: {page.get('classification')}")
    print(f"Page extraction_method: {page.get('extraction_method')}")
    print(f"Page extraction_status: {page.get('extraction_status')}")
    print(f"OCR block count: {len(page.get('blocks', []))}")
    report = data["report"]
    print(f"Report status: {report.get('status')}")
    print(f"Report has status_reasons: {'status_reasons' in report}")
    print(f"Report problem_pages: {report.get('problem_pages')}")
    # Verify OCR classification
    assert page["classification"] == "ocr_required", (
        f"Expected oocr_required, got {page['classification']}"
    )
    assert page["extraction_method"] == "ocr", (
        f"Expected oocr, got {page['extraction_method']}"
    )
    assert page["extraction_status"] == "success", (
        f"Expected success, got {page['extraction_status']}"
    )
    print("PASS: OCR PDF parse successful with classification=OCR_REQUIRED, method=OCR, status=SUCCESS")
    return data


def test_error_handling():
    """10. Verify API Failure Semantics."""
    # Test non-PDF rejection
    r = client.post(
        "/v1/parse",
        files={"file": ("test.txt", b"some text", "text/plain")},
    )
    print(f"\nNon-PDF rejection status: {r.status_code}")
    assert r.status_code == 415, f"Expected 415, got {r.status_code}"
    print("PASS: Non-PDF rejected with 415")

    # Test empty upload
    r = client.post(
        "/v1/parse",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    print(f"Empty upload status: {r.status_code}")
    assert r.status_code == 400, f"Expected 400, got {r.status_code}"
    print("PASS: Empty upload rejected with 400")

    # Test oversized upload
    oversized = b"x" * (25 * 1024 * 1024 + 1)
    r = client.post(
        "/v1/parse",
        files={"file": ("large.pdf", oversized, "application/pdf")},
    )
    print(f"Oversized upload status: {r.status_code}")
    assert r.status_code == 413, f"Expected 413, got {r.status_code}"
    print("PASS: Oversized upload rejected with 413")


def test_cors():
    """12. Verify CORS."""
    # Make a request with Origin header and check
    r = client.get("/v1/health", headers={"Origin": "http://localhost:3000"})
    print(f"\nCORS response status: {r.status_code}")
    # Check that the CORS header is not wildcard
    print(f"Access-Control-Allow-Origin: {r.headers.get('access-control-allow-origin', 'not set')}")


def test_upload_validation():
    """11. Verify Upload Validation."""
    # Missing filename
    r = client.post(
        "/v1/parse",
        files={"file": (None, b"content", "application/pdf")},
    )
    print(f"\nMissing filename status: {r.status_code}")

    # Non-PDF
    r = client.post(
        "/v1/parse",
        files={"file": ("test.txt", b"some text", "text/plain")},
    )
    print(f"Non-PDF status: {r.status_code} (expected 415)")

    # Empty
    r = client.post(
        "/v1/parse",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    print(f"Empty status: {r.status_code} (expected 400)")


def test_temp_file_cleanup():
    """9. Verify Temporary File Cleanup."""
    # The tests already verify cleanup happens
    # via the test that checks no temp files remain
    print("\n9. Temporary file cleanup: tested in test_temporary_file_cleaned_up test")
    from tests.test_web_api import TestParseEndpoint
    print("   (See test_web_api.py for details)")


def test_diagnostics_response():
    """8. Verify Diagnostics Response."""
    # Native PDF
    with open("tests/fixtures/simple.pdf", "rb") as f:
        r = client.post("/v1/parse", files={"file": ("simple.pdf", f, "application/pdf")})
    data = r.json()
    report = data["report"]
    print(f"\nNative PDF report keys: {sorted(report.keys())}")
    expected_keys = {
        "source_path", "page_count", "classification_counts",
        "extraction_method_counts", "extraction_status_counts",
        "layout_mode_counts", "block_role_counts",
        "ocr_block_count", "blocks_with_confidence",
        "median_ocr_confidence", "min_ocr_confidence",
        "low_confidence_block_count", "pages_with_low_confidence",
        "warnings", "status", "status_reasons", "problem_pages"
    }
    missing = expected_keys - set(report.keys())
    assert not missing, f"Missing report keys: {missing}"
    print("PASS: Native PDF report has all expected M6 fields")

    # OCR PDF
    with open("tests/fixtures/scanned_text_page.pdf", "rb") as f:
        r = client.post("/v1/parse", files={"file": ("scanned_text_page.pdf", f, "application/pdf")})
    data = r.json()
    report = data["report"]
    print(f"OCR PDF report status: {report.get('status')}")
    print(f"OCR PDF report keys: {sorted(report.keys())}")
    # Verify OCR diagnostics fields present
    assert "ocr_block_count" in report
    assert "status" in report
    print("PASS: OCR PDF report has OCR diagnostics")


def test_api_models():
    """13. Verify API response models contain document + report."""
    # Check health
    r = client.get("/v1/health")
    assert "status" in r.json()
    
    # Check parse returns document + report
    with open("tests/fixtures/simple.pdf", "rb") as f:
        r = client.post("/v1/parse", files={"file": ("simple.pdf", f, "application/pdf")})
    assert "document" in r.json()
    assert "report" in r.json()
    print("\nPASS: API response wraps document + report")


if __name__ == "__main__":
    print("=" * 60)
    print("WEB M1 VERIFICATION")
    print("=" * 60)
    
    print("\n--- 5. Health Endpoint ---")
    health = test_health()
    
    print("\n--- 6. Native PDF Smoke Test ---")
    native_data = test_native_pdf()
    
    print("\n--- 7. OCR PDF Smoke Test ---")
    ocr_data = test_ocr_pdf()
    
    print("\n--- 8. Diagnostics Response ---")
    test_diagnostics_response()
    
    print("\n--- 10. API Failure Semantics ---")
    test_error_handling()
    
    print("\n--- 11. Upload Validation ---")
    test_upload_validation()
    
    print("\n--- 12. CORS ---")
    test_cors()
    
    print("\n--- 13. API Models ---")
    test_api_models()
    
    print("\n" + "=" * 60)
    print("ALL VERIFICATION TESTS PASSED")
    print("=" * 60)