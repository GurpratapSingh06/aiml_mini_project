"""
VEDANTA — Answer Composer
Assembles evidence into structured, cited answers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# Related query suggestions per intent
_SUGGESTED_QUERIES = {
    "entity_lookup": [
        "What departments does MITAOE have?",
        "Who are the faculty members in Computer Engineering?",
        "MITAOE academic council members",
    ],
    "statistical": [
        "What is the average placement package at MITAOE?",
        "Compare placement statistics across departments",
        "MITAOE fee structure 2024-25",
    ],
    "factual": [
        "What programs does MITAOE offer?",
        "MITAOE NAAC accreditation",
        "MITAOE admission process",
    ],
    "temporal": [
        "Latest MITAOE academic calendar",
        "Current fee structure",
        "Recent placement report",
    ],
}


@dataclass
class ComposedAnswer:
    answer_text: str
    confidence: float
    is_answerable: bool
    verification_status: str
    cited_evidence: List[dict] = field(default_factory=list)
    suggested_queries: List[str] = field(default_factory=list)
    limitations: Optional[str] = None


class AnswerComposer:
    """
    Composes structured answers from validated evidence.
    Uses NLP extraction and templates — no generative LLM required.
    """

    def compose(
        self,
        query_context,
        validation,
    ) -> ComposedAnswer:
        """
        Compose an answer from query context and validation result.
        """
        # Insufficient evidence
        if validation.status == "insufficient_evidence":
            return ComposedAnswer(
                answer_text=self._insufficient_evidence_message(query_context),
                confidence=0.0,
                is_answerable=False,
                verification_status="insufficient_evidence",
                cited_evidence=[],
                suggested_queries=_SUGGESTED_QUERIES.get(
                    query_context.intent if query_context else "factual", []
                ),
                limitations=validation.limitations,
            )

        evidence = validation.validated_evidence
        if not evidence:
            return ComposedAnswer(
                answer_text="No relevant evidence was found.",
                confidence=0.0,
                is_answerable=False,
                verification_status="insufficient_evidence",
                cited_evidence=[],
            )

        # Choose answer strategy based on intent
        intent = query_context.intent if query_context else "factual"

        if intent == "statistical":
            answer_text = self._compose_statistical_answer(query_context, evidence)
        elif intent == "entity_lookup":
            answer_text = self._compose_entity_answer(query_context, evidence)
        elif intent == "comparison":
            answer_text = self._compose_comparison_answer(query_context, evidence)
        else:
            answer_text = self._compose_factual_answer(query_context, evidence)

        # Add conflict warning if needed
        if validation.conflicts:
            conflict_note = (
                "\n\n⚠️ **Note:** Multiple sources contain potentially conflicting information. "
                "Please verify with the linked sources."
            )
            answer_text += conflict_note

        # Format citations for display
        cited = [
            {
                "source_url": e.get("source_url", ""),
                "source_title": e.get("source_title", ""),
                "passage": e.get("text", "")[:300],
                "page_number": e.get("page_number"),
                "score": e.get("score", 0.0),
            }
            for e in evidence[:5]
        ]

        return ComposedAnswer(
            answer_text=answer_text,
            confidence=validation.confidence,
            is_answerable=True,
            verification_status=validation.status,
            cited_evidence=cited,
            suggested_queries=_SUGGESTED_QUERIES.get(intent, [])[:3],
            limitations=validation.limitations,
        )

    def _extract_key_sentence(self, text: str, query_tokens: List[str]) -> str:
        """Extract the most relevant sentence from a passage."""
        sentences = re.split(r"[.!?]\s+", text)
        if not sentences:
            return text[:300]

        # Score sentences by query token overlap
        scores = []
        for sent in sentences:
            sent_lower = sent.lower()
            overlap = sum(1 for t in query_tokens if t in sent_lower)
            scores.append((overlap, sent))

        scores.sort(reverse=True)
        best = scores[0][1] if scores else sentences[0]
        return best.strip()[:500]

    def _compose_factual_answer(self, query_context, evidence: List[dict]) -> str:
        """Compose a factual answer from the top evidence passage."""
        top = evidence[0]
        text = top.get("text", "")
        query_tokens = query_context.normalized_query.split() if query_context else []

        key_sentence = self._extract_key_sentence(text, query_tokens)

        source = top.get("source_title") or top.get("source_url", "")
        answer = key_sentence
        if source:
            answer += f"\n\n*Source: {source}*"

        return answer

    def _compose_entity_answer(self, query_context, evidence: List[dict]) -> str:
        """Compose an entity-focused answer (e.g., who is the HOD)."""
        top = evidence[0]
        text = top.get("text", "")

        # Try to extract person names
        name_pattern = r"\b(?:Dr|Prof|Mr|Ms|Mrs)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+"
        names = re.findall(name_pattern, text)

        query_tokens = query_context.normalized_query.split() if query_context else []
        key_sentence = self._extract_key_sentence(text, query_tokens)

        if names:
            answer = f"Based on indexed information: **{names[0]}**\n\n{key_sentence}"
        else:
            answer = key_sentence

        source = top.get("source_title") or top.get("source_url", "")
        if source:
            answer += f"\n\n*Source: {source}*"

        return answer

    def _compose_statistical_answer(self, query_context, evidence: List[dict]) -> str:
        """Compose a statistical answer with explicit provenance."""
        top = evidence[0]
        text = top.get("text", "")
        query_tokens = query_context.normalized_query.split() if query_context else []
        key_sentence = self._extract_key_sentence(text, query_tokens)

        lines = []
        lines.append(f"**Verified Institutional Intelligence:**\n{key_sentence}\n")

        # Extract numbers from evidence
        for ev in evidence[:3]:
            ev_text = ev.get("text", "")
            source = ev.get("source_title") or ev.get("source_url", "")

            # Look for LPA values
            lpa_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:LPA|lpa|lakhs?\s*per\s*annum)", ev_text)
            # Look for placement counts
            count_matches = re.findall(r"(\d+)\s+(?:students?|candidates?)\s+(?:placed|selected)", ev_text, re.I)
            # Look for fee figures
            fee_matches = re.findall(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", ev_text, re.I)

            if lpa_matches or count_matches or fee_matches:
                lines.append(f"**From:** {source}")
                if fee_matches:
                    lines.append(f"• Approved Fees: ₹ {', '.join(fee_matches)}")
                if lpa_matches:
                    lines.append(f"• Package figures: {', '.join(lpa_matches)} LPA")
                if count_matches:
                    lines.append(f"• Students placed: {', '.join(count_matches)}")
                lines.append("")

        lines.append(
            "\n> ⚠️ All numerical values are extracted directly from source documents. "
            "Verify with original sources for accuracy."
        )
        return "\n".join(lines)

    def _compose_comparison_answer(self, query_context, evidence: List[dict]) -> str:
        """Compose a comparison answer."""
        lines = ["**Comparison based on indexed sources:**\n"]

        for i, ev in enumerate(evidence[:4]):
            text = ev.get("text", "")
            source = ev.get("source_title") or ev.get("source_url", "")
            query_tokens = query_context.normalized_query.split() if query_context else []
            key_sent = self._extract_key_sentence(text, query_tokens)
            lines.append(f"{i+1}. {key_sent}")
            if source:
                lines.append(f"   *({source})*")
            lines.append("")

        return "\n".join(lines)

    def _insufficient_evidence_message(self, query_context) -> str:
        """Generate a helpful 'no information found' message."""
        query = query_context.raw_query if query_context else "your question"
        return (
            f"I was unable to find verified information about: *{query}*\n\n"
            "This may be because:\n"
            "- The relevant pages have not yet been crawled\n"
            "- The information exists in a document that has not been processed\n"
            "- The specific detail is not publicly available on the MITAOE website\n\n"
            "**Suggestion:** Try the official MITAOE website at https://mitaoe.ac.in "
            "or contact the relevant department directly."
        )
