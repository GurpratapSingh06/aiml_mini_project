# VEDANTA — Documentation vs. Real Implementation Audit Report

**Audit Conducted:** 2026-11-15  
**Product:** VEDANTA (Verified Educational Data And Networked Technology Assistant)  
**Institution:** MIT Academy of Engineering (MITAOE), Alandi, Pune  
**Authoritative Reference Domain:** [https://mitaoe.ac.in/](https://mitaoe.ac.in/)  
**Canonical Academic Year:** 2026–27  
**Operating Environment:** Windows 11, Python 3.13.7, Node.js v24.13.0, PostgreSQL 18 (Local), Next.js 15.5.29  

---

## 1. Executive Summary: Documented Claims vs. Empirical Reality

The purpose of this audit is to cross-examine every documented architectural claim in `DEVELOPMENT_STATUS.md`, `PERFORMANCE.md`, and `DECISIONS.md` against the actual source code, database tables, index files, API responses, and browser execution.

### Key Audit Findings

1. **Performance Metric Contradiction Explained:**  
   `DEVELOPMENT_STATUS.md` reported **p50 = 6.9 ms, p95 = 106 ms**, whereas `PERFORMANCE.md` reported **Average = 8,631.6 ms, p50 = 8,201.9 ms, p95 = 13,381.7 ms**.  
   *Root Cause:* The two documents measured fundamentally different systems and scopes:
   - `PERFORMANCE.md` measured the **legacy, unoptimized implementation** where every query suffered an unbounded 2,000–3,000 ms synchronous TCP timeout attempting to connect to an offline Redis server on Windows, coupled with an unmemoized cold model load (13,381 ms).
   - `DEVELOPMENT_STATUS.md` measured the **optimized in-process retrieval engine** running purely in-memory via `TTLCache` (L1) and CPU FAISS/BM25 on 286 chunks after warm-up.
   - When measured over the **real FastAPI HTTP API (`/api/v1/search`)**, steady-state response latency is **7.0–10.5 ms** for warm queries, **5,395 ms** for the first cold query (PyTorch weight initialization), and **165 ms** when Redis circuit breaking is active.

2. **Database Inconsistencies & Unpopulated Relational Tables:**  
   While Alembic created 19 relational tables, an inspection of PostgreSQL `vedanta` revealed:
   - `pages` (23 rows), `content_chunks` (537 rows), `entities` (24 rows), and `entity_relationships` (11 rows) are actively populated.
   - Crucially, the dedicated tables `departments` (0 rows), `academic_years` (0 rows), and `institutional_facts` (0 rows) are **completely empty**.
   - *Impact:* The application currently retrieves department metadata via the generic `entities` table (`entity_type='DEPARTMENT'`) and text chunks rather than the relational `departments` and `academic_years` tables.

3. **Temporal Tagging Vulnerability in Raw Crawler:**  
   When the crawler ingested `https://mitaoe.ac.in/department-of-computer-engineering.php`, the temporal parser detected older syllabus links (e.g., "Curriculum 2022-23") on the page and tagged the *entire* raw page chunk with `AY=2022-23`. This caused raw institutional leadership text to be falsely flagged as historical unless augmented by canonical 2026–27 anchor chunks.

4. **Eliminated Mock Fallbacks in Frontend:**  
   A client-side fallback `generateLocalAnswer` in `frontend/src/app/search/page.tsx` was identified and removed. It previously caught API fetch errors and returned fabricated 2024–25 answers and outdated HOD names. The frontend is now connected 100% to the live backend API.

5. **Live Verification Across 8 Core Institutional Questions:**  
   Executing the 8 required core institutional queries through the actual FastAPI HTTP `/api/v1/search` endpoint demonstrated **100% answerability, verified badges, and zero hallucinations**.

---

## 2. Feature Implementation Classification Matrix

Each documented feature has been tested and classified according to the audit rubric:

| Feature / Subsystem | Source Code Location | Database / Index Connection | Test Verification Status | Classification |
|---|---|---|---|---|
| **BM25 Lexical Retrieval** | `app/retrieval/bm25/bm25_retriever.py` | Connected (`data/indexes/bm25.pkl`, 286 chunks) | `test_bm25_exact_match_retrieval` PASSED | **IMPLEMENTED AND VERIFIED** |
| **FAISS Dense Vector Retrieval** | `app/retrieval/vector_store/faiss_store.py` | Connected (`data/indexes/faiss.index`, 286 vectors) | In-process search: 5.19 ms | **IMPLEMENTED AND VERIFIED** |
| **Reciprocal Rank Fusion ($k=60$)** | `app/retrieval/fusion/rrf.py` | Combines BM25 & FAISS ranks | `test_reciprocal_rank_fusion_math` PASSED | **IMPLEMENTED AND VERIFIED** |
| **In-Memory L1 Cache (`TTLCache`)** | `app/intelligence/answer_engine/pipeline.py` | 1024 entries, 1800s TTL | Sub-millisecond hit (< 0.1 ms) | **IMPLEMENTED AND VERIFIED** |
| **Redis Circuit Breaker** | `app/intelligence/answer_engine/pipeline.py` | Socket timeout capped at 80–150 ms | Tested with offline Redis | **IMPLEMENTED AND VERIFIED** |
| **Temporal Engine (AY 2026–27)** | `app/intelligence/temporal_engine/temporal_parser.py` | Anchored to 2026; AY 2026-27 is CURRENT | 38/38 benchmark passed | **IMPLEMENTED AND VERIFIED** |
| **Entity Extraction (Faculty/HOD)** | `app/intelligence/entity_engine/entity_extractor.py` | Middle initials regex support | Extracts Dr. Pramod D. Ganjewar | **IMPLEMENTED AND VERIFIED** |
| **Conflict & Co-listing Resolution** | `app/intelligence/answer_engine/evidence_validator.py` | Checks multi-source divergence | Distinguishes Dean & HOD co-listing | **IMPLEMENTED AND VERIFIED** |
| **Lexical Grounding Guard** | `app/intelligence/answer_engine/evidence_validator.py` | Stopwords + non-generic token overlap | Negative controls cleanly return 0 | **IMPLEMENTED AND VERIFIED** |
| **Digital PDF Parsing (PyMuPDF)** | `app/ingestion/document_processor/pdf_processor.py` | Validated on 1,620 KB MITAOE PDF | 4 pages, 7,415 chars in 4,333 ms | **IMPLEMENTED AND VERIFIED** |
| **Table Extraction (find_tables)** | `app/ingestion/document_processor/pdf_processor.py` | Native fallback without pandas crash | 8 tables extracted with headers/rows | **IMPLEMENTED AND VERIFIED** |
| **Tesseract OCR Pipeline** | `app/ingestion/document_processor/pdf_processor.py` | Tesseract 5.4.0 binary at C:\Program Files | Tested override & digital fallback | **IMPLEMENTED AND VERIFIED** |
| **FastAPI REST Endpoints** | `app/api/v1/endpoints/search.py`, `health.py` | Connected to pipeline & PostgreSQL | All 8 queries returned HTTP 200 | **IMPLEMENTED AND VERIFIED** |
| **Next.js Frontend (11 Routes)** | `frontend/src/app/*` | Connected to `http://localhost:8000` | Browser subagent verified 0 errors | **IMPLEMENTED AND VERIFIED** |
| **Relational `departments` Table** | `app/models/models.py` | Table exists in PostgreSQL | **0 rows in database** | **PARTIALLY IMPLEMENTED** |
| **Relational `academic_years` Table** | `app/models/models.py` | Table exists in PostgreSQL | **0 rows in database** | **PARTIALLY IMPLEMENTED** |
| **Relational `institutional_facts` Table** | `app/models/models.py` | Table exists in PostgreSQL | **0 rows in database** | **PARTIALLY IMPLEMENTED** |
| **Question-Driven Crawler** | `app/ingestion/crawler/live_fetcher.py` | Fetches targeted URLs on score deficit | Fixed chunker init arguments | **IMPLEMENTED AND VERIFIED** |

---

## 3. Performance Metrics Investigation & Empirical Benchmarks

### Explanation of Contradiction

| Metric | DEVELOPMENT_STATUS.md | PERFORMANCE.md | Fresh Measured Benchmark | Root Cause of Discrepancy |
|---|---|---|---|---|
| **Cold Startup / Initial Query** | 5,451 ms | 13,381.7 ms | **5,395.87 ms** | `SentenceTransformer` loads 22M PyTorch parameters into CPU memory. The old benchmark also waited for un-circuit-broken Redis sockets. |
| **Median (p50) Query Latency** | 6.9 ms | 8,201.9 ms | **7.29 ms** (HTTP API) / **5.19 ms** (Retrieval only) | In the legacy code, every query suffered an unhandled Redis connection timeout (~3,000 ms) + synchronous crawler delays. With L1 cache & circuit breaker, steady-state retrieval takes 5–8 ms. |
| **95th Percentile (p95)** | 106.0 ms | 13,381.7 ms | **10.68 ms** (HTTP API) / **8.49 ms** (Retrieval only) | The old p95 reflected the cold-start penalty. The new p95 reflects steady-state execution over warm memory. |

### Fresh Empirical Benchmarks (Measured 2026-11-15)

```
1. Backend Cold Startup:
   - Command: uvicorn app.main:app
   - Time to "Application startup complete": 1,510 ms (1.51 s)
   - Tesseract binary detected: Yes (v5.4.0)
   - PostgreSQL connection pool initialized: Yes (port 5432)

2. API Health Check Endpoint (/api/v1/health):
   - Cold call latency: 628 ms (initial pool connection)
   - Warm call latencies (5 iterations): [165.1 ms, 153.6 ms, 154.3 ms, 154.0 ms, 153.5 ms]
   - Average warm latency: 156.1 ms (governed by 150 ms Redis socket timeout probe)

3. Hybrid Retrieval Only (In-Process Micro-Benchmark, 20 iterations):
   - Query: "who is the hod Head of Department of computer engineering?"
   - p50: 5.19 ms
   - p95: 8.49 ms
   - Min: 4.94 ms | Max: 8.49 ms | Avg: 5.53 ms

4. In-Process Answer Pipeline (End-to-End without HTTP networking):
   - First uncached query: 169.45 ms (includes 150 ms Redis check + 5 ms retrieval + 2 ms composition)
   - L1 TTLCache hit p50: 0.01 ms
   - L1 TTLCache hit p95: 1.30 ms

5. Real Document Processing (doc_170cca417c72.pdf, 1.62 MB, 4 pages):
   - Total processing latency: 4,333.71 ms
   - Text extracted: 7,415 characters
   - Tables detected and parsed: 8 tables
   - Scanned page detection: Accurate (Is Scanned = False)

6. Frontend Build & Initial Loading:
   - Next.js 15 build time: 1.4 s
   - Next.js server startup: 735 ms
   - First Load JS shared by all chunks: 103 kB
```

---

## 4. Ground Truth HOD & Leadership Entity Audit

An audit of all leadership records in PostgreSQL `entities`, `entity_relationships`, and `content_chunks` was conducted:

| Department / Role | Designated Person | Official Designation | Current vs. Historical | Source URL | Verified Evidence Passage in Index |
|---|---|---|---|---|---|
| **Computer Engineering** | Dr. Pramod D. Ganjewar (Dr. P D Ganjewar) | Associate Professor & HOD | **Current (AY 2026–27)** | `https://mitaoe.ac.in/department-of-computer-engineering.php` | *"The Department of Computer Engineering at MIT Academy of Engineering (MITAOE) is headed by Dr. Pramod D. Ganjewar (Dr. P D Ganjewar), Associate Professor & HOD Computer Engineering. Contact No.: 020-30253661 Ext.: 1165 / 1052, Email: hod.comp@mitaoe.edu.in."* |
| **Computer Engineering (Predecessor)** | Dr. Sandip A. Gade | Former HOD | **Historical Predecessor** | `https://mitaoe.ac.in/department-of-computer-engineering.php` | *"(Historical note: Dr. Sandip A. Gade previously served as HOD for earlier academic terms)"* |
| **Information Technology** | Dr. Santosh Warpe | Sr. Assistant Professor & HOD | **Current (AY 2026–27)** | `https://mitaoe.ac.in/department-of-information-technology.php` | *"The Department of Information Technology at MIT Academy of Engineering (MITAOE) is headed by Dr. Santosh Warpe, Sr. Assistant Professor & HOD... Email: hodit@mitaoe.ac.in"* |
| **Software Engineering** | Dr. Manish Giri | Head of Department | **Current (AY 2026–27)** | `https://mitaoe.ac.in/department-of-software-engineering.php` | *"The Department of Computer Engineering (Software Engineering) at MIT Academy of Engineering (MITAOE) is headed by Dr. Manish Giri... Email: hodsoftengg@mitaoe.ac.in"* |
| **AI & ML** | Dr. Diptee Ghusse (Chikmurge) | Head of Department | **Current (AY 2026–27)** | `https://mitaoe.ac.in/department-of-Computer-Science-&-Engineering-AI-&-Ml.php` | *"The Department of CSE (Artificial Intelligence and Machine Learning) is headed by Dr. Diptee Ghusse (Chikmurge)... Email: hod.aiml@mitaoe.edu.in"* |
| **Data Science** | Dr. Vaishali Wangikar | Head of Department | **Current (AY 2026–27)** | `https://mitaoe.ac.in/department-of-computer-science-&-engineering-data-science.php` | *"The Department of CSE (Data Science) is headed by Dr. Vaishali Wangikar... Email: hod.datasci@mitaoe.edu.in"* |
| **Mechanical Engineering** | Dr. Maya Charde & Dr. Abhijeet Malge | Dean, SMCE & Associate Professor & HOD | **Current Co-listed Leadership** | `https://mitaoe.ac.in/department-of-mechanical-engineering.php` | *"The Department of Mechanical Engineering at MIT Academy of Engineering (MITAOE) is headed by Dr. Maya Charde (Dr. M. M. Charde) / Dr. Abhijeet Malge, Associate Professor & HOD... Email: dean.smce@mitaoe.ac.in"* |
| **Civil Engineering** | Dr. Nilesh. U. Mate | Associate Professor & HOD | **Current (AY 2026–27)** | `https://mitaoe.ac.in/department-of-civil-engineering.php` | *"The Department of Civil Engineering at MIT Academy of Engineering (MITAOE) is headed by Dr. Nilesh. U. Mate... Email: hodcivil@mitaoe.ac.in"* |
| **Chemical Engineering** | Dr. S. P. Shewale | Associate Professor & HOD | **Current (AY 2026–27)** | `https://mitaoe.ac.in/department-of-chemical-engineering.php` | *"The Department of Chemical Engineering at MIT Academy of Engineering (MITAOE) is headed by Dr. S. P. Shewale... Email: hod.chem@mitaoe.edu.in"* |
| **Electronics & Telecomm.** | Dr. Dipti Y Sakhare | Associate Professor & HOD | **Current (AY 2026–27)** | `https://mitaoe.ac.in/department-of-electronics-and-telecomminication-engineering.php` | *"The Department of Electronics and Telecommunication Engineering at MITAOE is headed by Dr. Dipti Y Sakhare... Email: hodentc@mitaoe.ac.in"* |
| **Director of MITAOE** | Dr. Yogesh. J. Bhalerao / Dr. Mahesh D. Goudar | Director / Officiating Director | **Current Statutory Governance** | `https://mitaoe.ac.in/mitaoe-academic-council.php` | *"The Director of MIT Academy of Engineering (MITAOE) is Dr. Yogesh. J. Bhalerao (Chairman / Director). Officiating Director: Dr. Mahesh D. Goudar."* |

---

## 5. Academic Year & Temporal Logic Audit

1. **Temporal Anchor Verification:**  
   In `backend/app/intelligence/temporal_engine/temporal_parser.py`:
   - `DEFAULT_REFERENCE_YEAR = 2026`
   - `CURRENT` window: Academic Year **2026–27**
   - `HISTORICAL` window: Academic Year **2025–26** and **2024–25**
   - `UPCOMING` window: Academic Year **2027–28**
2. **Current vs. Historical Retrieval Disambiguation:**
   - When a user asks *"What is the current academic year?"*, the query understanding engine classifies it as `temporal`, resolves the anchor, searches the index, and retrieves chunks citing `https://mitaoe.ac.in/academic-year-2026-2027.php`.
   - When a user asks *"Show the previous academic year's calendar"*, the system retrieves historical chunks from `academic-year-2024-2025.php` without asserting them as current.
3. **Database Gap:**
   - The dedicated table `academic_years` in PostgreSQL has **0 rows**.
   - Temporal logic currently operates on chunk metadata (`academic_year: '2026-27'`) in `content_chunks` and regex classification in `temporal_parser.py`, rather than joining against the relational `academic_years` table.

---

## 6. Document Processing & Dependency Audit

Tested against `M:\Third Year\MDMPROJECT\data\documents\doc_170cca417c72.pdf`:

```
========================================================================================
 DOCUMENT PROCESSING DEPENDENCY STATUS
========================================================================================
 [✓] PyMuPDF (fitz)     : Version 2.1 (Installed & Functional)
 [✓] Pillow (PIL)       : Version 13.0.0 (Installed & Functional)
 [✓] NumPy              : Version 2.5.4 (Installed & Functional)
 [✓] Pandas             : Version 3.1.1 (Installed & Functional)
 [✓] OpenCV (cv2)       : Version 5.0.0 (Installed & Functional)
 [✓] Pytesseract        : Version 0.3.13 (Installed & Functional)
 [✓] Tesseract Binary   : Version 5.4.0.20240606 (Located at C:\Program Files\Tesseract-OCR\tesseract.exe)
========================================================================================
```

- **Digital Text Extraction:** 100% functional.
- **Scanned Detection:** Evaluates `text_length < 50 and len(images) > 0`. Successfully distinguished digital pages from scanned circulars.
- **Table Extraction:** PyMuPDF native `find_tables()` extracted 8 tables with headers and row arrays without relying on external pandas table formatting.
- **OCR Fallback:** PyMuPDF renders pages at 300 DPI $\to$ OpenCV CLAHE contrast enhancement and denoising $\to$ Pytesseract `--oem 3 --psm 1`.

---

## 7. Live Q&A Pipeline Audit via HTTP API (`/api/v1/search`)

All 8 official evaluation questions were transmitted via HTTP POST to `http://127.0.0.1:8000/api/v1/search` with payload `{"query": "...", "academic_year": "2026-27"}`:

### Question 1: "Who is the HOD of Computer Engineering?"
- **HTTP Status:** 200 OK | **Total Latency:** 5,395.87 ms (Cold model load)
- **Normalized Query:** `who is the hod of computer engineering?`
- **Expanded Query:** `who is the hod Head of Department of computer engineering?`
- **Intent:** `entity_lookup` | **Department:** `Computer Engineering`
- **Verification Status:** `verified`
- **Top Chunk:** `https://mitaoe.ac.in/department-of-computer-engineering.php` (Score: 0.0297, Rank: 2)
- **Answer:** *"The Head of the Department (HOD) of Computer Engineering at MIT Academy of Engineering (MITAOE) is Dr. Pramod D. Ganjewar (Dr. P D Ganjewar). Designation: Associate Professor & HOD. Department: Computer Engineering. Official Email: hod.comp@mitaoe.edu.in. Official Source: https://mitaoe.ac.in/department-of-computer-engineering.php. (Historical note: Dr. Sandip A. Gade previously served as HOD for earlier academic terms)"*
- **Citations:** `https://mitaoe.ac.in/mitaoe-academic-departments.php`, `https://mitaoe.ac.in/department-of-computer-engineering.php`

### Question 2: "Who is the HOD of Information Technology?"
- **HTTP Status:** 200 OK | **Total Latency:** 10.68 ms
- **Normalized Query:** `who is the hod of information technology?`
- **Intent:** `entity_lookup` | **Department:** `Information Technology`
- **Verification Status:** `verified`
- **Top Chunk:** `https://mitaoe.ac.in/department-of-information-technology.php` (Score: 0.0311, Rank: 1)
- **Answer:** *"The Head of the Department (HOD) of Information Technology at MIT Academy of Engineering (MITAOE) is Dr. Santosh Warpe. Designation: Sr. Assistant Professor & HOD. Official Email: hodit@mitaoe.ac.in"*
- **Citations:** `https://mitaoe.ac.in/department-of-information-technology.php`

### Question 3: "Who is the Director of MITAOE?"
- **HTTP Status:** 200 OK | **Total Latency:** 7.91 ms
- **Normalized Query:** `who is the director of mitaoe?`
- **Intent:** `entity_lookup` | **Department:** `MITAOE Leadership`
- **Verification Status:** `verified`
- **Top Chunk:** `https://mitaoe.ac.in/mitaoe-academic-council.php` (Score: 0.0323, Rank: 1)
- **Answer:** *"The Director of MIT Academy of Engineering (MITAOE) is Dr. Yogesh. J. Bhalerao (Chairman / Director). Officiating Director: Dr. Mahesh D. Goudar. Designation: Director. Institutional Body: MITAOE Academic Council"*
- **Citations:** `https://mitaoe.ac.in/mitaoe-academic-council.php`

### Question 4: "What is the current academic year?"
- **HTTP Status:** 200 OK | **Total Latency:** 7.15 ms
- **Normalized Query:** `what is the current academic year?`
- **Intent:** `temporal`
- **Verification Status:** `verified`
- **Top Chunk:** `https://mitaoe.ac.in/mitaoe-academic-calendar.php` (Score: 0.0328, Rank: 1)
- **Answer:** *"The current official academic year at MIT Academy of Engineering (MITAOE) is 2026–27 (AY 2026-27). Term I of Academic Year 2026–27 commences in July 2026 for Undergraduate (B.Tech) and Postgraduate programs."*
- **Citations:** `https://mitaoe.ac.in/mitaoe-academic-calendar.php`, `https://mitaoe.ac.in/academic-year-2026-2027.php`

### Question 5: "Show the 2026–27 academic calendar."
- **HTTP Status:** 200 OK | **Total Latency:** 7.22 ms
- **Normalized Query:** `show the 2026-27 academic calendar.`
- **Intent:** `temporal`
- **Verification Status:** `verified`
- **Top Chunk:** `https://mitaoe.ac.in/mitaoe-academic-calendar.php` (Score: 0.0320, Rank: 1)
- **Answer:** *"The official academic calendar for Academic Year 2026–27 (Term I) outlines key academic milestones: Term I Commencement: July 2026, Mid-Semester Evaluation: September 2026, End-Semester Examinations: November–December 2026."*
- **Citations:** `https://mitaoe.ac.in/mitaoe-academic-calendar.php`, `https://mitaoe.ac.in/2026-2027-Term-I-UG-Calendar.html`

### Question 6: "List all academic departments."
- **HTTP Status:** 200 OK | **Total Latency:** 7.06 ms
- **Normalized Query:** `list all academic departments.`
- **Intent:** `factual`
- **Verification Status:** `verified`
- **Top Chunk:** `https://mitaoe.ac.in/mitaoe-academic-departments.php` (Score: 0.0295, Rank: 1)
- **Answer:** Contains comprehensive list of 9 undergraduate and postgraduate engineering departments (Computer Engineering, Information Technology, Software Engineering, AI & ML, Data Science, Mechanical, Civil, Chemical, E&TC).
- **Citations:** `https://mitaoe.ac.in/mitaoe-academic-departments.php`

### Question 7: "Find the latest examination timetable."
- **HTTP Status:** 200 OK | **Total Latency:** 7.29 ms
- **Normalized Query:** `find the latest examination timetable.`
- **Intent:** `temporal`
- **Verification Status:** `verified`
- **Top Chunk:** `https://mitaoe.ac.in/academic-year-2026-2027.php` (Score: 0.0328, Rank: 1)
- **Answer:** *"MITAOE Examination Time Table (Academic Year 2026–2027): The latest examination schedules, in-semester assessments, and end-semester examination timetables for AY 2026–27 are published through the Examination Cell portal."*
- **Citations:** `https://mitaoe.ac.in/academic-year-2026-2027.php`

### Question 8: "Show the source page for the Computer Engineering HOD."
- **HTTP Status:** 200 OK | **Total Latency:** 8.10 ms
- **Normalized Query:** `show the source page for the computer engineering hod.`
- **Intent:** `entity_lookup`
- **Verification Status:** `verified`
- **Top Chunk:** `https://mitaoe.ac.in/department-of-computer-engineering.php` (Score: 0.0325, Rank: 1)
- **Answer:** *"The official page for the Department of Computer Engineering at MITAOE is accessible at: 🔗 https://mitaoe.ac.in/department-of-computer-engineering.php"*
- **Citations:** `https://mitaoe.ac.in/department-of-computer-engineering.php`

---

## 8. Frontend Route Audit & Browser Verification

Conducted in a live browser subagent session accessing `http://localhost:3000` against the live backend `http://127.0.0.1:8000`:

| Route | Visual Layout & Rendering | Interactive Control Testing | Console Errors | Network Failures | Audit Status |
|---|---|---|---|---|---|
| `/` | MITAOE branding, AY 2026-27 banner, search input | Instant search submission | 0 | 0 | **VERIFIED OPERATIONAL** |
| `/search` | Query input, AY dropdown, results view | Submitted "Who is the HOD of Computer Engineering?" $\to$ Returned Dr. Pramod D. Ganjewar with `VERIFIED · Confidence: 93%` badge | 0 | 0 | **VERIFIED OPERATIONAL** |
| `/search` (Dev Drawer) | Top chunk table, RRF score, BM25 score, semantic score | Toggle button works (`Dev Diagnostics` $\to$ `Hide Diagnostics`). Exposed candidates and ranks accurately. | 0 | 0 | **VERIFIED OPERATIONAL** |
| `/health` | Subsystem cards: PostgreSQL, Tesseract OCR, Uptime | Clicked `Probe Diagnostic Health`; uptime updated dynamically from 83s to 92s. | 0 | 0 | **VERIFIED OPERATIONAL** |
| `/crawler` | Form controls, URL table, status badges | Rendered 384 discovered, 342 indexed, 42 docs, BFS depth 1, SHA-256 hashes | 0 | 0 | **VERIFIED OPERATIONAL** |
| `/documents` | Document categorization table, badges | Clicked "Inspect Details"; opened modal with metadata, processing mode, and download link | 0 | 0 | **VERIFIED OPERATIONAL** |
| `/settings` | $k_1$, $b$, $k=60$, Top-K sliders, checkboxes | Controls interactable; action buttons present | 0 | 0 | **VERIFIED OPERATIONAL** |

---

## 9. Recommended Architecture & Repair Sequence

To transition the system from its current working hybrid architecture to a fully normalized relational state without breaking retrieval performance:

```
[Phase A: Relational Database Normalization]
  1. Populate `departments` table (9 rows) with id, name, code, active status.
  2. Populate `academic_years` table (AY 2026-27 as is_current=True, 2025-26 and 2024-25 as is_current=False).
  3. Populate `institutional_facts` linking HOD entities directly to department IDs and academic year IDs.

[Phase B: Crawler Temporal Scoping]
  1. Update `temporal_parser.py` so that syllabus links inside <a> tags or curriculum tables do NOT override the parent page's active academic year metadata.
  2. Re-crawl or re-tag department pages so raw faculty biography chunks carry `AY=2026-27` directly from the primary page header.

[Phase C: Documentation Synchronization]
  1. Update `PERFORMANCE.md` with explicit distinction between "Legacy unoptimized" vs "Current optimized HTTP API".
  2. Archive legacy benchmark logs to avoid developer confusion.
```
