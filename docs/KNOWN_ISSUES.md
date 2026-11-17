# VEDANTA — Known Issues & Resolution Log

**Product:** VEDANTA  
**Institution:** MIT Academy of Engineering (MITAOE)  
**Last Updated:** 2026-11-15  
**Current Academic Year:** 2026–27  

---

## Active Operational Notes

### KI-001: Local Tesseract Binary Requirement for Scanned PDFs
- **Severity:** Low (Informational)
- **Description:** PyMuPDF extracts text directly from digitally generated PDFs. Scanned image-only PDFs require the local Tesseract OCR engine installed on the system PATH.
- **Status:** Verified & Handled gracefully by `document_pipeline` health check.

### KI-002: Optional Redis Server
- **Severity:** Low (Operational)
- **Description:** When Redis 7 is not running locally, VEDANTA automatically falls back to its in-memory L1 cache (`cachetools.TTLCache`) and passes health checks with status `degraded` without blocking request threads.
- **Status:** Handled via circuit breaker (150ms timeout).

---

## Resolved Issues Audit Log

### KI-R01: Duplicate Column Mapping on EvidenceRecord
- **Component:** `backend/app/models/models.py`
- **Root Cause:** Line 557 declared a duplicate `query_history_id` attribute, triggering SQLAlchemy `InvalidRequestError` on model mapper initialization.
- **Resolution:** Removed duplicate attribute and restored proper foreign key mapping.

### KI-R02: PostgreSQL Authentication Failure on Fresh Local Setup
- **Component:** `backend/app/core/database.py`
- **Root Cause:** Database `vedanta` and role `vedanta` did not exist on fresh local PostgreSQL 18.
- **Resolution:** Built and executed `scripts/setup_local_db.py` to create user, database, and extensions.

### KI-R03: Blocking Socket Timeout Freezing Request Loops
- **Component:** `backend/app/api/v1/endpoints/health.py` & `AnswerPipeline`
- **Root Cause:** Serial synchronous TCP connection attempts to unreachable Redis took 2000–3000ms.
- **Resolution:** Replaced serial calls with `asyncio.gather` and capped Redis socket connection timeout to 150ms with circuit-breaking backoff.

### KI-R04: Hardcoded 2024–25 Mock Fallback in Frontend Search Page
- **Component:** `frontend/src/app/search/page.tsx`
- **Root Cause:** A client-side `generateLocalAnswer` fallback silently caught API errors and displayed hardcoded 2024–25 dates and outdated HOD names.
- **Resolution:** Removed `generateLocalAnswer`. Connected frontend directly to backend API, added Developer Search Diagnostics drawer, and updated year filter to AY 2026–27.

### KI-R05: Missing Next.js Build Import
- **Component:** `frontend/src/app/crawler/page.tsx`
- **Root Cause:** Missing `useEffect` import caused `npm run build` to fail compilation.
- **Resolution:** Added `useEffect` to React imports. `npm run build` now compiles all 11 routes cleanly.

### KI-R06: Middle Initials Rejected in Faculty Name Extractor
- **Component:** `backend/app/intelligence/entity_engine/entity_extractor.py`
- **Root Cause:** Regex `[A-Z][a-z]+` failed to parse names with single-letter initials (e.g. `Dr. Sandip A. Gade`, `Dr. P D Ganjewar`).
- **Resolution:** Updated pattern to `\b(?:Dr|Prof)\.?\s+[A-Z][A-Za-z0-9\.\(\)]*(?:\s+[A-Z0-9][A-Za-z0-9\.\(\)]*)*`.

### KI-R07: AsyncPG Raw SQL Parameter Deduplication Error
- **Component:** `scripts/crawl_and_index_mitaoe.py`
- **Root Cause:** Reusing `$3` twice in parameter lists caused asyncpg type deduction errors.
- **Resolution:** Rewrote SQL using distinct named parameters `:name` and `:desc`.

### KI-R08: Chunker Keyword Parameter Mismatch in Live Fetcher
- **Component:** `backend/app/ingestion/crawler/live_fetcher.py`
- **Root Cause:** `TextChunker` was called with `chunk_size` and `chunk_overlap` instead of `max_tokens` and `overlap_tokens`.
- **Resolution:** Updated instantiation to `TextChunker(max_tokens=512, overlap_tokens=64)`.

