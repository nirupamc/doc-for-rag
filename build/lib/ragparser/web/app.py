"""FastAPI application assembly for RagParser Web API."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ragparser.web.routes import router


def _parse_cors_origins() -> list[str]:
    """Parse CORS origins from RAGPARSER_CORS_ORIGINS env var.

    Comma-separated list. Falls back to localhost:3000 for development.
    """
    raw = os.getenv("RAGPARSER_CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="RagParser Web API",
    version="0.1.0",
    description="Minimal HTTP API for RagParser document parsing library.",
)

# CORS configuration: origins driven by RAGPARSER_CORS_ORIGINS env var
app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include route handler router
app.include_router(router)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance (same as module-level app).
    """
    return app