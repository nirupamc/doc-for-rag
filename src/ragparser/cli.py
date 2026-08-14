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
) -> None:
    """
    Show basic document information without full extraction.
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

    typer.echo(f"Source: {doc.source_path}")
    typer.echo(f"Pages: {doc.page_count}")
    typer.echo(f"Metadata: {doc.metadata}")
    if doc.warnings:
        typer.echo(f"Warnings: {doc.warnings}")

    for page in doc.pages:
        block_count = len(page.blocks)
        text_chars = sum(len(b.text) for b in page.blocks)
        typer.echo(f"  Page {page.number}: {block_count} blocks, {text_chars} chars")


if __name__ == "__main__":
    app()