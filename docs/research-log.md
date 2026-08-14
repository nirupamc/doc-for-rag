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

---

## 2026-08-15: Milestone 2 — Page Analysis & Routing

### Decision: PageClassification in IR, PageSignals in Analysis (No Circular Dependency)

**Context:** `PageClassification` enum is needed by both IR (for `Page.classification`) and analysis module (for classifier output).

**Decision:** Place `PageClassification` in `src/ragparser/ir.py` (canonical IR layer). Keep `PageSignals` and `ClassificationResult` in `src/ragparser/analysis/`.

**Rationale:** IR is the stable contract; analysis is internal implementation. This avoids circular imports and keeps analysis types private.

---

### Decision: No Numeric Classification Confidence in M2

**Decision:** `ClassificationResult` contains only `classification`, `reason`, `signals`. No `confidence: float` field.

**Rationale:** Values like 0.9, 0.7, 0.6 are not calibrated probabilities. They would create false precision. Calibrated confidence requires a manually labeled benchmark and evidence — deferred to later.

---

### Decision: Image Coverage — Largest Image vs Summed Area

**Finding:** PyMuPDF's `get_image_rects()` returns placed image rectangles. Summing their areas overestimates coverage when images overlap (common in multi-column layouts with figures).

**M2 approach:**
- `largest_image_coverage` = single largest image rect / page area (reliable for scanned-page detection)
- `summed_image_area_ratio` = sum of all image rect areas / page area (capped at 1.0, labeled as potentially overlapping)
- Primary signal for `OCR_REQUIRED`: `largest_image_coverage >= 0.5`

**Rationale:** Full-page scans typically have one image covering >80%. Summed area is retained as a secondary signal but clearly named to avoid misinterpretation.

---

### Decision: `has_native_text` is Observable, Not Usability

**Distinction:**
- `has_native_text` = `native_char_count > 0` (observable fact)
- "usable native text" = classifier decision (interpretation)

**Example:** A scanned page with OCR'd invisible text layer has `native_char_count > 0` but the text may be garbage. The classifier evaluates usability, not the signal.

---

### Decision: Conservative Classification — Prefer SUSPICIOUS Over False NATIVE/OCR_REQUIRED

**Rules:**
- `EMPTY`: No text, no images, no drawings
- `OCR_REQUIRED`: No text, largest image >= 50% page
- `NATIVE`: Substantial text (>=50 chars), largest image < 30%
- `SUSPICIOUS`: Text + large image (>=50%), sparse text + image, drawings only, garbled text (U+FFFD)

**Key adjustment:** Sparse text (< 10 chars) alone is NOT suspicious. Legitimate pages (titles, dedications, dividers) have little text. Only sparse text + dominant image triggers `SUSPICIOUS`.

**Rationale:** False `EMPTY` silently discards content. False `OCR_REQUIRED` wastes compute. `SUSPICIOUS` flags for human review / M3 hybrid extraction.

---

### Decision: Limited Suspicious-Text Heuristic (U+FFFD Only)

**Finding:** PyMuPDF renders replacement characters (U+FFFD) as middle dots (U+00B7 ·) in `get_text("dict")`. The U+FFFD heuristic does not trigger on real garbled PDFs produced by PyMuPDF.

**M2 behavior:** Heuristic only catches actual U+FFFD in text. Middle dots pass as native text → `NATIVE`.

**Documentation:** This is a known limitation. Real pathological PDFs should become benchmark documents in later milestones. Do not claim robust garbled-text detection.

---

### Decision: Duplicate Extraction Accepted in M2

**Fact:** `PageAnalyzer.analyze_page()` calls `page.get_text("dict")` for signals. `NativeExtractor.extract_page()` calls it again for full block extraction.

**Position:** Accept the small duplication in M2. Profile before optimizing. The cost is one additional text-dict pass per page (~few ms). Optimization (shared text-dict) can be done if profiling shows it's a bottleneck.

---

### Decision: PageSignals in IR is Provisional

**Current:** `Page.classification`, `Page.classification_reason` attached to IR. `PageSignals` NOT attached (to avoid IR bloat).

**Future:** May move detailed signals to a separate extraction/diagnostics report while keeping canonical IR smaller. For M2, signals available via `DocumentParser.analyze()` and CLI.

---

### Experiment: What Does "Empty" Mean in a PDF?

**Tested page types:**
| Page Type | get_text blocks | get_images | get_drawings | Classification |
|-----------|----------------|------------|--------------|----------------|
| True blank | 0 | 0 | 0 | EMPTY |
| Full-page image (scan) | 1 (type=1, image bbox) | 1 | 0 | OCR_REQUIRED |
| Text + small figure | 3 (2 text, 1 image) | 1 | 0 | NATIVE |
| Replacement chars only | 2 (type=0, text=U+00B7) | 0 | 0 | NATIVE* |
| Single char 'x' | 1 | 0 | 0 | NATIVE |
| Vector graphics only | 0 | 0 | 2 | SUSPICIOUS |
| Few chars + full image | 1 + 1 image | 1 | 0 | SUSPICIOUS |

*Limitation: PyMuPDF renders U+FFFD as U+00B7, so replacement-char heuristic doesn't catch it.

**Surprising behavior:** `get_text("dict")` returns image blocks as type=1 with bbox matching the image rect. This is useful — we can detect image-only pages even without `get_images()`.

---

### CLI Inspection Output Example

```
$ ragparser info mixed_document.pdf
Page 1: Classification: NATIVE, Native chars: 96, Images: 0
Page 2: Classification: OCR_REQUIRED, Largest image coverage: 83.4%
Page 3: Classification: EMPTY, Native chars: 0, Images: 0
Page 4: Classification: NATIVE, Native chars: 1, Images: 0
Page 5: Classification: SUSPICIOUS, Native text (6 chars) but large image covers 83.4%
```