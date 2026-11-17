"""
VEDANTA — Cross-Encoder Reranker (Optional)
Improves ranking accuracy at the cost of additional latency.
"""

from __future__ import annotations

import threading
from typing import List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_reranker_lock = threading.Lock()
_reranker_instance = None


def _get_reranker():
    global _reranker_instance
    if _reranker_instance is not None:
        return _reranker_instance
    with _reranker_lock:
        if _reranker_instance is not None:
            return _reranker_instance
        try:
            from sentence_transformers import CrossEncoder
            logger.info("Loading cross-encoder model", model=settings.reranker_model)
            try:
                _reranker_instance = CrossEncoder(settings.reranker_model, local_files_only=True)
            except Exception:
                _reranker_instance = CrossEncoder(settings.reranker_model)
            logger.info("Cross-encoder loaded")
            return _reranker_instance
        except ImportError:
            logger.warning("sentence-transformers CrossEncoder not available")
            return None
        except Exception as e:
            logger.error("Failed to load cross-encoder", error=str(e))
            return None


class CrossEncoderReranker:
    """
    Optional cross-encoder reranker.
    Scores query-passage pairs for precise relevance ordering.
    Disabled by default (settings.reranker_enabled).
    """

    def __init__(self):
        self.enabled = settings.reranker_enabled
        self.top_k = settings.retrieval_rerank_top_k

    def rerank(
        self,
        query: str,
        candidates: List[dict],
    ) -> List[dict]:
        """
        Rerank candidates using the cross-encoder.

        Args:
            query: Original user query
            candidates: List of dicts with 'chunk_id' and 'text' keys

        Returns:
            Candidates sorted by cross-encoder score (highest first)
        """
        if not self.enabled:
            return candidates

        if not candidates:
            return []

        reranker = _get_reranker()
        if reranker is None:
            logger.warning("Reranker not available — returning unranked candidates")
            return candidates

        try:
            # Only rerank top N to control latency
            to_rerank = candidates[:self.top_k]
            rest = candidates[self.top_k:]

            pairs = [(query, c["text"]) for c in to_rerank]
            scores = reranker.predict(pairs)

            # Attach scores and sort
            scored = sorted(
                zip(to_rerank, scores),
                key=lambda x: x[1],
                reverse=True,
            )

            reranked = []
            for i, (candidate, score) in enumerate(scored):
                candidate = dict(candidate)
                candidate["reranker_score"] = float(score)
                candidate["reranker_rank"] = i + 1
                reranked.append(candidate)

            return reranked + rest

        except Exception as e:
            logger.error("Cross-encoder reranking failed", error=str(e))
            return candidates

    @property
    def is_ready(self) -> bool:
        if not self.enabled:
            return False
        return _get_reranker() is not None
