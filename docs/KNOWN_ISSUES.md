# VEDANTA — Known Issues

**Last Updated:** 2026-11-08

---

## Active Issues

### KI-001: Python 3.13 vs Spec 3.11

**Severity:** Low  
**Description:** The spec specifies Python 3.11. The system has Python 3.13.7.  
**Impact:** Most libraries support 3.13. If a library is incompatible, it will be documented here and a workaround implemented.  
**Status:** Monitoring

### KI-002: Tesseract Must Be Installed Separately

**Severity:** Medium  
**Description:** Tesseract OCR binary is not a Python package — it must be installed as a system binary.  
**Resolution:** Installation instructions provided in README. On Windows, Tesseract installer must be run. On WSL/Linux, `apt install tesseract-ocr`.  
**Status:** Documented

### KI-003: MITAOE Website May Have Dynamic Content

**Severity:** Medium  
**Description:** Some MITAOE pages may require JavaScript rendering (Playwright) for full content extraction.  
**Resolution:** Playwright integration is planned in Phase 1. Initial crawl uses httpx + BeautifulSoup for static pages.  
**Status:** Planned

### KI-004: Scanned PDFs Require Long OCR Processing

**Severity:** Medium  
**Description:** OCR for scanned institutional PDFs may take 30–120 seconds per document.  
**Resolution:** All OCR runs in background workers. Users see processing status. Results are cached permanently after first OCR run.  
**Status:** By Design

---

## Resolved Issues

None yet.

---

## Limitations (By Design)

1. VEDANTA will not answer questions whose answers do not exist in indexed sources.
2. VEDANTA cannot crawl password-protected or CAPTCHA-protected pages.
3. OCR accuracy on low-quality scans may be below 90%.
4. First-time queries on unindexed topics trigger background crawling and return a "processing" response.
5. Statistical calculations are only as accurate as the source documents.
6. The system does not use an LLM by default — answers are evidence-assembled, not generatively composed.
