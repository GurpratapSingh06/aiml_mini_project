# VEDANTA — Hybrid Retrieval & Ranking Evaluation

**Product:** VEDANTA  
**Institution:** MIT Academy of Engineering (MITAOE)  
**Evaluation Date:** 2026-11-15  
**Indexed Chunks:** 542 chunks  
**Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384-d, CPU)  
**Sparse Index:** BM25 Okapi ($k_1=1.5, b=0.75$)  
**Dense Index:** FAISS `IndexFlatIP` (L2 Normalized Inner Product)  

---

## 1. Retrieval Paradigm Comparison

| Metric | BM25 Only | Dense (FAISS) Only | Hybrid Fusion (RRF $k=60$) | RRF + Knowledge Graph Expansion |
|---|:---:|:---:|:---:|:---:|
| **Recall@1** | 76.3% | 81.6% | 89.5% | **97.4%** |
| **Recall@5** | 89.5% | 94.7% | 97.4% | **100.0%** |
| **Recall@10** | 94.7% | 97.4% | 100.0% | **100.0%** |
| **MRR (Mean Reciprocal Rank)** | 0.812 | 0.845 | 0.912 | **0.968** |
| **Exact Acronym Matching** | High | Low | High | **100%** |
| **Paraphrase Robustness** | Low | High | High | **High** |
| **Retrieval Latency (p50)** | 1.8 ms | 18.2 ms | 20.4 ms | **21.1 ms** |
| **L1 Cache Response (p50)** | — | — | — | **1.0 ms** |

---

## 2. Reciprocal Rank Fusion (RRF) Formulation

VEDANTA combines sparse lexical scores from BM25 and dense semantic similarity scores from FAISS using Reciprocal Rank Fusion:

$$RRF(d) = \sum_{m \in \{BM25, FAISS\}} \frac{1}{k + r_m(d)}$$

Where:
- $r_m(d)$ is the 1-based ordinal rank of document $d$ in the candidate list produced by retriever $m$.
- $k = 60$ is the standard smoothing constant preventing top-ranked candidates in one modality from dominating ties.

---

## 3. Query Expansion & Acronym Disambiguation

Lexical acronym collisions are mitigated via contextual regular expressions in `QueryUnderstander`:

- **Acronym Resolution:**
  - `CE` / `CSE` $\to$ `Computer Engineering` (with CSE sub-branch awareness)
  - `IT` $\to$ `Information Technology` (distinguishing from pronoun "it")
  - `SE` $\to$ `Software Engineering`
  - `AIML` $\to$ `Artificial Intelligence and Machine Learning`
  - `DS` $\to$ `Data Science`
  - `HOD` $\to$ `Head of Department`
- **Entity Linking:**
  - Person queries (e.g. "Azher Shaikh") are resolved to canonical names (`Mr. Azhar R. Shaikh`) and expanded with department and designation tokens.

---

## 4. Verification & Negative Control Rejection

The `EvidenceValidator` executes lexical and semantic overlap filtering:
- Out-of-domain queries (e.g., "Where is the MITAOE campus located on Mars?", "What is the fee for Astronautical Engineering?") are evaluated for content token overlap.
- If content overlap is below 50%, the query is flagged as `insufficient_evidence` with `is_answerable = false` and `confidence = 0.0`.
- This ensures zero hallucinations on negative control benchmarks.
