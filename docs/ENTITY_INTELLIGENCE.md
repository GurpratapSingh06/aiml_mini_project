# VEDANTA Entity Intelligence Engine

## 1. Overview and Problem Statement

Educational institutions function as complex interconnected graphs of people, departments, governance councils, regulatory committees, and student facilities. A question like:
> *"Who leads the computer engineering department and who sits on the academic council?"*

requires resolving not just keyword strings, but the relational hierarchy between academic departments, faculty appointments, and institutional leadership.

The VEDANTA Entity Intelligence Engine (`backend/app/intelligence/entity_engine/entity_extractor.py`) discovers, disambiguates, models, and stores entities and their relationships within the relational database (`entities`, `entity_aliases`, and `entity_relationships` tables).

---

## 2. Entity Taxonomy

VEDANTA categorizes institutional entities into six primary types:

| Entity Type | Description | Examples at MITAOE |
|---|---|---|
| `person` | Faculty members, leadership, deans, and officers | Dr. Mahesh Goudar (Director), Prof. N. B. Pokale |
| `department` | Academic departments and branches | School of Computer Engineering, School of Mechanical Engineering |
| `committee` | Statutory and institutional bodies | Academic Council, Board of Studies, Anti-Ragging Cell |
| `organization` | Governing trust, university affiliation, and accreditations | MIT Pune, SPPU, NAAC, NBA, AICTE |
| `facility` | Campus physical and student support infrastructure | Central Library, Boys Hostel, Girls Hostel, Gymnasium |
| `program` | Academic degrees and curricula | B.Tech Computer Engineering, M.Tech, PhD |

---

## 3. Relationship Modeling

Relationships between entities are represented as directed, attributed edges:

```
[Person: Dr. Mahesh Goudar] ──(heads)─────────────► [Institution: MITAOE]
[Person: Dr. Mahesh Goudar] ──(chairs)────────────► [Committee: Academic Council]
[Person: Prof. Faculty]    ──(heads)─────────────► [Department: Computer Engineering]
[Person: Prof. Faculty]    ──(member_of)─────────► [Committee: Academic Council]
[Department: Comp Eng]     ──(offers)────────────► [Program: B.Tech Computer Engineering]
[Committee: Anti-Ragging]  ──(governs)───────────► [Institution: MITAOE]
```

### Supported Relationship Types
- `heads`: Direct administrative leadership (HOD, Director, Principal, Dean).
- `member_of`: Membership in committees, academic councils, or editorial boards.
- `belongs_to`: Faculty affiliation with a primary department.
- `offers`: Department offering a specific academic degree or program.
- `chairs`: Presiding officer of a council, board, or cell.
- `reports_to`: Administrative hierarchy between personnel or departments.

---

## 4. Entity Extraction and Disambiguation

The extraction pipeline processes unstructured text from crawled web pages and PDF notices:

1. **Title & Prefix Detection:** Identifies honorifics and titles (`Dr.`, `Prof.`, `Mr.`, `Ms.`, `Mrs.`, `Shri`) paired with capitalized person names.
2. **Designation Pattern Matching:** Scans for structural titles:
   - *Director*, *Principal*, *Dean Academics*, *Dean R&D*, *Registrar*.
   - *Head of Department (HOD)*, *Associate Professor*, *Assistant Professor*.
   - *Member Secretary*, *Chairman*, *Presiding Officer*.
3. **Institutional Alias Resolution:**
   - Multiple references to the same entity (e.g., *"Dr. M. Goudar"*, *"Mahesh Goudar"*, *"Director MITAOE"*) are resolved to a single canonical entity ID via the `entity_aliases` table.
4. **Disambiguation & Hierarchy:**
   - When a person is mentioned in connection with both a department and a statutory council, separate relational records are populated with provenance references linking to the specific source document and academic year.

---

## 5. Governance Councils and Statutory Cells

VEDANTA provides specialized indexing for statutory bodies required by AICTE and UGC regulations:

- **Academic Council:** Principal governing body for academic curricula, examinations, and program approvals.
- **Internal Complaints Committee (ICC):** Statutory cell for gender equity and grievance redressal.
- **Anti-Ragging Committee & Squad:** Institutional cell ensuring student safety and disciplinary compliance.
- **Student Grievance Redressal Cell (SGRC):** Official body for addressing academic, administrative, and facility-related student grievances.

When queries target any of these bodies, the entity engine retrieves the verified committee roster, designated officers, contact details, and office location directly from corroborated institutional evidence.
