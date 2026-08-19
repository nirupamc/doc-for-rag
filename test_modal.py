import modal
import sys

app = modal.App(name="ragparser")

@modal.asgi_app()
def fastapi_app():
    from ragparser.web.app import create_app
    return create_app()

print("App created successfully")
print("App type:", type(app))