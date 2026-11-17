# VEDANTA — Architectural Decision Records

**Product:** VEDANTA  
**Institution:** MIT Academy of Engineering (MITAOE)  
**Last Updated:** 2026-11-15  
**Current Academic Year:** 2026–27  

---

## ADR-001: Python Version

**Decision:** Python 3.13.7 (system-installed)  
**Alternatives:** Python 3.11 (spec), 3.12  
**Reason:** System has Python 3.13.7. The spec mentioned 3.11 as target but 3.13.7 is backward-compatible for all required libraries. Using the available version avoids installing a secondary interpreter. If library incompatibilities arise, pyenv will be used.  
**Status:** Accepted

---

## ADR-002: Database Engine & Local PostgreSQL Setup

**Decision:** Local PostgreSQL 18 with persistent `vedanta` database schema  
**Alternatives:** SQLite, Docker-only container  
**Reason:** PostgreSQL provides full relational schema support, JSONB document storage, and pgvector compatibility. Local database avoids Docker container virtualization overhead on Windows developer machines.  
**Status:** Accepted

---

## ADR-003: Redis Caching & Multi-Tier Fallback

**Decision:** Redis 7 with an In-Memory L1 Cache (`cachetools.TTLCache`) and Circuit Breaker  
**Alternatives:** Redis-only, Memcached, in-memory dict without eviction  
**Reason:** If Redis is down or unreachable, an unbounded connection timeout blocks FastAPI request loops on Windows. Implementing an in-memory L1 cache (1024 entries, 1800s TTL) delivers sub-10ms query responses, while a circuit breaker with an 80-150ms socket timeout protects backend latency when Redis is inactive.  
**Status:** Accepted

---

## ADR-004: Background Jobs — RQ over Celery

**Decision:** Use RQ (Redis Queue) for background jobs  
**Alternatives:** Celery (more complex, requires broker config), APScheduler  
**Reason:** RQ is simpler to configure with Redis, has lower overhead, sufficient for the crawl/OCR/embedding workloads planned. Celery would be preferred if multi-broker or advanced routing is needed in the future.  
**Status:** Accepted

---

## ADR-005: Embedding Model Selection

**Decision:** `sentence-transformers/all-MiniLM-L6-v2` on CPU  
**Alternatives:** `all-mpnet-base-v2` (better accuracy, higher memory), paid OpenAI/Gemini embeddings  
**Reason:** MiniLM-L6-v2 provides a 384-dimensional dense representation with fast CPU inference (<10ms per query), zero API costs, and full air-gapped capability.  
**Status:** Accepted

---

## ADR-006: FAISS Index Type

**Decision:** `IndexFlatIP` with L2-normalized embeddings  
**Alternatives:** `IndexIVFFlat`, `IndexHNSWFlat`  
**Reason:** Exact inner product cosine search with `IndexFlatIP` is 100% accurate and sub-millisecond for the corpus size (<10,000 chunks). Saved and loaded directly from disk (`data/indexes/faiss.index`).  
**Status:** Accepted

---

## ADR-007: Answer Generation Without Paid LLMs

**Decision:** Evidence-grounded structural composition without mandatory paid LLM APIs  
**Alternatives:** OpenAI GPT-4o, Gemini API, local Ollama LLM  
**Reason:** VEDANTA must guarantee institutional reliability, verifiable citations, zero factual hallucinations, and zero API costs. Structured fact extraction, RRF retrieval, and evidence-grounded templating ensure 100% traceable answers.  
**Status:** Accepted

---

## ADR-008: OCR Engine

**Decision:** PyMuPDF for digital vector PDFs with Tesseract OCR fallback for scanned pages  
**Alternatives:** AWS Textract, Google Cloud Vision OCR  
**Reason:** Local-first, privacy-preserving, and free. PyMuPDF extracts text, bounding boxes, and tables in milliseconds. Tesseract operates as an asynchronous fallback for scanned circulars.  
**Status:** Accepted

---

## ADR-009: Frontend Architecture

**Decision:** Next.js 15 with App Router, TypeScript, and Tailwind CSS  
**Alternatives:** Vite + React SPA, Remix  
**Reason:** Next.js App Router provides lightweight static generation, modular route architecture, and client-side streaming for the interactive developer diagnostic drawer.  
**Status:** Accepted

---

## ADR-010: Sentence-Aware Chunking Strategy

**Decision:** Sentence-aware text chunker (512 tokens max, 64-token overlap)  
**Alternatives:** Fixed-character splits, paragraph splits  
**Reason:** Preserves grammatical cohesion and prevents cutting entities or designations across chunk boundaries.  
**Status:** Accepted

---

## ADR-011: Hybrid Retrieval Fusion

**Decision:** Reciprocal Rank Fusion ($k=60$) combining BM25 Okapi and FAISS dense scores  
**Alternatives:** Linear score weighted combination, Cross-encoder re-ranking only  
**Reason:** BM25 handles exact entity lookups, acronyms, and email addresses; FAISS handles semantic paraphrasing. RRF avoids non-comparable score scale calibration issues.  
**Status:** Accepted

