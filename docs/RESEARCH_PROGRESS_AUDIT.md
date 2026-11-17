# VEDANTA — Real-Time Research Progress Stream Audit & Event Protocol

**Project:** VEDANTA (Verified Educational Data And Networked Technology Assistant)  
**Institution:** MIT Academy of Engineering (MITAOE), Alandi, Pune  
**Official Portal:** `https://mitaoe.ac.in/`  
**Current Academic Year:** 2026–27  
**Endpoints:** `POST /api/v1/search/stream` & `GET /api/v1/search/stream?q=...`  
**Status:** IMPLEMENTED, TESTED & PRODUCTION VERIFIED

---

## 1. Executive Summary

Standard generative chat interfaces often display opaque spinners or simulated loading animations that conceal actual system progress. When operations take multiple seconds (such as dynamic website discovery across 13 departments or OCR extraction of large institutional circulars), users require transparent, deterministic visibility into what the engine is executing.

VEDANTA provides a **True Server-Sent Events (SSE) Research Pipeline**. Progress events represent real asynchronous milestones in the FastAPI pipeline. When a stage is not needed (such as web discovery during a cache hit), the backend explicitly emits a `status: "skipped"` event with technical rationale, which the frontend renders using a dedicated `SKIPPED` badge rather than pretending to execute unnecessary work.

---

## 2. The 10 Research Milestones Specification

Each research invocation transitions through up to 10 sequential stages:

```
┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
│ Step 1  │ ───► │ Step 2  │ ───► │ Step 3  │ ───► │ Step 4  │ ───► │ Step 5  │
│ Analyze │      │ Search  │      │ Discover│      │ Fetch   │      │ Extract │
│ Query   │      │ Memory  │      │ Sources │      │ Pages   │      │ Data    │
└─────────┘      └─────────┘      └─────────┘      └─────────┘      └─────────┘
                                       │                │                │
                                 (Can be Skipped) (Can be Skipped) (Can be Skipped)
                                       │                │                │
┌─────────┐      ┌─────────┐           ▼                ▼                ▼
│ Step 10 │ ◄─── │ Step 9  │ ◄─── ┌─────────┐ ◄─── ┌─────────┐ ◄─── ┌─────────┐
│ Complete│      │ Record  │      │ Step 8  │      │ Step 7  │      │ Step 6  │
│ & Emit  │      │ History │      │ Compose │      │ Verify  │      │ Analyze │
└─────────┘      └─────────┘      │ Answer  │      │ Facts   │      │ Evidence│
                      │           └─────────┘      └─────────┘      └─────────┘
                (Can be Skipped)
```

| Step # | Stage Identifier | Purpose | Typical Active Duration | Skipped Condition |
| :---: | :--- | :--- | :---: | :--- |
| **1** | `analyzing_question` | Intent extraction, entity isolation, temporal grounding | 2 – 5 ms | Never skipped |
| **2** | `searching_local_knowledge`| L1 cache, Redis, Knowledge Graph, BM25 + FAISS lookup | 5 – 25 ms | Never skipped |
| **3** | `discovering_sources` | Multi-department catalog scan, URL candidate resolution | 250 – 1,200 ms | Skipped if verified evidence is already present in memory |
| **4** | `fetching_pages` | Asynchronous HTTP fetch of authoritative `.php` / HTML / PDF | 400 – 2,500 ms | Skipped if no new sources needed |
| **5** | `extracting_information` | HTML parsing, metadata harvesting, OCR table extraction | 100 – 600 ms | Skipped if no new sources fetched |
| **6** | `analyzing_evidence` | Semantic similarity, BM25 rank, lexical grounding | 10 – 40 ms | Executed on retrieved or cached evidence |
| **7** | `verifying_information` | Strict identity verification, temporal check (2026–27) | 5 – 15 ms | Executed on all candidate chunks |
| **8** | `generating_answer` | Structured markdown composition, citation formatting | 5 – 20 ms | Executed for all answerable queries |
| **9** | `saving_to_history` | PostgreSQL persistence of query and evidence lineage | 10 – 30 ms | Skipped on repeat cached hits (prevents duplicate bloat) |
| **10**| `completed` | Finalization event emitting complete response payload | 1 ms | Terminal event |

---

## 3. SSE Protocol Payload Schema

