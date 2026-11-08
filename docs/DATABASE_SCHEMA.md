# VEDANTA — Database Schema Architecture

**Product:** VEDANTA  
**Database Engine:** PostgreSQL 16 (Production) / SQLite3 (Zero-config local fallback via aiosqlite)  
**ORM:** SQLAlchemy 2.0 (AsyncIO)  
**Migration Tool:** Alembic

---

## 1. Schema Design Principles

The database follows a normalized relational structure:
- **No Monolithic JSON Blobs:** Critical metadata, relations, dates, and package metrics reside in dedicated indexed columns.
- **Auditable Provenance:** Every fact, package stat, and entity link maintains a foreign key to the originating `content_chunks` or `documents` table and a `source_url`.
- **Temporal Versioning:** Academic years (`AY 2024-25`) are explicit columns on records, preventing temporal ambiguity.
- **Content Deduplication:** Content hashes (`SHA-256`) and document file hashes ensure duplicate documents and unchanged web pages are never reprocessed.

---

## 2. Table Catalog

| Table | Primary Key | Description | Key Foreign Keys |
|-------|-------------|-------------|------------------|
| `institutions` | UUID | Institutional profile and root settings | Self-contained |
| `domains` | UUID | Allowed domain list for polite crawler scoping | `institution_id` |
| `crawl_jobs` | UUID | Tracks crawl sessions, page counters, and duration | `institution_id` |
| `pages` | UUID | Crawled web pages, canonical URLs, HTTP status, and hashes | `institution_id`, `crawl_job_id` |
| `documents` | UUID | Downloaded PDF files, OCR engine, scan classification | `institution_id` |
| `document_pages` | UUID | Per-page text extraction, OCR confidence, and image paths | `document_id` |
| `document_tables` | UUID | Structured extracted table rows, columns, and types | `document_id` |
| `content_chunks` | UUID | 512-token retrieval chunks, token counts, and FAISS vector IDs | `page_id`, `document_id`, `model_registry_id` |
| `model_registry` | UUID | Active embedding and reranker model versions | Self-contained |
| `entities` | UUID | Institutional persons, departments, councils, and schools | `institution_id` |
| `entity_aliases` | UUID | Alternate names, titles, and acronyms (e.g. HOD, CE) | `entity_id` |
| `entity_relationships`| UUID | Directional relationships (heads, teaches_in, member_of) | `source_entity_id`, `target_entity_id` |
| `departments` | UUID | Formal academic departments and abbreviations | `institution_id` |
| `academic_years` | UUID | Structured cycles (e.g. 2024-25, start_year, is_current) | `institution_id` |
| `institutional_facts` | UUID | Triple assertions (subject, predicate, object) with confidence | `institution_id`, `source_chunk_id` |
| `placement_records` | UUID | Packages (highest, average, median LPA), placed student counts | `institution_id`, `department_id`, `source_doc_id` |
| `fee_records` | UUID | Approved tuition, development, and category fees (FRA) | `institution_id`, `department_id`, `source_doc_id` |
| `query_history` | UUID | Search audit logs, user queries, answers, and latencies | `institution_id` |
| `evidence_records` | UUID | M:N links from queries to cited chunk passages | `query_history_id`, `chunk_id`, `doc_id` |
| `processing_jobs` | UUID | Background RQ job status, retries, and errors | Self-contained |
