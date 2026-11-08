# VEDANTA Temporal Intelligence Engine

## 1. Overview and Problem Statement

Academic institutions operate on rolling cycles: academic years, terms, semesters, and regulatory update cycles. Institutional websites frequently accumulate outdated documents alongside current circulars. 

A major pitfall of standard search engines and naïve RAG chatbots is treating old notices with equal weight to current circulars. For example:
- A fee circular from **2021-22** might rank higher on keyword density than a **2024-25** fee schedule.
- A faculty page listing an former HOD might conflict with a newly published office order.

The VEDANTA Temporal Intelligence Engine (`backend/app/intelligence/temporal_engine/temporal_parser.py`) assesses the publication date, effective period, and currency of every piece of institutional information.

---

## 2. Temporal Validity Lifecycle

Every document, chunk, and fact is classified into one of five temporal states:

```
                  ┌───────────────────────────────┐
                  │           UPCOMING            │
                  │  (Commencement / Next AY)     │
                  └──────────────┬────────────────┘
                                 │ Effective Date reached
                                 ▼
                  ┌───────────────────────────────┐
                  │            CURRENT            │
                  │ (Active AY / Latest Notice)   │
                  └──────────────┬────────────────┘
                                 │ Subsequent AY published
                                 ▼
                  ┌───────────────────────────────┐
                  │          HISTORICAL           │
                  │   (Valid in prior years)      │
                  └──────────────┬────────────────┘
                                 │ Explicit cancellation
                                 ▼
                  ┌───────────────────────────────┐
                  │          SUPERSEDED           │
                  │ (Withdrawn / Cancelled Order) │
                  └───────────────────────────────┘
```

| Validity Status | Definition | Example |
|---|---|---|
| `CURRENT` | Applies to the active academic year (e.g., 2024–25). | Approved fee circular for 2024-25. |
| `HISTORICAL` | Legitimate institutional fact from a prior period. | Placement report for 2022-23. |
| `UPCOMING` | Future event, schedule, or planned term date. | Academic calendar term start for July 2025. |
| `SUPERSEDED` | Explicitly revoked, cancelled, or overwritten circular. | Revised examination timetable replacing draft schedule. |
| `UNKNOWN` | No date or temporal reference identified in source. | Generic campus map or mission statement. |

---

## 3. Academic Year Parsing & Normalization

Academic years in India follow the `YYYY-YY` or `YYYY-YYYY` pattern spanning two calendar years (e.g., *AY 2024-25* or *2024-2025*).

VEDANTA normalizes all academic year notations into a standard format:
$$\text{"AY 24-25"}, \text{"2024/2025"}, \text{"Academic Year 2024-25"} \implies \mathbf{"2024\text{-}25"}$$

```python
AY_REGEX = re.compile(
    r"\b(?:AY|A\.Y\.|Academic\s+Year)?\s*(20[12]\d)\s*[-–/]\s*([12]\d|20[12]\d)\b",
    re.IGNORECASE,
)
```

---

## 4. Date and Effective Period Extraction

The engine extracts temporal bounds using multi-pattern regexes:
- **Numerical dates:** `DD/MM/YYYY`, `DD-MM-YYYY`, `YYYY-MM-DD`.
- **Textual dates:** `15th July 2024`, `August 1, 2024`.
- **Effective date markers:** `with effect from (w.e.f.)`, `commencing on`, `dated:`.
- **Supersession markers:** `supersedes circular no.`, `cancelled`, `withdrawn`, `obsolete`.

---

## 5. Temporal Conflict Resolution & Currency Ranking

When user queries contain temporal keywords like *"current"*, *"latest"*, or *"now"*:

1. **Temporal Re-ranking:** Retrieved passages with `validity_status = CURRENT` receive an evidence score boost.
2. **Conflict Detection:** If multiple passages assert contradictory leadership or fee facts across different academic years, the answer engine flags the situation with `status: conflicting_sources`.
3. **Transparent Timeline Display:** Rather than arbitrarily guessing which fact is true, VEDANTA presents the evidence chronologically:
   - *"According to the 2024-25 circular, X is listed as HOD."*
   - *"In the prior 2022-23 record, Y was listed."*
   This eliminates hallucinations and gives users fully verifiable clarity.
