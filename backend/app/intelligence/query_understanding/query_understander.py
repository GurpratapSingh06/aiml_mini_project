"""
VEDANTA — Query Understanding Engine
Extracts intent, entities, and structure from natural language questions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# ---- Abbreviation Dictionary ----------------------------
ABBREVIATION_DICT = {
    "CE": "Computer Engineering",
    "CSE": "Computer Science and Engineering",
    "AIML": "Artificial Intelligence and Machine Learning",
    "AI&ML": "Artificial Intelligence and Machine Learning",
    "IT": "Information Technology",
    "ENTC": "Electronics and Telecommunication Engineering",
    "E&TC": "Electronics and Telecommunication Engineering",
    "ETC": "Electronics and Telecommunication Engineering",
    "MECH": "Mechanical Engineering",
    "ME": "Mechanical Engineering",
    "CIVIL": "Civil Engineering",
    "HOD": "Head of Department",
    "HoD": "Head of Department",
    "MIT": "MIT Academy of Engineering",
    "MITAOE": "MIT Academy of Engineering",
    "BE": "Bachelor of Engineering",
    "BTECH": "Bachelor of Technology",
    "MTECH": "Master of Technology",
    "MBA": "Master of Business Administration",
    "LPA": "Lakhs Per Annum",
    "AY": "Academic Year",
    "NAAC": "National Assessment and Accreditation Council",
    "NBA": "National Board of Accreditation",
    "AICTE": "All India Council for Technical Education",
    "UG": "Undergraduate",
    "PG": "Postgraduate",
    "PhD": "Doctor of Philosophy",
    "VC": "Vice Chancellor",
    "HOI": "Head of Institution",
    "DR": "Doctor",
    "PROF": "Professor",
    "ASST": "Assistant",
    "ASSOC": "Associate",
}

# ---- Intent Keywords ------------------------------------
_STATISTICAL_KEYWORDS = {
    "how many", "count", "total", "number of", "percentage", "percent",
    "average", "mean", "median", "highest", "lowest", "minimum", "maximum",
    "lpa", "package", "salary", "fee", "fees", "cost", "statistics", "data",
    "placed", "placement",
}

_TEMPORAL_KEYWORDS = {
    "current", "latest", "recent", "new", "updated", "this year", "now",
    "2024", "2025", "2026", "2023", "2022", "2021", "previous", "last year",
    "academic year", "ay", "semester",
}

_ENTITY_LOOKUP_KEYWORDS = {
    "who is", "who are", "name of", "contact", "email", "phone",
    "head of", "hod", "dean", "director", "principal", "faculty",
    "professor", "dr.", "prof.", "committee", "council",
}

_COMPARISON_KEYWORDS = {
    "compare", "comparison", "versus", " vs ", "difference between",
    "higher than", "lower than", "better than", "which is better",
}


@dataclass
class ExtractedEntity:
    text: str
    entity_type: str  # person, department, year, position, institution
    normalized: str = ""
    confidence: float = 1.0


@dataclass
class QueryContext:
    raw_query: str
    normalized_query: str
    intent: str  # factual | statistical | temporal | entity_lookup | comparison | unanswerable
    entities: List[ExtractedEntity] = field(default_factory=list)
    departments: List[str] = field(default_factory=list)
    temporal_refs: List[str] = field(default_factory=list)
    is_statistical: bool = False
    is_comparison: bool = False
    expanded_query: str = ""
    sub_queries: List[str] = field(default_factory=list)


def normalize_query(text: str) -> str:
    """Normalize query text for consistent processing."""
    # Expand contractions
    contractions = {
        "what's": "what is", "who's": "who is", "where's": "where is",
        "when's": "when is", "how's": "how is", "it's": "it is",
        "don't": "do not", "doesn't": "does not", "can't": "cannot",
        "won't": "will not", "isn't": "is not", "aren't": "are not",
    }
    text_lower = text.lower()
    for contraction, expansion in contractions.items():
        text_lower = text_lower.replace(contraction, expansion)

    # Remove excessive whitespace but preserve question mark
    text_lower = re.sub(r"\s+", " ", text_lower).strip()
    return text_lower


def expand_abbreviations(text: str, abbrev_dict: dict = None) -> str:
    """
    Expand abbreviations while preserving the original acronym for search recall.
    Prevents over-expansion of common English pronouns (me, it, be).
    """
    abbrev_dict = abbrev_dict or ABBREVIATION_DICT
    result = text

    # Words that must strictly match uppercase to avoid mangling English pronouns
    case_sensitive_acronyms = {"ME", "IT", "BE", "AY"}

    for abbrev, expansion in abbrev_dict.items():
        if abbrev in case_sensitive_acronyms:
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            # Append expansion alongside acronym: e.g. "ME Mechanical Engineering"
            result = re.sub(pattern, lambda m: f"{m.group(0)} {expansion}", result)
        else:
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            result = re.sub(pattern, lambda m: f"{m.group(0)} {expansion}", result, flags=re.IGNORECASE)

    return result


def _extract_academic_years(text: str) -> List[str]:
    """Extract academic year references from text."""
    patterns = [
        r"\b(20\d{2}[-–]\d{2,4})\b",
        r"\bAY\s+(20\d{2}[-–]\d{2,4})\b",
        r"\b(20\d{2})\b",
    ]
    years = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        years.extend(matches)

    # Also check for temporal keywords
    temporal_words = ["current", "latest", "recent", "this year", "last year", "previous"]
    for tw in temporal_words:
        if tw in text.lower():
            years.append(tw)

    return list(dict.fromkeys(years))  # deduplicate preserving order


def _extract_departments(text: str) -> List[str]:
    """Extract department names from text."""
    dept_patterns = [
        r"computer\s+engineering",
        r"computer\s+science\s+and\s+engineering",
        r"artificial\s+intelligence\s+and\s+machine\s+learning",
        r"information\s+technology",
        r"electronics\s+and\s+telecommunication",
        r"mechanical\s+engineering",
        r"civil\s+engineering",
        r"first\s+year",
    ]
    found = []
    for pattern in dept_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found.append(match.group(0).title())
    return found


def _classify_intent(query_lower: str) -> str:
    """Classify query intent using keyword rules."""
    # Check for comparison first (more specific)
    if any(kw in query_lower for kw in _COMPARISON_KEYWORDS):
        return "comparison"

    # Statistical queries
    if any(kw in query_lower for kw in _STATISTICAL_KEYWORDS):
        return "statistical"

    # Entity lookup
    if any(kw in query_lower for kw in _ENTITY_LOOKUP_KEYWORDS):
        return "entity_lookup"

    # Temporal
    if any(kw in query_lower for kw in _TEMPORAL_KEYWORDS):
        return "temporal"

    return "factual"


def _decompose_query(query: str) -> List[str]:
    """Split multi-part questions into sub-queries."""
    # Detect conjunction patterns
    conjunctions = [" and ", " & ", " also "]
    sub_queries = [query]

    for conj in conjunctions:
        new_parts = []
        for part in sub_queries:
            split = part.split(conj, 1)
            if len(split) > 1 and len(split[0]) > 10 and len(split[1]) > 10:
                new_parts.extend(split)
            else:
                new_parts.append(part)
        sub_queries = new_parts

    return [q.strip() for q in sub_queries if q.strip()] if len(sub_queries) > 1 else []


class QueryUnderstander:
    """
    Deterministic query understanding engine.
    No ML required — uses rule-based patterns for reliability.
    """

    def understand(self, query: str) -> QueryContext:
        """
        Process a natural language query and return a structured QueryContext.
        """
        if not query or not query.strip():
            return QueryContext(
                raw_query=query,
                normalized_query="",
                intent="unanswerable",
            )

        raw_query = query.strip()
        normalized = normalize_query(raw_query)
        expanded = expand_abbreviations(normalized)

        # Extract information
        departments = _extract_departments(expanded)
        temporal_refs = _extract_academic_years(expanded)
        is_statistical = any(kw in normalized for kw in _STATISTICAL_KEYWORDS)
        is_comparison = any(kw in normalized for kw in _COMPARISON_KEYWORDS)
        intent = _classify_intent(normalized)
        sub_queries = _decompose_query(raw_query)

        # Extract entities (simple pattern-based)
        entities = []

        # Person names (Dr./Prof. Title Case)
        name_pattern = r"\b(?:Dr|Prof|Mr|Ms|Mrs)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*"
        for match in re.finditer(name_pattern, raw_query):
            entities.append(ExtractedEntity(
                text=match.group(0),
                entity_type="person",
                normalized=match.group(0).strip(),
            ))

        # Department entities
        for dept in departments:
            entities.append(ExtractedEntity(
                text=dept,
                entity_type="department",
                normalized=dept,
            ))

        logger.debug(
            "Query understood",
            intent=intent,
            departments=departments,
            temporal_refs=temporal_refs,
            is_statistical=is_statistical,
        )

        return QueryContext(
            raw_query=raw_query,
            normalized_query=normalized,
            intent=intent,
            entities=entities,
            departments=departments,
            temporal_refs=temporal_refs,
            is_statistical=is_statistical,
            is_comparison=is_comparison,
            expanded_query=expanded,
            sub_queries=sub_queries,
        )
