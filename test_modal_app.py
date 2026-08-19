import modal
app = modal.App('test_minimal')

@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    return FastAPI()