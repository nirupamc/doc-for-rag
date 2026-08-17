"""Typer CLI for RagParser."""

import json
import sys
from pathlib import Path
import typer
from ragparser.parser import DocumentParser

app = typer.Typer(
    name="ragparser",
    help="Document parsing pipeline for RAG applications",
    add_completion=False,
)


@app.command()
def parse(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to input PDF document",
    ),
    output: Path | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Output file path (default: stdout)",
    ),
    pretty: bool = typer.Option(
        False,
        "--pretty",
        help="Pretty-print JSON output",
    ),
) -> None:
    """
    Parse a PDF document and output the canonical IR as JSON.
    """
    parser = DocumentParser()

    try:
        doc = parser.parse(input_path)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    output_data = doc.to_dict()
    json_str = json.dumps(output_data, indent=2 if pretty else None, ensure_ascii=False)

    if output:
        output.write_text(json_str, encoding="utf-8")
        typer.echo(f"Written to {output}")
    else:
        typer.echo(json_str)


@app.command()
def info(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to input PDF document",
    ),
    analyze: bool = typer.Option(
        True,
        "--analyze/--no-analyze",
        help="Show per-page analysis (classification, signals, layout)",
    ),
) -> None:
    """
    Show document information with optional per-page analysis.
    """
    parser = DocumentParser()

    try:
        if analyze:
            analyses = parser.analyze_with_layout(input_path)
            doc = parser.parse(input_path)
        else:
            doc = parser.parse(input_path)
            analyses = []
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Source: {doc.source_path}")
    typer.echo(f"Pages: {doc.page_count}")
    typer.echo(f"Metadata: {doc.metadata}")
    if doc.warnings:
        typer.echo(f"Warnings: {doc.warnings}")

    for i, page in enumerate(doc.pages):
        block_count = len(page.blocks)
        text_chars = sum(len(b.text) for b in page.blocks)

        if analyze and i < len(analyses):
            a, layout = analyses[i]
            s = a.signals
            typer.echo(f"  Page {page.number}:")
            typer.echo(f"    Classification: {a.classification.value.upper()}")
            if page.extraction_method:
                typer.echo(f"    Extraction method: {page.extraction_method.value.upper()}")
            if page.extraction_status:
                typer.echo(f"    Extraction status: {page.extraction_status.value.upper()}")
            if page.layout_mode:
                typer.echo(f"    Layout mode: {page.layout_mode.value.upper()}")
                typer.echo(f"    Layout reason: {page.layout_reason}")
            typer.echo(f"    Reason: {a.reason}")
            typer.echo(f"    Native chars: {s.native_char_count}")
            typer.echo(f"    Native blocks: {s.native_block_count}")
            typer.echo(f"    Images: {s.image_count}")
            typer.echo(f"    Largest image coverage: {s.largest_image_coverage:.1%}")
            if s.summed_image_area_ratio > 0:
                typer.echo(f"    Summed image area ratio: {s.summed_image_area_ratio:.1%}")
            if s.drawing_count > 0:
                typer.echo(f"    Drawings: {s.drawing_count}")
            if layout:
                typer.echo(f"    Raw extraction order: {layout.input_order}")
                typer.echo(f"    Resolved reading order: {layout.resolved_order}")
            if page.warnings:
                typer.echo(f"    Warnings: {page.warnings}")
        else:
            typer.echo(f"  Page {page.number}: {block_count} blocks, {text_chars} chars")
            if page.extraction_method:
                typer.echo(f"    Extraction method: {page.extraction_method.value.upper()}")
            if page.extraction_status:
                typer.echo(f"    Extraction status: {page.extraction_status.value.upper()}")


import json
from pathlib import Path
import typer
from ragparser.parser import DocumentParser
from ragparser.diagnostics import analyze_document, ExtractionReport, ReportStatus


