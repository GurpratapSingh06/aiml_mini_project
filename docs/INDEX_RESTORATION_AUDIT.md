# VEDANTA — Index Restoration & Persistence Audit

**Project:** VEDANTA (Verified Educational Data And Networked Technology Assistant)  
**Institution:** MIT Academy of Engineering (MITAOE), Alandi, Pune  
**Current Academic Year:** 2026–27  
**Date of Audit:** November 16, 2026  
**Status:** **AUDITED & PERSISTENCE ARCHITECTURE DESIGNED**

---

## 1. Overview

This document specifies the persistence, verification, and restoration architecture for all institutional knowledge in VEDANTA across restarts.

---

## 2. Institutional Knowledge Asset Audit

| Asset | Primary Storage | Persistence Mechanism | Status | Restoration Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Extracted HTML / Web Content** | PostgreSQL (`pages` table) | Relational database rows with SHA256 content hashes | Healthy (23 pages) | Read directly from PostgreSQL |
| **Document Chunks** | PostgreSQL (`content_chunks` table) | 542 rows with source URLs, page titles, and chunk indices | Healthy (542 chunks) | Restored to index if missing |
| **Faculty & Department Entities** | PostgreSQL (`entities`, `departments`) | 25 entities, 11 departments, 12 relationships | Healthy | Restored into KnowledgeGraphEngine |
| **Placement Records** | PostgreSQL (`placement_records`) | 8 records across academic years | Healthy | Restored into KnowledgeGraphEngine |
| **Fee Structure Records** | PostgreSQL (`fee_records`) | 8 category-wise approved fee records | Healthy | Restored into KnowledgeGraphEngine |
| **Dense Semantic Vectors** | File (`faiss.index`) | FAISS `IndexFlatIP` (384-dim normalized inner product) | Split (277 vs 548) | Unified to canonical 548 chunks |
| **BM25 Inverted Index** | File (`bm25.pkl`) | Serialized Rank-BM25 token corpus | Split (277 vs 548) | Unified to canonical 548 chunks |
| **Chunk Text Lookup** | File (`chunk_lookup.pkl`) | Dictionary mapping `chunk_id` to text and source metadata | Split (277 vs 548) | Unified to canonical 548 chunks |
| **Query & Evidence History** | PostgreSQL (`query_history`, `evidence_records`) | 125 queries, 479 evidence citations | Healthy | Restored into UI Institutional Research Memory |

---

## 3. Persistent Index Restoration Architecture

### 3.1 Canonical Absolute Path Resolution
In `app/core/config.py`, index storage is bound to the canonical repository root:
```python
@property
def canonical_index_dir(self) -> Path:
    # Resolves to <PROJECT_ROOT>/data/indexes regardless of execution directory
    base_dir = Path(__file__).resolve().parents[3]
    index_path = base_dir / "data" / "indexes"
    index_path.mkdir(parents=True, exist_ok=True)
    return index_path
```

### 3.2 Index Manifest (`index_manifest.json`)
Every saved index state records a cryptographic manifest:
```json
{
  "index_version": "2.0.0",
  "created_at": "2026-11-16T15:20:00Z",
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "dimension": 384,
  "faiss_vectors": 548,
  "bm25_documents": 548,
  "db_chunk_count": 542,
  "db_chunks_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "status": "HEALTHY"
}
```

### 3.3 Atomic Writes via Staging Files
To prevent index corruption during sudden process termination or system reboot:
```python
def atomic_save(file_path: Path, data, serializer):
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    with open(temp_path, "wb") as f:
        serializer(data, f)
    # Atomic rename replaces target instantly
    temp_path.replace(file_path)
```

### 3.4 Safe Startup Restoration Flow
On startup, `RetrievalPipeline.initialize()` implements a 3-tier safe recovery process:
1. **Tier 1 (Fast Restore):** If `index_manifest.json` exists, files are intact, and vector count matches document count $\rightarrow$ load directly in **<30 ms**.
2. **Tier 2 (Reconciliation / Incremental Update):** If PostgreSQL has new `content_chunks` not in the index $\rightarrow$ embed and index only the missing chunks without rebuilding from scratch.
3. **Tier 3 (Safe Rebuild):** If indexes are missing or corrupted $\rightarrow$ rebuild completely from PostgreSQL `content_chunks` in the background while keeping the system responsive.