Every SSE message conforms to the following JSON structure emitted on line `data: <json>\n\n`:

```typescript
interface ResearchProgressEvent {
  request_id: string;             // UUID identifying the research session
  stage: string;                  // e.g. "discovering_sources", "completed"
  message: string;                // Human-readable operational description
  timestamp: string;              // ISO 8601 UTC timestamp
  elapsed_ms: number;             // Wall-clock latency since request receipt
  status: "running" | "completed" | "skipped" | "failed";
  details?: {
    intent?: string;
    sources_discovered?: number;
    pages_fetched?: number;
    verification_status?: string;
    confidence?: number;
  };
  answer?: string;                // Present on terminal "completed" event
  citations?: Array<Citation>;    // Present on terminal "completed" event
}
```

### Example 1: Live Discovery Stream (Cold Query)
```json
data: {"request_id": "83494216...", "stage": "analyzing_question", "status": "completed", "elapsed_ms": 4, "message": "Analyzing question intent and target entities..."}
data: {"request_id": "83494216...", "stage": "searching_local_knowledge", "status": "completed", "elapsed_ms": 28, "message": "Searching local memory..."}
data: {"request_id": "83494216...", "stage": "discovering_sources", "status": "running", "elapsed_ms": 35, "message": "Discovering official MITAOE department pages..."}
data: {"request_id": "83494216...", "stage": "fetching_pages", "status": "completed", "elapsed_ms": 1840, "message": "Fetched 1 authoritative faculty profile page."}
data: {"request_id": "83494216...", "stage": "extracting_information", "status": "completed", "elapsed_ms": 2100, "message": "Extracted credentials, designation and research interests."}
data: {"request_id": "83494216...", "stage": "verifying_information", "status": "completed", "elapsed_ms": 2140, "message": "Evidence verified against institutional records."}
data: {"request_id": "83494216...", "stage": "completed", "status": "completed", "elapsed_ms": 2210, "message": "Research completed successfully."}
```

### Example 2: In-Memory Cached Stream (Warm Query)
```json
data: {"request_id": "00f41f55...", "stage": "analyzing_question", "status": "completed", "elapsed_ms": 1, "message": "Question understood. Reusing verified institutional evidence."}
data: {"request_id": "00f41f55...", "stage": "searching_local_knowledge", "status": "completed", "elapsed_ms": 3, "message": "Verified institutional evidence found in local memory."}
data: {"request_id": "00f41f55...", "stage": "discovering_sources", "status": "skipped", "elapsed_ms": 3, "message": "Web discovery skipped: verified evidence already cached."}
data: {"request_id": "00f41f55...", "stage": "fetching_pages", "status": "skipped", "elapsed_ms": 3, "message": "Page fetch skipped: using cached sources."}
data: {"request_id": "00f41f55...", "stage": "extracting_information", "status": "skipped", "elapsed_ms": 3, "message": "Information extraction skipped."}
data: {"request_id": "00f41f55...", "stage": "analyzing_evidence", "status": "completed", "elapsed_ms": 4, "message": "Evidence verified against institutional records."}
data: {"request_id": "00f41f55...", "stage": "verifying_information", "status": "completed", "elapsed_ms": 5, "message": "Verified cached evidence against institutional records."}
data: {"request_id": "00f41f55...", "stage": "generating_answer", "status": "completed", "elapsed_ms": 6, "message": "Preparing answer from verified records."}
data: {"request_id": "00f41f55...", "stage": "saving_to_history", "status": "skipped", "elapsed_ms": 6, "message": "History recording skipped for cached hit."}
data: {"request_id": "00f41f55...", "stage": "completed", "status": "completed", "elapsed_ms": 7, "message": "Research completed (served from institutional memory)."}
```

---

## 4. Frontend Rendering & Badge System

In `frontend/src/app/search/page.tsx`, the SSE stream updates a structured React state:
- **`COMPLETED` (Emerald Badge / Green Checkmark):** Stage executed and succeeded.
- **`SKIPPED` (Slate Badge / Dimmed Label):** Stage bypassed due to memory/cache availability.
- **`RUNNING` (Blue Pulsing Indicator):** Stage currently in active execution.
- **`FAILED` (Red Badge):** Stage encountered an unrecoverable network or validation error.

This provides complete, tamper-proof user confidence that VEDANTA executes authentic research.
