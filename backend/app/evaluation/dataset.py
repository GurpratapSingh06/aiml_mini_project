"""
VEDANTA — MITAOE Standardized Evaluation Benchmark Dataset
38 verified institutional benchmark items covering all required evaluation categories:
- Faculty & HOD across all 9+ departments
- Institutional leadership & governance
- Academic year 2026-27 & temporal intelligence
- Previous academic year & historical calendars
- Department navigation & URLs
- PDF document intelligence
- Unanswerable / out-of-scope negative controls
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class EvaluationItem:
    id: str
    category: str
    question: str
    expected_answer_keywords: List[str]
    expected_source_domain: str
    is_answerable: bool
    description: str
    expected_status: str = "verified"


MITAOE_EVALUATION_DATASET: List[EvaluationItem] = [
    # ---- 1. Department HODs & Leadership ----------------------------------
    EvaluationItem(
        id="q01_hod_ce",
        category="Faculty / HOD",
        question="Who is the HOD of Computer Engineering?",
        expected_answer_keywords=["Dr. Pramod D. Ganjewar", "Ganjewar", "Associate Professor & HOD", "Computer Engineering"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Department leadership lookup for Computer Engineering.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q02_hod_it",
        category="Faculty / HOD",
        question="Who is the HOD of Information Technology?",
        expected_answer_keywords=["Dr. Santosh Warpe", "Warpe", "Information Technology", "hodit@mitaoe.ac.in"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Department leadership lookup for Information Technology.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q03_hod_se",
        category="Faculty / HOD",
        question="Who is the Head of the Department of Software Engineering?",
        expected_answer_keywords=["Dr. Manish Giri", "Giri", "Software Engineering", "hodsoftengg@mitaoe.ac.in"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Department leadership lookup for Software Engineering.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q04_hod_aiml",
        category="Faculty / HOD",
        question="Who is the HOD of AI and ML?",
        expected_answer_keywords=["Dr. Diptee Ghusse", "Chikmurge", "Artificial Intelligence", "hod.aiml@mitaoe.edu.in"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Department leadership lookup for AI and ML.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q05_hod_ds",
        category="Faculty / HOD",
        question="Who is the HOD of Data Science?",
        expected_answer_keywords=["Dr. Vaishali Wangikar", "Wangikar", "Data Science", "hod.datasci@mitaoe.edu.in"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Department leadership lookup for Data Science.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q06_hod_mech",
        category="Faculty / HOD",
        question="Who is the HOD of Mechanical Engineering?",
        expected_answer_keywords=["Dr. Maya Charde", "Charde", "Mechanical Engineering"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Department leadership lookup for Mechanical Engineering.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q07_hod_civil",
        category="Faculty / HOD",
        question="Who is the HOD of Civil Engineering?",
        expected_answer_keywords=["Dr. Nilesh. U. Mate", "Mate", "Civil Engineering", "hodcivil@mitaoe.ac.in"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Department leadership lookup for Civil Engineering.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q08_hod_chem",
        category="Faculty / HOD",
        question="Who is the Head of Department of Chemical Engineering?",
        expected_answer_keywords=["Dr. S. P. Shewale", "Shewale", "Chemical Engineering"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Department leadership lookup for Chemical Engineering.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q09_hod_entc",
        category="Faculty / HOD",
        question="Who is the HOD of Electronics and Telecommunication Engineering?",
        expected_answer_keywords=["Dr. Dipti Y Sakhare", "Sakhare", "Telecommunication"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Department leadership lookup for E&TC Engineering.",
        expected_status="verified",
    ),

    # ---- 2. Acronym & Paraphrased Queries ---------------------------------
    EvaluationItem(
        id="q10_hod_ce_acronym",
        category="Acronym / Paraphrase",
        question="Who is the HOD of CE?",
        expected_answer_keywords=["Dr. Pramod D. Ganjewar", "Ganjewar", "Computer Engineering"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Acronym disambiguation CE -> Computer Engineering.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q11_hod_it_acronym",
        category="Acronym / Paraphrase",
        question="Who heads the IT department at MITAOE?",
        expected_answer_keywords=["Dr. Santosh Warpe", "Warpe", "Information Technology"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Paraphrased query for Information Technology head.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q12_hod_ds_acronym",
        category="Acronym / Paraphrase",
        question="Who is the HOD of DS at MITAOE?",
        expected_answer_keywords=["Dr. Vaishali Wangikar", "Wangikar", "Data Science"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Acronym disambiguation DS -> Data Science.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q13_comp_lead_paraphrase",
        category="Acronym / Paraphrase",
        question="Can you tell me the person leading the computer engineering branch at mitaoe?",
        expected_answer_keywords=["Dr. Pramod D. Ganjewar", "Ganjewar", "Computer Engineering"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Natural language colloquial query for Computer Engineering HOD.",
        expected_status="verified",
    ),

    # ---- 3. Institutional Governance & Leadership -------------------------
    EvaluationItem(
        id="q14_director",
        category="Institutional Leadership",
        question="Who is the Director of MITAOE?",
        expected_answer_keywords=["Dr. Yogesh. J. Bhalerao", "Bhalerao", "Director", "Dr. Mahesh D. Goudar"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Institutional director lookup from official records.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q15_academic_council",
        category="Institutional Leadership",
        question="Who are the key members of the MITAOE Academic Council?",
        expected_answer_keywords=["Academic Council", "Director", "Chairman", "Council"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Academic Council constitution and governance.",
        expected_status="verified",
    ),

    # ---- 4. Department Catalog & URLs ------------------------------------
    EvaluationItem(
        id="q16_available_departments",
        category="Department Directory",
        question="Which departments are available at MITAOE?",
        expected_answer_keywords=["Computer Engineering", "Information Technology", "Chemical Engineering", "Mechanical", "Civil"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Complete institutional department listing.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q17_ce_page_url",
        category="Department Directory",
        question="Where can I find the Computer Engineering department page?",
        expected_answer_keywords=["https://mitaoe.ac.in/department-of-computer-engineering.php", "department-of-computer-engineering"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Direct URL lookup for Computer Engineering.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q18_it_page_url",
        category="Department Directory",
        question="Where can I find the Information Technology department page?",
        expected_answer_keywords=["https://mitaoe.ac.in/department-of-information-technology.php", "department-of-information-technology"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Direct URL lookup for Information Technology.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q19_aiml_page_url",
        category="Department Directory",
        question="Where can I find the AI and ML department page?",
        expected_answer_keywords=["department-of-Computer-Science-&-Engineering-AI-&-Ml.php", "mitaoe.ac.in"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Direct URL lookup for AI and ML.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q20_departments_overview_url",
        category="Department Directory",
        question="Where is the overview page for academic departments at MITAOE?",
        expected_answer_keywords=["mitaoe-academic-departments.php", "mitaoe.ac.in"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Academic departments overview page URL.",
        expected_status="verified",
    ),

    # ---- 5. Academic Year 2026-27 & Temporal Intelligence ------------------
    EvaluationItem(
        id="q21_current_ay",
        category="Temporal Intelligence",
        question="What is the current academic year at MITAOE?",
        expected_answer_keywords=["2026–27", "2026-27", "AY 2026-27"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Verification of current active academic year (2026-27).",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q22_active_year_phrase",
        category="Temporal Intelligence",
        question="What is the active academic year for instructional classes?",
        expected_answer_keywords=["2026–27", "2026-27", "Term I"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Active academic cycle verification.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q23_calendar_2026_27",
        category="Temporal Intelligence",
        question="Show the academic calendar for 2026–27.",
        expected_answer_keywords=["2026–27", "2026-27", "Term I", "July 2026", "2026-2027-Term-I-UG-Calendar.html"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Institutional academic calendar for active 2026-27 cycle.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q24_calendar_term_1",
        category="Temporal Intelligence",
        question="What is the academic calendar for Term I of 2026–27?",
        expected_answer_keywords=["2026–27", "Term I", "July 2026", "Calendar"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Term I 2026-27 academic schedules and examination periods.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q25_timetable_latest",
        category="Temporal Intelligence",
        question="What is the latest available academic timetable?",
        expected_answer_keywords=["2026-2027", "academic-year-2026-2027.php", "Time Table", "Examination"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Latest published examination timetable (AY 2026-27).",
        expected_status="verified",
    ),

    # ---- 6. Historical Academic Years & Calendars ------------------------
    EvaluationItem(
        id="q26_previous_calendar",
        category="Historical Intelligence",
        question="Show the previous academic year's calendar.",
        expected_answer_keywords=["2025–26", "2025-26", "2024-25", "Academic Calendar"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Historical academic calendar lookup preceding active cycle.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q27_calendar_2024_25",
        category="Historical Intelligence",
        question="What was the academic calendar for academic year 2024-25?",
        expected_answer_keywords=["2024-25", "Academic-Calendar-2024-25.pdf", "Term I"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Historical schedule verification without confusing with current year.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q28_timetable_2025_26",
        category="Historical Intelligence",
        question="Show examination timetables for academic year 2025-2026.",
        expected_answer_keywords=["academic-year-2025-2026.php", "2025-2026", "Time Table"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Archived timetable lookup for AY 2025-26.",
        expected_status="verified",
    ),

    # ---- 7. PDF Document Intelligence & Statutory Filings -----------------
    EvaluationItem(
        id="q29_mandatory_disclosure",
        category="Document Intelligence",
        question="What is the mandatory disclosure document for 2026-27?",
        expected_answer_keywords=["Mandatory-Disclosure-2026-27.pdf", "Mandatory Disclosure", "2026-27"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Statutory AICTE/DTE mandatory disclosure PDF reference.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q30_downloads_page",
        category="Document Intelligence",
        question="Where can I find official institutional downloads and circulars?",
        expected_answer_keywords=["downloads.php", "https://mitaoe.ac.in/downloads.php"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Official downloads portal verification.",
        expected_status="verified",
    ),
    EvaluationItem(
        id="q31_information_brochure",
        category="Document Intelligence",
        question="What is published in the Information Brochure for AY 2026-27?",
        expected_answer_keywords=["Information Brochure", "2026-27", "AY 2026-27"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Official admissions information brochure content.",
        expected_status="verified",
    ),

    # ---- 8. Conflict Handling & Historical Notes --------------------------
    EvaluationItem(
        id="q32_historical_hod_ce",
        category="Conflict Handling",
        question="Did Dr. Sandip A. Gade previously serve as HOD of Computer Engineering?",
        expected_answer_keywords=["Dr. Sandip A. Gade", "previously served", "earlier", "historical"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=True,
        description="Resolution of previous vs current HOD designation.",
        expected_status="verified",
    ),

    # ---- 9. Unanswerable / Negative Controls (Honest Refusal) ------------
    EvaluationItem(
        id="q33_unanswerable_dept",
        category="Negative Controls",
        question="Who is the HOD of Aerospace Engineering at MITAOE?",
        expected_answer_keywords=["unable to find", "cannot find", "not available", "insufficient evidence", "no verified information"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=False,
        description="Aerospace Engineering is not offered at MITAOE (honest refusal).",
        expected_status="insufficient_evidence",
    ),
    EvaluationItem(
        id="q34_unanswerable_medical",
        category="Negative Controls",
        question="What is the tuition fee structure for MBBS program at MITAOE?",
        expected_answer_keywords=["unable to find", "cannot find", "not available", "insufficient evidence", "no verified information"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=False,
        description="Medical MBBS degree is not offered at MITAOE (honest refusal).",
        expected_status="insufficient_evidence",
    ),
    EvaluationItem(
        id="q35_unanswerable_weather",
        category="Negative Controls",
        question="What is the weather forecast for Pune next month?",
        expected_answer_keywords=["unable to find", "cannot find", "not available", "insufficient evidence", "no verified information"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=False,
        description="External meteorological question outside institutional scope.",
        expected_status="insufficient_evidence",
    ),
    EvaluationItem(
        id="q36_unanswerable_cricket",
        category="Negative Controls",
        question="Who won the Cricket World Cup in 2023?",
        expected_answer_keywords=["unable to find", "cannot find", "not available", "insufficient evidence", "no verified information"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=False,
        description="External sports question outside institutional scope.",
        expected_status="insufficient_evidence",
    ),
    EvaluationItem(
        id="q37_unanswerable_campus_mars",
        category="Negative Controls",
        question="Where is the MITAOE campus located on Mars?",
        expected_answer_keywords=["unable to find", "cannot find", "not available", "insufficient evidence", "no verified information"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=False,
        description="Absurd factual question requiring honest refusal.",
        expected_status="insufficient_evidence",
    ),
    EvaluationItem(
        id="q38_unanswerable_stock_price",
        category="Negative Controls",
        question="What is the current stock price of Apple Inc.?",
        expected_answer_keywords=["unable to find", "cannot find", "not available", "insufficient evidence", "no verified information"],
        expected_source_domain="mitaoe.ac.in",
        is_answerable=False,
        description="Financial equities question outside institutional scope.",
        expected_status="insufficient_evidence",
    ),
]
