"""FastAPI application assembly for RagParser Web API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ragparser.web.routes import router


app = FastAPI(
    title="RagParser Web API",
    version="0.1.0",
    description="Minimal HTTP API for RagParser document parsing library.",
)

# CORS configuration: explicit allowlist for future Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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