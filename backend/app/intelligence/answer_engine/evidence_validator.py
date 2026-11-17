"""
VEDANTA — Evidence Validator
Validates and ranks retrieval evidence for answer generation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# Minimum score threshold for useful evidence (scaled for RRF where max score is ~0.033)
_MIN_EVIDENCE_SCORE = 0.005
_HIGH_CONFIDENCE_SCORE = 0.015


@dataclass
class ValidationResult:
    status: str  # verified | partially_verified | uncertain | insufficient_evidence | conflicting_sources
    validated_evidence: List[dict] = field(default_factory=list)
    confidence: float = 0.0
    conflicts: List[str] = field(default_factory=list)
    limitations: Optional[str] = None


class EvidenceValidator:
    """
    Validates retrieval results and determines answer confidence.
    """

    def validate(
        self,
        query_context,
        retrieval_results: List,
    ) -> ValidationResult:
        """
        Validate retrieval results and produce a ValidationResult.

        Args:
            query_context: QueryContext from query understanding
            retrieval_results: List of RetrievalResult objects
        """
        if not retrieval_results:
            return ValidationResult(
                status="insufficient_evidence",
                confidence=0.0,
                limitations="No relevant content was found in the indexed knowledge base.",
            )

        # Filter to meaningful results
        meaningful = [r for r in retrieval_results if r.score >= _MIN_EVIDENCE_SCORE]

        if not meaningful:
            return ValidationResult(
                status="insufficient_evidence",
                confidence=0.0,
                limitations=(
                    "Retrieved results did not meet minimum relevance threshold. "
                    "The knowledge base may not contain information about this topic."
                ),
            )

        # Lexical grounding check: ensure specific non-generic query tokens are grounded in top evidence
        framing_words = {
            "what", "who", "where", "when", "how", "why", "which", "is", "are", "the", "of", "at", "in", "on", "to", "from", "by", "with", "as", "for", "and", "a", "an",
            "can", "you", "tell", "me", "about", "mitaoe", "mit", "academy", "engineering", "hod", "head", "heads", "headed",
            "lead", "leads", "leading", "person", "department", "dept", "branch", "program", "course", "school",
            "fee", "fees", "structure", "tuition", "pune", "campus", "located", "current", "latest", "year", "academics",
            "institution", "official", "details", "find", "page", "url", "link", "show", "give", "available",
            "does", "do", "did", "have", "has", "had", "will", "would", "shall", "should", "may", "might"
        }
        if query_context and query_context.normalized_query:
            # Extract content words that are not purely question framing
            content_words = [
                w for w in re.findall(r"\b[a-zA-Z]{2,}\b", query_context.normalized_query.lower())
                if w not in framing_words and w.rstrip("s") not in framing_words
            ]
            if query_context.departments:
                for d in query_context.departments:
                    content_words.extend([w for w in d.lower().split() if w not in framing_words])
            content_words = list(dict.fromkeys(content_words))

            if content_words:
                all_text = " ".join(r.text.lower() for r in meaningful[:3])
                overlap = [w for w in content_words if w in all_text]
                overlap_ratio = len(overlap) / len(content_words) if content_words else 1.0
                # If distinct subject words are mostly absent or overlap ratio is too low (< 0.50)
                if overlap_ratio < 0.50:
                    return ValidationResult(
                        status="insufficient_evidence",
                        confidence=0.0,
                        limitations="No relevant evidence exists for this query in the institutional knowledge base.",
                    )

        # Strict Person Identity Isolation Check:
        # If the query requests a specific person, evidence MUST assert facts about that person.
        person_name = None
        if query_context and query_context.entities:
            for ent in query_context.entities:
                if ent.entity_type == "person":
                    person_name = ent.normalized
                    break

        if not person_name and query_context:
            from app.intelligence.entity_engine.identity_resolver import extract_person_name_from_query
            person_name = extract_person_name_from_query(query_context.raw_query)

        if person_name:
            from app.intelligence.entity_engine.identity_resolver import is_name_in_text
            person_matching = []
            for r in meaningful:
                is_in, _ = is_name_in_text(person_name, r.text)
                if is_in:
                    person_matching.append(r)

            if not person_matching:
                return ValidationResult(
                    status="insufficient_evidence",
                    confidence=0.0,
                    limitations=f"No verified institutional evidence found for requested identity: '{person_name}'.",
                )
            # Retain only chunks that discuss the requested person
            meaningful = person_matching

        # Convert to evidence dicts
        evidence_list = [
            {
                "chunk_id": r.chunk_id,
                "text": r.text,
                "source_url": r.source_url,
                "source_title": r.source_title,
                "page_number": r.page_number,
                "score": r.score,
                "retrieval_method": r.retrieval_method,
            }
            for r in meaningful
        ]

        # Detect potential conflicts (simple: check if multiple sources
        # mention different values for the same entity type)
        conflicts = self._detect_conflicts(query_context, evidence_list)

        # Determine confidence and status with strict Answer Completeness Validation
        top_score = meaningful[0].score
        num_sources = len(set(e["source_url"] for e in evidence_list if e["source_url"]))
        norm_score = min(1.0, top_score / 0.033) if top_score > 0 else 0.0

        # Check for outdated source condition
        is_current_requested = query_context and any(
            t in query_context.normalized_query.lower() for t in ["current", "latest", "active", "present", "now", "2026-27", "2026-2027"]
        )
        has_2026_evidence = any(
            "2026-27" in (e.get("academic_year") or "") or "2026-27" in e.get("text", "") or "2026-2027" in e.get("text", "")
            for e in evidence_list[:3]
        )
        is_outdated = is_current_requested and not has_2026_evidence and any(
            "2024-25" in e.get("text", "") or "2025-26" in e.get("text", "") for e in evidence_list[:3]
        )

        category = getattr(query_context, "requested_intent_category", "general_factual") if query_context else "general_factual"
        target_role = getattr(query_context, "target_role", None) if query_context else None
        required_fields = getattr(query_context, "required_fields", []) if query_context else []

        # --- COMPLETENESS VALIDATION: ROLE HOLDER ---
        if category == "role_holder" and target_role:
            from app.intelligence.entity_engine.identity_resolver import resolve_role_holder
            dept = query_context.departments[0] if (query_context and query_context.departments) else None
            role_holder = resolve_role_holder(target_role, dept, query_context.raw_query, evidence_list)
            if not role_holder or not role_holder.get("person_name"):
                return ValidationResult(
                    status="insufficient_evidence",
                    confidence=0.0,
                    limitations=f"No verified person holding the position of '{target_role}' could be confirmed in institutional records.",
                    validated_evidence=evidence_list,
                )
            # Person is verified
            status = "verified"
            confidence = 0.95
            limitations = None
            return ValidationResult(
                status=status,
                validated_evidence=evidence_list,
                confidence=round(confidence, 3),
                conflicts=conflicts,
                limitations=limitations,
            )

        # --- COMPLETENESS VALIDATION: VISION AND MISSION ---
        all_text_lower = " ".join(e.get("text", "").lower() for e in evidence_list)
        has_vision = ("to be a new age learning center" in all_text_lower) or ("vision" in all_text_lower and "holistic development" in all_text_lower)
        has_mission = ("providing new age infrastructural facilities" in all_text_lower) or ("mission" in all_text_lower and "lifelong learning" in all_text_lower)

        # If not present in retrieved evidence, check canonical about-mitaoe chunks in lookup
        if category in ["vision_and_mission", "institutional_vision", "institutional_mission"]:
            try:
                from app.retrieval.pipeline import get_retrieval_pipeline
                pipeline = get_retrieval_pipeline()
                for cid, chk in pipeline._chunk_lookup.items():
                    if "about-mitaoe" in chk.get("source_url", ""):
                        txt_l = chk.get("text", "").lower()
                        if "to be a new age learning center" in txt_l:
                            has_vision = True
                        if "providing new age infrastructural facilities" in txt_l or "lifelong learning" in txt_l:
                            has_mission = True
            except Exception:
                pass

        if category == "vision_and_mission":
            if has_vision and has_mission:
                status = "verified"
                confidence = 0.95
            elif has_vision or has_mission:
                status = "partially_verified"
                confidence = 0.70
            else:
                return ValidationResult(
                    status="insufficient_evidence",
                    confidence=0.0,
                    limitations="Institutional Vision and Mission statements were not found in the evidence.",
                    validated_evidence=evidence_list,
                )
            return ValidationResult(
                status=status,
                validated_evidence=evidence_list,
                confidence=round(confidence, 3),
                conflicts=conflicts,
                limitations=None,
            )

        if category == "institutional_vision":
            if has_vision:
                status = "verified"
                confidence = 0.95
            else:
                return ValidationResult(
                    status="insufficient_evidence",
                    confidence=0.0,
                    limitations="Institutional Vision statement was not found in the evidence.",
                    validated_evidence=evidence_list,
                )
            return ValidationResult(
                status=status,
                validated_evidence=evidence_list,
                confidence=round(confidence, 3),
                conflicts=conflicts,
                limitations=None,
            )

        if category == "institutional_mission":
            if has_mission:
                status = "verified"
                confidence = 0.95
            else:
                return ValidationResult(
                    status="insufficient_evidence",
                    confidence=0.0,
                    limitations="Institutional Mission statement was not found in the evidence.",
                    validated_evidence=evidence_list,
                )
            return ValidationResult(
                status=status,
                validated_evidence=evidence_list,
                confidence=round(confidence, 3),
                conflicts=conflicts,
                limitations=None,
            )

        # General status resolution
        if conflicts:
            status = "conflicting_sources"
            confidence = 0.4
        elif is_outdated:
            status = "outdated_source"
            confidence = 0.65
        elif top_score >= _HIGH_CONFIDENCE_SCORE and num_sources >= 2:
            status = "verified"
            confidence = min(0.96, 0.75 + 0.20 * norm_score)
        elif top_score >= _HIGH_CONFIDENCE_SCORE:
            status = "partially_verified"
            confidence = min(0.85, 0.60 + 0.20 * norm_score)
        elif top_score >= _MIN_EVIDENCE_SCORE:
            status = "uncertain"
            confidence = min(0.55, 0.35 + 0.15 * norm_score)
        else:
            status = "insufficient_evidence"
            confidence = 0.0

        limitations = None
        if conflicts:
            limitations = (
                "Multiple sources contain potentially conflicting information. "
                "Verify with the original sources linked below."
            )
        elif is_outdated:
            limitations = "The retrieved evidence is from a previous academic cycle and may not represent the current active year (2026-27)."
        elif num_sources == 1:
            limitations = "Information verified from a single source only."

        return ValidationResult(
            status=status,
            validated_evidence=evidence_list,
            confidence=round(confidence, 3),
            conflicts=conflicts,
            limitations=limitations,
        )

    def _detect_conflicts(self, query_context, evidence_list: List[dict]) -> List[str]:
        """
        Detect true conflicts in evidence (e.g., contradictory current HOD names for the same department from different sources).
        Distinguishes cross-department matches, co-listed faculty, or historical notes from true conflicting sources.
        """
        conflicts = []
        target_depts = query_context.departments if query_context else []
        query_text = query_context.normalized_query.lower() if query_context else ""

        is_leadership_query = any(k in query_text for k in ["hod", "head", "director", "dean"])

        if is_leadership_query and target_depts:
            dept = target_depts[0]
            leader_sources: dict[str, set[str]] = {}
            for ev in evidence_list[:5]:
                text = ev.get("text", "")
                src = ev.get("source_url") or "unknown"
                for line in text.split("\n"):
                    line_lower = line.lower()
                    if ("hod" in line_lower or "head" in line_lower or "headed by" in line_lower):
                        # Ensure line is about target department, not a different department
                        if dept.lower() in line_lower or "headed by" in line_lower:
                            # Avoid attributing other departments (e.g. Chemical) to Computer Engineering
                            other_depts = [
                                d.lower() for d in [
                                    "chemical", "civil", "mechanical", "information technology",
                                    "data science", "artificial intelligence", "software engineering"
                                ] if d.lower() != dept.lower()
                            ]
                            if any(od in line_lower for od in other_depts) and dept.lower() not in line_lower:
                                continue
                            matches = re.findall(
                                r"\b((?:Dr|Prof|Mr|Ms)\.?\s+[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)",
                                line,
                            )
                            for m in matches:
                                clean_name = m.strip().split(",")[0].strip()
                                if "historical" not in line_lower and "previously" not in line_lower:
                                    if clean_name not in leader_sources:
                                        leader_sources[clean_name] = set()
                                    leader_sources[clean_name].add(src)

            # A true conflict occurs when distinct, independent sources assert different leaders without co-listing
            if len(leader_sources) > 1:
                # Check if multiple distinct URLs contradict each other
                all_sources = set().union(*leader_sources.values())
                # If they all originate from the same page (e.g. co-listed Dean & HOD), it is not a conflicting source
                if len(all_sources) > 1:
                    conflicts.append(
                        f"Multiple current leaders identified for {dept} across different sources: {', '.join(leader_sources.keys())}. Please verify current appointment."
                    )

        return conflicts
