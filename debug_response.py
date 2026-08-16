import json
from fastapi.testclient import TestClient
from ragparser.web.app import create_app

app = create_app()
client = TestClient(app)

# Test native PDF
with open('tests/fixtures/simple.pdf', 'rb') as f:
    r = client.post('/v1/parse', files={'file': ('simple.pdf', f, 'application/pdf')})

data = r.json()
print('=== NATIVE PDF RESPONSE ===')
print(json.dumps(data, indent=2))

print()
print('=== DOCUMENT TREE ===')
doc = data['document']
print(f'source_path: {doc["source_path"]}')
print(f'page_count: {doc["page_count"]}')
for i, page in enumerate(doc['pages']):
    print(f'\nPage {page["number"]}:')
    print(f'  classification: {page["classification"]}')
    print(f'  extraction_method: {page["extraction_method"]}')
    print(f'  extraction_status: {page["extraction_status"]}')
    print(f'  layout_mode: {page["layout_mode"]}')
    print(f'  warnings: {page["warnings"]}')
    print(f'  blocks ({len(page["blocks"])}):')
    for j, block in enumerate(page['blocks']):
        print(f'    Block {j}: type={block["type"]}, role={block["role"]}, text="{block["text"][:30]}", method={block["extraction_method"]}, conf={block["confidence"]}, bbox={block["bbox"]}')

# Test OCR PDF
print()
print('=== OCR PDF RESPONSE ===')
with open('tests/fixtures/scanned_text_page.pdf', 'rb') as f:
    r = client.post('/v1/parse', files={'file': ('scanned_text_page.pdf', f, 'application/pdf')})

data = r.json()
print(json.dumps(data, indent=2))

doc = data['document']
print()
print('=== OCR DOCUMENT TREE ===')
for i, page in enumerate(doc['pages']):
    print(f'\nPage {page["number"]}:')
    print(f'  classification: {page["classification"]}')
    print(f'  extraction_method: {page["extraction_method"]}')
    print(f'  extraction_status: {page["extraction_status"]}')
    print(f'  layout_mode: {page["layout_mode"]}')
    print(f'  warnings: {page["warnings"]}')
    print(f'  blocks ({len(page["blocks"])}):')
    for j, block in enumerate(page['blocks']):
        print(f'    Block {j}: type={block["type"]}, role={block["role"]}, text="{block["text"][:30]}", method={block["extraction_method"]}, conf={block["confidence"]}, bbox={block["bbox"]}')

# Test health
print()
print('=== HEALTH RESPONSE ===')
r = client.get('/v1/health')
print(json.dumps(r.json(), indent=2))