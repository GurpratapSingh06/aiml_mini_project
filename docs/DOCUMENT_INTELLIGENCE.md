# VEDANTA Document Intelligence Architecture

## 1. Overview and Mission

Institutional documents—such as circulars, fee structures, academic calendars, placement brochures, and regulatory notifications—are foundational sources of truth in academic institutions like MIT Academy of Engineering (MITAOE). However, these documents are frequently stored as heterogeneous PDF files comprising:
- Clean, searchable **digital PDFs** (native vector fonts and selectable text streams).
- **Scanned physical notices** (raster bitmap images of stamped circulars and signed letters).
- **Mixed-mode PDFs** (digital headers with scanned embedded tables or endorsements).
- Multi-column and bordered **tabular data** (fee breakdowns across categories, placement company rosters).

The VEDANTA Document Intelligence Engine (`backend/app/ingestion/document_processor/pdf_processor.py`) processes these documents deterministically, producing structured, traceable, page-indexed content chunks with full provenance metadata.

---

## 2. Core Processing Pipeline

```
PDF File / Stream
       │
       ▼
[SHA-256 Content Hashing & Deduplication]
       │
       ▼
[PyMuPDF (fitz) Document Open & Metadata Extraction]
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[Per-Page Analysis]                     [Table Extraction]
       │                                         │
       ├─ Digital Text: len(text) >= 50          ├─ PyMuPDF find_tables()
       │  Extract direct text stream             ├─ Pandas DataFrame normalization
       │                                         └─ Category & column mapping
       └─ Scanned Image: len(text) < 50 + image
          Render pixmap (300 DPI)
          Tesseract OCR with word confidence
       │
       ▼
[Chunking & Provenance Tagging]
  - Preserve page numbers (1-indexed)
  - Retain source URL & local path
  - Extract Academic Year & Dates
       │
       ▼
[Indexed in BM25 & FAISS CPU Vector Index]
```

---

## 3. Digital vs. Scanned PDF Detection

Rather than running heavy OCR pipelines uniformly across all documents, VEDANTA executes an intelligent per-page heuristic:

1. **Direct Text Extraction:** Each page is queried using `page.get_text("text")`.
2. **Image Inspection:** The page's embedded raster objects are counted using `page.get_images(full=False)`.
3. **Classification Rule:**
   - If selectable text length $< 50$ characters AND embedded raster images $> 0$, the page is classified as **Scanned** (`is_scanned = True`).
   - If selectable text $\ge 50$ characters, the page is classified as **Digital** (`is_scanned = False`).
   - If a document contains both scanned and digital pages, it is flagged as **Mixed** (`is_mixed = True`).

```python
def _is_page_scanned(page) -> bool:
    text = page.get_text("text").strip()
    images = page.get_images(full=False)
    return len(text) < 50 and len(images) > 0
```

---

## 4. Optical Character Recognition (OCR) Engine

For scanned pages, VEDANTA integrates Google's Tesseract OCR via `pytesseract` and `Pillow`:

- **Rendering:** PyMuPDF renders the page to a high-fidelity image pixmap at $2\times$ zoom matrix ($150 \times 2 = 300\text{ DPI}$ equivalent) to ensure clear character edge definition for OCR.
- **Image Conversion:** Pixmap bytes are converted to a `PIL.Image` in RGB mode.
- **Word-Level Confidence Tracking:** Tesseract's `image_to_data` output format (`Output.DICT`) is parsed to capture per-word confidence metrics ($0.0 - 100.0$). Only tokens with non-empty text and non-negative confidence are factored into the page's mean confidence score.
- **Graceful Degradation:** If Tesseract OCR is not installed on the host system or fails to initialize, the processor catches the exception, logs a warning, records `ocr_engine = None`, and falls back to extracting whatever textual fragments exist without crashing the application.

---

## 5. Structured Table Processing

Institutional fee schedules and placement reports are tabular by nature. Extracting them as raw unformatted strings corrupts row-column semantics (e.g. mapping an open-category fee to a reserved-category column).

1. **Table Detection:** PyMuPDF's built-in table finder (`page.find_tables()`) identifies grid lines, borders, and whitespace gutters.
2. **Tabular Conversion:** Detected tables are converted directly to structured Pandas DataFrames.
3. **Structured Representation:**
   - Headers and data rows are sanitized of `None` values and whitespace.
   - Structured JSON records are emitted with `table_index`, `headers`, and `rows`.
   - In addition to JSON, tables are serialized as Markdown-formatted text strings within the page content chunks, ensuring that both lexical BM25 and dense semantic embeddings capture tabular cell relationships.

---

## 6. Page-Level Provenance & Citations

Every extracted sentence or table row retains:
- `source_url`: The public institutional URL from which the PDF was discovered.
- `file_path`: The local canonical cache path on disk.
- `page_number`: 1-based page index.
- `chunk_index`: Unique sub-page chunk identifier.

When the answer engine cites information derived from a document, the UI displays clickable citation badges linking to `Page X of [Document Title]` with direct visual verification.
