"""
VEDANTA — Search and Question-Answer Endpoints
Core user-facing search and Q&A API.
"""

from __future__ import annotations

import time
import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ---- Request/Response Schemas ----------------------------

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000, description="Natural language question")
    institution_id: Optional[str] = Field(None, description="Institution UUID (defaults to MITAOE)")
    top_k: int = Field(10, ge=1, le=50, description="Number of results to return")
    include_evidence: bool = Field(True, description="Include source passages in response")
    academic_year: Optional[str] = Field(None, description="Filter by academic year e.g. 2024-25")


class SourceCitation(BaseModel):
    source_url: str
    source_title: Optional[str]
    page_number: Optional[int]
    passage: Optional[str]
    academic_year: Optional[str]
    retrieval_score: float
    retrieval_rank: int


class SearchResult(BaseModel):
    query_id: str
    query: str
    answer: str
    answer_confidence: float
    verification_status: str
    is_answerable: bool
    citations: List[SourceCitation]
    retrieval_latency_ms: int
    total_latency_ms: int
    cache_hit: bool
    limitations: Optional[str] = None
    suggested_queries: List[str] = []


class SearchSuggestion(BaseModel):
    suggestion: str
    category: str


# ---- Endpoints -------------------------------------------

@router.post("", response_model=SearchResult, summary="Search the knowledge base")
async def search(request: SearchRequest) -> SearchResult:
    """
    Submit a natural-language question and receive an evidence-backed answer.

    The system:
    1. Understands the query intent and extracts entities
    2. Searches indexed content using hybrid BM25 + semantic retrieval
    3. Ranks evidence using Reciprocal Rank Fusion
    4. Optionally reranks with a Cross-Encoder
    5. Validates evidence and composes an answer
    6. Returns citations with source URLs and page references
    """
    t_start = time.perf_counter()
    query_id = str(uuid.uuid4())

    logger.info("Search request received", query=request.query[:100], query_id=query_id)

    try:
        # Import retrieval pipeline
        from app.intelligence.answer_engine.pipeline import AnswerPipeline
        pipeline = AnswerPipeline()

        t_retrieval_start = time.perf_counter()
        result = await pipeline.answer(
            query=request.query,
            top_k=request.top_k,
            academic_year_filter=request.academic_year,
        )
        retrieval_latency_ms = int((time.perf_counter() - t_retrieval_start) * 1000)
        total_latency_ms = int((time.perf_counter() - t_start) * 1000)

        citations = [
            SourceCitation(
                source_url=e.get("source_url", ""),
                source_title=e.get("source_title"),
                page_number=e.get("page_number"),
                passage=e.get("passage") if request.include_evidence else None,
                academic_year=e.get("academic_year"),
                retrieval_score=e.get("score", 0.0),
                retrieval_rank=i + 1,
            )
            for i, e in enumerate(result.get("evidence", []))
        ]

        return SearchResult(
            query_id=query_id,
            query=request.query,
            answer=result.get("answer", ""),
            answer_confidence=result.get("confidence", 0.0),
            verification_status=result.get("verification_status", "uncertain"),
            is_answerable=result.get("is_answerable", True),
            citations=citations,
            retrieval_latency_ms=retrieval_latency_ms,
            total_latency_ms=total_latency_ms,
            cache_hit=result.get("cache_hit", False),
            limitations=result.get("limitations"),
            suggested_queries=result.get("suggested_queries", []),
        )

    except Exception as e:
        logger.error("Search failed", query=request.query[:100], error=str(e), exc_info=True)
        total_latency_ms = int((time.perf_counter() - t_start) * 1000)
        # Return graceful error response instead of 500
        return SearchResult(
            query_id=query_id,
            query=request.query,
            answer="I was unable to process your query at this time. Please try again.",
            answer_confidence=0.0,
            verification_status="insufficient_evidence",
            is_answerable=False,
            citations=[],
            retrieval_latency_ms=0,
            total_latency_ms=total_latency_ms,
            cache_hit=False,
            limitations=f"Search engine error: {str(e)}" if settings.is_development else "Internal error.",
        )


@router.get("/suggestions", response_model=List[SearchSuggestion], summary="Query suggestions")
async def get_suggestions(
    q: str = Query("", min_length=0, max_length=200, description="Partial query for suggestions"),
) -> List[SearchSuggestion]:
    """Return query suggestions for the search interface."""
    # Static suggestions for initial deployment — will become dynamic
    static_suggestions = [
        SearchSuggestion(suggestion="Who is the HOD of Computer Engineering?", category="faculty"),
        SearchSuggestion(suggestion="What is the fee structure for 2024-25?", category="fees"),
        SearchSuggestion(suggestion="Computer Engineering placement statistics 2024", category="placements"),
        SearchSuggestion(suggestion="Academic calendar 2024-25", category="academics"),
        SearchSuggestion(suggestion="Admission process for BE programs", category="admissions"),
        SearchSuggestion(suggestion="Faculty list for AIML department", category="faculty"),
        SearchSuggestion(suggestion="MITAOE NAAC accreditation grade", category="accreditation"),
        SearchSuggestion(suggestion="Student support and grievance cell", category="student_support"),
    ]

    if not q:
        return static_suggestions[:5]

    q_lower = q.lower()
    return [s for s in static_suggestions if q_lower in s.suggestion.lower()][:5]


@router.get("/history", summary="Recent queries")
async def get_query_history(
    limit: int = Query(10, ge=1, le=50),
) -> List[Dict[str, Any]]:
    """Return recent anonymized query history."""
    # Will query database in full implementation
    return []
