"""Modal deployment wrapper for RagParser FastAPI backend."""

import modal

app = modal.App("ragparser")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "tesseract-ocr",
        "tesseract-ocr-eng",
    )
    .pip_install(
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.27.0",
        "python-multipart>=0.0.5",
        "pymupdf",
        "pytesseract",
        "pillow",
        "typer",
    )
    .add_local_python_source("ragparser")
)

@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    from ragparser.web.app import create_app

    return create_app()