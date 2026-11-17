"""
VEDANTA — Query History and Evidence Persistence Store
Saves verified institutional queries, answers, latency metrics, and cited evidence.
"""

from __future__ import annotations

import json
import uuid
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text, select, desc
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)

INSTITUTION_ID = "00000000-0000-0000-0000-000000000001"


async def save_query_history(
    raw_query: str,
    normalized_query: str,
    query_intent: str,
    answer_text: str,
    answer_confidence: float,
    verification_status: str,
    is_answerable: bool,
    total_latency_ms: int,
    retrieval_latency_ms: int,
    cache_hit: bool,
    query_entities: Optional[List[str]] = None,
    citations: Optional[List[Dict[str, Any]]] = None,
) -> Optional[str]:
    """
    Persist query, answer, and citations into PostgreSQL query_history and evidence_records.
    """
    history_id = str(uuid.uuid4())
    citations = citations or []
    query_entities = query_entities or []

    # Map verification_status to database enum values (UPPERCASE)
    status_map = {
        "verified": "VERIFIED",
        "partially_verified": "PARTIALLY_VERIFIED",
        "uncertain": "UNCERTAIN",
        "insufficient_evidence": "INSUFFICIENT_EVIDENCE",
        "conflicting_sources": "CONFLICTING_SOURCES",
        "outdated_source": "OUTDATED_SOURCE",
    }
    db_status = status_map.get(str(verification_status).lower(), "UNCERTAIN")

    try:
        async with AsyncSessionLocal() as session:
            # 1. Insert query_history
            await session.execute(
                text("""
                    INSERT INTO query_history (
                        id, institution_id, raw_query, normalized_query, query_intent,
                        query_entities, answer_text, answer_confidence, verification_status,
                        is_answerable, total_latency_ms, retrieval_latency_ms, cache_hit,
                        created_at
                    ) VALUES (
                        :id, :inst_id, :raw_q, :norm_q, :intent,
                        :entities, :answer, :conf, :status,
                        :answerable, :total_lat, :ret_lat, :cache_hit,
                        NOW()
                    )
                """),
                {
                    "id": history_id,
                    "inst_id": INSTITUTION_ID,
                    "raw_q": raw_query,
                    "norm_q": normalized_query,
                    "intent": query_intent,
                    "entities": json.dumps(query_entities),
                    "answer": answer_text,
                    "conf": answer_confidence,
                    "status": db_status,
                    "answerable": is_answerable,
                    "total_lat": total_latency_ms,
                    "ret_lat": retrieval_latency_ms,
                    "cache_hit": cache_hit,
                },
            )

            # 2. Insert evidence_records
            for i, c in enumerate(citations[:5]):
                ev_id = str(uuid.uuid4())
                await session.execute(
                    text("""
                        INSERT INTO evidence_records (
                            id, query_history_id, source_url, source_title,
                            page_number, passage, academic_year,
                            retrieval_score, retrieval_rank, verification_status,
                            created_at
                        ) VALUES (
                            :id, :qh_id, :url, :title,
                            :page, :passage, :ay,
                            :score, :rank, :status,
                            NOW()
                        )
                    """),
                    {
                        "id": ev_id,
                        "qh_id": history_id,
                        "url": c.get("source_url", ""),
                        "title": c.get("source_title", "MITAOE Source"),
                        "page": c.get("page_number"),
                        "passage": (c.get("passage") or c.get("text", ""))[:500],
                        "ay": c.get("academic_year", "2026-27"),
                        "score": float(c.get("retrieval_score") or c.get("score") or 0.0),
                        "rank": i + 1,
                        "status": db_status,
                    },
                )

            await session.commit()
            return history_id

    except Exception as e:
        logger.warning("Failed to save query history", error=str(e))
        return None


async def get_recent_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve recent queries and verified answers from query_history.
    """
    try:
        async with AsyncSessionLocal() as session:
            res = await session.execute(
                text("""
                    SELECT 
                        id, raw_query, query_intent, answer_text,
                        answer_confidence, verification_status, total_latency_ms,
                        cache_hit, created_at
                    FROM query_history
                    ORDER BY created_at DESC
                    LIMIT :limit
                """),
                {"limit": limit},
            )
            rows = res.fetchall()

            results = []
            for r in rows:
                results.append({
                    "id": str(r[0]),
                    "query": r[1],
                    "intent": r[2],
                    "answer": r[3],
                    "confidence": float(r[4] or 0.0),
                    "verification_status": r[5],
                    "total_latency_ms": r[6],
                    "cache_hit": r[7],
                    "created_at": r[8].isoformat() if r[8] else None,
                })
            return results

    except Exception as e:
        logger.warning("Failed to retrieve query history", error=str(e))
        return []
