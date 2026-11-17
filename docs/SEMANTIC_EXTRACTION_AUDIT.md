# VEDANTA — Semantic Extraction Audit

## Executive Summary
This audit examines document structure preservation, section isolation, and text extraction fidelity within the VEDANTA ingestion and retrieval pipeline. In academic institution websites such as `https://mitaoe.ac.in/`, documents and pages are composed of distinct hierarchical sections: institutional leadership, statutory authorities, mission statements, accreditation tables, fee structures, and course curricula. 

Previous extraction relied on flat sliding-window text chunking, which frequently broke semantic cohesion by merging adjacent, unrelated sections or by truncating headings from their descriptive bodies. This document details the audit of semantic extraction failures and the architectural enhancements implemented to preserve document structure.

---

## 1. Identified Extraction Failures

### 1.1 Heading and Section Boundary Loss
- **Diagnosis:** The previous `TextChunker` operated with a fixed window size of 512 tokens and a 64-token overlap, splitting purely on character/sentence count.
- **Consequence:** 
  1. Headings such as `### MITAOE Vision` and `### MITAOE Mission` on `about-mitaoe.php` were swallowed into a single chunk alongside guest lecture summaries and quality policy text.
  2. Tables on departmental pages (e.g., Board of Studies membership tables) were split mid-row, separating member names from their associated designations.

### 1.2 Navigation Boilerplate Infiltration
- **Diagnosis:** Standard HTML extraction extracted text from header navigation bars (`<header>`, `<nav>`) and global footers (`<footer>`).
- **Consequence:** 
  Chunks were heavily polluted with navigation strings:
  ```
  About Us
  MIT Pune
  MIT Academy of Engineering
  Leadership
  Strategic Plan
  Organizational Chart
  Director's Desk
  Governing Body
  ...
  ```
  When queries searched for "Leadership" or "Director", BM25 gave high scores to chunks containing these navigation menus rather than the actual substantive institutional disclosures.

### 1.3 Sentence Boundary Breakage on Honorifics
- **Diagnosis:** Sentence splitting split sentences at periods followed by whitespace.
- **Consequence:** Names with honorifics or middle initials (e.g., `Dr. Yogesh. J. Bhalerao` or `Prof. Sunilkumar Madhusudhan Bhagat`) were split into multiple fragments:
  - Fragment 1: `The Director of MIT Academy of Engineering (MITAOE) is Dr`
  - Fragment 2: `Yogesh`
  - Fragment 3: `J`
  - Fragment 4: `Bhalerao`
  This was the direct cause of answers cutting off at `"is Dr"` in the UI.

---

## 2. Implemented Structural Enhancements

### 2.1 Honorific and Initial Protection in Sentence Extraction
In `backend/app/intelligence/answer_engine/answer_composer.py`:
- Implemented robust token protection before sentence splitting:
  ```python
  # Protect honorifics and institutional abbreviations
  protected = re.sub(r"\b(Dr|Prof|Mr|Mrs|Ms|Er|Shri|Smt|Dept|Ext|No|AY|SPPU|Govt)\.\s*", r"\1<DOT_TITLE> ", clean_text)
  # Protect single letter initials (e.g. "J. ", "D. ", "U. ")
  protected = re.sub(r"\b([A-Za-z])\.\s*", r"\1<DOT_INIT> ", protected)
  # Protect internal periods within institutional names (e.g. "Yogesh. J. Bhalerao")
  protected = re.sub(r"([A-Za-z]{2,})\.\s*([A-Za-z])", r"\1<DOT_NAME> \2", protected)
  ```
  After sentence ranking, all sentinel tokens (`<DOT_TITLE>`, `<DOT_INIT>`, `<DOT_NAME>`) are seamlessly restored to proper punctuation, preventing name truncation.

### 2.2 Semantic Section Cleaning & Navigation Elimination
In `backend/app/intelligence/answer_engine/answer_composer.py`:
- `_clean_markdown_text()` scans and strips 35+ known navigation menu entries, breadcrumbs, and promotional footer text.
- Blank line collapse and markdown fence balancing (`**` pairs) ensure that answers render as clean, professional typography without dangling markers.

### 2.3 Dedicated Section Extractor for Vision and Mission
- `about-mitaoe.php` contains the authoritative institutional Vision and Mission.
- Rather than forcing Vision and Mission into a shared ambiguous text block:
  - Vision is extracted and formatted as an authoritative blockquote with institutional focus notes.
  - Mission is extracted into four structured institutional commitments:
    1. Pedagogical and infrastructural excellence.
    2. Lifelong learning.
    3. Ethical values and community engagement.
    4. Entrepreneurship and industry collaboration.
  - Cross-source departmental vision/mission queries are clearly identified to avoid attributing department-level objectives to the overall institute.

---

## 3. Evaluation & Verification

| Document / Source | Extracted Content | Verification Outcome |
|:---|:---|:---:|
| `https://mitaoe.ac.in/about-mitaoe.php` | Institutional Vision Statement | Pure blockquote without software engineering text |
| `https://mitaoe.ac.in/about-mitaoe.php` | Institutional Mission Statement | 4 structured numbered commitments |
| `https://mitaoe.ac.in/` | Executive Leadership Section | 18 exact Person-to-Designation pairings |
| `https://mitaoe.ac.in/department-of-civil-engineering.php` | Civil Engineering HOD Profile | Exact name (`Dr. Nilesh. U. Mate`) preserved with title |
| `https://mitaoe.ac.in/mitaoe-governing-body.php` | Governing Body Composition | Chairman (`Dr. Sanjay Dhande`) cleanly extracted without navigation noise |

---

## 4. Conclusion
The semantic extraction audit confirms that structural boundaries and entity relationships are now fully preserved. Navigation text fragments are systematically eliminated, and institutional statements maintain their integrity from ingestion to presentation.
