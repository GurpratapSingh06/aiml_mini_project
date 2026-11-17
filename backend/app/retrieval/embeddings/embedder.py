"""
VEDANTA — Sentence Embedding Engine
Generates semantic vector representations using Sentence Transformers.
"""

from __future__ import annotations

import threading
from typing import List, Optional

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_model_lock = threading.Lock()
_model_instance = None


def _get_model():
    """Return the singleton SentenceTransformer model (lazy load)."""
    global _model_instance
    if _model_instance is not None:
        return _model_instance
    with _model_lock:
        if _model_instance is not None:
            return _model_instance
        try:
            from sentence_transformers import SentenceTransformer
            import time
            device = _detect_device()
            t0 = time.perf_counter()
            logger.info("Loading embedding model", model=settings.embedding_model, device=device)
            try:
                # Fast path: load from local cache without remote HuggingFace Hub network checks
                _model_instance = SentenceTransformer(settings.embedding_model, device=device, local_files_only=True)
            except Exception as e_local:
                logger.warning("Local-only model load failed, falling back to network download", error=str(e_local))
                _model_instance = SentenceTransformer(settings.embedding_model, device=device)
            load_ms = (time.perf_counter() - t0) * 1000
            logger.info("Embedding model loaded", model=settings.embedding_model, load_ms=round(load_ms, 2))
            return _model_instance
        except ImportError:
            logger.error("sentence-transformers not installed")
            return None
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            return None


def _detect_device() -> str:
    """Detect best available device (GPU or CPU)."""
    configured = settings.embedding_device.lower()
    if configured == "cpu":
        return "cpu"
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            logger.info("NVIDIA GPU detected", vram_gb=round(vram_gb, 1))
            return "cuda"
        else:
            logger.info("No GPU available — using CPU")
            return "cpu"
    except ImportError:
        return "cpu"


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    """L2-normalize a batch of vectors for cosine similarity via inner product."""
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return vectors / norms


class SentenceEmbedder:
    """
    Sentence embedding engine.
    Provides batch embedding for indexing and single-query embedding for retrieval.
    Model is loaded lazily and cached as a module-level singleton.
    """

    def __init__(self):
        self._dim = settings.embedding_dimension

    @property
    def model(self):
        return _get_model()

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = None,
    ) -> Optional[np.ndarray]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings
            normalize: L2-normalize for cosine similarity
            batch_size: Override default batch size

        Returns:
            numpy array of shape (N, dim) or None on failure
        """
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.empty((0, self._dim), dtype=np.float32)

        m = self.model
        if m is None:
            logger.error("Embedding model not available")
            return None

        try:
            bs = batch_size or settings.embedding_batch_size
            embeddings = m.encode(
                texts,
                batch_size=bs,
                show_progress_bar=len(texts) > 100,
                convert_to_numpy=True,
                normalize_embeddings=False,
            ).astype(np.float32)

            if normalize:
                embeddings = _l2_normalize(embeddings)

            return embeddings

        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            return None

    def embed_query(self, query: str, normalize: bool = True) -> Optional[np.ndarray]:
        """
        Generate a single query embedding.
        Returns array of shape (1, dim) or None on failure.
        """
        result = self.embed([query], normalize=normalize)
        return result


# Module-level singleton instance
embedder = SentenceEmbedder()
