"""
VEDANTA Unit Tests — BM25, Semantic FAISS, and Reciprocal Rank Fusion
"""

import pytest
from app.retrieval.bm25.bm25_retriever import BM25Retriever
from app.retrieval.fusion.rrf import reciprocal_rank_fusion, HybridFuser


def test_bm25_exact_match_retrieval():
    retriever = BM25Retriever(k1=1.5, b=0.75)
    chunks = [
        {"chunk_id": "c1", "text": "Dr. Sandip A. Gade is the Head of Computer Engineering at MITAOE."},
        {"chunk_id": "c2", "text": "The Mechanical Engineering department offers robotics and automation."},
        {"chunk_id": "c3", "text": "Civil Engineering conducts structural testing and surveying."},
    ]
    retriever.build_index(chunks)
    assert retriever.is_ready is True

    results = retriever.search("Head of Computer Engineering", top_k=2)
    assert len(results) > 0
    assert results[0].chunk_id == "c1"


def test_reciprocal_rank_fusion_math():
    # RRF = sum(1 / (k + rank))
    bm25_ranks = ["c1", "c2", "c3"]
    semantic_ranks = ["c2", "c1", "c3"]

    fused = reciprocal_rank_fusion([bm25_ranks, semantic_ranks], k=60)
    # c1 has ranks 1 & 2 -> 1/61 + 1/62 = 0.01639 + 0.01613 = 0.03252
    # c2 has ranks 2 & 1 -> same score
    # c3 has ranks 3 & 3 -> 1/63 + 1/63 = 0.03175
    assert len(fused) == 3
    top_ids = [f[0] for f in fused[:2]]
    assert "c1" in top_ids and "c2" in top_ids
    assert fused[2][0] == "c3"
