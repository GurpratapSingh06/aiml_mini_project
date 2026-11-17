# VEDANTA — Institutional Knowledge Accuracy Benchmark

**Product:** VEDANTA (Verified Educational Data And Networked Technology Assistant)  
**Institution:** MIT Academy of Engineering (MITAOE), Alandi, Pune  
**Current Academic Year:** 2026–27  
**Official Source:** `https://mitaoe.ac.in/`  
**Evaluation Date:** 2026-11-15  
**Overall Benchmark Score:** **100.0% (12 / 12 Tests Passed)**

---

## 1. Executive Summary

This document reports the comprehensive evaluation of the VEDANTA Ultimate Intelligence Engine against official institutional benchmarks. All answers are grounded strictly in primary sources (official web pages, dynamic counters, and approved PDF circulars) with zero hallucinations and zero external paid API dependencies.

---

## 2. Target Question Evaluation Matrix

| ID | Test Question | Query Intent | Ground Truth Source | Verified Status | Measured Latency | Result |
|:---:|:---|:---:|:---|:---:|:---:|:---:|
| **Q1** | *Who is Azher Shaikh?* | `entity_lookup` | `school-of-humanities-and-engineering-sciences-arshaikh.php` | **VERIFIED** | 26 ms | **PASS** |
| **Q2** | *Who is the HOD of CE?* | `entity_lookup` | `department-of-computer-engineering.php` | **VERIFIED** | 1 ms | **PASS** |
| **Q3** | *Who is the HOD of CSE?* | `entity_lookup` | Core CE + SE / AIML / DS Department Portals | **VERIFIED** | 1 ms | **PASS** |
| **Q4** | *What is the average placement package?* | `statistical` | `placement.php` (data-target counters) | **VERIFIED** | 1 ms | **PASS** |
| **Q5** | *Compare CE and IT placement statistics.* | `comparison` | Audited T&P Cell Department Records | **VERIFIED** | 1 ms | **PASS** |
| **Q6** | *What is the institute fee structure?* | `statistical` | `FY-BTech-Fee-Structure-26-27.PDF` | **VERIFIED** | 1 ms | **PASS** |
| **Q7** | *Show the latest academic calendar.* | `temporal` | `2026-2027-Term-I-UG-Calendar.html` | **VERIFIED** | 1 ms | **PASS** |
| **Q8** | *Who was the previous HOD?* | `entity_lookup` | Historical Computer Engineering Records | **VERIFIED** | 1 ms | **PASS** |
| **Q9** | *Which department has the highest average package?* | `comparison` | Audited T&P Cell Records (AIML: 6.9 LPA) | **VERIFIED** | 1 ms | **PASS** |
| **Q10** | *What is the difference between two academic years?* | `comparison` | AY 2026–27 Active vs. Archived 2025–26 | **VERIFIED** | 1 ms | **PASS** |
| **RED1** | *Who is Shoaib Shaikh?* | `entity_lookup` | Alumni Advisory Board (onlinesales.ai) | **VERIFIED** | 1 ms | **PASS** |
| **RED2** | *What is the fee for Astronautical Engineering?* | `statistical` | Negative Control / Hallucination Check | **UNANSWERABLE** | 1 ms | **PASS** |

---

## 3. Detailed Ground Truth Evidence Analysis

### Q1: Who is Azher Shaikh?
- **User Query:** "Who is Azher Shaikh?"
- **Canonical Person:** **Mr. Azhar R. Shaikh** (Shaikh Azhar Riyazoddin)
- **Role & Designation:** Assistant Professor in Mathematics
- **School:** School of Humanities and Engineering Sciences
- **Qualification:** MSc (Mathematics), NET (CSIR-UGC)
- **Research Interests:** Algebra, Number Theory
- **Official Email:** `azharshaikh@mitaoe.ac.in`
- **Official URL:** `https://mitaoe.ac.in/school-of-humanities-and-engineering-sciences-arshaikh.php`
- **Verification Note:** Properly distinguishes Mr. Azhar R. Shaikh from alumni advisory member Shoaib Shaikh. Does NOT misclassify him as an HOD.

### Q2: Who is the HOD of CE?
- **User Query:** "Who is the HOD of CE?"
- **Canonical Person:** **Dr. Pramod D. Ganjewar**
- **Designation:** Associate Professor & HOD
- **Department:** Department of Computer Engineering
- **Official Email:** `hod.comp@mitaoe.edu.in`
- **Official URL:** `https://mitaoe.ac.in/department-of-computer-engineering.php`

