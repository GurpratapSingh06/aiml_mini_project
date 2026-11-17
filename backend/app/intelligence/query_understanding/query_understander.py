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
    "SE": "Software Engineering",
    "DS": "Data Science",
    "ENTC": "Electronics and Telecommunication Engineering",
    "E&TC": "Electronics and Telecommunication Engineering",
    "ETC": "Electronics and Telecommunication Engineering",
    "MECH": "Mechanical Engineering",
    "ME": "Mechanical Engineering",
    "CIVIL": "Civil Engineering",
    "CHEM": "Chemical Engineering",
    "HOD": "Head of Department",
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
    "lpa", "package", "salary", "fee", "fees", "cost", "statistics",
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
    "where can i find", "where is", "department page", "which department",
    "which departments", "what departments", "available departments",
    "who heads", "who leads", "heads the", "leads the", "leading",
    "downloads", "download",
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
    # Semantic extraction extensions
    requested_intent_category: str = "general_factual"
    target_role: Optional[str] = None
    requested_attributes: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    expected_answer_type: str = "text"


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
    Prevents over-expansion of common English pronouns (me, it, be) while reliably
    handling departmental context (e.g. 'it department', 'who heads the it', 'HOD of CE').
    """
    abbrev_dict = abbrev_dict or ABBREVIATION_DICT
    result = text

    # Contextual patterns for ambiguous acronyms (works even if text is lowercase)
    context_patterns = {
        "IT": [
            r"\bIT\b",
            r"\bit\s+(?:dept|department|branch|school|engineering)\b",
            r"\b(?:heads?|leads?|hod of|head of)\s+(?:the\s+)?it\b",
        ],
        "CE": [
            r"\bCE\b",
            r"\bce\s+(?:dept|department|branch|school|engineering)\b",
            r"\b(?:heads?|leads?|hod of|head of)\s+(?:the\s+)?ce\b",
        ],
        "SE": [
            r"\bSE\b",
            r"\bse\s+(?:dept|department|branch|school|engineering)\b",
            r"\b(?:heads?|leads?|hod of|head of)\s+(?:the\s+)?se\b",
        ],
        "DS": [
            r"\bDS\b",
            r"\bds\s+(?:dept|department|branch|school|engineering)\b",
            r"\b(?:heads?|leads?|hod of|head of)\s+(?:the\s+)?ds\b",
        ],
        "ME": [
            r"\bME\b",
            r"\bme\s+(?:dept|department|branch|school|engineering)\b",
        ],
        "BE": [
            r"\bBE\b",
            r"\bbe\s+(?:degree|admission|students?|syllabus|curriculum)\b",
        ],
        "AY": [
            r"\bAY\b",
            r"\bay\s+(?:20\d{2})\b",
        ],
    }

    for abbrev, expansion in abbrev_dict.items():
        if expansion.lower() in result.lower():
            continue
        if abbrev in context_patterns:
            for pat in context_patterns[abbrev]:
                # If pattern matches, expand
                if re.search(pat, result, flags=0 if r"\b" + abbrev + r"\b" == pat else re.IGNORECASE):
                    result = re.sub(pat, lambda m: f"{m.group(0)} {expansion}", result, count=1, flags=0 if r"\b" + abbrev + r"\b" == pat else re.IGNORECASE)
                    break
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
    """Extract canonical department names from text, giving precedence to specialized sub-branches."""
    dept_mappings = [
        (r"computer\s+engineering\s*\(software\s+engineering\)|software\s+engineering|\bse\b", "Software Engineering"),
        (r"data\s+science|\bds\b", "Data Science"),
        (r"artificial\s+intelligence\s+(?:and|&)\s+machine\s+learning|ai\s*(?:and|&|/)\s*ml|\baiml\b", "Artificial Intelligence and Machine Learning"),
        (r"electronics\s+(?:and|&)\s+telecommunication|\bentc\b|\betc\b", "Electronics and Telecommunication Engineering"),
        (r"electronics\s+(?:and|&)\s+computer", "Electronics and Computer Engineering"),
        (r"information\s+technology|\bit\b", "Information Technology"),
        (r"computer\s+(?:science\s+(?:and|&)\s+)?engineering|\bcomp\b|\bce\b|\bcse\b", "Computer Engineering"),
        (r"mechanical\s+engineering|\bmech\b", "Mechanical Engineering"),
        (r"civil\s+engineering|\bcivil\b", "Civil Engineering"),
        (r"chemical\s+engineering|\bchem\b", "Chemical Engineering"),
        (r"humanities\s+(?:and|&)\s+engineering\s+sciences", "Humanities and Engineering Sciences"),
        (r"school\s+of\s+design|\bdesign\b", "School of Design"),
    ]
    found = []
    text_lower = text.lower()
    for pattern, canonical in dept_mappings:
        if re.search(pattern, text_lower):
            if canonical not in found:
                found.append(canonical)
    return found


def _has_kw(text: str, keywords) -> bool:
    """Match keyword using whole-word boundary check to prevent substring collisions (e.g. 'lpa' in 'kalpana')."""
    for kw in keywords:
        if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE):
            return True
    return False


def _classify_intent(query_lower: str) -> str:
    """Classify query intent using robust keyword rules with word-boundary isolation."""
    # 1. Comparison & ranking
    if _has_kw(query_lower, _COMPARISON_KEYWORDS) or \
       any(kw in query_lower for kw in ["which department has the highest", "which department has highest", "highest average package", "highest average"]):
        return "comparison"

    # 2. Specific calendar and academic year temporal queries
    if _has_kw(query_lower, ["calendar", "timetable", "time table", "schedule", "term i", "term 1", "term 2", "term ii", "difference between two academic years"]):
        return "temporal"

    # 3. Entity lookup (person, faculty, leadership, HOD, who is) — checked before generic statistical terms
    if _has_kw(query_lower, _ENTITY_LOOKUP_KEYWORDS) or \
       any(kw in query_lower for kw in ["who is", "who was", "previous hod", "former hod", "earlier hod", "who was the previous"]):
        return "entity_lookup"

    # 4. Placement and salary statistics
    if _has_kw(query_lower, ["placement", "package", "salary", "lpa", "ctc", "placed", "highest package", "average package", "placement statistics"]):
        return "statistical"

    # 5. Fee inquiries
    if _has_kw(query_lower, ["fee", "fees", "fee structure", "tuition"]):
        return "statistical"

    # 6. General statistical
    if _has_kw(query_lower, _STATISTICAL_KEYWORDS):
        return "statistical"

    # 7. General temporal
    if _has_kw(query_lower, _TEMPORAL_KEYWORDS):
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


def _analyze_query_semantics(
    raw_query: str,
    normalized: str,
    intent: str,
    departments: List[str],
    entities: List[ExtractedEntity],
) -> tuple[str, Optional[str], List[str], List[str], str]:
    """
    Extracts the semantic intent category, target role, requested attributes,
    required fields (for completeness validation), and expected answer type.
    """
    q_lower = normalized.lower()

    # 1. Vision and Mission
    has_vision = "vision" in q_lower
    has_mission = "mission" in q_lower
    if has_vision and has_mission:
        return (
            "vision_and_mission",
            None,
            ["vision", "mission"],
            ["vision_statement", "mission_statement"],
            "structured_sections",
        )
    elif has_vision:
        return (
            "institutional_vision",
            None,
            ["vision"],
            ["vision_statement"],
            "section_text",
        )
    elif has_mission:
        return (
            "institutional_mission",
            None,
            ["mission"],
            ["mission_statement"],
            "section_text",
        )

    # 2. Institutional Role Holder (e.g. "Who is the [role]?", "Who heads [department]?", "Who is the Chairman?")
    is_who_question = bool(re.search(r"\b(who\s+is|who\s+are|who\s+was|who\s+heads|who\s+leads|name\s+of\s+the|which\s+person)\b", q_lower))

    role_patterns = [
        (r"\b(director|principal|officiating\s+director)\b", "Director"),
        (r"\b(vice[\s\-]+chancellor|vc)\b", "Vice Chancellor"),
        (r"\b(chairman|chairperson)\b", "Chairman"),
        (r"\b(hod|head\s+of\s+department|head\s+of\s+the\s+department)\b", "Head of Department"),
        (r"\b(dean\s+academics?|dean\s+of\s+academics?)\b", "Dean Academics"),
        (r"\b(dean\s+student\s+affairs?)\b", "Dean Student Affairs"),
        (r"\b(dean\s+rd|dean\s+research)\b", "Dean Research"),
        (r"\b(dean\s+quality(?:\s+assurance)?)\b", "Dean Quality Assurance"),
        (r"\b(dean\s+branding(?:\s+and\s+communication)?)\b", "Dean Branding & Communication"),
        (r"\b(dean\s+of\s+[a-z]+|dean\s+[a-z]+)\b", None),  # Dynamically extracted
        (r"\b(dean)\b", "Dean"),
        (r"\b(registrar)\b", "Registrar"),
        (r"\b(trustee|treasurer)\b", "Trustee"),
        (r"\b(executive\s+president|president)\b", "President"),
        (r"\b(chief[\s\-]+financial[\s\-]+officer|cfo)\b", "Chief Financial Officer"),
        (r"\b(chief[\s\-]+executive[\s\-]+officer|ceo)\b", "Chief Executive Officer"),
        (r"\b(training\s+and\s+placement\s+officer|tpo)\b", "Training & Placement Officer"),
        (r"\b(controller\s+of\s+examinations?|coe)\b", "Controller of Examinations"),
    ]

    target_role = None
    for pattern, role_name in role_patterns:
        m = re.search(pattern, q_lower)
        if m:
            if role_name is None:
                # Capitalize extracted role phrase e.g. "Dean of Aeronautics"
                target_role = " ".join(w.capitalize() for w in m.group(0).split())
            else:
                target_role = role_name
            break

    # If asking "who heads [department]" without explicit HOD word
    if is_who_question and not target_role and (departments or "department" in q_lower or "school" in q_lower):
        if re.search(r"\b(who\s+heads?|who\s+leads?)\b", q_lower):
            target_role = "Head of Department"

    if is_who_question and target_role:
        return (
            "role_holder",
            target_role,
            ["person_name", "role", "department", "source"],
            ["person_name"],  # Essential required field: CANNOT be verified without person name!
            "person_name",
        )

    # 3. Faculty Profile / Attributes (asking about a specific person)
    has_person = any(e.entity_type == "person" for e in entities)
    if has_person or re.search(r"\bwho\s+is\s+(?:dr|prof|mr|mrs|ms)?\.?\s*[a-z]+", q_lower):
        req_attrs = ["person_name", "designation", "department"]
        if any(w in q_lower for w in ["qualification", "degree", "phd"]):
            req_attrs.append("qualification")
        if any(w in q_lower for w in ["email", "contact", "mail"]):
            req_attrs.append("email")
        if any(w in q_lower for w in ["research", "publication", "paper", "interest"]):
            req_attrs.append("research")
        return (
            "faculty_attribute",
            None,
            req_attrs,
            ["person_name", "designation"],
            "person_profile",
        )

    # 4. Fee Structure
    if any(w in q_lower for w in ["fee", "fees", "tuition", "cost", "deposit", "fra"]):
        return (
            "fee_structure",
            None,
            ["category", "tuition_fee", "total_fee", "academic_year"],
            ["total_fee", "academic_year"],
            "table",
        )

    # 5. Placement Statistics
    if any(w in q_lower for w in ["placement", "package", "salary", "lpa", "ctc", "placed", "recruiters"]):
        return (
            "placement_statistics",
            None,
            ["average_package", "highest_package", "department"],
            ["average_package"],
            "stats",
        )

    # 6. Academic Calendar & Timetables
    if any(w in q_lower for w in ["calendar", "timetable", "time table", "schedule", "commence", "exam", "vacation"]):
        return (
            "academic_calendar",
            None,
            ["event", "date_range", "academic_year"],
            ["event", "date_range"],
            "schedule",
        )

    # 7. Department Overview
    if departments or "department" in q_lower:
        return (
            "department_information",
            None,
            ["programs", "hod", "overview"],
            ["department_name"],
            "department_overview",
        )

    return (
        "general_factual",
        None,
        ["answer_text"],
        [],
        "text",
    )


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

        # Extract entities dynamically without hardcoded names
        entities = []
        try:
            from app.intelligence.entity_engine.identity_resolver import extract_person_name_from_query
            person_candidate = extract_person_name_from_query(raw_query)
            if person_candidate:
                canonical_name = person_candidate
                try:
                    from app.intelligence.knowledge_graph import get_knowledge_graph
                    kg = get_knowledge_graph()
                    matched_ent = kg.find_entity(person_candidate, entity_type="person")
                    if matched_ent:
                        canonical_name = matched_ent["canonical_name"]
                        meta = matched_ent.get("metadata", {})
                        expanded += f" {canonical_name} {meta.get('designation', '')}"
                except Exception as e:
                    logger.debug("KG entity linking skipped", error=str(e))

                entities.append(ExtractedEntity(
                    text=person_candidate,
                    entity_type="person",
                    normalized=canonical_name,
                    confidence=1.0,
                ))
        except Exception as e:
            logger.debug("Dynamic entity extraction error", error=str(e))

        # Additional regex for title-prefixed person names (e.g., Dr./Prof.)
        name_pattern = r"\b(?:Dr|Prof|Mr|Ms|Mrs|Shri|Smt)\.?\s+[A-Z][A-Za-z0-9\.\(\)]*(?:\s+[A-Z0-9][A-Za-z0-9\.\(\)]*)*"
        for match in re.finditer(name_pattern, raw_query):
            extracted = match.group(0).strip()
            existing_names = [e.normalized.lower() for e in entities]
            if extracted.lower() not in existing_names and not any(extracted.lower() in en for en in existing_names):
                entities.append(ExtractedEntity(
                    text=extracted,
                    entity_type="person",
                    normalized=extracted,
                ))

        # Department entities
        for dept in departments:
            entities.append(ExtractedEntity(
                text=dept,
                entity_type="department",
                normalized=dept,
            ))

        # Semantic intent and completeness requirements analysis
        cat, role, attrs, req_fields, ans_type = _analyze_query_semantics(
            raw_query, normalized, intent, departments, entities
        )

        logger.debug(
            "Query understood",
            intent=intent,
            category=cat,
            target_role=role,
            required_fields=req_fields,
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
            requested_intent_category=cat,
            target_role=role,
            requested_attributes=attrs,
            required_fields=req_fields,
            expected_answer_type=ans_type,
        )