### KI-R09: Case-Sensitive Acronym Expansion Miss on Lowercased Queries
- **Component:** `backend/app/intelligence/query_understanding/query_understander.py`
- **Root Cause:** Queries lowercased by `normalize_query` never matched `case_sensitive_acronyms` (e.g. `"IT"`).
- **Resolution:** Added contextual regex patterns (e.g. `\bit\s+(?:dept|department|engineering)\b`) and expanded acronyms prior to lowercasing.

### KI-R10: Co-Listed Departmental Faculty Flagged as Conflicting Sources
- **Component:** `backend/app/intelligence/answer_engine/evidence_validator.py`
- **Root Cause:** Multiple titles or co-listed leaders (e.g. Dean & Associate HOD Dr. Maya Charde & Dr. Abhijeet Malge) on the same page were falsely flagged as conflicting sources.
- **Resolution:** Re-scoped conflict detection to only trigger when distinct independent source URLs report contradictory leaders without co-listing.

### KI-R11: Preposition Leakage in Negative Control Grounding Check
- **Component:** `backend/app/intelligence/answer_engine/evidence_validator.py`
- **Root Cause:** Prepositions like "on" were not treated as framing words, allowing queries like "Where is the campus located on Mars?" to reach 50% overlap on "on".
- **Resolution:** Added prepositions ("on", "to", "from", "by", "with", "as") to framing stopwords, ensuring out-of-domain negative controls cleanly trigger `insufficient_evidence`.

### KI-R12: Dynamic Data-Target Counters Missed by Static Text Scrapers in Placement Portal
- **Component:** `backend/app/ingestion/crawler/html_parser.py` & `scripts/seed_comprehensive_knowledge.py`
- **Root Cause:** Key placement numbers on `mitaoe.ac.in/placement.php` are stored in `<span class="counter" data-target="27">` and `<span class="counter" data-target="6.75">`, which standard `BeautifulSoup.get_text()` misses.
- **Resolution:** Targeted `data-target` counter attributes and seeded structured `placement_records` (27 LPA highest, 6.75 LPA average, 500+ offers, 800+ internships, 450+ companies).

### KI-R13: Analytics Page Disconnected from Backend Statistics Store
- **Component:** `frontend/src/app/analytics/page.tsx`
- **Root Cause:** Frontend Analytics was rendering a static `mockStats` array with fake duplicated CE vs CSE rows and missing the fee structure entirely.
- **Resolution:** Rewrote `page.tsx` with dynamic `useEffect` data fetching from `/api/v1/statistics/placements` and `/api/v1/statistics/fees`, rendering verified placement and approved AY 2026–27 fee tables.

### KI-R14: Missing stats_store.py Data Access Layer
- **Component:** `backend/app/storage/stats_store.py`
- **Root Cause:** `statistics.py` attempted to import `get_placement_records` and `get_fee_records` from non-existent `app.storage.stats_store`.
- **Resolution:** Implemented `backend/app/storage/stats_store.py` with SQLAlchemy async queries joining `placement_records` and `fee_records` with `departments`.

### KI-R15: Computer Science and Engineering (CSE) Omitted from Department Acronym Mapping
- **Component:** `backend/app/intelligence/query_understanding/query_understander.py`
- **Root Cause:** Regex only matched `computer\s+engineering` and `\bce\b`, failing to capture `\bcse\b` and `computer science and engineering`.
- **Resolution:** Updated pattern to `(r"computer\s+(?:science\s+(?:and|&)\s+)?engineering|\bcomp\b|\bce\b|\bcse\b", "Computer Engineering")`.

### KI-R16: Faculty Members Misclassified as HOD in Entity Answer Extraction
- **Component:** `backend/app/intelligence/answer_engine/answer_composer.py`
- **Root Cause:** Fallback regex in `_compose_entity_answer` assigned the designation "Head of Department" to any person entity found in leadership passages.
- **Resolution:** Integrated Knowledge Graph entity resolution (`kg.get_faculty_profile`), correctly identifying Mr. Azhar R. Shaikh as Assistant Professor in Mathematics in the School of Humanities and Engineering Sciences.
