"""
VEDANTA — FAISS Vector Store
Persistent vector index for semantic similarity search.
"""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FAISSResult:
    chunk_id: str
    score: float
    rank: int


class FAISSVectorStore:
    """
    FAISS-based vector store for semantic chunk retrieval.
    Uses IndexFlatIP with L2-normalized embeddings (equivalent to cosine similarity).
    """

    def __init__(self, dimension: int = None):
        self.dimension = dimension or settings.embedding_dimension
        self._index = None
        self._chunk_ids: List[str] = []

    def _get_faiss(self):
        try:
            import faiss
            return faiss
        except ImportError:
            logger.error("faiss-cpu not installed — vector search unavailable")
            return None

    def build_index(self, embeddings: np.ndarray, chunk_ids: List[str]) -> None:
        """
        Build a FAISS IndexFlatIP index from embeddings.

        Args:
            embeddings: L2-normalized float32 array of shape (N, dim)
            chunk_ids: Corresponding chunk ID strings
        """
        faiss = self._get_faiss()
        if faiss is None:
            return

        if len(embeddings) == 0:
            logger.warning("No embeddings provided for FAISS indexing")
            return

        embeddings = embeddings.astype(np.float32)
        self._index = faiss.IndexFlatIP(self.dimension)
        self._index.add(embeddings)
        self._chunk_ids = list(chunk_ids)
        logger.info("FAISS index built", num_vectors=len(chunk_ids))

    def add_embeddings(self, embeddings: np.ndarray, chunk_ids: List[str]) -> None:
        """
        Add new embeddings to an existing index.
        Creates the index if it doesn't exist.
        """
        faiss = self._get_faiss()
        if faiss is None:
            return

        embeddings = embeddings.astype(np.float32)

        if self._index is None:
            self._index = faiss.IndexFlatIP(self.dimension)

        self._index.add(embeddings)
        self._chunk_ids.extend(chunk_ids)
        logger.info("Embeddings added to FAISS", added=len(chunk_ids), total=len(self._chunk_ids))

    def search(self, query_embedding: np.ndarray, top_k: int = 20) -> List[FAISSResult]:
        """
        Search the index for the most similar vectors.

        Args:
            query_embedding: L2-normalized float32 array of shape (1, dim) or (dim,)
            top_k: Number of results to return

        Returns:
            Sorted list of FAISSResult
        """
        if self._index is None or len(self._chunk_ids) == 0:
            logger.warning("FAISS index not ready — returning empty results")
            return []

        if query_embedding is None:
            return []

        # Ensure shape is (1, dim)
        qe = query_embedding.astype(np.float32)
        if qe.ndim == 1:
            qe = qe.reshape(1, -1)

        actual_k = min(top_k, len(self._chunk_ids))
        scores, indices = self._index.search(qe, actual_k)

        results = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx == -1:
                continue
            results.append(FAISSResult(
                chunk_id=self._chunk_ids[idx],
                score=float(score),
                rank=rank + 1,
            ))

        return results

    def save(self, directory: str) -> None:
        """Save FAISS index and chunk ID mapping to disk."""
        import faiss

        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        index_path = dir_path / "faiss.index"
        ids_path = dir_path / "chunk_ids.pkl"

        if self._index is not None:
            faiss.write_index(self._index, str(index_path))

        with open(ids_path, "wb") as f:
            pickle.dump(self._chunk_ids, f)

        logger.info("FAISS index saved", directory=directory, vectors=len(self._chunk_ids))

    def load(self, directory: str) -> bool:
        """Load FAISS index from disk. Returns True on success."""
        import faiss

        dir_path = Path(directory)
        index_path = dir_path / "faiss.index"
        ids_path = dir_path / "chunk_ids.pkl"

        if not index_path.exists() or not ids_path.exists():
            logger.info("FAISS index files not found", directory=directory)
            return False

        try:
            self._index = faiss.read_index(str(index_path))
            with open(ids_path, "rb") as f:
                self._chunk_ids = pickle.load(f)
            logger.info("FAISS index loaded", vectors=len(self._chunk_ids))
            return True
        except Exception as e:
            logger.error("Failed to load FAISS index", error=str(e))
            return False

    @property
    def is_ready(self) -> bool:
        return self._index is not None and len(self._chunk_ids) > 0

    @property
    def num_vectors(self) -> int:
        return len(self._chunk_ids)
