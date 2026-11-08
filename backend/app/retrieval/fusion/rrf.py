"""
VEDANTA — Reciprocal Rank Fusion
Combines BM25 and semantic retrieval results without score normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FusedResult:
    chunk_id: str
    rrf_score: float
    bm25_rank: Optional[int] = None
    semantic_rank: Optional[int] = None
    bm25_score: float = 0.0
    semantic_score: float = 0.0


def reciprocal_rank_fusion(
    rankings: List[List[str]],
    k: int = 60,
) -> List[Tuple[str, float]]:
    """
    Compute RRF scores for multiple ranked lists of item IDs.

    RRF score = sum(1 / (k + rank_i)) across all lists where item appears.

    Args:
        rankings: List of ranked item ID lists (each sorted best-first)
        k: Smoothing constant (default 60, well-validated in literature)

    Returns:
        List of (item_id, rrf_score) sorted by descending RRF score
    """
    scores: Dict[str, float] = {}

    for ranked_list in rankings:
        for rank, item_id in enumerate(ranked_list, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


class HybridFuser:
    """
    Fuses BM25 and semantic search results using Reciprocal Rank Fusion.
    """

    def __init__(self, k: int = None):
        self.k = k or settings.rrf_k

    def fuse(
        self,
        bm25_results: list,
        semantic_results: list,
        top_k: int = 20,
    ) -> List[FusedResult]:
        """
        Combine BM25Result and FAISSResult lists into a unified ranking.

        Args:
            bm25_results: List of BM25Result objects
            semantic_results: List of FAISSResult objects
            top_k: Maximum number of fused results to return

        Returns:
            List of FusedResult sorted by descending RRF score
        """
        # Build ranked lists
        bm25_ranking = [r.chunk_id for r in bm25_results]
        semantic_ranking = [r.chunk_id for r in semantic_results]

        # Build lookup maps for original scores
        bm25_map = {r.chunk_id: (r.rank, r.score) for r in bm25_results}
        semantic_map = {r.chunk_id: (r.rank, r.score) for r in semantic_results}

        # Run RRF
        fused = reciprocal_rank_fusion(
            [bm25_ranking, semantic_ranking],
            k=self.k,
        )

        results: List[FusedResult] = []
        for chunk_id, rrf_score in fused[:top_k]:
            b_rank, b_score = bm25_map.get(chunk_id, (None, 0.0))
            s_rank, s_score = semantic_map.get(chunk_id, (None, 0.0))

            results.append(FusedResult(
                chunk_id=chunk_id,
                rrf_score=rrf_score,
                bm25_rank=b_rank,
                semantic_rank=s_rank,
                bm25_score=b_score,
                semantic_score=s_score,
            ))

        return results
