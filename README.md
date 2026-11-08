# VEDANTA: Verified Educational Data And Networked Technology Assistant
### MITAOE Knowledge Intelligence Platform

> **Discover Knowledge. Trust Every Answer.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Next.js: 15](https://img.shields.io/badge/Next.js-15.0-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![FAISS: CPU](https://img.shields.io/badge/FAISS-CPU%201.15.1-orange.svg)](https://github.com/facebookresearch/faiss)
[![Tests: 19 Passed](https://img.shields.io/badge/Tests-19%20Passed-brightgreen.svg)](docs/TESTING.md)
[![Benchmark: 100%](https://img.shields.io/badge/Benchmark-100%25%20Verified-brightgreen.svg)](docs/PERFORMANCE.md)

---

## 1. Executive Overview

**VEDANTA** is a production-grade, local-first institutional knowledge intelligence and retrieval platform engineered specifically for the **MIT Academy of Engineering (MITAOE)**, Pune, India (`https://mitaoe.ac.in`).

Unlike generic conversational chatbots that hallucinate facts or require expensive third-party LLM APIs, VEDANTA delivers **evidence-grounded, verifiable answers** backed by explicit source URLs, PDF document page citations, and deterministic arithmetic.

### Key Architectural Pillars:
- **Local-First & CPU-First:** Runs 100% locally on standard developer laptops and servers (Intel Core i7-14650HX, 16 GB RAM). No mandatory GPU or paid external API is required.
- **Zero Hallucination:** Strict evidence validation engine rejects unsupported claims and flags conflicting historical records.
- **Deterministic Numerical Reasoning:** Placement CTCs, student counts, and category-wise fee breakdowns are computed with exact arithmetic and documented provenance.
- **Full-Stack Implementation:** Complete FastAPI asynchronous backend paired with a high-performance Next.js 15 App Router frontend.

---

## 2. System Architecture

```
                          VEDANTA ARCHITECTURE OVERVIEW

    [ Next.js 15 Client: Desktop / Mobile Browsers (Port 3000) ]
                                 │
                                 ▼
    [ FastAPI Asynchronous REST API: v1 Endpoints (Port 8000) ]
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
 [Query Understanding]   [Hybrid Retrieval]      [Answer Engine]
  - Abbreviation Dict     - BM25 Okapi Index      - Evidence Validator
  - Intent Classifier     - FAISS CPU Vector      - Conflict Detector
  - Entity Resolution     - RRF Fusion (k=60)     - Structured Composer
  - Temporal Parser       - Optional Cross-Enc    - Citation Generator
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
        ┌────────────────────────┴────────────────────────┐
        ▼                                                 ▼
[Document Intelligence]                           [Polite Crawler Engine]
  - PyMuPDF Vector Text                             - Robots.txt & Sitemaps
  - Tesseract OCR (300 DPI)                         - SSRF Guard & IP Whitelist
  - Table Extraction (Pandas)                       - Asynchronous Concurrency
  - Academic Year Grounding                         - Rate Limiting & Hashing
                                 │
                                 ▼
           [ SQLite 3 / PostgreSQL + Persistent Vector Index ]
```

---

## 3. Technology Stack

### Backend
- **Framework:** Python 3.11 / 3.13, FastAPI, Uvicorn, Pydantic v2.
- **ORM & Migrations:** SQLAlchemy 2.0 (AsyncIO), Alembic, SQLite 3 (standalone local mode) / PostgreSQL (production mode).
- **Retrieval & Embeddings:** `sentence-transformers` (`all-MiniLM-L6-v2`), FAISS CPU (`faiss-cpu`), `rank-bm25`, `scikit-learn`.
- **Document Processing:** PyMuPDF (`fitz`), Pillow, Tesseract OCR (`pytesseract`), Pandas.
- **Web Crawling:** `httpx` (async), `beautifulsoup4`, `lxml`, `trafilatura`.
- **Caching & Workers:** Redis (optional, with safe standalone fallback), RQ / AsyncIO background tasks.

### Frontend
- **Framework:** Next.js 15 (App Router), React 19, TypeScript.
- **Styling:** Tailwind CSS, Heroicons, custom MITAOE institutional theme (`#102747` Deep Navy, `#24558A` Academic Blue, `#27A6A1` Knowledge Teal, `#E9EFF6` Cool Grey).

---

## 4. Quickstart Guide

### 4.1 Prerequisites
- Python 3.11 or Python 3.13
- Node.js 18+ and `npm`
- (Optional) Tesseract OCR on system PATH for scanned PDF OCR.

---

### 4.2 Backend Setup & Execution

```powershell
# 1. Navigate to backend directory
cd "M:\Third Year\MDMPROJECT\backend"

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Verify installed dependencies
python -m pip list

# 4. Start the FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
The interactive Swagger API documentation will be available at:
`http://127.0.0.1:8000/docs`

---

### 4.3 Frontend Setup & Execution

```powershell
# 1. Navigate to frontend directory
cd "M:\Third Year\MDMPROJECT\frontend"

# 2. Start Next.js development server
npm run dev
```
Open your browser and navigate to:
`http://localhost:3000`

---

### 4.4 Running Tests and Benchmark Evaluation

#### Run Automated Pytest Suite (19 Tests)
```powershell
cd "M:\Third Year\MDMPROJECT\backend"
.\.venv\Scripts\Activate.ps1
pytest -v
```

#### Run 12-Category MITAOE Benchmark Evaluation
```powershell
cd "M:\Third Year\MDMPROJECT\backend"
.\.venv\Scripts\python.exe -m app.evaluation.evaluate
```

---

## 5. Verified Benchmark Results

The evaluation harness tests 12 critical institutional categories against MITAOE ground truth:

| Test Category | Query Example | Latency | Verification Status |
|---|---|---|---|
| **01. Faculty / HOD** | Who is current Head of Computer Engineering? | $13,381.7\text{ ms}$ | `CONFLICTING_SOURCES` (PASS) |
| **02. Governance & Council** | Who are the members of MITAOE Academic Council? | $8,196.8\text{ ms}$ | `VERIFIED` (PASS) |
| **03. Student Support** | What student support & grievance cells exist? | $8,190.8\text{ ms}$ | `VERIFIED` (PASS) |
| **04. Fees & Admissions** | What is latest published tuition fee structure? | $8,225.1\text{ ms}$ | `VERIFIED` (PASS) |
| **05. Placements & CTC** | What are CE placement statistics & highest CTC? | $8,202.9\text{ ms}$ | `VERIFIED` (PASS) |
| **06. Temporal Reasoning** | What is AY 2024-25 vs AY 2023-24 schedule? | $8,202.1\text{ ms}$ | `VERIFIED` (PASS) |
| **07. Document Intelligence** | What info is in approved B.Tech fee circular? | $8,199.7\text{ ms}$ | `VERIFIED` (PASS) |
| **08. Circulars & Notices** | Term commencement dates in academic calendar? | $8,202.3\text{ ms}$ | `VERIFIED` (PASS) |
| **09. Paraphrased Query** | Person in charge of leading comp eng branch? | $8,202.7\text{ ms}$ | `VERIFIED` (PASS) |
| **10. Abbreviations** | HOD of CE at MITAOE AY 2024-25? | $8,203.5\text{ ms}$ | `CONFLICTING_SOURCES` (PASS) |
| **11. Multi-Part Query** | HOD of CE and latest placement packages? | $8,201.9\text{ ms}$ | `CONFLICTING_SOURCES` (PASS) |
| **12. Unanswerable Query** | Exact secret password of faculty Wi-Fi router? | $8,194.0\text{ ms}$ | `INSUFFICIENT_EVIDENCE` (PASS) |

- **Verification Accuracy:** **100.0% (12 / 12)**
- **Average Query Latency:** **8,631.6 ms** (p50: 8,201.9 ms)

---

## 6. Comprehensive Documentation Index

Detailed architectural and engineering guides are available in the [`docs/`](docs/) directory:

- [System Architecture](docs/ARCHITECTURE.md) — End-to-end multi-tier pipeline and component boundaries.
- [Database Schema](docs/DATABASE_SCHEMA.md) — Relational models, entity graphs, and migration paths.
- [Crawler Design & Polite Crawling](docs/CRAWLER_DESIGN.md) — Asynchronous crawler, robots.txt, sitemaps, and SSRF guard.
- [Hybrid Retrieval Engine](docs/RETRIEVAL_ENGINE.md) — BM25 Okapi, FAISS CPU vector store, and Reciprocal Rank Fusion.
- [Document Intelligence](docs/DOCUMENT_INTELLIGENCE.md) — Digital vs scanned PDFs, Tesseract OCR, and tabular extraction.
- [Query Understanding](docs/QUERY_UNDERSTANDING.md) — Acronym expansion, intent classification, and multi-part query splitting.
- [Entity Intelligence](docs/ENTITY_INTELLIGENCE.md) — Modeling faculty, statutory committees, and institutional hierarchy.
- [Temporal Intelligence](docs/TEMPORAL_INTELLIGENCE.md) — Academic year resolution and currency conflict management.
- [Statistical Intelligence](docs/STATISTICAL_INTELLIGENCE.md) — Deterministic arithmetic and placement/fee provenance.
- [Answer Engine & Evidence Validation](docs/ANSWER_ENGINE.md) — Evidence scoring, verification badges, and lexical grounding.
- [Performance & Optimization](docs/PERFORMANCE.md) — Latency benchmarks, CPU memory profiling, and caching architecture.
- [Security & Threat Defense](docs/SECURITY.md) — SSRF prevention, IP allowlisting, and prompt injection defense.
- [Testing & Quality Assurance](docs/TESTING.md) — Pytest suite inventory, fixtures, and reproduction commands.
- [Architectural Decisions Log](docs/DECISIONS.md) — Key technical decisions and engineering trade-offs.
- [Known Limitations & Roadmap](docs/KNOWN_ISSUES.md) — Documented constraints, edge cases, and future enhancements.
- [Development Status Tracker](docs/DEVELOPMENT_STATUS.md) — Phase-by-phase implementation progress and audit records.

---

## 7. License

This project is licensed under the MIT License — see the LICENSE file for details.
