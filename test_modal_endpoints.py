"""Start Modal server and test endpoints."""

import subprocess
import time
import urllib.request
import json

# Start Modal server in background
proc = subprocess.Popen(
    ["python", "-X", "utf8", "-m", "modal", "serve", "modal_app.py"],
    cwd="D:\\protofolo projectzzz\\ragparser",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Wait for server to start
time.sleep(15)

# Test health endpoint
try:
    req = urllib.request.Request('http://127.0.0.1:8000/v1/health')
    with urllib.request.urlopen(req) as resp:
        print("=== Health Check ===")
        print("Status:", resp.status)
        body = resp.read().decode()
        print("Body:", body)
        data = json.loads(body)
        print("tesseract_available:", data.get("tesseract_available"))
except Exception as e:
    print("Health check error:", e)

# Test parse endpoint with a simple PDF
try:
    # Create a simple PDF
    import fitz
    doc = fitz.open()
    doc.add_page()
    doc_bytes = doc.write()
    doc.close()
    
    # Convert to bytes for upload
    file_bytes = doc_bytes
    filename = "test.pdf"
    
    # POST /v1/parse
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + file_bytes + b"\r\n--" + boundary + "--\r\n"
    
    req = urllib.request.Request(
        'http://127.0.0.1:8000/v1/parse',
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        print("\n=== Parse Response ===")
        print("Status:", resp.status)
        result = resp.read().decode()
        print("Response:", result[:500])
except Exception as e:
    print("\nParse error:", e)

# Wait a bit then stop the server
proc.terminate()
proc.wait()
print("\nServer stopped")