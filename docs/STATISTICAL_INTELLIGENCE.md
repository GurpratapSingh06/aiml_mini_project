# VEDANTA Statistical Intelligence Engine

## 1. Overview and Engineering Principles

Statistical claims—especially regarding student placement packages, highest CTCs, and category-wise fee structures—are highly sensitive in academic institutions. Inaccurate or fabricated figures damage institutional credibility and mislead students.

Generative LLMs frequently hallucinate numbers or perform flawed arithmetic. To eliminate this risk, VEDANTA enforces strict **Deterministic Numerical Processing**:

1. **Zero Generative Arithmetic:** No generative model is permitted to invent, interpolate, or extrapolate numerical figures.
2. **Explicit Denominators:** Averages or percentages are calculated only when the exact numerator, denominator, and sample scope are documented.
3. **Tabular and Regex Extraction:** Numbers are parsed directly from structured tables or validated regex matches.
4. **Complete Lineage:** Every metric is bound to an exact document title, table index, row number, and source URL.

---

## 2. Statistical Data Models

The engine (`backend/app/intelligence/statistical_engine/stats_processor.py`) populates two core relational data structures:

### PlacementFact Data Contract
```python
@dataclass
class PlacementFact:
    academic_year: str
    department: str
    total_students: Optional[int] = None
    students_placed: Optional[int] = None
    offers_made: Optional[int] = None
    highest_package_lpa: Optional[float] = None
    average_package_lpa: Optional[float] = None
    median_package_lpa: Optional[float] = None
    placement_percentage: Optional[float] = None
    companies_visited: Optional[int] = None
    source_url: str = ""
    source_page: Optional[int] = None
    provenance_note: str = ""
```

### FeeFact Data Contract
```python
@dataclass
class FeeFact:
    academic_year: str
    program: str
    category: str  # OPEN, OBC, SC, ST, VJNT, TFWS, EWS, NRI
    tuition_fee: Optional[float] = None
    development_fee: Optional[float] = None
    other_fees: Optional[float] = None
    total_fee: Optional[float] = None
    source_url: str = ""
    source_page: Optional[int] = None
    provenance_note: str = ""
```

---

## 3. Numerical Extraction Patterns

VEDANTA employs regex parsers calibrated for Indian academic financial conventions:

- **Salary Packages (CTC):**
  - Patterns: `highest package`, `top CTC`, `average package`, `LPA`, `lakhs per annum`.
  - Captures float values and normalizes them to LPA (e.g., `"₹24.5 LPA"` $\implies 24.5$).
- **Fee Schedules:**
  - Identifies fee components: *Tuition Fee*, *Development Fee*, *Exam Fee*, *Eligibility Fee*, *Total Fee*.
  - Maps values across quota and social reservation categories (OPEN, OBC, SC/ST, EWS, TFWS).
- **Placement Counts:**
  - Parses distinct counts for *Total Eligible Students*, *Single Offers*, *Multiple Offers*, and *Companies Visited*.

---

## 4. Deterministic Arithmetic & Validation

When computing derived metrics:

### Placement Percentage
$$\text{Placement Rate} = \left( \frac{\text{Students Placed}}{\text{Eligible Students}} \right) \times 100$$
- If `eligible_students` is not explicitly stated in the document, VEDANTA reports the raw number of placed students without inventing a percentage.

### Fee Sum Verification
$$\text{Total Fee} \stackrel{?}{=} \text{Tuition Fee} + \text{Development Fee} + \text{Other Statutory Fees}$$
- The engine cross-verifies that column totals match the sum of their individual component rows. If a discrepancy exists in the published document, the provenance note highlights the internal discrepancy.

---

## 5. Statistical Answer Formatting

When presenting statistical information to users:
- Numbers are presented in clear Markdown tables with unit labels (e.g., `LPA`, `₹ / Year`).
- Provenance footnotes cite the exact table and circular page number.
- Ambiguous or partial figures are explicitly tagged with caution disclaimers (e.g., *"Note: Ongoing placement cycle for AY 2024-25 as of latest circular dated October 2024"*).
