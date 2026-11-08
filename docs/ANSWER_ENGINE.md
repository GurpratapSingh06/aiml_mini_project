# VEDANTA Answer Engine & Evidence Validation

## 1. Overview and Core Philosophy

The VEDANTA Answer Engine (`backend/app/intelligence/answer_engine/`) is the synthesis tier that converts raw retrieved passages into verified, structured, and cited answers for students and faculty.

Unlike conventional generative AI chatbots that generate unchecked answers from opaque weights, VEDANTA operates on the principle of **Evidence-Bound Synthesis**:
- Every factual assertion must be grounded in an identifiable passage.
- If evidence is weak, ambiguous, or absent, the system must explicitly state what is unknown rather than fabricate an answer.
- If multiple institutional documents present contradictory facts (e.g., across revisions or academic years), the system must present the conflict transparently.

---

## 2. Answer Generation Pipeline

```
Retrieved Passages from Hybrid Fusion (BM25 + FAISS)
                         │
                         ▼
             [Evidence Validator]
  - Filter by minimum score (_MIN_EVIDENCE_SCORE = 0.005)
  - Lexical grounding check (query non-stopwords in candidates)
  - Cross-source consistency check (conflict detection)
  - Compute overall confidence metric (0.0 - 1.0)
                         │
                         ▼
        Assign Verification Classification:
  ┌──────────────────────────────────────────────────┐
  │ • VERIFIED             • UNCERTAIN               │
  │ • PARTIALLY_VERIFIED   • INSUFFICIENT_EVIDENCE   │
  │ • CONFLICTING_SOURCES                            │
  └──────────────────────┬───────────────────────────┘
                         │
                         ▼
             [Answer Composer]
  - Direct Synthesis (concise, factual summary)
  - Structured Table Generation (for fees / placements)
  - Source Citation Badges (URL + PDF Page Number)
  - Limitations & Provenance Disclosure
                         │
                         ▼
          Final Answer Payload to Client
```

---

## 3. Evidence Validation Statuses

The Evidence Validator classifies every query response into one of five statuses:

| Status Badge | Criteria | System Behavior |
|---|---|---|
| `VERIFIED` | Top evidence score $\ge 0.015$, lexical overlap confirmed, no source contradictions. | Direct answer with full confidence and clickable citations. |
| `PARTIALLY_VERIFIED` | Score between $0.005$ and $0.015$, or answers single sub-part of multi-part query. | Answers supported portions; highlights unverified components. |
| `CONFLICTING_SOURCES` | Multiple passages assert conflicting facts (e.g. different personnel or fee revisions). | Presents conflicting claims chronologically with source links. |
| `UNCERTAIN` | Score near minimum threshold ($0.005$), weak lexical grounding. | Displays cautionary disclaimer advising manual verification. |
| `INSUFFICIENT_EVIDENCE` | No passages exceed threshold or query tokens completely absent from index. | Declines to answer; offers guidance on where to inquire officially. |

---

## 4. Lexical Grounding Defense

Dense semantic vector models can sometimes assign moderate cosine similarity scores to institutional boilerplate (e.g. copyright notices or generic disclaimers) even when the user asks about an unanswerable or nonexistent topic, such as:
> *"What is the exact secret password of the MITAOE faculty Wi-Fi router?"*

To prevent the model from hallucinating an answer or returning irrelevant text with unwarranted confidence, VEDANTA executes a **Lexical Grounding Check**:

1. Extract non-stopword query tokens (e.g., `['secret', 'password', 'wifi', 'router']`).
2. Search candidate passages for token occurrences.
3. If zero or negligible keyword overlap is detected across candidate chunks, the validation engine overrides the score and immediately flags `status: insufficient_evidence`.

---

## 5. Answer Composition Structure

Answers delivered to the frontend adhere to a strict structured schema:

```json
{
  "query": "What are the latest fees for B.Tech programs?",
  "status": "verified",
  "confidence": 0.94,
  "answer": "According to the approved fee structure for AY 2024-25, the total tuition fee for OPEN category is ₹1,65,000...",
  "key_findings": [
    "OPEN category total fee: ₹1,65,000",
    "OBC/EBC category fee: ₹95,000 (after 50% tuition concession)",
    "SC/ST category fee: ₹15,000 (development fee only)"
  ],
  "tabular_data": [ ... ],
  "citations": [
    {
      "source_title": "MITAOE Approved Fee Structure AY 2024-25",
      "url": "https://mitaoe.ac.in/admissions/fees-2024-25.pdf",
      "page_number": 2,
      "academic_year": "2024-25"
    }
  ],
  "limitations": "Fees subject to Fee Regulating Authority (FRA) revisions."
}
```

The user is empowered to click any citation badge to immediately review the underlying document page.
