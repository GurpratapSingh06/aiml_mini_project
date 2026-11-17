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
    predicate: str  # e.g., "heads_department", "has_designation", "member_of", "contact_email", "contact_phone"
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

    # Comprehensive Department normalization mapping
    DEPT_NORMALIZATION = {
        "computer engineering (software engineering)": "Software Engineering",
        "cse (software engineering)": "Software Engineering",
        "software engineering": "Software Engineering",
        "software": "Software Engineering",
        "cse (data science)": "Data Science",
        "data science": "Data Science",
        "datasci": "Data Science",
        "cse (artificial intelligence & machine learning)": "Artificial Intelligence and Machine Learning",
        "cse (aiml)": "Artificial Intelligence and Machine Learning",
        "artificial intelligence and machine learning": "Artificial Intelligence and Machine Learning",
        "artificial intelligence & machine learning": "Artificial Intelligence and Machine Learning",
        "artificial intelligence": "Artificial Intelligence and Machine Learning",
        "aiml": "Artificial Intelligence and Machine Learning",
        "ai & ml": "Artificial Intelligence and Machine Learning",
        "ai and ml": "Artificial Intelligence and Machine Learning",
        "computer engineering": "Computer Engineering",
        "computer science & engineering": "Computer Science and Engineering",
        "computer science and engineering": "Computer Science and Engineering",
        "computer science": "Computer Science and Engineering",
        "cse": "Computer Science and Engineering",
        "comp": "Computer Engineering",
        "computer": "Computer Engineering",
        "ce": "Computer Engineering",
        "information technology": "Information Technology",
        "it": "Information Technology",
        "electronics and telecommunication": "Electronics and Telecommunication Engineering",
        "electronics & telecommunication": "Electronics and Telecommunication Engineering",
        "electronics and telecomminication": "Electronics and Telecommunication Engineering",
        "e&tc": "Electronics and Telecommunication Engineering",
        "entc": "Electronics and Telecommunication Engineering",
        "electronics and computer": "Electronics and Computer Engineering",
        "electronics": "Electronics and Telecommunication Engineering",
        "mechanical engineering": "Mechanical Engineering",
        "mechanical": "Mechanical Engineering",
        "mech": "Mechanical Engineering",
        "civil engineering": "Civil Engineering",
        "civil engineeringg": "Civil Engineering",
        "civil": "Civil Engineering",
        "chemical engineering": "Chemical Engineering",
        "chemical": "Chemical Engineering",
        "chem": "Chemical Engineering",
        "humanities and engineering sciences": "Humanities and Engineering Sciences",
        "humanities": "Humanities and Engineering Sciences",
        "school of design": "School of Design",
        "design": "School of Design",
        "first year": "First Year Engineering",
        "applied sciences": "First Year Engineering",
    }

    # Clean name regex
    NAME_PREFIX = r"(?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?|Shri|Smt\.?)"
    PERSON_NAME = r"(?:(?:" + NAME_PREFIX + r"\s+)?(?:[A-Z][A-Za-z0-9\.\(\)]*(?:\s+[A-Z0-9][A-Za-z0-9\.\(\)]*){1,4}))"

    # Contact info regexes
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@mitaoe\.(?:ac\.in|edu\.in)\b", re.IGNORECASE)
    PHONE_PATTERN = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}|\b020[\-\s]?\d{6,8}\b")

    def normalize_department(self, raw_dept: str) -> Optional[str]:
        if not raw_dept:
            return None
        cleaned = raw_dept.strip().lower()
        cleaned = re.sub(
            r"\b(department\s+of|dept\s+of|department|dept|school\s+of|school)\b",
            "",
            cleaned,
        ).strip()
        # Clean parenthetical or punctuation
        cleaned_simple = re.sub(r"[,\.:;\n\r]", " ", cleaned).strip()
        cleaned_simple = re.sub(r"\s+", " ", cleaned_simple)

        for key, canonical in self.DEPT_NORMALIZATION.items():
            if key in cleaned_simple:
                return canonical
        return raw_dept.strip().title() if len(raw_dept.strip()) > 2 else None

    def clean_name(self, raw_name: str) -> str:
        """Clean and normalize a person name."""
        name = re.sub(r"^\d+\s+", "", raw_name.strip())
        name = re.sub(r"\s+", " ", name).strip()
        # Truncate at sentence boundary if preceded by a word
        sentences = re.split(r"(?<=[a-z]{2})\.\s+", name)
        first_part = sentences[0] if sentences else name
        # Strip trailing connector words
        first_part = re.sub(r"\b(is\s+the|is|as|was|the|who)\b.*$", "", first_part, flags=re.IGNORECASE)
        first_part = re.sub(r"[,;:\.]$", "", first_part).strip()
        return first_part

    def extract_from_text(
        self,
        text: str,
        source_url: str = "",
        academic_year: Optional[str] = None,
    ) -> List[ExtractedFact]:
        """
        Extract structured institutional facts from raw crawled or document text.
        """
        facts: List[ExtractedFact] = []

        if not text or len(text.strip()) < 10:
            return facts

        clean_text = re.sub(r"\s+", " ", text).strip()

        # 1. HOD Card / Table / Listing Patterns
        # e.g., "Dr. P D Ganjewar , Associate Professor & HOD Computer Engineering"
        hod_pattern_1 = re.compile(
            r"((?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-Za-z0-9\.\(\)\s]+?)\s*(?:,|\s+Chairman|\s+Member)?\s*(?:(?:Associate|Sr\.\s+Assistant|Assistant)?\s*Professor)?\s*(?:and|&)?\s*(?:HOD|HoD|Head\s+of\s+(?:the\s+)?Department)\s*(?:of|,)?\s*([A-Za-z\s&–\(\)]+?)(?:,\s*Contact|,\s*Email|Contact|Email|Phone|\.|\n|$)",
            re.IGNORECASE,
        )
        for match in hod_pattern_1.finditer(clean_text):
            person = self.clean_name(match.group(1))
            dept_raw = match.group(2).strip()
            dept = self.normalize_department(dept_raw)
            if dept and person:
                facts.append(
                    ExtractedFact(
                        subject=person,
                        predicate="heads_department",
                        object_value=dept,
                        confidence=0.95,
                        source_url=source_url,
                        academic_year=academic_year,
                        designation="Head of Department",
                        department=dept,
                    )
                )

        # 2. "headed by <Name>" pattern
        # e.g. "Department of Computer Engineering at MITAOE is headed by Dr. Sandip A. Gade"
        headed_by_pattern = re.compile(
            r"(?:department\s+of\s+)?([A-Za-z\s&–\(\)]+?)(?:\s+at\s+MITAOE|\s+at\s+MIT\s+Academy\s+of\s+Engineering)?\s+is\s+headed\s+by\s+((?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-Za-z0-9\.\(\)\s]+?)(?:\.|\n|$)",
            re.IGNORECASE,
        )
        for match in headed_by_pattern.finditer(clean_text):
            dept_raw = match.group(1).strip()
            person = self.clean_name(match.group(2))
            dept = self.normalize_department(dept_raw)
            if dept and person:
                facts.append(
                    ExtractedFact(
                        subject=person,
                        predicate="heads_department",
                        object_value=dept,
                        confidence=0.92,
                        source_url=source_url,
                        academic_year=academic_year,
                        designation="Head of Department",
                        department=dept,
                    )
                )

        # 3. "<Name> is the Head of Department (HOD) for <Dept>"
        hod_for_pattern = re.compile(
            r"((?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-Za-z0-9\.\(\)\s]+?)\s+is\s+(?:the\s+)?Head\s+of\s+Department\s*(?:\(HOD\))?\s+(?:for|of)\s+([A-Za-z\s&–\(\)]+?)(?:\.|\n|$)",
            re.IGNORECASE,
        )
        for match in hod_for_pattern.finditer(clean_text):
            person = self.clean_name(match.group(1))
            dept_raw = match.group(2).strip()
            dept = self.normalize_department(dept_raw)
            if dept and person:
                facts.append(
                    ExtractedFact(
                        subject=person,
                        predicate="heads_department",
                        object_value=dept,
                        confidence=0.92,
                        source_url=source_url,
                        academic_year=academic_year,
                        designation="Head of Department",
                        department=dept,
                    )
                )

        # 4. Director / Officiating Director / Dean Patterns
        director_pattern = re.compile(
            r"((?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-Za-z0-9\.\(\)\s]+?)\s+(?:Chairman|Member\s+Secretary)?\s*,?\s*(Director|Officiating\s+Director|Deputy\s+Director|Dean)\s*,?\s*(?:MITAOE|MIT\s+Academy\s+of\s+Engineering|[A-Za-z\s&–\(\)]+)?(?:\.|\n|$)",
            re.IGNORECASE,
        )
        for match in director_pattern.finditer(clean_text):
            person = self.clean_name(match.group(1))
            role = match.group(2).strip()
            if person and len(person) > 4:
                facts.append(
                    ExtractedFact(
                        subject=person,
                        predicate="has_designation",
                        object_value=role.title(),
                        confidence=0.95,
                        source_url=source_url,
                        academic_year=academic_year,
                        designation=role.title(),
                        department="MITAOE Leadership",
                    )
                )

        # 5. Extract Academic Council Head of Departments
        # e.g., "Dr. Pramod Ganjewar Head of Departments, Head of Department, Computer Engineering"
        council_hod_pattern = re.compile(
            r"((?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\s+[A-Za-z0-9\.\(\)\s]+?)\s+Head\s+of\s+Departments?,\s+Head\s+of\s+Department,\s+([A-Za-z\s&–\(\)]+?)(?:Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?|\.|\n|$)",
            re.IGNORECASE,
        )
        for match in council_hod_pattern.finditer(clean_text):
            person = self.clean_name(match.group(1))
            dept_raw = match.group(2).strip()
            dept = self.normalize_department(dept_raw)
            if dept and person:
                facts.append(
                    ExtractedFact(
                        subject=person,
                        predicate="heads_department",
                        object_value=dept,
                        confidence=0.95,
                        source_url=source_url,
                        academic_year=academic_year,
                        designation="Head of Department",
                        department=dept,
                    )
                )

        # 6. Extract Contact Details
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
