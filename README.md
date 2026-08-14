# RagParser

Document parsing pipeline for RAG applications.

## Installation

```bash
pip install -e .
```

## Development

```bash
pip install -e .[dev]
pytest
ruff check .
mypy src
```

## CLI Usage

```bash
ragparser parse path/to/document.pdf --output output.json
```