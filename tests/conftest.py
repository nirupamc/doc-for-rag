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