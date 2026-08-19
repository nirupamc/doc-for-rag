"""Modal deployment wrapper for RagParser FastAPI backend."""

import modal

app = modal.App(name="ragparser")


@app.function()
@modal.asgi_app()
def fastapi_app():
    from ragparser.web.app import create_app
    return create_app()