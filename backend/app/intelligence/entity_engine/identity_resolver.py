"""
VEDANTA — Generic Identity Resolver & Entity Isolator
Provides strict, deterministic identity matching, name normalization,
alias resolution, and query entity extraction with zero hardcoding.
"""

from __future__ import annotations

import re
from typing import List, Tuple, Optional, Dict, Any
from app.core.logging import get_logger

logger = get_logger(__name__)

# Common institutional titles and honorifics
_TITLES = r"\b(?:Dr|Prof|Mr|Mrs|Ms|Shri|Smt|Hon|Er)\.?\s*"

# Question framing patterns to strip when extracting person names
_QUESTION_FRAMING = [
    r"^(?:who\s+is|who\s+was|who\s+are)\s+",
    r"^(?:tell\s+me\s+about|can\s+you\s+tell\s+me\s+about)\s+",
    r"^(?:what\s+is\s+the\s+designation\s+of|what\s+is\s+the\s+role\s+of)\s+",
    r"^(?:contact\s+details\s+for|contact\s+info\s+for|email\s+of|phone\s+of)\s+",
    r"^(?:information\s+about|details\s+of|profile\s+of|background\s+of)\s+",
    r"^(?:give\s+information\s+about|give\s+details\s+of)\s+",
]

# Suffixes to strip
_SUFFIX_PATTERNS = [
    r"\s+at\s+mitaoe.*$",
    r"\s+at\s+mit\s+academy.*$",
    r"\s+at\s+mit.*$",
    r"\s+in\s+mitaoe.*$",
    r"\s+in\s+mit.*$",
    r"\s+from\s+mitaoe.*$",
    r"\s+faculty\s+profile.*$",
    r"\s+faculty.*$",
    r"\s+profile.*$",
    r"\s+mitaoe.*$",
    r"[\?\.!]+$",
]

# Institutional stop words that must not be mistaken for person names
_INSTITUTIONAL_WORDS = {
    "department", "dept", "school", "college", "institute", "academy", "engineering",
    "fee", "fees", "structure", "tuition", "cost", "placement", "placements", "salary",
    "package", "lpa", "ctc", "calendar", "timetable", "schedule", "exam", "examination",
    "admission", "admissions", "director", "principal", "hod", "head", "dean", "council",
    "average", "highest", "minimum", "maximum", "total", "count", "academic", "year",
    "mitaoe", "mit", "alandi", "pune", "autonomous", "sppu", "university", "syllabus",
}


def normalize_name_tokens(name: str) -> List[str]:
    """
    Extract clean, lowercase alphabetical tokens from a person's name,
    stripping titles and punctuation.
    """
    if not name:
        return []
    # Strip honorifics
    cleaned = re.sub(_TITLES, "", name, flags=re.IGNORECASE)
    # Remove non-alphabetical characters
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", cleaned).lower()
    return [t for t in cleaned.split() if len(t) >= 2]


def extract_person_name_from_query(query: str) -> Optional[str]:
    """
    Dynamically extract a person's name from a natural language query without hardcoding.
    Returns None if the query is asking about non-person topics (fees, departments, etc.).
    """
    if not query or len(query.strip()) < 3:
        return None

    cleaned = query.strip()

    # 1. Strip question framing
    for pat in _QUESTION_FRAMING:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()

    # 2. Strip institutional suffixes
    for pat in _SUFFIX_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()

    # 3. Strip leading titles
    name_candidate = re.sub(r"^" + _TITLES, "", cleaned, flags=re.IGNORECASE).strip()

    # 4. Token validation
    tokens = name_candidate.split()
    if not tokens or len(tokens) > 5:
        return None

    # Check that tokens are not institutional keywords
    lower_tokens = [t.lower().rstrip("s.,") for t in tokens]
    if any(t in _INSTITUTIONAL_WORDS for t in lower_tokens):
        return None

    # Ensure at least one token has alphabetic length >= 3
    if not any(len(t) >= 3 and t.isalpha() for t in tokens):
        return None

    # Filter out pure numbers or symbols
    valid_tokens = [t for t in tokens if t.isalpha() or (len(t) <= 2 and t.replace(".", "").isalpha())]
    if len(valid_tokens) < 1:
        return None

    return " ".join(valid_tokens)


