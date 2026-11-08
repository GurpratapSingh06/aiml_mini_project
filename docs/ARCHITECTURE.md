# VEDANTA — System Architecture

**Product:** VEDANTA (Verified Educational Data And Networked Technology Assistant)  
**Institution:** MIT Academy of Engineering (MITAOE), Pune, Maharashtra, India  
**System Version:** v0.1.0  
**Tagline:** Discover Knowledge. Trust Every Answer.

---

## 1. Architectural Philosophy

VEDANTA is an institutional knowledge intelligence platform built from absolute zero. Unlike typical conversational chatbots that rely on generative Large Language Models prone to hallucinations, VEDANTA is grounded in:
1. **Local-First Processing:** Runs entirely on CPU or optional GPU acceleration without mandatory cloud APIs.
2. **Deterministic Evidence Retrieval:** Every answer is backed by verifiable web URLs and primary PDF page numbers.
3. **Exact Arithmetic:** Mathematical calculations (averages, package changes, fee summaries) are performed deterministically in Python/SQL, never guessed.
4. **Resilient Failure Handling:** Insufficient or conflicting evidence is explicitly surfaced rather than fabricated.

```
+-----------------------------------------------------------------------------------+
|                           USER / STUDENT DEVICE                                   |
|   (Any web browser: Laptops, Desktops, Android, iOS, Tablets — Zero Model Download)   |
+-----------------------------------------------------------------------------------+
                                        |  HTTP/JSON
                                        v
+-----------------------------------------------------------------------------------+
|                        FRONTEND — Next.js 15 App Router                           |
|   - Branded Academic Theme (Deep Navy, Academic Blue, Knowledge Teal, Cool Grey) |
|   - Search & Evidence Viewer, Document Library, Crawl Console, Analytics, Health  |
+-----------------------------------------------------------------------------------+
                                        |  REST / OpenAPI (/api/v1/)
                                        v
+-----------------------------------------------------------------------------------+
|                        APPLICATION API GATEWAY — FastAPI                          |
|   - Asynchronous Request Dispatching, Rate Limiting, Input Sanitization           |
|   - Gzip Middleware, OpenAPI Schema Generation, CORS Security                     |
+-----------------------------------------------------------------------------------+
                                        |
       +--------------------------------+-------------------------------+
       |                                                                |
       v                                                                v
+----------------------------------+          +-------------------------------------+
|      INTELLIGENCE ENGINES        |          |      INGESTION & RETRIEVAL CORE     |
| - Query Understanding            |          | - SSRF-Guarded Website Crawler      |
| - Entity Intelligence Engine     |          | - PyMuPDF & Tesseract OCR Pipeline  |
| - Temporal Validity Engine       |          | - BM25 Okapi Lexical Retriever      |
| - Statistical Intelligence Engine|          | - Sentence-Transformers Embedder    |
| - Document Intelligence Engine   |          | - FAISS IndexFlatIP Vector Store    |
| - Evidence Validator & Composer  |          | - Reciprocal Rank Fusion (RRF)      |
+----------------------------------+          +-------------------------------------+
       |                                                                |
       +--------------------------------+-------------------------------+
                                        |
                                        v
+-----------------------------------------------------------------------------------+
|                         PERSISTENCE & BACKGROUND TIER                             |
|   - PostgreSQL (AsyncPG): Normalized relational records (pages, entities, stats)  |
|   - Redis (aioredis): High-speed query answer caching & RQ job queue broker       |
|   - On-Disk Storage: FAISS binary index, BM25 corpus pickle, raw PDF repository    |
+-----------------------------------------------------------------------------------+
```

---

## 2. Logical Layers

### Layer 1: Presentation (Next.js 15)
- App Router with statically optimized routes (`/`, `/search`, `/documents`, `/crawler`, `/analytics`, `/health`, `/settings`).
- Tailwind CSS v4 design system adhering to the official VEDANTA palette.
- Accessible components with Lucide icons.

### Layer 2: API & Application Service (FastAPI)
- Modular versioned routers under `/api/v1/`.
- Strict Pydantic models for request validation and response serialization.
- Diagnostic health probes for continuous monitoring.

### Layer 3: Query Understanding & NLP
- Regex-driven abbreviation expansion (e.g. `HOD of CE` → `Head of Department of Computer Engineering`).
- Deterministic intent classification (factual, statistical, comparison, entity lookup).
- Entity extraction for institutional people and departments.

### Layer 4: Hybrid Information Retrieval
- **Lexical:** BM25 Okapi for exact names, course acronyms, and institutional titles.
- **Semantic:** `sentence-transformers/all-MiniLM-L6-v2` generating 384-dimensional dense vectors.
- **Vector Search:** FAISS CPU `IndexFlatIP` on L2-normalized vectors.
- **Fusion:** Reciprocal Rank Fusion (RRF) with configurable smoothing ($k=60$).

### Layer 5: Specialized Institutional Intelligence
- **Entity Intelligence Engine:** Faculty profiles, departmental leadership, council memberships.
- **Temporal Engine:** Academic year extraction ($2024-25$), currency classification.
- **Statistical Engine:** Deterministic math for placement rates and fee calculations.
- **Document Engine:** Page-level chunking and PDF table preservation.

### Layer 6: Evidence Validation & Answer Composition
- Score thresholding calibrated for RRF fusion.
- Verification statuses: `VERIFIED`, `PARTIALLY_VERIFIED`, `UNCERTAIN`, `INSUFFICIENT_EVIDENCE`, `CONFLICTING_SOURCES`.
- Ground truth answer synthesis with clickable source URLs and PDF page citations.
