"""Tests for CLI."""

import json
import subprocess
import sys
from pathlib import Path


def test_cli_parse_simple(simple_pdf):
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "parse", str(simple_pdf)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["source_path"] == str(simple_pdf)
    assert data["page_count"] == 1
    assert len(data["pages"]) == 1


def test_cli_parse_two_pages(two_page_pdf):
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "parse", str(two_page_pdf)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["page_count"] == 2
    assert len(data["pages"]) == 2


def test_cli_parse_output_file(simple_pdf, tmp_path):
    output_file = tmp_path / "output.json"
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "parse", str(simple_pdf), "-o", str(output_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["page_count"] == 1


def test_cli_parse_pretty(simple_pdf):
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "parse", str(simple_pdf), "--pretty"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Pretty output should have newlines and indentation
    assert "\n" in result.stdout
    assert "  " in result.stdout


def test_cli_parse_invalid_file():
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "parse", "nonexistent.pdf"],
        capture_output=True,
        text=True,
    )
    # Typer returns 2 for invalid argument errors
    assert result.returncode == 2
    assert "Error" in result.stderr or "does not exist" in result.stderr


def test_cli_info(simple_pdf):
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "info", str(simple_pdf)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Pages: 1" in result.stdout
    assert "Page 1:" in result.stdout


def test_cli_info_two_pages(two_page_pdf):
    result = subprocess.run(
        [sys.executable, "-m", "ragparser.cli", "info", str(two_page_pdf)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Pages: 2" in result.stdout
    assert "Page 1:" in result.stdout
    assert "Page 2:" in result.stdout