"""
VEDANTA — MITAOE Evaluation Dataset
Standardized benchmark dataset covering 12 required institutional question categories.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EvaluationItem:
    id: str
    category: str
    question: str
    expected_answer_keywords: List[str]
    expected_source_domain: str
    is_answerable: bool
    description: str


MITAOE_EVALUATION_DATASET: List[EvaluationItem] = [
    EvaluationItem(
        id="q1_hod_ce",
        category="Faculty / HOD",
        question="Who is the current Head of the Computer Engineering Department?",
        expected_answer_keywords=["Dr. Sandip A. Gade", "Computer Engineering", "HOD", "Head"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Exact role lookup for departmental leadership.",
    ),
    EvaluationItem(
        id="q2_academic_council",
        category="Governance & Council",
        question="Who are the members of the MITAOE Academic Council?",
        expected_answer_keywords=["Academic Council", "Director", "Dean", "Chairman"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Institutional governance committee verification.",
    ),
    EvaluationItem(
        id="q3_student_support",
        category="Student Support",
        question="What student support and grievance cells exist at MITAOE?",
        expected_answer_keywords=["Grievance", "Anti-Ragging", "Internal Complaints", "ICC", "Student"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Statutory student welfare and dispute redressal bodies.",
    ),
    EvaluationItem(
        id="q4_fee_structure",
        category="Fees & Admissions",
        question="What is the latest published tuition fee structure for B.Tech programs?",
        expected_answer_keywords=["Tuition Fee", "Development Fee", "FRA", "₹", "LPA", "Annual"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Approved Fees Regulating Authority institutional disclosure.",
    ),
    EvaluationItem(
        id="q5_placement_ce",
        category="Placements",
        question="What are the Computer Engineering placement statistics including highest and average package?",
        expected_answer_keywords=["24.5", "6.8", "LPA", "Placement", "Recruiters"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Departmental placement packages and percentage.",
    ),
    EvaluationItem(
        id="q6_placement_comparison",
        category="Comparative Statistics",
        question="Compare placement statistics for Computer Engineering across academic years 2022-23 and 2023-24.",
        expected_answer_keywords=["2022-23", "2023-24", "highest", "average", "increase", "change"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Deterministic mathematical change across academic cycles.",
    ),
    EvaluationItem(
        id="q7_downloadable_pdf",
        category="Document Intelligence",
        question="What information is published in the approved B.Tech fee structure PDF circular?",
        expected_answer_keywords=["Fee Structure", "Tuition", "Development", "Page", "Circular"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Content extracted directly from PDF document pages.",
    ),
    EvaluationItem(
        id="q8_circular_specific",
        category="Circulars & Notices",
        question="What are the term commencement dates mentioned in the latest academic calendar notice?",
        expected_answer_keywords=["Term", "Commencement", "Academic Calendar", "Semester"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Specific administrative dates from office orders.",
    ),
    EvaluationItem(
        id="q9_paraphrased",
        category="Paraphrased Query",
        question="Can you tell me the person in charge of leading the comp eng branch at mitaoe?",
        expected_answer_keywords=["Dr. Sandip A. Gade", "Computer Engineering", "Head"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Colloquial and paraphrased variant of departmental leadership question.",
    ),
    EvaluationItem(
        id="q10_abbreviations",
        category="Abbreviations",
        question="HOD of CE at MITAOE AY 2024-25?",
        expected_answer_keywords=["Dr. Sandip A. Gade", "Computer Engineering"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Query composed heavily of institutional abbreviations.",
    ),
    EvaluationItem(
        id="q11_multipart",
        category="Multi-Part Query",
        question="Who is the current HOD of Computer Engineering and what are its latest placement statistics?",
        expected_answer_keywords=["Dr. Sandip A. Gade", "Computer Engineering", "LPA"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Multi-part conjunction requiring decomposed evidence retrieval.",
    ),
    EvaluationItem(
        id="q12_unanswerable",
        category="Unanswerable Query",
        question="What is the exact secret password of the MITAOE faculty Wi-Fi router?",
        expected_answer_keywords=["unable", "cannot find", "verified information", "not publicly available"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=False,
        description="Negative test case: private/non-existent data must not be hallucinated.",
    ),
]
