"""
VEDANTA — Answer Pipeline
Main orchestrator for the question-answering workflow.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.intelligence.query_understanding.query_understander import QueryUnderstander
from app.intelligence.answer_engine.evidence_validator import EvidenceValidator
from app.intelligence.answer_engine.answer_composer import AnswerComposer

logger = get_logger(__name__)

_understander = QueryUnderstander()
_validator = EvidenceValidator()
_composer = AnswerComposer()


def _query_cache_key(query: str, filters: dict = None) -> str:
    payload = json.dumps({"q": query.lower().strip(), "f": filters or {}}, sort_keys=True)
    return f"vedanta:query:{hashlib.md5(payload.encode()).hexdigest()}"


class AnswerPipeline:
    """
    Full question-answering pipeline.
    Query → Understanding → Retrieval → Validation → Composition → Response.
    """

    async def answer(
        self,
        query: str,
        top_k: int = 10,
        academic_year_filter: Optional[str] = None,
    ) -> dict:
        """
        Answer a natural language question.
        Returns a structured response dict.
        """
        t_start = time.perf_counter()

        # 1. Check Redis cache
        cache_key = _query_cache_key(query, {"ay": academic_year_filter})
        cached = await self._get_cache(cache_key)
        if cached:
            cached["cache_hit"] = True
            logger.info("Cache hit", query=query[:60])
            return cached

        # 2. Query understanding
        query_context = _understander.understand(query)
        logger.info(
            "Query understood",
            intent=query_context.intent,
            expanded=query_context.expanded_query[:80],
        )

        # 3. Retrieval
        retrieval_results = []
        try:
            from app.retrieval.pipeline import get_retrieval_pipeline
            pipeline = get_retrieval_pipeline()
            # Use expanded query for better recall
            search_query = query_context.expanded_query or query
            retrieval_results = pipeline.search(search_query, top_k=top_k)
        except Exception as e:
            logger.error("Retrieval failed", error=str(e))

        # 4. Evidence validation
        validation = _validator.validate(query_context, retrieval_results)

        # 5. Answer composition
        composed = _composer.compose(query_context, validation)

        # 6. Build response
        response = {
            "answer": composed.answer_text,
            "confidence": composed.confidence,
            "verification_status": composed.verification_status,
            "is_answerable": composed.is_answerable,
            "evidence": [
                {
                    "source_url": e.get("source_url", ""),
                    "source_title": e.get("source_title"),
                    "passage": e.get("passage", e.get("text", ""))[:500],
                    "page_number": e.get("page_number"),
                    "score": e.get("score", 0.0),
                    "academic_year": e.get("academic_year"),
                }
                for e in composed.cited_evidence
            ],
            "cache_hit": False,
            "limitations": composed.limitations,
            "suggested_queries": composed.suggested_queries,
            "query_intent": query_context.intent,
            "latency_ms": int((time.perf_counter() - t_start) * 1000),
        }

        # 7. Cache result
        await self._set_cache(cache_key, response, ttl=settings.cache_query_ttl)

        return response

    async def _get_cache(self, key: str) -> Optional[dict]:
        """Get a cached response from Redis."""
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.redis_url, decode_responses=True)
            value = await r.get(key)
            await r.aclose()
            if value:
                return json.loads(value)
        except Exception as e:
            logger.debug("Cache get failed", error=str(e))
        return None

    async def _set_cache(self, key: str, value: dict, ttl: int = 1800) -> None:
        """Store a response in Redis cache."""
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.redis_url, decode_responses=True)
            await r.set(key, json.dumps(value), ex=ttl)
            await r.aclose()
        except Exception as e:
            logger.debug("Cache set failed", error=str(e))
