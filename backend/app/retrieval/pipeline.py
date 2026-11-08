"""
VEDANTA — Retrieval Pipeline
Unified hybrid retrieval: BM25 + Semantic + RRF + Optional Reranking.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_pipeline_lock = threading.Lock()
_pipeline_instance: Optional["RetrievalPipeline"] = None


@dataclass
class RetrievalResult:
    chunk_id: str
    text: str
    source_url: str
    source_title: Optional[str]
    page_number: Optional[int]
    score: float
    rank: int
    retrieval_method: str  # bm25_only | semantic_only | hybrid | reranked
    bm25_score: float = 0.0
    semantic_score: float = 0.0
    rrf_score: float = 0.0


class RetrievalPipeline:
    """
    Unified retrieval pipeline combining BM25, FAISS, and RRF fusion.
    Singleton — initialized once per process.
    """

    def __init__(self):
        from app.retrieval.bm25.bm25_retriever import BM25Retriever
        from app.retrieval.embeddings.embedder import SentenceEmbedder
        from app.retrieval.vector_store.faiss_store import FAISSVectorStore
        from app.retrieval.fusion.rrf import HybridFuser
        from app.retrieval.reranking.cross_encoder import CrossEncoderReranker

        self.bm25 = BM25Retriever()
        self.embedder = SentenceEmbedder()
        self.faiss = FAISSVectorStore()
        self.fuser = HybridFuser()
        self.reranker = CrossEncoderReranker()

        # In-memory chunk lookup for text retrieval
        self._chunk_lookup: Dict[str, dict] = {}

        self._initialized = False

    def initialize(self) -> None:
        """Load persisted indexes from disk."""
        index_dir = Path(settings.faiss_index_path)

        # Load BM25
        bm25_path = index_dir / "bm25.pkl"
        if self.bm25.load(str(bm25_path)):
            logger.info("BM25 index loaded from disk")

        # Load FAISS
        if self.faiss.load(str(index_dir)):
            logger.info("FAISS index loaded from disk")

        # Load chunk lookup
        lookup_path = index_dir / "chunk_lookup.pkl"
        if lookup_path.exists():
            import pickle
            with open(lookup_path, "rb") as f:
                self._chunk_lookup = pickle.load(f)
            logger.info("Chunk lookup loaded", chunks=len(self._chunk_lookup))

        self._initialized = True
        logger.info(
            "Retrieval pipeline initialized",
            bm25_ready=self.bm25.is_ready,
            faiss_ready=self.faiss.is_ready,
            bm25_docs=self.bm25.num_docs,
            faiss_vectors=self.faiss.num_vectors,
        )

    def _save_indexes(self) -> None:
        """Persist all indexes to disk."""
        import pickle

        index_dir = Path(settings.faiss_index_path)
        index_dir.mkdir(parents=True, exist_ok=True)

        self.bm25.save(str(index_dir / "bm25.pkl"))
        self.faiss.save(str(index_dir))

        with open(index_dir / "chunk_lookup.pkl", "wb") as f:
            pickle.dump(self._chunk_lookup, f)

        logger.info("All indexes saved to disk")

    def add_chunks(self, chunks: List[dict]) -> None:
        """
        Add new chunks to both BM25 and FAISS indexes.

        Args:
            chunks: List of dicts with keys: chunk_id, text, source_url,
                    source_title, page_number
        """
        if not chunks:
            return

        # Update chunk lookup
        for chunk in chunks:
            self._chunk_lookup[chunk["chunk_id"]] = {
                "text": chunk["text"],
                "source_url": chunk.get("source_url", ""),
                "source_title": chunk.get("source_title", ""),
                "page_number": chunk.get("page_number"),
            }

        # Rebuild BM25 (BM25 doesn't support incremental updates efficiently)
        all_chunks = [
            {"chunk_id": cid, **meta}
            for cid, meta in self._chunk_lookup.items()
        ]
        self.bm25.build_index(all_chunks)

        # Generate embeddings and add to FAISS
        texts = [c["text"] for c in chunks]
        chunk_ids = [c["chunk_id"] for c in chunks]

        embeddings = self.embedder.embed(texts, normalize=True)
        if embeddings is not None:
            self.faiss.add_embeddings(embeddings, chunk_ids)

        # Save updated indexes
        self._save_indexes()
        logger.info("Chunks added to retrieval pipeline", added=len(chunks))

    def rebuild_indexes(self, chunks: List[dict]) -> None:
        """Full rebuild of all indexes from provided chunks."""
        import numpy as np

        if not chunks:
            logger.warning("No chunks provided for index rebuild")
            return

        # Reset
        from app.retrieval.bm25.bm25_retriever import BM25Retriever
        from app.retrieval.vector_store.faiss_store import FAISSVectorStore
        self.bm25 = BM25Retriever()
        self.faiss = FAISSVectorStore()
        self._chunk_lookup = {}

        # Build chunk lookup
        for chunk in chunks:
            self._chunk_lookup[chunk["chunk_id"]] = {
                "text": chunk["text"],
                "source_url": chunk.get("source_url", ""),
                "source_title": chunk.get("source_title", ""),
                "page_number": chunk.get("page_number"),
            }

        # Build BM25
        self.bm25.build_index(chunks)

        # Build FAISS
        logger.info("Generating embeddings for FAISS rebuild", chunks=len(chunks))
        texts = [c["text"] for c in chunks]
        chunk_ids = [c["chunk_id"] for c in chunks]
        embeddings = self.embedder.embed(texts, normalize=True)
        if embeddings is not None:
            self.faiss.build_index(embeddings, chunk_ids)

        self._save_indexes()
        logger.info("Full index rebuild complete", chunks=len(chunks))

    def search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[dict] = None,
    ) -> List[RetrievalResult]:
        """
        Execute the full hybrid retrieval pipeline.

        Steps:
        1. Embed query
        2. BM25 search
        3. FAISS semantic search
        4. RRF fusion
        5. Optional cross-encoder reranking
        6. Return top_k results with metadata
        """
        top_k = top_k or settings.retrieval_top_k

        if not self.bm25.is_ready and not self.faiss.is_ready:
            logger.warning("No retrieval indexes available")
            return []

        # BM25 search
        bm25_results = []
        if self.bm25.is_ready:
            bm25_results = self.bm25.search(query, top_k=top_k * 2)

        # Semantic search
        semantic_results = []
        if self.faiss.is_ready:
            query_emb = self.embedder.embed_query(query, normalize=True)
            if query_emb is not None:
                semantic_results = self.faiss.search(query_emb, top_k=top_k * 2)

        # Determine method
        has_bm25 = len(bm25_results) > 0
        has_semantic = len(semantic_results) > 0

        if not has_bm25 and not has_semantic:
            return []

        if has_bm25 and has_semantic:
            # RRF fusion
            fused = self.fuser.fuse(bm25_results, semantic_results, top_k=top_k)
            retrieval_method = "hybrid"
        elif has_bm25:
            # BM25 only
            from app.retrieval.fusion.rrf import FusedResult
            fused = [
                FusedResult(
                    chunk_id=r.chunk_id,
                    rrf_score=r.score,
                    bm25_rank=r.rank,
                    bm25_score=r.score,
                )
                for r in bm25_results[:top_k]
            ]
            retrieval_method = "bm25_only"
        else:
            # Semantic only
            from app.retrieval.fusion.rrf import FusedResult
            fused = [
                FusedResult(
                    chunk_id=r.chunk_id,
                    rrf_score=r.score,
                    semantic_rank=r.rank,
                    semantic_score=r.score,
                )
                for r in semantic_results[:top_k]
            ]
            retrieval_method = "semantic_only"

        # Build results with metadata
        results: List[RetrievalResult] = []
        for rank, fr in enumerate(fused):
            meta = self._chunk_lookup.get(fr.chunk_id, {})
            results.append(RetrievalResult(
                chunk_id=fr.chunk_id,
                text=meta.get("text", ""),
                source_url=meta.get("source_url", ""),
                source_title=meta.get("source_title"),
                page_number=meta.get("page_number"),
                score=fr.rrf_score,
                rank=rank + 1,
                retrieval_method=retrieval_method,
                bm25_score=fr.bm25_score,
                semantic_score=fr.semantic_score,
                rrf_score=fr.rrf_score,
            ))

        # Optional reranking
        if self.reranker.enabled and results:
            candidates = [{"chunk_id": r.chunk_id, "text": r.text} for r in results]
            reranked = self.reranker.rerank(query, candidates)
            # Rebuild results in reranked order
            id_to_result = {r.chunk_id: r for r in results}
            reranked_results = []
            for i, c in enumerate(reranked):
                if c["chunk_id"] in id_to_result:
                    r = id_to_result[c["chunk_id"]]
                    r.rank = i + 1
                    r.retrieval_method = "reranked"
                    reranked_results.append(r)
            results = reranked_results

        return results[:top_k]


def get_retrieval_pipeline() -> RetrievalPipeline:
    """Get or create the singleton retrieval pipeline."""
    global _pipeline_instance
    if _pipeline_instance is not None:
        return _pipeline_instance
    with _pipeline_lock:
        if _pipeline_instance is not None:
            return _pipeline_instance
        _pipeline_instance = RetrievalPipeline()
        _pipeline_instance.initialize()
    return _pipeline_instance
