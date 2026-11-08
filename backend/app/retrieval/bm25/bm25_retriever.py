"""
VEDANTA — BM25 Retriever
Lexical retrieval for exact terms, names, and institutional terminology.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BM25Result:
    chunk_id: str
    text: str
    score: float
    rank: int
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    page_number: Optional[int] = None


def _tokenize(text: str) -> List[str]:
    """Simple whitespace tokenizer with lowercasing."""
    import re
    text = text.lower()
    # Remove punctuation except hyphens in compound words
    text = re.sub(r"[^\w\s-]", " ", text)
    return [t for t in text.split() if t and len(t) > 1]


class BM25Retriever:
    """
    BM25 retrieval using rank_bm25 library.
    Configured for institutional content (names, designations, terminology).
    """

    def __init__(
        self,
        k1: float = None,
        b: float = None,
    ):
        self.k1 = k1 or settings.bm25_k1
        self.b = b or settings.bm25_b
        self._bm25 = None
        self._chunk_ids: List[str] = []
        self._chunk_texts: List[str] = []
        self._chunk_metadata: List[dict] = []

    def build_index(self, chunks: List[dict]) -> None:
        """
        Build BM25 index from a list of chunk dicts.

        Args:
            chunks: List of dicts with keys: chunk_id, text, source_url, source_title, page_number
        """
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.error("rank_bm25 not installed — BM25 retrieval unavailable")
            return

        if not chunks:
            logger.warning("No chunks provided for BM25 indexing")
            return

        self._chunk_ids = [c["chunk_id"] for c in chunks]
        self._chunk_texts = [c["text"] for c in chunks]
        self._chunk_metadata = [
            {
                "source_url": c.get("source_url", ""),
                "source_title": c.get("source_title", ""),
                "page_number": c.get("page_number"),
            }
            for c in chunks
        ]

        tokenized_corpus = [_tokenize(text) for text in self._chunk_texts]
        self._bm25 = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)
        logger.info("BM25 index built", num_chunks=len(chunks))

    def search(self, query: str, top_k: int = 20) -> List[BM25Result]:
        """
        Search the BM25 index for the given query.

        Returns sorted list of BM25Result objects.
        """
        if self._bm25 is None:
            logger.warning("BM25 index not built — returning empty results")
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # Get top_k indices sorted by score
        indexed_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        top_indices = [i for i, s in indexed_scores[:top_k] if s > 0]

        results = []
        for rank, idx in enumerate(top_indices):
            meta = self._chunk_metadata[idx]
            results.append(BM25Result(
                chunk_id=self._chunk_ids[idx],
                text=self._chunk_texts[idx],
                score=float(scores[idx]),
                rank=rank + 1,
                source_url=meta.get("source_url"),
                source_title=meta.get("source_title"),
                page_number=meta.get("page_number"),
            ))

        return results

    def save(self, path: str) -> None:
        """Persist the BM25 index to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "bm25": self._bm25,
                "chunk_ids": self._chunk_ids,
                "chunk_texts": self._chunk_texts,
                "chunk_metadata": self._chunk_metadata,
                "k1": self.k1,
                "b": self.b,
            }, f)
        logger.info("BM25 index saved", path=str(path))

    def load(self, path: str) -> bool:
        """Load a persisted BM25 index from disk. Returns True on success."""
        path = Path(path)
        if not path.exists():
            logger.info("BM25 index file not found", path=str(path))
            return False
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self._bm25 = data["bm25"]
            self._chunk_ids = data["chunk_ids"]
            self._chunk_texts = data["chunk_texts"]
            self._chunk_metadata = data["chunk_metadata"]
            self.k1 = data.get("k1", self.k1)
            self.b = data.get("b", self.b)
            logger.info("BM25 index loaded", chunks=len(self._chunk_ids), path=str(path))
            return True
        except Exception as e:
            logger.error("Failed to load BM25 index", path=str(path), error=str(e))
            return False

    @property
    def is_ready(self) -> bool:
        return self._bm25 is not None and len(self._chunk_ids) > 0

    @property
    def num_docs(self) -> int:
        return len(self._chunk_ids)
