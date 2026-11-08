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

        # Lexical grounding check: ensure at least one content token from query exists in top passage
        stopwords = {
            "what", "who", "is", "are", "the", "of", "at", "in", "for", "and", "a", "an",
            "can", "you", "tell", "me", "about", "mitaoe", "mit", "academy", "engineering"
        }
        if query_context and query_context.normalized_query:
            query_words = [
                w for w in re.findall(r"\b[a-zA-Z]{3,}\b", query_context.normalized_query.lower())
                if w not in stopwords
            ]
            if query_words:
                top_text = meaningful[0].text.lower()
                overlap = [w for w in query_words if w in top_text]
                if not overlap and getattr(meaningful[0], "semantic_score", 0.0) < 0.40:
                    return ValidationResult(
                        status="insufficient_evidence",
                        confidence=0.0,
                        limitations="No relevant evidence exists for this query in the institutional knowledge base.",
                    )

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

        # Determine confidence
        top_score = meaningful[0].score
        num_sources = len(set(e["source_url"] for e in evidence_list if e["source_url"]))

        norm_score = min(1.0, top_score / 0.033) if top_score > 0 else 0.0
        if conflicts:
            status = "conflicting_sources"
            confidence = 0.4
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
        Detect obvious conflicts in evidence (e.g., different HOD names).
        Returns list of conflict descriptions.
        """
        import re
        conflicts = []

        # Check for HOD/Head conflicts
        if query_context and "hod" in query_context.normalized_query.lower() or \
           (query_context and "head" in query_context.normalized_query.lower()):

            name_pattern = r"\b(?:Dr|Prof|Mr|Ms|Mrs)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*"
            names_found = set()

            for ev in evidence_list[:5]:  # Check top 5
                matches = re.findall(name_pattern, ev.get("text", ""))
                for name in matches:
                    names_found.add(name.strip())

            if len(names_found) > 2:
                conflicts.append(
                    f"Multiple person names found across sources: {', '.join(list(names_found)[:3])}. "
                    "Verify which is current."
                )

        return conflicts
