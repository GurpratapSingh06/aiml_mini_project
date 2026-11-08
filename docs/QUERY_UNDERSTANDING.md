# VEDANTA Query Understanding Engine

## 1. Overview and Purpose

Students and faculty interact with institutional knowledge using shorthand, acronyms, conversational language, and composite multi-part questions (e.g., *"Who is the HOD of CE and what was their highest package in 2024?"*). 

The VEDANTA Query Understanding Engine (`backend/app/intelligence/query_understanding/query_understander.py`) acts as the front door of the retrieval and intelligence pipeline. It transforms raw, ambiguous user input into a strongly-typed `QueryContext` object enriched with:
- Intent classification
- Abbreviation expansion with lexical preservation
- Institutional department resolution
- Named entity recognition (faculty, leadership, councils)
- Temporal reference identification
- Sub-query decomposition for multi-part questions

---

## 2. Query Understanding Pipeline

```
Raw User Input (e.g. "HOD of CE at MITAOE AY 2024-25?")
       │
       ▼
[Punctuation & Whitespace Normalization]
       │
       ▼
[Abbreviation Expansion (Dual-Token Preservation)]
  "CE" -> "ce Computer Engineering"
  "AY 2024-25" -> "Academic Year 2024-25"
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[Intent Classification]                 [Entity & Department Match]
  - statistical                           - Dept: Computer Engineering
  - temporal                              - Role: Head of Department
  - entity_lookup                         - Institution: MITAOE
  - comparison                            - Councils/Cells: Academic Council
  - factual (fallback)
       │                                         │
       └────────────────────┬────────────────────┘
                            │
                            ▼
              [Temporal Reference Parsing]
                - Years: ['2024-25', '2024']
                - Temporal markers: ['current', 'latest']
                            │
                            ▼
              [Sub-Query Decomposition]
                - Sub-query 1: HOD entity lookup
                - Sub-query 2: Statistical placement lookup
                            │
                            ▼
             Output: Strongly-Typed QueryContext
```

---

## 3. Abbreviation Dictionary & Expansion

Academic institutions rely heavily on specialized acronyms. VEDANTA maintains a curated institutional abbreviation dictionary:

| Abbreviation | Expanded Form | Category |
|---|---|---|
| `CE` / `CSE` | Computer Engineering / Computer Science and Engineering | Academic Department |
| `AIML` / `AI&ML` | Artificial Intelligence and Machine Learning | Academic Department |
| `ENTC` / `E&TC` | Electronics and Telecommunication Engineering | Academic Department |
| `MECH` / `ME` | Mechanical Engineering | Academic Department |
| `CIVIL` | Civil Engineering | Academic Department |
| `IT` | Information Technology | Academic Department |
| `HOD` / `HoD` | Head of Department | Administrative Role |
| `MIT` / `MITAOE` | MIT Academy of Engineering | Institution |
| `AY` / `A.Y.` | Academic Year | Temporal Dimension |
| `LPA` | Lakhs Per Annum | Financial / Salary Metric |
| `NAAC` / `NBA` | Accreditation Bodies | Regulatory & Governance |
| `UG` / `PG` / `PhD` | Undergraduate / Postgraduate / Doctorate | Academic Programs |

### Dual-Token Preservation Rule
In standard NLP, replacing `"CE"` with `"Computer Engineering"` can degrade lexical BM25 retrieval against documents that exclusively use the acronym `"CE"`. 

VEDANTA employs a **dual-token expansion strategy**:
$$\text{Query: } \text{"HOD of CE"} \implies \text{Expanded: } \text{"HOD Head of Department of ce Computer Engineering"}$$

Furthermore, to prevent catastrophic false positives where common lowercase English words or pronouns (`"me"`, `"it"`, `"be"`) are incorrectly expanded into `"Mechanical Engineering"` or `"Information Technology"`, the expansion enforces strict uppercase word-boundary checks (`\b[A-Z]{2,}\b`).

---

## 4. Intent Classification Engine

The engine identifies 5 discrete intent categories using prioritized multi-token phrase matching:

1. **`statistical`:** Queries requesting numbers, placements, fees, percentages, averages, or salaries (keywords: *how many, percentage, highest package, average ctc, fee structure, placed*).
2. **`temporal`:** Queries regarding schedules, dates, academic calendars, or historical comparisons (keywords: *dates, calendar, term commencement, schedule, when does, academic year*).
3. **`entity_lookup`:** Queries seeking specific persons, faculty designations, committees, or council compositions (keywords: *who is, head of, hod, director, principal, faculty, professor, academic council*).
4. **`comparison`:** Queries requesting comparisons between departments, years, or programs (keywords: *compare, versus, vs, difference between, higher than*).
5. **`factual`:** General informational questions regarding campus facilities, policies, hostel rules, or accreditations.

---

## 5. Multi-Part Query Decomposition

Institutional users often combine multiple questions in a single sentence:
> *"Who is the current HOD of Computer Engineering and what are its latest placement packages?"*

The Query Understanding Engine splits composite queries using conjunctions (`" and "`, `" also "`, `";"`) into discrete sub-queries. The retrieval pipeline executes independent searches for each sub-query and merges the retrieved evidence, ensuring that neither part of the user's intent is dropped.

---

## 6. QueryContext Data Contract

The output is represented by the following Python dataclass:

```python
@dataclass
class QueryContext:
    original_query: str
    expanded_query: str
    cleaned_query: str
    intent: str
    departments: List[str]
    entities: List[ExtractedEntity]
    temporal_refs: List[str]
    sub_queries: List[str]
    is_statistical: bool = False
    is_temporal: bool = False
    target_metric: Optional[str] = None
```
This context directly guides hybrid retrieval filtering, evidence scoring, and answer validation.
