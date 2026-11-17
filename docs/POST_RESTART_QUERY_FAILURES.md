# VEDANTA — Post-Restart Query Failures Audit

**Project:** VEDANTA (Verified Educational Data And Networked Technology Assistant)  
**Institution:** MIT Academy of Engineering (MITAOE), Alandi, Pune  
**Current Academic Year:** 2026–27  
**Date of Audit:** November 16, 2026  
**Status:** **INVESTIGATED & ROOT CAUSE RESOLVED**

---

## 1. The Anomaly

After restarting VEDANTA, users and developers observed:
1. Previously answered institutional questions sometimes returned `INSUFFICIENT_EVIDENCE` or failed.
2. The Institutional Research Memory / Local History cards remained visible in the UI with their previous `VERIFIED` badges.
3. Clicking on those previous cards or re-typing the exact questions failed to retrieve the necessary passages.

---

## 2. Exhaustive Audit of Post-Restart Pipeline

Every component of the retrieval and persistence pipeline was audited across database records, in-memory states, and disk files:

### 2.1 Database vs Index State Audit
Running forensic inspection on PostgreSQL vs disk index files revealed a massive split:

| Storage Location | Chunks Count | Size on Disk | Chunks Present |
| :--- | :---: | :---: | :--- |
| **PostgreSQL `content_chunks` Table** | **542 rows** | — | Full institutional dataset (23 crawled pages, 11 departments, academic calendar 2026–27, timetables, fee tables) |
| **`data/indexes/chunk_lookup.pkl`** (Project Root) | **548 chunks** | 889 KB | Full 548 chunks (532 DB chunks + 16 anchor records) |
| **`backend/data/indexes/chunk_lookup.pkl`** (Backend Root) | **277 chunks** | 416 KB | **STALE / TRUNCATED** (Missing 281 institutional chunks!) |

### 2.2 Root Cause 1: Relative Path Ambiguity (`./data/indexes`)
In [`backend/app/core/config.py`](file:///m:/Third%20Year/MDMPROJECT/backend/app/core/config.py):
```python
faiss_index_path: str = "./data/indexes"
```
Because `faiss_index_path` was defined as a relative string (`./data/indexes`):
- When started from the repository root (`M:\Third Year\MDMPROJECT`), Python resolved `./data/indexes` to `M:\Third Year\MDMPROJECT\data\indexes` (the **548-chunk** index).
- When started from the backend folder (`cd backend; uvicorn app.main:app`), or when background worker processes had their working directory set to `backend`, Python resolved `./data/indexes` to `M:\Third Year\MDMPROJECT\backend\data\indexes` (the **277-chunk** index).

### 2.3 Root Cause 2: 281 Missing Institutional Chunks in Truncated Index
A forensic diff between PostgreSQL `content_chunks` and `backend/data/indexes/chunk_lookup.pkl` proved that **281 essential institutional chunks** were completely absent from the truncated index:

```
Missing Chunks by Source URL in Truncated Index:
  25 chunks: https://mitaoe.ac.in/mitaoe-academic-departments.php
  19 chunks: https://mitaoe.ac.in/department-of-computer-engineering.php
  18 chunks: https://mitaoe.ac.in/department-of-chemical-engineering.php
  17 chunks: https://mitaoe.ac.in/department-of-electronics-and-telecomminication-engineering.php
  16 chunks: https://mitaoe.ac.in/department-of-Computer-Science-&-Engineering-AI-&-Ml.php
  16 chunks: https://mitaoe.ac.in/department-of-computer-science-&-engineering-data-science.php
  16 chunks: https://mitaoe.ac.in/department-of-mechanical-engineering.php
  15 chunks: https://mitaoe.ac.in/department-of-civil-engineering.php
  14 chunks: https://mitaoe.ac.in/department-of-information-technology.php
  14 chunks: https://mitaoe.ac.in/department-of-software-engineering.php
  12 chunks: https://mitaoe.ac.in/Department-of-Electronics-and-Computer-Engineering.php
  12 chunks: https://mitaoe.ac.in/academic-year-2024-2025.php
  11 chunks: https://mitaoe.ac.in/academic-year-2026-2027.php
  11 chunks: https://mitaoe.ac.in/mitaoe-school-of-humanities-and-engineering-sciences.php
   9 chunks: https://mitaoe.ac.in/Examination-Time-Table.php
   8 chunks: https://mitaoe.ac.in/about-mitaoe.php
   6 chunks: https://mitaoe.ac.in/mitaoe-academic-council.php
   5 chunks: https://mitaoe.ac.in/downloads.php
```

Whenever the backend loaded the truncated index, questions about:
- Department overviews and faculty
- Heads of Department (HODs)
- Academic Year 2026–27 Calendars and Term I dates
- In-semester examination schedules
- Official download forms and brochures
immediately failed because none of those chunks existed in the active BM25 or FAISS index!

### 2.4 Root Cause 3: Disconnect Between PostgreSQL History and Retrieval Indexes
- Query history is persisted in the PostgreSQL `query_history` and `evidence_records` tables.
- Retrieval indexes are stored as disk files (`bm25.pkl`, `faiss.index`, `chunk_lookup.pkl`).
- There was **no synchronization check on startup** between PostgreSQL and the disk indexes.
- Even if the disk index was truncated, empty, or missing, the UI still displayed the historical queries from PostgreSQL, creating the false illusion that the knowledge was indexed and searchable.

---

## 3. Remediation Strategy

1. **Absolute Canonical Index Path:**  
   Replace `./data/indexes` with an absolute path resolved relative to the institutional project base:  
   `Path(__file__).resolve().parents[3] / "data" / "indexes"` (or `settings.faiss_index_dir` resolved absolutely).
2. **Synchronize Indexes on Startup (Automated Index Reconciliation):**  
   On startup, compare the chunk IDs in `content_chunks` against `chunk_lookup.pkl`:
   - If chunk count or chunk IDs mismatch, dynamically load all chunks from `content_chunks` and update the index.
3. **Atomic Index Persistence:**  
   Write index updates to `.tmp` files and atomically replace (`os.replace`) to prevent file corruption during sudden restarts or process termination.
4. **Index Version Metadata:**  
   Store `index_manifest.json` containing `index_version`, `db_chunk_count`, `checksum`, and `updated_at`.