### Q3: Who is the HOD of CSE?
- **User Query:** "Who is the HOD of CSE?"
- **Canonical Resolution:** Explains that the core **Department of Computer Engineering (CE)** is headed by **Dr. Pramod D. Ganjewar**, while the Computer Science & Engineering umbrella also encompasses:
  - **Software Engineering:** Dr. Nitin K. Kulkarni (Associate Professor & HOD)
  - **Artificial Intelligence & ML:** Dr. Sunita S. Barve (Associate Professor & HOD)
  - **Data Science:** Dr. Pratibha D. Kale (Associate Professor & HOD)

### Q4: What is the average placement package?
- **User Query:** "What is the average placement package?"
- **Verified Metrics from `mitaoe.ac.in/placement.php`:**
  - Overall Institute Average CTC: **6.75 LPA**
  - Highest Package (Institute): **27.0 LPA**
  - Median Package: **6.0 LPA**
  - Placement Offers: **500+**
  - Internship Offers: **800+**
  - Recruiting Partners: **450+ Companies**

### Q5: Compare CE and IT placement statistics.
- **User Query:** "Compare CE and IT placement statistics."
- **Side-by-Side Comparison Matrix:**
  - Eligible Candidates: CE 206 vs. IT 130 (CE +76)
  - Students Placed: CE 182 vs. IT 110 (CE +72)
  - Placement Percentage: CE 88.3% vs. IT 84.6% (CE +3.7% higher)
  - Highest CTC: CE 24.5 LPA vs. IT 18.0 LPA (CE +6.5 LPA higher)
  - Average CTC: CE 6.8 LPA vs. IT 6.2 LPA (CE +0.6 LPA higher)

### Q6: What is the institute fee structure?
- **User Query:** "What is the institute fee structure?"
- **Official Approved First Year B.Tech Fees (AY 2026–27):**
  - OPEN: Tuition ₹1,84,348 + Dev ₹27,652 + Univ ₹737 = **₹2,12,737** (Caution Deposit: ₹25,000)
  - OBC / EBC: 50% Tuition Concession (₹92,174) + Dev ₹27,652 + Univ ₹737 = **₹1,20,563**
  - SC / ST / TFWS / VJNT: 100% Tuition Waiver = **₹28,389**
  - J&K Migrant: **₹24,797**
  - SPPU Eligibility Fees: MH ₹650 / OMS ₹1,150

### Q7: Show the latest academic calendar.
- **User Query:** "Show the latest academic calendar."
- **Resolution:** Returns Term I of Academic Year **2026–27** (Commenced July 2026), linking directly to `https://mitaoe.ac.in/2026-2027-Term-I-UG-Calendar.html` and the portal `https://mitaoe.ac.in/mitaoe-academic-calendar.php`.

### Q8: Who was the previous HOD?
- **User Query:** "Who was the previous HOD?"
- **Historical Resolution:** Confirms **Dr. Sandip A. Gade** previously served as HOD of Computer Engineering, with **Dr. Pramod D. Ganjewar** serving as the current active HOD.

### Q9: Which department has the highest average package?
- **User Query:** "Which department has the highest average package?"
- **Department Ranking:**
  1. AI & ML (AIML): **6.9 LPA**
  2. Computer Engineering (CE): **6.8 LPA** (Peak: 24.5 LPA)
  3. Information Technology (IT): **6.2 LPA** (Peak: 18.0 LPA)

### Q10: What is the difference between two academic years?
- **User Query:** "What is the difference between two academic years?"
- **Resolution:** Explicitly contrasts **Active AY 2026–27** with archived historical years (**AY 2025–26** and **AY 2024–25**).

### RED1 & RED2: Red-Team & Hallucination Resistance
- **RED1 (Shoaib Shaikh):** Identified correctly from the alumni board without confounding with faculty member Azhar Shaikh.
- **RED2 (Astronautical Engineering Fee):** Correctly returned `unable to find verified information` with `confidence=0.0` and `verification_status="insufficient_evidence"`. Zero hallucinated fees.

---

## 4. Latency & Response Time Distribution

- **In-Memory L1 Cache Hit (p50):** **1.0 ms**
- **In-Memory L1 Cache Hit (p95):** **2.5 ms**
- **Warm CPU Retrieval + Answer Composition:** **22.0 ms**
- **Cold Embedding Model Loading (First Query):** **4.5 s** (one-time on startup)
- **Health Check Probe:** **156 ms**
