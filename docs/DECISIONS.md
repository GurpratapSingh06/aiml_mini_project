# VEDANTA — Architectural Decision Records

**Product:** VEDANTA  
**Last Updated:** 2026-11-08

---

## ADR-001: Python Version

**Decision:** Python 3.13.7 (system-installed)  
**Alternatives:** Python 3.11 (spec), 3.12  
**Reason:** System has Python 3.13.7. The spec mentioned 3.11 as target but 3.13.7 is backward-compatible for all required libraries. Using the available version avoids installing a secondary interpreter. If library incompatibilities arise, pyenv will be used.  
**Status:** Accepted

---

## ADR-002: Database (PostgreSQL via Docker)

**Decision:** Run PostgreSQL 16 via Docker Compose  
**Alternatives:** Local PostgreSQL install, SQLite (rejected — not suitable for production)  
**Reason:** Docker provides a clean, reproducible environment that works identically across developer machines and future deployment targets. No manual PostgreSQL installation required.  
**Status:** Accepted

---

## ADR-003: Redis via Docker

**Decision:** Redis 7 via Docker Compose  
**Alternatives:** Memcached, in-memory dict  
**Reason:** Redis provides persistent caching, pub/sub for job status notifications, and is the standard backend for RQ/Celery job queues. Docker simplifies setup.  
**Status:** Accepted

---

## ADR-004: Background Jobs — RQ over Celery

**Decision:** Use RQ (Redis Queue) for background jobs  
**Alternatives:** Celery (more complex, requires broker config), APScheduler  
**Reason:** RQ is simpler to configure with Redis, has lower overhead, sufficient for the crawl/OCR/embedding workloads planned. Celery would be preferred if multi-broker or advanced routing is needed in the future.  
**Status:** Accepted

---

## ADR-005: Embedding Model Selection

**Decision:** `sentence-transformers/all-MiniLM-L6-v2` as the initial embedding model  
**Alternatives:** `all-mpnet-base-v2` (better accuracy, higher memory), `paraphrase-multilingual-MiniLM-L12-v2` (multilingual)  
**Reason:** MiniLM-L6-v2 provides a strong accuracy-to-speed tradeoff on CPU. 384-dimensional vectors are compact for FAISS. Can be upgraded later without schema changes (embedding_model_id tracked in DB).  
**Status:** Accepted

---

## ADR-006: FAISS Index Type

**Decision:** `IndexFlatIP` with L2-normalized embeddings initially  
**Alternatives:** `IndexIVFFlat` (faster at scale), `IndexHNSWFlat` (approximate but fast)  
**Reason:** Exact search with `IndexFlatIP` is accurate and adequate for the initial corpus size (< 100k chunks). Will switch to `IndexIVFFlat` or HNSW if corpus exceeds 500k chunks and latency degrades.  
**Status:** Accepted

---

## ADR-007: Answer Generation Without LLM

**Decision:** Evidence-based template answer generation without a mandatory LLM  
**Alternatives:** OpenAI GPT, Gemini API, local Ollama LLM  
**Reason:** Per spec requirements — no mandatory paid APIs, no mandatory GPU. Answer engine uses NLP + rule-based extraction + structured retrieval. An optional LLM interface will be added later as a plugin.  
**Status:** Accepted

---

## ADR-008: OCR Engine

**Decision:** Tesseract as primary OCR, PaddleOCR as optional  
**Alternatives:** AWS Textract (paid), Azure Form Recognizer (paid), EasyOCR  
**Reason:** Tesseract is free, local, battle-tested, and supports English well. PaddleOCR provides better accuracy for complex layouts and will support Hindi/Marathi in future phases. No paid cloud OCR to maintain local-first principle.  
**Status:** Accepted

---

## ADR-009: Frontend Framework

**Decision:** Next.js 15 with App Router, TypeScript, Tailwind CSS  
**Alternatives:** Vite + React SPA, Remix  
**Reason:** Next.js provides SSR for initial page loads (better UX), API routes if needed, and strong TypeScript support. App Router enables streaming responses for search results.  
**Status:** Accepted

---

## ADR-010: Content Chunking Strategy

**Decision:** Sentence-aware recursive chunking (512 tokens, 64-token overlap)  
**Alternatives:** Fixed-character splits, paragraph splits, semantic splits  
**Reason:** Sentence-aware chunking preserves semantic context better than character splits. 512 tokens aligns with the MiniLM context window. 64-token overlap prevents answer loss at chunk boundaries.  
**Status:** Accepted

---

## ADR-011: Hybrid Retrieval Fusion

**Decision:** Reciprocal Rank Fusion (RRF) over score normalization  
**Alternatives:** Linear score combination, CombSUM, CombMNZ  
**Reason:** RRF is robust to score scale differences between BM25 and cosine similarity. No calibration required. Well-validated in literature. Parameters (k=60) are configurable.  
**Status:** Accepted

---

## ADR-012: Security — SSRF Protection

**Decision:** Explicit allowlist of crawlable domains + IP range blocking  
**Alternatives:** Reverse proxy filtering, DNS-level blocking  
**Reason:** Application-level validation is mandatory regardless of infrastructure. Block private IP ranges (10.x, 192.168.x, 172.16-31.x, 127.x, 169.254.x) and validate URL scheme before any outbound request.  
**Status:** Accepted