@app.command()
def report(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        readable=True,
        help="Path to input PDF document",
    ),
    output: Path | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Output file path (default: stdout)",
    ),
    pretty: bool = typer.Option(
        False,
        "--pretty",
        help="Pretty-print JSON report",
    ),
) -> None:
    """
    Generate an extraction diagnostics report for a parsed PDF document.

    Reports extraction counts, layout summary, structure summary,
    OCR diagnostics, warning aggregation, overall status with reasons,
    and problem-page listing.
    """
    parser = DocumentParser()

    try:
        doc = parser.parse(input_path)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    report = analyze_document(doc)

    # Decide output format
    if output:
        if pretty:
            json_str = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        else:
            json_str = json.dumps(report.to_dict(), ensure_ascii=False)
        output.write_text(json_str, encoding="utf-8")
        typer.echo(f"Written to {output}")
    else:
        _print_report_text(report)


def _print_report_text(report: ExtractionReport) -> None:
    """Print a human-readable extraction report to typer output."""

    lines: list[str] = []

    # Document header
    lines.append("RagParser Extraction Report")
    lines.append(f"Document: {report.source_path}")
    lines.append(f"Pages: {report.page_count}")
    lines.append("")

    # Extraction section
    lines.append("Extraction:")
    lines.append(f"  Native:      {report.classification_counts.get('native', 0)}")
    lines.append(f"  OCR:           {report.classification_counts.get('ocr_required', 0)}")
    lines.append(f"  Empty:         {report.classification_counts.get('empty', 0)}")
    lines.append(f"  Suspicious:    {report.classification_counts.get('suspicious', 0)}")
    lines.append("")

    # Extraction method counts
    lines.append("  (extraction method counts)")
    lines.append(f"  Native blocks: {report.extraction_method_counts.get('native', 0)}")
    lines.append(f"  OCR blocks:      {report.extraction_method_counts.get('ocr', 0)}")
    lines.append("")

    # Extraction status counts
    lines.append("  (extraction status counts)")
    lines.append(f"  Success: {report.extraction_status_counts.get('success', 0)}")
    lines.append(f"  Failed:  {report.extraction_status_counts.get('failed', 0)}")
    lines.append("")

    # Layout section
    lines.append("Layout:")
    lines.append(f"  Single:      {report.layout_mode_counts.get('single_column', 0)}")
    lines.append(f"  Two-column:    {report.layout_mode_counts.get('two_column', 0)}")
    lines.append(f"  Uncertain:     {report.layout_mode_counts.get('uncertain', 0)}")
    lines.append("")

    # Structure section
    lines.append("Structure:")
    lines.append(f"  Headings:     {report.block_role_counts.get('heading', 0)}")
    lines.append(f"  Paragraphs:   {report.block_role_counts.get('paragraph', 0)}")
    lines.append(f"  Headers:      {report.block_role_counts.get('header', 0)}")
    lines.append(f"  Footers:      {report.block_role_counts.get('footer', 0)}")
    lines.append(f"  Page numbers: {report.block_role_counts.get('page_number', 0)}")
    lines.append(f"  Unknown:       {report.block_role_counts.get('unknown', 0)}")
    lines.append("")

    # OCR diagnostics section
    lines.append("OCR:")
    lines.append(f"  OCR block count:    {report.ocr_block_count}")
    lines.append(f"  Blocks with confidence: {report.blocks_with_confidence}")
    if report.median_ocr_confidence is not None:
        lines.append(f"  Median confidence:  {report.median_ocr_confidence:.2f}")
    if report.min_ocr_confidence is not None:
        lines.append(f"  Minimum confidence: {report.min_ocr_confidence:.2f}")
    lines.append(f"  Low-confidence blocks: {report.low_confidence_block_count}")
    if report.pages_with_low_confidence:
        lines.append(f"  Pages with low confidence: {', '.join(str(p) for p in report.pages_with_low_confidence)}")
    lines.append("")

    # Status section
    lines.append(f"Status: {report.status.value.upper()}")
    if report.status_reasons:
        lines.append("Reasons:")
        for reason in report.status_reasons:
            lines.append(f"  - {reason.message}")
    else:
        lines.append("Reasons: none")

    # Problem pages
    if report.problem_pages:
        lines.append(f"Problem pages: {', '.join(str(p) for p in report.problem_pages)}")
    else:
        lines.append("Problem pages: none")

    for line in lines:
        typer.echo(line)


if __name__ == "__main__":
    app()