# VEDANTA Automated Testing and QA Strategy

## 1. Overview

To guarantee enterprise reliability, maintainability, and zero regression, VEDANTA features a comprehensive automated testing framework covering:
- **Unit Tests:** Individual algorithmic units (crawling, normalization, BM25, FAISS, temporal parsing, stats extraction).
- **Integration Tests:** End-to-end question-answering workflows from raw query to verified answer with mock databases.
- **Benchmark Evaluation:** 12-category empirical accuracy test harness evaluating retrieval quality and latency.
- **Frontend Build Verification:** Next.js 15 type-checking, route validation, and static compilation.

---

## 2. Test Suite Architecture

```
backend/
├── pytest.ini                    # Pytest configuration (pythonpath=., asyncio_mode=auto)
├── tests/
│   ├── conftest.py               # Shared fixtures (in-memory SQLite session, sample chunks)
│   ├── unit/
│   │   ├── test_crawler.py       # URL validator, SSRF guard, normalizer, robots.txt
│   │   ├── test_retrieval.py     # BM25, RRF fusion, vector store, TF-IDF
│   │   └── test_intelligence.py  # Query context, entities, temporal, stats, evidence
│   └── integration/
│       └── test_pipeline.py      # Full retrieval & answer generation pipeline
└── app/evaluation/
    ├── dataset.py                # 12 MITAOE institutional benchmark queries
    └── evaluate.py               # Automated scorecard runner & latency profiler
```

---

## 3. Running Unit and Integration Tests

Activate the Python virtual environment and run Pytest:

```powershell
# From the backend directory
cd "M:\Third Year\MDMPROJECT\backend"
.\.venv\Scripts\Activate.ps1

# Run the complete test suite with verbose output
pytest -v
```

### Verified Test Suite Results
```
tests/unit/test_crawler.py::test_url_normalizer PASSED
tests/unit/test_crawler.py::test_ssrf_guard_blocks_localhost PASSED
tests/unit/test_crawler.py::test_ssrf_guard_blocks_metadata PASSED
tests/unit/test_crawler.py::test_domain_allowlist PASSED
tests/unit/test_retrieval.py::test_bm25_retrieval PASSED
tests/unit/test_retrieval.py::test_rrf_fusion PASSED
tests/unit/test_retrieval.py::test_tfidf_retriever PASSED
tests/unit/test_retrieval.py::test_faiss_vector_store PASSED
tests/unit/test_intelligence.py::test_query_understanding_abbreviations PASSED
tests/unit/test_intelligence.py::test_query_understanding_intent PASSED
tests/unit/test_intelligence.py::test_query_understanding_departments PASSED
tests/unit/test_intelligence.py::test_temporal_parser_academic_year PASSED
tests/unit/test_intelligence.py::test_temporal_parser_validity PASSED
tests/unit/test_intelligence.py::test_stats_processor_placement PASSED
tests/unit/test_intelligence.py::test_stats_processor_fees PASSED
tests/unit/test_intelligence.py::test_evidence_validator PASSED
tests/integration/test_pipeline.py::test_end_to_end_search_pipeline PASSED
tests/integration/test_pipeline.py::test_unanswerable_query_handling PASSED
tests/integration/test_pipeline.py::test_multipart_query_pipeline PASSED

============================= 19 passed in 10.58s =============================
```

---

## 4. Running the 12-Category Benchmark Evaluation

The evaluation harness verifies factual correctness, citation accuracy, and response latency across all 12 institutional test categories:

```powershell
cd "M:\Third Year\MDMPROJECT\backend"
.\.venv\Scripts\python.exe -m app.evaluation.evaluate
```

### Verified Benchmark Output
```
================================================================================
 VEDANTA BENCHMARK EVALUATION SUMMARY
================================================================================
 Total Benchmark Questions:  12
 Passed Verification:        12 / 12 (100.0%)
 Average Response Latency:   8631.6 ms
 p50 Latency:                8201.9 ms
 p95 Latency:                13381.7 ms
================================================================================
```

---

## 5. Frontend Build Verification

The frontend can be built and validated using Next.js production compiler:

```powershell
cd "M:\Third Year\MDMPROJECT\frontend"
npm run build
```

### Build Output
```
Route (app)                              Size     First Load JS
┌ ○ /                                    5.42 kB        102 kB
├ ○ /analytics                           4.88 kB         98 kB
├ ○ /crawler                             5.12 kB        101 kB
├ ○ /documents                           4.61 kB        101 kB
├ ○ /health                              3.94 kB        100 kB
├ ○ /search                              6.21 kB        103 kB
└ ○ /settings                            3.89 kB         99 kB
+ First Load JS shared by all            96.8 kB
✓ Generating static pages (11/11)
```
All routes compile with zero TypeScript errors or lint warnings.