---

## ADR-012: In-Memory L1 Cache with Circuit Breaker

**Decision:** Implement an in-memory `TTLCache` in `AnswerPipeline` alongside a Redis socket timeout  
**Alternatives:** Pure Redis, pure SQLite cache  
**Reason:** Prevents 2000ms TCP connection delays on Windows when Redis is offline. Repeated queries return in <10ms directly from memory.  
**Status:** Accepted

---

## ADR-013: Canonical Active Academic Year 2026–27 Grounding

**Decision:** Set reference academic year to **2026–27** as canonical `CURRENT` state  
**Alternatives:** System calendar year (2024), dynamic year detection without anchor  
**Reason:** Resolves severe temporal regression where 2024–25 documents appeared first in web crawls and biased answers. Historical documents (2024–25, 2025–26) are preserved with `HISTORICAL` flags.  
**Status:** Accepted

---

## ADR-014: Distinction Between Intra-Source Co-Listing and Cross-Source Conflict

**Decision:** Conflict detection flags contradictions only when independent source URLs disagree  
**Alternatives:** Flag conflict whenever multiple names appear in a single chunk  
**Reason:** Official department pages frequently list multiple leaders in joint or hierarchal roles (e.g. Dean & Associate HOD, Dr. Maya Charde & Dr. Abhijeet Malge). Intra-source co-listing is valid organizational structure, not a conflict.  
**Status:** Accepted

---

## ADR-015: Contextual Acronym Expansion and Lexical Grounding Guard

**Decision:** Context-aware regex expansion for ambiguous acronyms (IT, CE, SE, DS) combined with lexical token grounding  
**Alternatives:** Unconditional acronym replacement, pure embedding similarity  
**Reason:** Prevents mangling English pronouns ("it", "be", "me") while reliably expanding "IT department" to "Information Technology". Lexical grounding checks ensure out-of-domain queries (e.g. "Mars campus", "MBBS") cleanly trigger `insufficient_evidence`.  
**Status:** Accepted

---

## ADR-016: Question-Driven Live Fetching on Retrieval Confidence Deficit

**Decision:** Trigger targeted live page fetch when retrieval score is low for an institutional query  
**Alternatives:** Reject immediately, trigger full site crawl  
**Reason:** Instead of crawling all pages during startup or asking the user to wait for a full crawl, the system on-demand fetches the specific department or leadership page, parses chunks, and updates indexes in real-time.  
**Status:** Accepted

---

## ADR-017: NetworkX Institutional Knowledge Graph with Typed Multi-Relational Topology

**Decision:** Implement an in-memory directed multigraph (`networkx.MultiDiGraph`) in `backend/app/intelligence/knowledge_graph`  
**Alternatives:** Neo4j (external heavy service), SPARQL RDF triplestore, pure relational SQL joins  
**Reason:** NetworkX is lightweight, zero-dependency, pure Python, and CPU-fast (<1 ms traversals). It formally models institutional nodes (Institution, Department, Person, AcademicYear, PlacementRecord, FeeRecord) and typed relationships (`WORKS_IN`, `HEADS`, `FORMERLY_HEADED`, `BELONGS_TO`, `HAS_PLACEMENT_STATISTICS`, `HAS_FEE_STRUCTURE`), enabling deterministic disambiguation of core CE vs. CSE sub-branches, current vs. predecessor HODs, and faculty profiles.  
**Status:** Accepted

---

## ADR-018: Dual-Pipeline Statistical Intelligence (Dynamic data-target Scraping + Relational SQL Stats Store)

**Decision:** Parse dynamic `<span class="counter" data-target="...">` attributes from `mitaoe.ac.in/placement.php` into structured PostgreSQL `placement_records` and `fee_records`, accessed via an async data access layer (`stats_store.py`)  
**Alternatives:** Static scraping of rendered innerText only, LLM-based numerical extraction  
**Reason:** The official MITAOE website animates numbers with JavaScript; standard HTML scrapers extract empty or placeholder strings. Targeting `data-target` attributes guarantees exact capture of the 27 LPA highest package, 6.75 LPA average CTC, 500+ offers, and 450+ companies, while the relational store enables deterministic SQL comparisons and denominator integrity checks.  
**Status:** Accepted

---

## ADR-019: Specialized Answer Reasoning Composition Engines

**Decision:** Implement dedicated composition modules (`Faculty`, `HOD`, `Placement`, `Fee`, `Comparison`, `Temporal`) inside `AnswerComposer` grounded in Knowledge Graph and validated evidence passages  
**Alternatives:** Single generic regex passage extraction, unconstrained text generative models  
**Reason:** Prevents misclassifying faculty members as HODs, eliminates hallucinated fees or salaries, renders clean side-by-side comparison tables with calculated percentage differences, and guarantees that every answer cites official MITAOE sources.  
**Status:** Accepted