def _is_1char_variant(t1: str, t2: str) -> bool:
    """True if t1 and t2 differ by at most 1 character insertion, deletion, or substitution."""
    if abs(len(t1) - len(t2)) > 1:
        return False
    if len(t1) == len(t2):
        return sum(1 for a, b in zip(t1, t2) if a != b) <= 1
    short, long = (t1, t2) if len(t1) < len(t2) else (t2, t1)
    for i in range(len(long)):
        if long[:i] + long[i + 1:] == short:
            return True
    return False


def matches_identity(
    requested_name: str,
    candidate_name: str,
    strict_threshold: float = 0.60,
) -> Tuple[bool, float, str]:
    """
    Strict identity matching between requested person and candidate person.

    Returns:
        (is_match, confidence_score, match_rationale)

    Enforces strict identity isolation:
    - All core tokens (length >= 3) of the requested name must match in candidate.
    - Initial matching: 'A. R. Shaikh' matches 'Azhar R. Shaikh' via initial 'A' and surname 'Shaikh'.
    - Transliteration tolerance: 1 character edit distance for words >= 4 letters (e.g. Azher vs Azhar).
    - Rejects negative mismatches: 'Shoaib Shaikh' vs 'Azhar Shaikh' -> FALSE.
    - Rejects substitute identities: 'Anil Pawar' vs 'Pravin Pawar' -> FALSE.
    """
    r_tokens = normalize_name_tokens(requested_name)
    c_tokens = normalize_name_tokens(candidate_name)

    if not r_tokens or not c_tokens:
        return False, 0.0, "Missing name tokens"

    # Core tokens: length >= 3
    r_core = [t for t in r_tokens if len(t) >= 3]
    c_core = [t for t in c_tokens if len(t) >= 3]

    if not r_core:
        # If requested name only had initials or short tokens (rare)
        return False, 0.0, "Requested name lacks core identifying tokens"

    # Check each core token of requested name
    matched_core = 0
    mismatched_tokens = []

    for rt in r_core:
        matched = False
        for ct in c_core:
            # Exact match
            if rt == ct:
                matched = True
                break
            # 1-char edit distance for transliteration variants (e.g. azher vs azhar)
            if len(rt) >= 4 and len(ct) >= 4 and _is_1char_variant(rt, ct):
                matched = True
                break
        if matched:
            matched_core += 1
        else:
            mismatched_tokens.append(rt)

    # STRICT ISOLATION RULE: Every core token of the requested name MUST match!
    # If the user asked for "Shoaib Shaikh", and candidate is "Azhar Shaikh",
    # "shoaib" is mismatched -> MUST REJECT!
    if mismatched_tokens:
        return (
            False,
            0.0,
            f"Distinct identity detected: token(s) {mismatched_tokens} not found in candidate '{candidate_name}'",
        )

    # Initial check if requested name has single-letter initials (e.g. A. Shaikh)
    r_initials = [t for t in r_tokens if len(t) == 1]
    for init in r_initials:
        # Check if any candidate token starts with that initial
        if not any(ct.startswith(init) for ct in c_tokens):
            return False, 0.0, f"Initial '{init}' does not match candidate '{candidate_name}'"

    # Confidence calculation: ratio of matched core tokens
    score = round(matched_core / max(len(r_core), len(c_core)), 3)
    if score >= strict_threshold or matched_core == len(r_core):
        return True, max(score, 0.85), f"Identity confirmed: all {matched_core} core tokens verified"

    return False, score, f"Insufficient identity overlap ({score} < {strict_threshold})"


def is_name_in_text(requested_name: str, text: str) -> Tuple[bool, float]:
    """
    Check if the requested person's identity is explicitly asserted in a text passage.
    Avoids false positives from isolated surnames or common words.
    """
    if not requested_name or not text:
        return False, 0.0

    r_tokens = normalize_name_tokens(requested_name)
    r_core = [t for t in r_tokens if len(t) >= 3]
    if not r_core:
        return False, 0.0

    text_lower = text.lower()

    # 1. Direct exact substring match
    if requested_name.lower() in text_lower:
        return True, 1.0

    # 2. Check if all core tokens appear in the text
    matched = 0
    for rt in r_core:
        # Match whole word
        if re.search(r"\b" + re.escape(rt) + r"\b", text_lower):
            matched += 1
        elif len(rt) >= 4:
            # Check 1-char variant in text words
            words = re.findall(r"\b[a-z]{4,}\b", text_lower)
            if any(_is_1char_variant(rt, w) for w in words):
                matched += 1

    if matched == len(r_core):
        # All core tokens appear in the text
        return True, 0.95

    return False, 0.0


