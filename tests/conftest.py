"""Test configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def simple_pdf() -> Path:
    return Path("tests/fixtures/simple.pdf")


@pytest.fixture
def two_page_pdf() -> Path:
    return Path("tests/fixtures/two_pages.pdf")


@pytest.fixture
def nonexistent_pdf() -> Path:
    return Path("tests/fixtures/does_not_exist.pdf")


# M2 fixtures
@pytest.fixture
def empty_page_pdf() -> Path:
    return Path("tests/fixtures/empty_page.pdf")


@pytest.fixture
def scanned_page_pdf() -> Path:
    return Path("tests/fixtures/scanned_page.pdf")


@pytest.fixture
def mixed_page_pdf() -> Path:
    return Path("tests/fixtures/mixed_page.pdf")


@pytest.fixture
def garbled_page_pdf() -> Path:
    return Path("tests/fixtures/garbled_page.pdf")


@pytest.fixture
def sparse_page_pdf() -> Path:
    return Path("tests/fixtures/sparse_page.pdf")


@pytest.fixture
def drawing_page_pdf() -> Path:
    return Path("tests/fixtures/drawing_page.pdf")


@pytest.fixture
def text_with_large_image_pdf() -> Path:
    return Path("tests/fixtures/text_with_large_image.pdf")


@pytest.fixture
def mixed_document_pdf() -> Path:
    return Path("tests/fixtures/mixed_document.pdf")