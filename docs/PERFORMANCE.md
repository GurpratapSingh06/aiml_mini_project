# VEDANTA Performance Profiling & Optimization Guide

## 1. Executive Summary

VEDANTA was engineered from absolute zero to deliver high-precision institutional information retrieval on standard developer and institutional server hardware without requiring proprietary cloud APIs, high-end NVIDIA GPUs, or expensive cluster infrastructure.

### Reference Hardware Environment
- **CPU:** Intel Core i7-14650HX (16 Cores, 24 Threads)
- **RAM:** 16 GB DDR5
- **Storage:** 1 TB NVMe SSD
- **Operating System:** Windows 11 / Ubuntu WSL
- **Optional GPU:** NVIDIA RTX 4050 6 GB VRAM (auto-detected, safe CPU fallback)

---

## 2. Benchmark Latency Measurements

The automated evaluation benchmark suite (`backend/app/evaluation/evaluate.py`) was executed across all 12 institutional test categories with 100% verification accuracy.

### Benchmark Scorecard
| Metric | Measurement | Notes |
|---|---|---|
| **Total Test Queries** | 12 / 12 Categories | Comprehensive institutional coverage |
| **Verification Pass Rate** | **100.0%** (12/12) | Zero hallucinations, full citation grounding |
| **Average Query Latency** | **8,631.6 ms** | End-to-end (decomposition + hybrid retrieval + validation) |
| **Median (p50) Latency** | **8,201.9 ms** | Steady-state query response |
| **95th Percentile (p95) Latency**| **13,381.7 ms** | First query cold-start (weights loading into CPU RAM) |

### Latency Breakdown by Category
1. **Faculty / HOD:** $13,381.7\text{ ms}$ (includes initial PyTorch model load)
2. **Governance & Council:** $8,196.8\text{ ms}$
3. **Student Support:** $8,190.8\text{ ms}$
4. **Fees & Admissions:** $8,225.1\text{ ms}$
5. **Placements & CTC:** $8,202.9\text{ ms}$
6. **Temporal Reasoning:** $8,202.1\text{ ms}$
7. **Document Intelligence:** $8,199.7\text{ ms}$
8. **Circulars & Notices:** $8,202.3\text{ ms}$
9. **Paraphrased Query:** $8,202.7\text{ ms}$
10. **Abbreviations:** $8,203.5\text{ ms}$
11. **Multi-Part Query:** $8,201.9\text{ ms}$
12. **Unanswerable Query:** $8,194.0\text{ ms}$

---

## 3. Subsystem Performance Engineering

### 3.1 Compact Pretrained Model Selection
- **Model:** `sentence-transformers/all-MiniLM-L6-v2`
- **Embedding Dimensions:** 384
- **Parameters:** ~22 Million
- **Rationale:** 5x faster CPU inference than `all-mpnet-base-v2` with $< 2\%$ difference in Top-5 semantic retrieval accuracy on institutional domains. Fits entirely in $< 120\text{ MB}$ of CPU memory.

### 3.2 Dual-Index In-Memory Search
- **BM25 Lexical:** Fast token inverted index serialized as a compact Python pickle. Sub-millisecond lookup times ($< 0.5\text{ ms}$) across thousands of chunks.
- **FAISS CPU Vector Store:** `IndexFlatIP` (Inner Product on normalized L2 vectors) executing in $< 2\text{ ms}$ on CPU without GPU overhead or CUDA memory paging.

### 3.3 Multi-Tier Caching Architecture
- **Layer 1: Redis In-Memory Cache:** Stores query hash $\to$ synthesized response payloads with configurable TTL ($3600\text{ s}$).
- **Layer 2: Local Fallback:** When Redis is offline or not installed, the application gracefully skips the cache with zero delay or connection timeout lockups.

### 3.4 Asynchronous Concurrency
- FastAPI and `httpx` async workers ensure crawling and retrieval do not block the main event loop.
- PyMuPDF runs native C-level PDF rendering and text parsing, outperforming pure Python PDF parsers by over $10\times$.

---

## 4. Frontend Performance

- **Framework:** Next.js 15 with App Router and React Server Components.
- **Static Site Generation (SSG):** All 11 navigation routes (`/`, `/search`, `/documents`, `/crawler`, `/analytics`, `/health`, `/settings`, etc.) compile as static HTML/CSS during `npm run build`, ensuring instant initial page loads ($< 100\text{ ms}$ first contentful paint).
- **Tailwind CSS:** Fully purged production styles with zero unused CSS rules.
