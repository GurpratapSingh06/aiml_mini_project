# VEDANTA — Hybrid Information Retrieval Engine

**Product:** VEDANTA Hybrid Retrieval Core  
**Modules:**
- `backend/app/retrieval/bm25/` (BM25 Okapi)
- `backend/app/retrieval/embeddings/` (Sentence Transformers)
- `backend/app/retrieval/vector_store/` (FAISS CPU)
- `backend/app/retrieval/fusion/` (Reciprocal Rank Fusion)
- `backend/app/retrieval/reranking/` (Cross-Encoder)
- `backend/app/retrieval/tfidf/` (TF-IDF Baseline)

---

## 1. Retrieval Rationale: Lexical + Dense Semantic Synergy

Institutional queries present dual challenges:
1. **Exact Precision Queries:** Questions with proper nouns, faculty names (e.g. *Dr. Sandip A. Gade*), designations (*HOD*), department codes (*CE*, *AIML*), and course codes fail when relying solely on dense vector cosine similarity.
2. **Semantic / Paraphrased Queries:** Questions such as *"who is the person leading the comp eng branch"* fail with strict keyword search.

VEDANTA resolves this by fusing both paradigms using Reciprocal Rank Fusion without fragile score normalization.

---

## 2. Mathematical Formulations

### 2.1 BM25 Okapi
For query terms $Q = \{q_1, q_2, \dots, q_n\}$ and document $D$:
$$\text{BM25}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

- Default Parameters: $k_1 = 1.5$, $b = 0.75$.
- Tokenization: Lowercase, punctuation stripping with preservation of compound hyphenations.

### 2.2 Semantic Vector Embeddings
- Pretrained Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimensions: 384
- Normalization: $L_2$ vector normalization $\hat{v} = \frac{v}{\|v\|_2}$
- Similarity Measure: Inner Product (FAISS `IndexFlatIP`), equivalent to Cosine Similarity for normalized vectors:
$$\text{CosineSim}(u, v) = \langle \hat{u}, \hat{v} \rangle$$

### 2.3 Reciprocal Rank Fusion (RRF)
Combines distinct ranked lists $R_1, R_2, \dots, R_m$:
$$\text{RRF\_Score}(d \in D) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

- Constant $k = 60$ prevents top-ranked outliers from dominating.
- Automatically handles scale mismatch between BM25 scores (unbounded positive) and cosine similarity ($[-1, 1]$).
