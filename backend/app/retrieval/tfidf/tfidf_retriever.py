"""
VEDANTA — TF-IDF Retriever
Baseline lexical retrieval for comparison and evaluation.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TFIDFResult:
    chunk_id: str
    text: str
    score: float
    rank: int


class TFIDFRetriever:
    """TF-IDF cosine similarity retriever (baseline for evaluation)."""

    def __init__(self):
        self._vectorizer = None
        self._matrix = None
        self._chunk_ids: List[str] = []
        self._chunk_texts: List[str] = []

    def build_index(self, chunks: List[dict]) -> None:
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            import scipy.sparse
        except ImportError:
            logger.error("scikit-learn not installed — TF-IDF unavailable")
            return

        if not chunks:
            return

        self._chunk_ids = [c["chunk_id"] for c in chunks]
        self._chunk_texts = [c["text"] for c in chunks]

        self._vectorizer = TfidfVectorizer(
            max_features=50000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
        )
        self._matrix = self._vectorizer.fit_transform(self._chunk_texts)
        logger.info("TF-IDF index built", chunks=len(chunks))

    def search(self, query: str, top_k: int = 20) -> List[TFIDFResult]:
        if self._vectorizer is None or self._matrix is None:
            return []
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np

            query_vec = self._vectorizer.transform([query])
            scores = cosine_similarity(query_vec, self._matrix).flatten()
            top_indices = scores.argsort()[::-1][:top_k]

            results = []
            for rank, idx in enumerate(top_indices):
                if scores[idx] == 0:
                    break
                results.append(TFIDFResult(
                    chunk_id=self._chunk_ids[idx],
                    text=self._chunk_texts[idx],
                    score=float(scores[idx]),
                    rank=rank + 1,
                ))
            return results
        except Exception as e:
            logger.error("TF-IDF search failed", error=str(e))
            return []

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump({
                "vectorizer": self._vectorizer,
                "matrix": self._matrix,
                "chunk_ids": self._chunk_ids,
                "chunk_texts": self._chunk_texts,
            }, f)

    def load(self, path: str) -> bool:
        path = Path(path)
        if not path.exists():
            return False
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self._vectorizer = data["vectorizer"]
            self._matrix = data["matrix"]
            self._chunk_ids = data["chunk_ids"]
            self._chunk_texts = data["chunk_texts"]
            return True
        except Exception as e:
            logger.error("TF-IDF load failed", error=str(e))
            return False
