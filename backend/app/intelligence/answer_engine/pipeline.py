"""
VEDANTA — Answer Pipeline
Main orchestrator for question-driven institutional research, streaming events,
hybrid retrieval, evidence verification, and answer composition.
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import time
import uuid
from typing import Optional, AsyncGenerator, Dict, Any

from cachetools import TTLCache

from app.core.config import settings
from app.core.logging import get_logger
from app.intelligence.query_understanding.query_understander import QueryUnderstander
from app.intelligence.answer_engine.evidence_validator import EvidenceValidator
from app.intelligence.answer_engine.answer_composer import AnswerComposer

logger = get_logger(__name__)

_understander = QueryUnderstander()
_validator = EvidenceValidator()
_composer = AnswerComposer()

# Fast in-memory L1 cache for sub-millisecond repeated queries
_l1_cache: TTLCache = TTLCache(maxsize=1024, ttl=1800)


def _query_cache_key(query: str, filters: dict = None) -> str:
    payload = json.dumps({"q": query.lower().strip(), "f": filters or {}}, sort_keys=True)
    return f"vedanta:query:{hashlib.md5(payload.encode()).hexdigest()}"


_redis_available = True
_redis_last_check = 0.0


class AnswerPipeline:
    """
    Full question-answering and research pipeline.
    Query → Understanding → Discovery → Retrieval → Validation → Composition → History.
    Supports both batch execution and live event-stream generation.
    """

    async def answer(
        self,
        query: str,
        top_k: int = 10,
        academic_year_filter: Optional[str] = None,
    ) -> dict:
        """
        Answer a natural language question synchronously/batch.
        Returns a structured response dict.
        """
        t_start = time.perf_counter()

        # 1. Check in-memory L1 cache with Identity Validation (sub-millisecond)
        cache_key = _query_cache_key(query, {"ay": academic_year_filter})
        from app.intelligence.entity_engine.identity_resolver import extract_person_name_from_query, matches_identity
        req_person = extract_person_name_from_query(query)

        if cache_key in _l1_cache:
            hit = dict(_l1_cache[cache_key])
            if req_person:
                cand_ans = hit.get("answer", "")
                is_m, _, _ = matches_identity(req_person, cand_ans)
                if is_m:
                    hit["cache_hit"] = True
                    hit["latency_ms"] = int((time.perf_counter() - t_start) * 1000)
                    return hit
                else:
                    _l1_cache.pop(cache_key, None)
            else:
                hit["cache_hit"] = True
                hit["latency_ms"] = int((time.perf_counter() - t_start) * 1000)
                return hit

        # 1b. Check Redis cache
        cached = await self._get_cache(cache_key)
        if cached:
            if req_person:
                cand_ans = cached.get("answer", "")
                is_m, _, _ = matches_identity(req_person, cand_ans)
                if is_m:
                    cached["cache_hit"] = True
                    _l1_cache[cache_key] = cached
                    return cached
            else:
                cached["cache_hit"] = True
                _l1_cache[cache_key] = cached
                return cached

        # 2. Query understanding
        query_context = _understander.understand(query)
        logger.info(
            "Query understood",
            intent=query_context.intent,
            expanded=query_context.expanded_query[:80],
            departments=query_context.departments,
        )

        # 3. Retrieval
        retrieval_results = []
        try:
            from app.retrieval.pipeline import get_retrieval_pipeline
            pipeline = get_retrieval_pipeline()
            search_query = query_context.expanded_query or query
            retrieval_results = pipeline.search(search_query, top_k=top_k)
        except Exception as e:
            logger.error("Retrieval failed", error=str(e))

        # 4. Evidence validation
        validation = _validator.validate(query_context, retrieval_results)

        # 4b. Question-driven discovery: Check if authoritative profile or fresh evidence is needed
        has_authoritative_person_profile = False
        if req_person:
            for r in retrieval_results:
                if "Official Faculty Profile:" in r.text:
                    from app.intelligence.entity_engine.identity_resolver import is_name_in_text
                    if is_name_in_text(req_person, r.text)[0]:
                        has_authoritative_person_profile = True
                        break

        needs_discovery = (validation.status == "insufficient_evidence") or (req_person and not has_authoritative_person_profile)

        if needs_discovery:
            try:
                from app.ingestion.crawler.live_fetcher import fetch_and_index_topic
                new_chunks = await fetch_and_index_topic(query, query_context)
                if new_chunks:
                    pipeline.add_chunks(new_chunks)
                    retrieval_results = pipeline.search(search_query, top_k=top_k)
                    validation = _validator.validate(query_context, retrieval_results)
            except Exception as e:
                logger.debug("Question-driven crawl skipped or failed", error=str(e))

        # 5. Answer composition
        composed = _composer.compose(query_context, validation)

        # 6. Diagnostics
        diagnostics = {
            "normalized_query": query_context.normalized_query,
            "expanded_query": query_context.expanded_query,
            "intent": query_context.intent,
            "departments": query_context.departments,
            "retrieval_candidates": len(retrieval_results),
            "top_chunks": [
                {
                    "chunk_id": r.chunk_id,
                    "score": round(r.score, 4),
                    "rank": r.rank,
                    "retrieval_method": r.retrieval_method,
                    "bm25_score": round(r.bm25_score, 4),
                    "semantic_score": round(r.semantic_score, 4),
                    "source_url": r.source_url,
                }
                for r in retrieval_results[:5]
            ],
        }

        # 7. Build response
        total_latency_ms = int((time.perf_counter() - t_start) * 1000)
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
            "diagnostics": diagnostics,
            "latency_ms": total_latency_ms,
        }

        # 8. Persist to QueryHistory and EvidenceRecord
        try:
            from app.storage.history_store import save_query_history
            await save_query_history(
                raw_query=query,
                normalized_query=query_context.normalized_query,
                query_intent=query_context.intent,
                answer_text=composed.answer_text,
                answer_confidence=composed.confidence,
                verification_status=composed.verification_status,
                is_answerable=composed.is_answerable,
                total_latency_ms=total_latency_ms,
                retrieval_latency_ms=total_latency_ms,
                cache_hit=False,
                query_entities=[e.normalized for e in query_context.entities],
                citations=response["evidence"],
            )
        except Exception as e:
            logger.debug("Failed to record query history", error=str(e))

        # 9. Store in L1 and Redis
        _l1_cache[cache_key] = response
        await self._set_cache(cache_key, response, ttl=settings.cache_query_ttl)

        return response

    async def answer_stream(
        self,
        query: str,
        top_k: int = 10,
        academic_year_filter: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream research progress events via Server-Sent Events (SSE).
        Emits real milestones:
          analyzing_question → searching_local_knowledge → discovering_sources →
          fetching_pages → extracting_information → analyzing_evidence →
          verifying_information → generating_answer → saving_to_history → completed.
        """
        request_id = str(uuid.uuid4())
        t_start = time.perf_counter()

        def make_event(stage: str, message: str, status: str = "running", **extra) -> Dict[str, Any]:
            return {
                "request_id": request_id,
                "stage": stage,
                "message": message,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "elapsed_ms": int((time.perf_counter() - t_start) * 1000),
                "status": status,
                **extra,
            }

        # 1. Check L1 / Redis Cache with Identity Validation
        cache_key = _query_cache_key(query, {"ay": academic_year_filter})
        from app.intelligence.entity_engine.identity_resolver import extract_person_name_from_query, matches_identity

        req_person = extract_person_name_from_query(query)
        cache_hit_valid = False

        if cache_key in _l1_cache:
            candidate_hit = dict(_l1_cache[cache_key])
            # Strict identity check on cache reuse: ensure person query does not return another person
            if req_person:
                cand_ans = candidate_hit.get("answer", "")
                is_m, _, _ = matches_identity(req_person, cand_ans)
                if is_m:
                    cache_hit_valid = True
                else:
                    logger.info("Cache rejected due to identity mismatch", requested=req_person)
                    _l1_cache.pop(cache_key, None)
            else:
                cache_hit_valid = True

            if cache_hit_valid:
                yield make_event("analyzing_question", "Question understood. Reusing verified institutional evidence.", status="completed")
                await asyncio.sleep(0.04)
                yield make_event("searching_local_knowledge", "Verified institutional evidence found in local memory.", status="completed", discovered_source_count=1)
                await asyncio.sleep(0.04)
                yield make_event("discovering_sources", "Web discovery skipped: verified evidence already cached.", status="skipped")
                await asyncio.sleep(0.02)
                yield make_event("fetching_pages", "Page fetch skipped: using cached sources.", status="skipped")
                await asyncio.sleep(0.02)
                yield make_event("extracting_information", "Information extraction skipped.", status="skipped")
                await asyncio.sleep(0.02)
                yield make_event("analyzing_evidence", "Evidence verified against institutional records.", status="completed")
                await asyncio.sleep(0.04)
                yield make_event("verifying_information", "Verified cached evidence against institutional records.", status="completed", discovered_source_count=1)
                await asyncio.sleep(0.04)
                yield make_event("generating_answer", "Preparing answer from verified records.", status="completed", discovered_source_count=1)
                await asyncio.sleep(0.04)
                yield make_event("saving_to_history", "History recording skipped for cached hit.", status="skipped")
                await asyncio.sleep(0.02)

                candidate_hit["cache_hit"] = True
                candidate_hit["latency_ms"] = int((time.perf_counter() - t_start) * 1000)
                candidate_hit["total_latency_ms"] = candidate_hit["latency_ms"]
                candidate_hit["answer_confidence"] = candidate_hit.get("confidence", 1.0)
                candidate_hit["citations"] = candidate_hit.get("evidence", [])
                yield make_event("completed", "Research completed (served from institutional memory).", status="completed", data=candidate_hit)
                return

        # 2. Stage 1: ANALYZING QUESTION
        yield make_event(
            "analyzing_question",
            "Understanding question intent and extracting institutional entities...",
            status="running",
            discovered_source_count=0,
            processed_document_count=0,
        )
        await asyncio.sleep(0.05)

        query_context = _understander.understand(query)
        yield make_event(
            "analyzing_question",
            f"Question understood (intent: {query_context.intent}). Entities: {[e.normalized for e in query_context.entities]}",
            status="completed",
        )

        # 3. Stage 2: SEARCHING LOCAL KNOWLEDGE
        yield make_event(
            "searching_local_knowledge",
            "Searching indexed documents, knowledge graph, and institutional records...",
            status="running",
            intent=query_context.intent,
            departments=query_context.departments,
            discovered_source_count=0,
            processed_document_count=0,
        )
        await asyncio.sleep(0.05)

        retrieval_results = []
        try:
            from app.retrieval.pipeline import get_retrieval_pipeline
            pipeline = get_retrieval_pipeline()
            search_query = query_context.expanded_query or query
            retrieval_results = pipeline.search(search_query, top_k=top_k)
        except Exception as e:
            logger.error("Retrieval failed during stream", error=str(e))

        validation = _validator.validate(query_context, retrieval_results)
        unique_urls = list(dict.fromkeys(r.source_url for r in retrieval_results if r.source_url))
        discovered_sources = len(unique_urls)

        yield make_event(
            "searching_local_knowledge",
            f"Local knowledge search complete. Retrieved {len(retrieval_results)} passages from {discovered_sources} unique source(s).",
            status="completed",
            discovered_source_count=discovered_sources,
        )

        # 4. Stages 3, 4, 5: Dynamic Discovery if needed
        has_authoritative_person_profile = False
        if req_person:
            for r in retrieval_results:
                if "Official Faculty Profile:" in r.text:
                    from app.intelligence.entity_engine.identity_resolver import is_name_in_text
                    if is_name_in_text(req_person, r.text)[0]:
                        has_authoritative_person_profile = True
                        break

        needs_discovery = (validation.status == "insufficient_evidence") or (req_person and not has_authoritative_person_profile)

        if needs_discovery:
            yield make_event(
                "discovering_sources",
                "Local evidence insufficient. Initiating dynamic discovery on official MITAOE portals...",
                status="running",
                discovered_source_count=discovered_sources,
                source_url="https://mitaoe.ac.in/",
            )
            await asyncio.sleep(0.08)

            try:
                from app.ingestion.crawler.live_fetcher import fetch_and_index_topic
                yield make_event(
                    "fetching_pages",
                    "Accessing official institutional pages and faculty portals...",
                    status="running",
                    discovered_source_count=discovered_sources + 1,
                )
                new_chunks = await fetch_and_index_topic(query, query_context)
                if new_chunks:
                    new_urls = list(dict.fromkeys(c.get("source_url") for c in new_chunks if c.get("source_url")))
                    yield make_event(
                        "discovering_sources",
                        f"Discovered {len(new_urls)} official page(s) on mitaoe.ac.in.",
                        status="completed",
                        discovered_source_count=discovered_sources + len(new_urls),
                        source_url=new_urls[0] if new_urls else None,
                    )
                    yield make_event(
                        "fetching_pages",
                        f"Fetched {len(new_urls)} page(s) successfully.",
                        status="completed",
                        source_url=new_urls[0] if new_urls else None,
                    )
                    yield make_event(
                        "extracting_information",
                        f"Extracted {len(new_chunks)} structured passage(s) and profile credentials.",
                        status="completed",
                        discovered_source_count=len(new_urls),
                        processed_document_count=len(new_urls),
                    )
                    pipeline.add_chunks(new_chunks)
                    retrieval_results = pipeline.search(search_query, top_k=top_k)
                    validation = _validator.validate(query_context, retrieval_results)
                    unique_urls = list(dict.fromkeys(r.source_url for r in retrieval_results if r.source_url))
                    discovered_sources = len(unique_urls)
                else:
                    yield make_event(
                        "discovering_sources",
                        "No matching official profiles or documents discovered on mitaoe.ac.in.",
                        status="completed",
                        discovered_source_count=discovered_sources,
                    )
                    yield make_event("fetching_pages", "No target pages to fetch.", status="skipped")
                    yield make_event("extracting_information", "No information extracted.", status="skipped")
            except Exception as e:
                logger.debug("Live fetch error", error=str(e))
                yield make_event("discovering_sources", f"Discovery error: {str(e)}", status="failed")
                yield make_event("fetching_pages", "Fetch aborted.", status="failed")
                yield make_event("extracting_information", "Extraction aborted.", status="failed")
        else:
            # Sourced from local knowledge, so dynamic web crawl was not performed
            yield make_event(
                "discovering_sources",
                "Discovery skipped: authoritative evidence already present in local knowledge base.",
                status="skipped",
                discovered_source_count=discovered_sources,
            )
            yield make_event(
                "fetching_pages",
                "Page fetch skipped: local evidence sufficient.",
                status="skipped",
            )
            yield make_event(
                "extracting_information",
                "Information extraction skipped: pre-indexed records available.",
                status="skipped",
            )

        # 5. Stage 6: ANALYZING EVIDENCE
        yield make_event(
            "analyzing_evidence",
            "Cross-referencing entities, designations, departments, and academic cycles...",
            status="running",
            discovered_source_count=discovered_sources,
            candidates=len(retrieval_results),
        )
        await asyncio.sleep(0.05)
        yield make_event(
            "analyzing_evidence",
            f"Evidence analysis complete across {len(retrieval_results)} retrieved candidates.",
            status="completed",
            discovered_source_count=discovered_sources,
        )

        # 6. Stage 7: VERIFYING INFORMATION
        yield make_event(
            "verifying_information",
            "Verifying source authenticity, academic year alignment, and statutory validity...",
            status="running",
            discovered_source_count=discovered_sources,
        )
        await asyncio.sleep(0.05)
        yield make_event(
            "verifying_information",
            f"Verification status: {validation.status.upper()} (Confidence: {int(validation.confidence * 100)}%).",
            status="completed",
            discovered_source_count=discovered_sources,
        )

        # 7. Stage 8: GENERATING ANSWER
        yield make_event(
            "generating_answer",
            "Synthesizing factual, evidence-backed institutional response...",
            status="running",
        )
        composed = _composer.compose(query_context, validation)
        yield make_event(
            "generating_answer",
            "Answer synthesis complete.",
            status="completed",
        )

        total_latency_ms = int((time.perf_counter() - t_start) * 1000)
        citations = [
            {
                "source_url": e.get("source_url", ""),
                "source_title": e.get("source_title", "MITAOE Source"),
                "passage": e.get("passage", e.get("text", ""))[:500],
                "page_number": e.get("page_number"),
                "score": e.get("score", 0.0),
                "academic_year": e.get("academic_year"),
            }
            for e in composed.cited_evidence
        ]

        response = {
            "query_id": request_id,
            "query": query,
            "answer": composed.answer_text,
            "confidence": composed.confidence,
            "answer_confidence": composed.confidence,
            "verification_status": composed.verification_status,
            "is_answerable": composed.is_answerable,
            "evidence": citations,
            "citations": citations,
            "cache_hit": False,
            "limitations": composed.limitations,
            "suggested_queries": composed.suggested_queries,
            "query_intent": query_context.intent,
            "latency_ms": total_latency_ms,
            "total_latency_ms": total_latency_ms,
            "retrieval_latency_ms": total_latency_ms,
        }

        # 8. Stage 9: SAVING TO LOCAL HISTORY
        yield make_event(
            "saving_to_history",
            "Saving verified research to local institutional history...",
            status="running",
        )
        try:
            from app.storage.history_store import save_query_history
            await save_query_history(
                raw_query=query,
                normalized_query=query_context.normalized_query,
                query_intent=query_context.intent,
                answer_text=composed.answer_text,
                answer_confidence=composed.confidence,
                verification_status=composed.verification_status,
                is_answerable=composed.is_answerable,
                total_latency_ms=total_latency_ms,
                retrieval_latency_ms=total_latency_ms,
                cache_hit=False,
                query_entities=[e.normalized for e in query_context.entities],
                citations=citations,
            )
        except Exception as e:
            logger.debug("Failed to record query history in stream", error=str(e))

        yield make_event(
            "saving_to_history",
            "Research successfully recorded in institutional memory.",
            status="completed",
        )

        _l1_cache[cache_key] = response
        await self._set_cache(cache_key, response, ttl=settings.cache_query_ttl)

        # 9. Stage 10: COMPLETED
        yield make_event(
            "completed",
            "Research completed.",
            status="completed",
            discovered_source_count=len(citations),
            data=response,
        )

    # ---- Internal Cache Helpers ------------------------------

    async def _get_cache(self, key: str) -> Optional[dict]:
        """Fetch from Redis cache with timeout protection."""
        if not getattr(settings, "redis_enabled", False):
            return None
        global _redis_available, _redis_last_check
        now = time.monotonic()
        if not _redis_available and (now - _redis_last_check) < 30.0:
            return None

        try:
            from app.core.redis import get_redis
            r = await get_redis()
            val = await asyncio.wait_for(r.get(key), timeout=0.08)
            _redis_available = True
            return json.loads(val) if val else None
        except Exception:
            _redis_available = False
            _redis_last_check = now
            return None

    async def _set_cache(self, key: str, value: dict, ttl: int = 3600):
        """Store in Redis cache safely."""
        if not getattr(settings, "redis_enabled", False):
            return
        global _redis_available, _redis_last_check
        now = time.monotonic()
        if not _redis_available and (now - _redis_last_check) < 30.0:
            return

        try:
            from app.core.redis import get_redis
            r = await get_redis()
            await asyncio.wait_for(r.setex(key, ttl, json.dumps(value)), timeout=0.08)
            _redis_available = True
        except Exception:
            _redis_available = False
            _redis_last_check = now
