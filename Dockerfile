FROM python:3.11-slim

# Install OS packages required by Tesseract and PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy source code first (setuptools needs src/ layout present)
WORKDIR /app
COPY pyproject.toml .
COPY src/ragparser ./src/ragparser/

# Install Python dependencies (includes RagParser package)
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

# Environment-driven port with 8000 default
# CORS origins from RAGPARSER_CORS_ORIGINS env var
CMD ["uvicorn", "ragparser.web.app:app", "--host", "0.0.0.0"]