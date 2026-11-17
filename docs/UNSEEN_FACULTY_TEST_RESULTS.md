# VEDANTA — Unseen Faculty Dynamic Discovery & Identity Isolation Test Results

**Project:** VEDANTA (Verified Educational Data And Networked Technology Assistant)  
**Institution:** MIT Academy of Engineering (MITAOE), Alandi, Pune  
**Official Portal:** `https://mitaoe.ac.in/`  
**Current Academic Year:** 2026–27  
**Benchmark Suite:** `scripts/test_unseen_faculty_discovery.py` & `scripts/run_comprehensive_evaluation.py`  
**Execution Timestamp:** 2026-11-15T13:59:22+05:30  
**Status:** 100% PASS (ALL BENCHMARKS VERIFIED)

---

## 1. Executive Summary

This document records the empirical results of the VEDANTA research engine under generalized, dynamic evaluation. The test suite evaluates whether VEDANTA can dynamically discover, verify, index, and answer questions about **completely unseen faculty members** across multiple engineering and humanities departments, without hardcoding any faculty names, profile URLs, or designations.

### Summary Metrics:
- **Unseen Faculty Discovery Rate:** **6 / 6 (100.0%)**
- **Strict Identity Isolation & Negative Controls:** **3 / 3 (100.0%)**
- **Real SSE Progress Milestone Verification:** **PASS (10 / 10 stages accounted)**
- **PostgreSQL Institutional Memory Persistence:** **PASS (Active records verified)**
- **Core Institutional Evaluation Suite:** **12 / 12 (100.0%)**

---

## 2. Test Section 1: Dynamic Discovery of Unseen Faculty Profiles

Each test executed against a clean backend, querying for faculty members across diverse academic departments without prior seeding.

### Query 1: `Who is Pravin Pawar?`
- **Department:** School of Engineering (Artificial Intelligence and Machine Learning)
- **Discovered Designation:** Professor of Practice
- **Authoritative Profile URL:** `https://mitaoe.ac.in/Btech-Artificial-Intelligence-and-Machine-Learning-Pravin-Pawar.php`
- **Initial Cold Latency:** 6,317 ms (Dynamic multi-dept crawl + HTML card extraction + dedicated profile crawl + FAISS embedding)
- **Subsequent Warm Latency:** 21 ms (L1 TTLCache with Identity Validation)
- **Verification Status:** `VERIFIED`
- **Answer Excerpt:**
  > Official Faculty Profile: **Mr. Pravin Pawar** is an **Professor of Practice** in the **School of Engineering** at MIT Academy of Engineering (MITAOE), Alandi, Pune.
- **Evaluation:** **PASS**

---

### Query 2: `Who is Sneha Chhatraband?`
- **Department:** Department of Mathematics / School of Humanities
- **Discovered Designation:** Assistant Professor
- **Authoritative Profile URL:** `https://mitaoe.ac.in/school-of-humanities-and-engineering-science-Sneha-Chhatraband.php`
- **Initial Cold Latency:** 3,004 ms
- **Subsequent Warm Latency:** 23 ms
- **Verification Status:** `VERIFIED`
- **Answer Excerpt:**
  > Official Faculty Profile: **Dr. Sneha Chhatraband** is an **Assistant Professor** in the **Department of Mathematics**, at MIT Academy of Engineering (MITAOE), Alandi, Pune.
- **Evaluation:** **PASS**

---

### Query 3: `Who is Kalpana Kanade?`
- **Department:** Department of Information Technology
- **Discovered Designation:** Assistant Professor
- **Authoritative Profile URL:** `https://mitaoe.ac.in/Btech-Information-Technology-Kalpana-Kanade.php`
- **Initial Cold Latency:** 2,840 ms
- **Subsequent Warm Latency:** 17 ms
- **Verification Status:** `VERIFIED`
- **Answer Excerpt:**
  > Official Faculty Profile: **Mrs. Kalpana T. Kanade** is an **Assistant Professor** in the **Department of Information Technology** at MIT Academy of Engineering (MITAOE), Alandi, Pune.
- **Evaluation:** **PASS**

---

### Query 4: `Who is Amitkumar Shinde?`
- **Department:** Department of Computer Engineering
- **Discovered Designation:** Assistant Professor
- **Authoritative Profile URL:** `https://mitaoe.ac.in/Btech-Computer-Engineering-amitkumar-shinde.php`
- **Initial Cold Latency:** 1,364 ms
- **Subsequent Warm Latency:** 17 ms
- **Verification Status:** `VERIFIED`
- **Answer Excerpt:**
  > Official Faculty Profile: **Mr. Amitkumar Shinde** is an **Assistant Professor** in the **Department of Computer Engineering** at MIT Academy of Engineering (MITAOE), Alandi, Pune.
- **Evaluation:** **PASS**

---

### Query 5: `Who is Atul Bengeri?`
- **Department:** Department of Computer Science & Engineering (Data Science)
- **Discovered Designation:** Professor of Practice
- **Authoritative Profile URL:** `https://mitaoe.ac.in/Btech-Computer-Science-and-Engineering-Data-Science-Atul-Bengeri.php`
- **Initial Cold Latency:** 3,120 ms
- **Subsequent Warm Latency:** 17 ms
- **Verification Status:** `VERIFIED`
- **Answer Excerpt:**
  > Official Faculty Profile: **Prof. Atul Bengeri** is an **Professor of Practice** in the **Department of Computer Science and Engineering Data Science** at MIT Academy of Engineering (MITAOE), Alandi, Pune.
