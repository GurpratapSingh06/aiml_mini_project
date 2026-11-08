"""
VEDANTA — Entity Intelligence Engine
Extracts institutional people, departments, designations, contacts, and councils.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedFact:
    subject: str
    predicate: str  # e.g., "head_of", "faculty_in", "dean_of", "member_of", "contact_email", "contact_phone"
    object_value: str
    confidence: float
    source_url: str
    academic_year: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EntityExtractor:
    """
    Rule-based and pattern-driven entity relationship extractor.
    Deterministic, auditable, and resilient to LLM hallucinations.
    """

    # Department normalization mapping
    DEPT_NORMALIZATION = {
        "computer": "Computer Engineering",
        "computer engineering": "Computer Engineering",
        "computer science": "Computer Science and Engineering",
        "cse": "Computer Science and Engineering",
        "aiml": "Artificial Intelligence and Machine Learning",
        "ai & ml": "Artificial Intelligence and Machine Learning",
        "information technology": "Information Technology",
        "it": "Information Technology",
        "entc": "Electronics and Telecommunication Engineering",
        "electronics": "Electronics and Telecommunication Engineering",
        "mechanical": "Mechanical Engineering",
        "mech": "Mechanical Engineering",
        "civil": "Civil Engineering",
        "first year": "First Year Engineering",
        "applied sciences": "First Year Engineering",
    }

    # HOD detection regexes
    HOD_PATTERNS = [
        re.compile(
            r"(?:head\s+of\s+(?:the\s+)?department|hod|head)\s*(?:of|:|-)?\s*([A-Za-z\s&]+?)(?:department)?\s*[:\-\u2013]\s*(?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:Dr\.?|Prof\.?)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)[,\s]+(?:Head\s+of\s+Department|HOD|Head)\s*(?:of|,)?\s*([A-Za-z\s&]+?)(?:Department|\.|$)",
            re.IGNORECASE,
        ),
    ]

    # Faculty & designation patterns
    FACULTY_PATTERNS = [
        re.compile(
            r"(?:Dr\.?|Prof\.?)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)[,\s]+(Professor|Associate\s+Professor|Assistant\s+Professor|Adjunct\s+Faculty|Dean|Director)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(Professor|Associate\s+Professor|Assistant\s+Professor)\s*[:\-\u2013]\s*(?:Dr\.?|Prof\.?)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            re.IGNORECASE,
        ),
    ]

    # Council & committee patterns
    COUNCIL_PATTERNS = [
        re.compile(
            r"(?:member|chairman|secretary|coordinator)\s*(?:of|:|-)?\s*([A-Za-z\s]+?(?:Council|Committee|Cell|Board))\s*[:\-\u2013]\s*(?:Dr\.?|Prof\.?|Mr\.?|Ms\.?)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            re.IGNORECASE,
        ),
    ]

    # Contact info regexes
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@mitaoe\.ac\.in\b", re.IGNORECASE)
    PHONE_PATTERN = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}|\b020[\-\s]?\d{8}\b")

    def normalize_department(self, raw_dept: str) -> Optional[str]:
        cleaned = raw_dept.strip().lower()
        cleaned = re.sub(r"\b(department\s+of|dept\s+of|department|dept|school\s+of)\b", "", cleaned).strip()
        for key, canonical in self.DEPT_NORMALIZATION.items():
            if key in cleaned:
                return canonical
        return raw_dept.strip().title() if len(raw_dept.strip()) > 2 else None

    def extract_from_text(self, text: str, source_url: str = "", academic_year: Optional[str] = None) -> List[ExtractedFact]:
        """
        Extract structured institutional facts from raw crawled or document text.
        """
        facts: List[ExtractedFact] = []

        if not text or len(text.strip()) < 10:
            return facts

        # 1. Extract HOD relationships
        for pattern in self.HOD_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) == 2:
                    val1, val2 = groups
                    # Check which group is person vs department
                    if any(title in val1.lower() for title in ["dr", "prof", "mr", "mrs", "ms"]):
                        person, dept_raw = val1.strip(), val2.strip()
                    else:
                        dept_raw, person = val1.strip(), val2.strip()

                    dept = self.normalize_department(dept_raw)
                    if dept and person:
                        facts.append(
                            ExtractedFact(
                                subject=f"Dr./Prof. {person}" if not person.startswith(("Dr", "Prof")) else person,
                                predicate="heads_department",
                                object_value=dept,
                                confidence=0.92,
                                source_url=source_url,
                                academic_year=academic_year,
                                designation="Head of Department",
                                department=dept,
                            )
                        )

        # 2. Extract Faculty and Designations
        for pattern in self.FACULTY_PATTERNS:
            for match in pattern.finditer(text):
                g1, g2 = match.groups()
                if any(desig in g1.lower() for desig in ["professor", "dean", "director"]):
                    desig, name = g1.strip(), g2.strip()
                else:
                    name, desig = g1.strip(), g2.strip()

                facts.append(
                    ExtractedFact(
                        subject=name,
                        predicate="has_designation",
                        object_value=desig.title(),
                        confidence=0.88,
                        source_url=source_url,
                        academic_year=academic_year,
                        designation=desig.title(),
                    )
                )

        # 3. Extract Committee / Academic Council Memberships
        for pattern in self.COUNCIL_PATTERNS:
            for match in pattern.finditer(text):
                council, name = match.groups()
                facts.append(
                    ExtractedFact(
                        subject=name.strip(),
                        predicate="member_of",
                        object_value=council.strip().title(),
                        confidence=0.85,
                        source_url=source_url,
                        academic_year=academic_year,
                    )
                )

        # 4. Extract Contact Details associated with nearby entities
        emails = self.EMAIL_PATTERN.findall(text)
        phones = self.PHONE_PATTERN.findall(text)

        for email in set(emails):
            facts.append(
                ExtractedFact(
                    subject="MITAOE Institution",
                    predicate="contact_email",
                    object_value=email.lower(),
                    confidence=0.95,
                    source_url=source_url,
                    academic_year=academic_year,
                )
            )

        for phone in set(phones):
            facts.append(
                ExtractedFact(
                    subject="MITAOE Institution",
                    predicate="contact_phone",
                    object_value=phone.strip(),
                    confidence=0.90,
                    source_url=source_url,
                    academic_year=academic_year,
                )
            )

        logger.debug("Entities extracted", facts_count=len(facts), source_url=source_url)
        return facts