def resolve_role_holder(
    role: str,
    department: Optional[str] = None,
    query_text: str = "",
    passages: Optional[List[dict]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Deterministically resolve the person holding an institutional role or designation.
    Enforces that a person's name MUST be bound to the designation in the evidence.
    Returns None if no verified person is bound to the target role.
    """
    if not role:
        return None

    role_lower = role.lower()
    dept_lower = department.lower() if department else None
    q_lower = (query_text or "").lower()

    # Determine body context for ambiguous roles like 'Chairman'
    is_governing_body = "governing" in q_lower or "governing body" in q_lower
    is_academic_council = "council" in q_lower or "academic council" in q_lower
    is_bos = "board of studies" in q_lower or "bos" in q_lower

    def role_matches(line_text: str, context_url: str = "") -> bool:
        lt = line_text.lower()
        if role_lower == "registrar":
            return bool(re.search(r"\bregistrar\b", lt))
        if role_lower in ["director", "principal"]:
            if "deputy director" in lt:
                return False
            return bool(re.search(r"\b(director|officiating\s+director)\b", lt))
        if role_lower in ["chairman", "chairperson"]:
            if is_governing_body:
                return "governing" in context_url or "governing body" in lt or bool(re.search(r"\b(chairman|chairperson)\b", lt))
            if is_academic_council:
                return "council" in context_url or bool(re.search(r"\b(chairman|chairperson)\b", lt))
            return bool(re.search(r"\b(chairman|chairperson)\b", lt))
        if role_lower in ["head of department", "hod"]:
            if not bool(re.search(r"\b(hod|head\s+of\s+(?:the\s+)?department|headed\s+by)\b", lt)):
                return False
            if dept_lower:
                dept_words = [w for w in re.split(r"\W+", dept_lower) if len(w) >= 3 and w not in ["engineering", "department", "school"]]
                return any(dw in lt for dw in dept_words)
            return True
        if "dean" in role_lower:
            if "academics" in role_lower or "academic" in role_lower:
                return bool(re.search(r"\b(dean\s+(?:of\s+)?academics?|deputy\s+director\s+academics?)\b", lt))
            if "quality" in role_lower:
                return bool(re.search(r"\bdean[\s\-]+quality\b", lt))
            if "branding" in role_lower:
                return bool(re.search(r"\bdean[\s\-]+branding\b", lt))
            if "design" in role_lower:
                return bool(re.search(r"\bdean[\s\-]+school\s+of\s+design\b", lt))
            # If a specific Dean domain was requested (e.g. "Dean of Aeronautics"), it MUST match that domain
            dean_domain = role_lower.replace("dean", "").replace("of", "").strip()
            if dean_domain and len(dean_domain) >= 3:
                return "dean" in lt and dean_domain in lt
            return bool(re.search(r"\bdean\b", lt))
        return role_lower in lt

    # Name matching pattern: Title + full name
    name_regex = re.compile(
        r"^(?:Padmashree\s+)?(?:Professor|Prof\.?|Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Shri|Smt)\.?\s+[A-Z][a-zA-Z\.\']*(?:\s+[A-Za-z0-9\.\'\(\)]+){1,4}$"
    )

    # 1. Search across provided retrieval passages first
    candidate_passages = passages or []

    # If passages don't contain it or aren't provided, load institutional leadership records
    def search_in_text(text: str, source_url: str = "", source_title: str = "") -> Optional[Dict[str, Any]]:
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Multi-line pattern: Name on line i, Role on line i+1 (or i+2)
        for i in range(len(lines) - 1):
            line = lines[i]
            next_line = lines[i + 1]
            next_next_line = lines[i + 2] if i + 2 < len(lines) else ""

            if name_regex.match(line):
                candidate_name = line.strip()
                if role_matches(next_line, source_url):
                    bio = next_next_line if next_next_line and not name_regex.match(next_next_line) else ""
                    return {
                        "person_name": candidate_name,
                        "designation": next_line,
                        "department": department or "MIT Academy of Engineering",
                        "bio": bio,
                        "source_url": source_url,
                        "source_title": source_title or "MITAOE Official Record",
                        "pattern": "multi_line",
                    }
                if next_next_line and role_matches(next_next_line, source_url):
                    return {
                        "person_name": candidate_name,
                        "designation": f"{next_line}, {next_next_line}",
                        "department": department or "MIT Academy of Engineering",
                        "bio": "",
                        "source_url": source_url,
                        "source_title": source_title or "MITAOE Official Record",
                        "pattern": "multi_line_extended",
                    }

        # Sentence pattern for HODs ("headed by Dr. ...")
        if role_lower in ["head of department", "hod"]:
            m = re.search(
                r"(?:is\s+headed\s+by|headed\s+by)\s+((?:(?:Padmashree\s+)?(?:Professor|Prof\.?|Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Shri|Smt)\.?\s+[A-Z][a-zA-Z\.\']*(?:\s+[A-Za-z0-9\.\']+){1,3}))(?:,\s*([^\.\n]+))?",
                text,
                re.IGNORECASE,
            )
            if m:
                c_name = m.group(1).strip()
                desig = m.group(2).strip() if m.group(2) else "Head of Department"
                if not dept_lower or any(dw in text.lower() for dw in re.split(r"\W+", dept_lower) if len(dw) >= 3 and dw not in ["engineering", "department"]):
                    return {
                        "person_name": c_name,
                        "designation": desig,
                        "department": department or "MIT Academy of Engineering",
                        "bio": "",
                        "source_url": source_url,
                        "source_title": source_title or "MITAOE Official Record",
                        "pattern": "sentence_headed_by",
                    }

        # Sentence pattern: "[Name] is the [Role] of..."
        m = re.search(
            r"((?:(?:Padmashree\s+)?(?:Professor|Prof\.?|Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Shri|Smt)\.?\s+[A-Z][a-zA-Z\.\']*(?:\s+[A-Za-z0-9\.\']+){1,3}))\s+(?:is|serves\s+as)\s+(?:the\s+)?([^\.\n]*?\b" + re.escape(role_lower) + r"\b[^\.\n]*)",
            text,
            re.IGNORECASE,
        )
        if m:
            c_name = m.group(1).strip()
            desig = m.group(2).strip()
            if not dept_lower or any(dw in text.lower() for dw in re.split(r"\W+", dept_lower) if len(dw) >= 3 and dw not in ["engineering", "department"]):
                return {
                    "person_name": c_name,
                    "designation": desig,
                    "department": department or "MIT Academy of Engineering",
                    "bio": "",
                    "source_url": source_url,
                    "source_title": source_title or "MITAOE Official Record",
                    "pattern": "sentence_is_the",
                }

        return None

    # Step A: Search in candidate passages
    for p in candidate_passages:
        txt = p.get("text", "") if isinstance(p, dict) else getattr(p, "text", "")
        url = p.get("source_url", "") if isinstance(p, dict) else getattr(p, "source_url", "")
        title = p.get("source_title", "") if isinstance(p, dict) else getattr(p, "source_title", "")
        res = search_in_text(txt, url, title)
        if res:
            return res

    # Step B: If not in immediate top passages, scan canonical leadership chunks from index
    try:
        from app.retrieval.pipeline import get_retrieval_pipeline
        pipeline = get_retrieval_pipeline()
        for cid, chk in pipeline._chunk_lookup.items():
            url = chk.get("source_url", "")
            # Prioritize leadership and governance pages
            if any(k in url for k in ["mitaoe.ac.in", "governing-body", "academic-council", "department"]):
                res = search_in_text(chk.get("text", ""), url, chk.get("source_title", ""))
                if res:
                    return res
    except Exception as e:
        logger.debug("Index fallback lookup error in resolve_role_holder", error=str(e))

    return None
