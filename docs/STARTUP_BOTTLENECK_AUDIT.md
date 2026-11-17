# VEDANTA — Startup Bottleneck Audit

**Project:** VEDANTA (Verified Educational Data And Networked Technology Assistant)  
**Institution:** MIT Academy of Engineering (MITAOE), Alandi, Pune  
**Current Academic Year:** 2026–27  
**Date of Audit:** November 16, 2026  
**Status:** **PROFILED, DIAGNOSED & ROOT CAUSES IDENTIFIED**

---

## 1. Executive Summary

A comprehensive microsecond-level profiling of VEDANTA startup was executed to instrument every component of application initialization before any code was modified. 

### Key Findings
1. **Primary Bottleneck — Embedding Model Remote Hub Verification (5,590.89 ms):**  
   `SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")` defaulted to online repository verification on every initialization, making unauthenticated HTTPS calls to HuggingFace Hub. When testing with `local_files_only=True`, loading dropped from **5,590 ms** to **183 ms** (**96.7% reduction / 30x speedup**).
2. **Secondary Bottleneck — Redis Socket Timeout (561.54 ms):**  
   The application unconditionally attempted to connect to `redis://localhost:6379/0` with a 500 ms socket timeout even when Redis was offline, blocking initialization for over half a second.
3. **Tertiary Bottleneck — Database Connection Handshake (492.61 ms):**  
   Initial asynchronous engine pool connection and SSL/catalog queries accounted for ~490 ms.
4. **False Readiness & First-Query Hang (>15,000 ms timeout):**  
   FastAPI's startup lifespan reported `"ready to serve requests"` after only ~2.1 seconds without initializing the retrieval pipeline or embedding model. When the first real user query arrived, the lazy initialization triggered remote HuggingFace Hub network checks that timed out after 15 seconds.
5. **Non-Bottlenecks Confirmed by Measurement:**  
   - Database health check: **0.81 ms**
   - Database schema table checks: **6.31 ms**
   - FAISS vector index restoration: **21.98 ms**
   - BM25 index restoration: **9.72 ms**
   - Knowledge graph compilation: **111.77 ms**
   - In-memory L1 cache initialization: **6.75 ms**
   - PDF reprocessing / web crawling: **0.00 ms** (not executed on startup).

---

## 2. Stage-by-Stage Profiling Measurements

Every required stage was instrumented using high-resolution monotonic timers (`time.perf_counter()`):

| Stage | Subsystem / Operation | Initial Measured Time (ms) | % of Startup Time | Classification |
| :--- | :--- | :---: | :---: | :--- |
| **Stage 1** | Backend process initialization (`sys`, base modules) | 1.77 ms | 0.02% | Negligible |
| **Stage 2** | Environment & configuration loading (`pydantic_settings`) | 93.17 ms | 1.23% | Normal |
| **Stage 3** | PostgreSQL async connection & pool establishment | 492.61 ms | 6.51% | Normal DB latency |
| **Stage 4** | Database health check (`SELECT 1`) | 0.81 ms | 0.01% | Highly efficient |
| **Stage 5** | Database schema check (public tables scan) | 6.31 ms | 0.08% | Highly efficient |
| **Stage 6** | Redis connection probe (`aioredis` socket check) | **561.54 ms** | 7.42% | **Bottleneck (Offline timeout)** |
| **Stage 7** | Embedding model initialization (`SentenceTransformer`) | **5,590.89 ms** | 73.86% | **Critical Bottleneck (Remote HF calls)** |
| **Stage 8** | FAISS index restoration from disk (`faiss.read_index`) | 21.98 ms | 0.29% | Highly efficient |
| **Stage 9** | BM25 index restoration from disk (`pickle.load`) | 9.72 ms | 0.13% | Highly efficient |
| **Stage 10** | Knowledge graph initialization (`KnowledgeGraphEngine`) | 111.77 ms | 1.48% | Normal |
| **Stage 11** | In-memory cache initialization (`TTLCache`) | 6.75 ms | 0.09% | Highly efficient |
| **Stage 12** | Background worker initialization | 0.00 ms | 0.00% | No startup blocking |
| **Stage 13** | Frontend startup (`next start -p 3000`) | 536.00 ms | — | Standalone process |
| **Stage 14** | Backend application readiness (e2e including model) | **7,034.21 ms** | 100.0% | Unoptimized baseline |
| **Stage 15** | Overall application readiness (Backend + Frontend) | **~7,570.00 ms** | — | Unoptimized baseline |

---

## 3. Detailed Root Cause Analysis

### Bottleneck A: Remote Repository Network Latency on Local Embedding Models
- **File:** [`backend/app/retrieval/embeddings/embedder.py`](file:///m:/Third%20Year/MDMPROJECT/backend/app/retrieval/embeddings/embedder.py)
- **Code:** `SentenceTransformer(settings.embedding_model, device=device)`
- **Mechanism:** Even though `all-MiniLM-L6-v2` was already fully cached in `C:\Users\gsand\.cache\huggingface\hub\models--sentence-transformers--all-MiniLM-L6-v2`, `SentenceTransformer` connects to HuggingFace Hub via HTTPS to verify commit hashes and look for updates on every instantiation.
- **Impact:** 5.59 seconds wasted on startup. In poor connectivity environments, this hung indefinitely or caused request timeouts.
- **Empirical Proof:** When testing with `local_files_only=True`, the model loaded from disk in **183.72 ms**.

### Bottleneck B: Unprotected Redis Connection Timeout
- **File:** [`backend/app/intelligence/answer_engine/pipeline.py`](file:///m:/Third%20Year/MDMPROJECT/backend/app/intelligence/answer_engine/pipeline.py)
- **Code:** Redis probe without fast connection check or bypass flag.
- **Mechanism:** Redis is not running in the standard local development environment. Attempting to connect to `localhost:6379` hangs until the operating system socket connect timeout expires (~560 ms).
- **Impact:** 561 ms delay on startup.

### Bottleneck C: Premature "READY" State & First-Query Freeze
- **File:** [`backend/app/main.py`](file:///m:/Third%20Year/MDMPROJECT/backend/app/main.py)
- **Code:** Lifespan function logged `"VEDANTA startup complete — ready to serve requests"` without pre-loading the retrieval pipeline.
- **Mechanism:** `/api/v1/health` responded with `status="healthy"` before the embedder, FAISS vector store, or BM25 index were loaded. The very first search request had to bear the full burden of loading models and indexes synchronously, causing the first query to take 15+ seconds or time out.
- **Impact:** Misleading health checks and severe first-query latency spike.

---

## 4. Remediation Plan

1. **Local-First Model Loading:** In `SentenceEmbedder` and `CrossEncoderReranker`, set `local_files_only=True` first, with graceful fallback to download only if local files are missing.
2. **Fast-Failing Redis Probe:** Set Redis socket timeout to 50 ms and check availability once with a cooldown, bypassing Redis completely when disabled.
3. **Eager Pre-warming in Startup Lifespan:** Pre-warm the retrieval pipeline and embedding model during lifespan under structured startup states:
   - `INITIALIZING`
   - `RESTORING KNOWLEDGE`
   - `LOADING SEARCH INDEX`
   - `READY`
4. **Ensure E2E Ready Status:** `/health` must report `READY` only when all essential retrieval and database services are operational.