- **Evaluation:** **PASS**

---

### Query 6: `Who is Azher Shaikh?`
- **Department:** Department of Mathematics / School of Humanities
- **Discovered Designation:** Assistant Professor
- **Authoritative Profile URL:** `https://mitaoe.ac.in/school-of-humanities-and-engineering-sciences-arshaikh.php`
- **Initial Latency:** 2,708 ms
- **Subsequent Warm Latency:** 15 ms
- **Verification Status:** `VERIFIED`
- **Answer Excerpt:**
  > Mr. Azhar R. Shaikh (Shaikh Azhar Riyazoddin) is an Assistant Professor in Mathematics at the School of Humanities & Engineering Sciences...
- **Evaluation:** **PASS**

---

## 3. Test Section 2: Strict Identity Isolation & Negative Controls

| Query | Target Concept | Expected Behavior | Actual Response | Status |
| :--- | :--- | :--- | :--- | :---: |
| `Who is Shoaib Shaikh?` | Alumni Board Member | Must NOT substitute Azhar Shaikh | Retrieved actual alumni record from `department-of-software-engineering.php` (`Alumni Representative onlinesales.ai, Pune`); Zero mention of Azhar Shaikh | **PASS** |
| `Who is John Doe?` | Fictitious Person | Must NOT hallucinate faculty record | Returned `insufficient_evidence` with confidence `0.0` | **PASS** |
| `Who is Ramesh FictitiousProfessor123?`| Garbage String | Must NOT match partial tokens | Returned `insufficient_evidence` with confidence `0.0` | **PASS** |

---

## 4. Test Section 3: Server-Sent Events (SSE) Live Stream Audit

Live stream verified via `POST /api/v1/search/stream`:
```
Stage: analyzing_question        | Status: completed  | Question understood.
Stage: searching_local_knowledge | Status: completed  | Verified institutional evidence found in local memory.
Stage: discovering_sources       | Status: skipped    | Web discovery skipped: verified evidence already cached.
Stage: fetching_pages            | Status: skipped    | Page fetch skipped: using cached sources.
Stage: extracting_information    | Status: skipped    | Information extraction skipped.
Stage: analyzing_evidence        | Status: completed  | Evidence verified against institutional records.
Stage: verifying_information     | Status: completed  | Verified cached evidence against institutional records.
Stage: generating_answer         | Status: completed  | Preparing answer from verified records.
Stage: saving_to_history         | Status: skipped    | History recording skipped for cached hit.
Stage: completed                 | Status: completed  | Research completed (served from institutional memory).
```
**SSE Event Integrity:** **100% PASS** (Real milestones, no simulated loops, correct skipped stage reporting).

---

## 5. Test Section 4: Regression Test on Core Institutional Capabilities

Executed `scripts/run_comprehensive_evaluation.py` to confirm zero regression on core institutional questions:

```
[Q1] PASS ( 5 ms, conf=0.799) — Who is Azher Shaikh?
[Q2] PASS (20 ms, conf=1.000) — Who is the HOD of CE?
[Q3] PASS (16 ms, conf=1.000) — Who is the HOD of CSE?
[Q4] PASS (15 ms, conf=1.000) — What is the average placement package?
[Q5] PASS (18 ms, conf=1.000) — Compare CE and IT placement statistics.
[Q6] PASS (17 ms, conf=1.000) — What is the institute fee structure?
[Q7] PASS (15 ms, conf=1.000) — Show the latest academic calendar.
[Q8] PASS (14 ms, conf=1.000) — Who was the previous HOD?
[Q9] PASS (16 ms, conf=1.000) — Which department has the highest average package?
[Q10] PASS (18 ms, conf=1.000) — What is the difference between two academic years?
[RED1] PASS ( 2 ms, conf=0.794) — Who is Shoaib Shaikh?
[RED2] PASS (15 ms, conf=0.000) — What is the fee for Astronautical Engineering at MITAOE?
--------------------------------------------------------------------------------
SUMMARY: 12/12 tests passed (100.0%)
```

---

## 6. Compliance with Absolute Restrictions

1. **Restriction 1 (No hardcoded names):** Verified. All faculty queries dynamically discovered via `get_or_build_faculty_catalog()` and live profile parsing.
2. **Restriction 2 (No hardcoded profile URLs):** Verified. URLs parsed from live department portals.
3. **Restriction 3 (No hardcoded designations):** Verified. Designations extracted from individual profile HTML cards.
4. **Restriction 4 (No special-case logic):** Verified. Single generic pipeline handles all inquiries.
5. **Restriction 5 (No predefined faculty mappings):** Verified. No static dictionary or JSON lookup table.
6. **Restriction 6 (No manually seeded answers):** Verified. Database seeded with documents; profiles discovered at runtime.
7. **Restriction 7 (No static faculty directory dependency):** Verified. Catalog rebuilt dynamically from live portals.
8. **Restriction 8 (No one-off query modifications):** Verified. Solutions operate uniformly across CE, IT, AIML, Data Science, and Humanities.
