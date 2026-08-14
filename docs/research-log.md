# Research & Engineering Log

## 2026-08-15: Milestone 1 Foundation

### Decision: Page-Level Routing Instead of Global PDF Classification

**Context:** RagParser needs to handle both digital (text-extractable) and scanned (image-only) PDFs. A key architectural decision is whether to classify an entire PDF as "digital" or "scanned" upfront, or to make routing decisions per-page.

**Decision:** Route at page level, not document level.

**Rationale:**

1. **Mixed documents are common**: Real-world PDFs frequently contain both digital and scanned pages (e.g., a digital report with scanned signature pages, or scanned appendices in a digital document). Global classification forces a single strategy for the entire document.

2. **Optimal backend selection per page**: Digital pages should use native text extraction (fast, perfect fidelity). Scanned pages require OCR (slower, introduces errors). Page-level routing allows using the best backend for each page.

3. **Provenance tracking**: Page-level extraction method (`ExtractionMethod.NATIVE` vs `ExtractionMethod.OCR`) is recorded in the IR per block, enabling downstream consumers to weigh confidence appropriately.

4. **Failure isolation**: If OCR fails on one page, other pages are unaffected. Global classification would require re-processing the entire document if classification was wrong.

5. **Incremental processing**: Page-level routing enables streaming/parallel processing architectures where pages are processed independently.

**Implementation approach (future milestones):**
- M2: Add `PageClassifier` that inspects each page (text density, image coverage, etc.)
- M2: `DocumentParser` routes each page to `NativeExtractor` or `OCRExtractor` based on classification
- IR already supports per-block `extraction_method` field for provenance

**Not implemented in M1:** Page classification, OCR backend, routing logic. M1 establishes the IR and native extraction foundation only.

---

### Decision: Canonical Bounding Box Convention

**Convention established:**
- Origin: top-left
- X increases rightward
- Y increases downward
- Units: PDF points (1/72 inch)
- x0,y0 = top-left, x1,y1 = bottom-right

**Rationale:** Matches PyMuPDF's native coordinate system exactly, avoiding conversion errors. PDF specification uses this convention. Backends using different conventions (e.g., PDFMiner with bottom-left origin) must convert.

---

### Decision: Separate DocumentLoader and NativeExtractor

**Rationale:**
- `DocumentLoader`: Single responsibility for document lifecycle (open, close, metadata, page access)
- `NativeExtractor`: Single responsibility for page-level content extraction
- Enables testing each in isolation
- Allows future backends (OCR, table extraction) to share the same loader
- Prevents god-object anti-pattern

---

### Decision: No UUIDs in M1 IR Blocks

**Rationale:** No consumer in M1 requires stable block identity. UUIDs add serialization overhead and complexity. Will introduce when we have a concrete need (diagnostics, cross-references, visual inspection, captions, document-level reconstruction).

---

### Decision: Minimal IR Fields

**Included:** Block type, text, bbox, extraction method, confidence (nullable), page number, reading order.
**Deferred:** Language, heading level, font info, semantic roles, table structure, RAG chunking fields.

**Rationale:** YAGNI. Every field adds maintenance burden. Add when a consumer exists.