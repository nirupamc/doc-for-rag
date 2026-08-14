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
        help="Show per-page analysis (classification, signals)",
    ),
) -> None:
    """
    Show document information with optional per-page analysis.
    """
    parser = DocumentParser()

    try:
        if analyze:
            analyses = parser.analyze(input_path)
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
            a = analyses[i]
            s = a.signals
            typer.echo(f"  Page {page.number}:")
            typer.echo(f"    Classification: {a.classification.value.upper()}")
            if page.extraction_method:
                typer.echo(f"    Extraction method: {page.extraction_method.value.upper()}")
            if page.extraction_status:
                typer.echo(f"    Extraction status: {page.extraction_status.value.upper()}")
            typer.echo(f"    Reason: {a.reason}")
            typer.echo(f"    Native chars: {s.native_char_count}")
            typer.echo(f"    Native blocks: {s.native_block_count}")
            typer.echo(f"    Images: {s.image_count}")
            typer.echo(f"    Largest image coverage: {s.largest_image_coverage:.1%}")
            if s.summed_image_area_ratio > 0:
                typer.echo(f"    Summed image area ratio: {s.summed_image_area_ratio:.1%}")
            if s.drawing_count > 0:
                typer.echo(f"    Drawings: {s.drawing_count}")
            if page.warnings:
                typer.echo(f"    Warnings: {page.warnings}")
        else:
            typer.echo(f"  Page {page.number}: {block_count} blocks, {text_chars} chars")
            if page.extraction_method:
                typer.echo(f"    Extraction method: {page.extraction_method.value.upper()}")
            if page.extraction_status:
                typer.echo(f"    Extraction status: {page.extraction_status.value.upper()}")


if __name__ == "__main__":
    app()