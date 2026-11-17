"""
VEDANTA — Core Configuration
Loads all settings from environment variables via Pydantic Settings.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----------------------------------------
    app_name: str = "VEDANTA"
    app_env: str = "development"
    app_debug: bool = False
    app_secret_key: str = "change-this-secret-key"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_log_level: str = "INFO"
    app_version: str = "0.1.0"

    # ---- Database -------------------------------------------
    database_url: str = "postgresql+asyncpg://vedanta:vedanta_dev_password@localhost:5432/vedanta"
    database_sync_url: str = "postgresql://vedanta:vedanta_dev_password@localhost:5432/vedanta"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ---- Redis ----------------------------------------------
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False
    cache_default_ttl: int = 3600
    cache_query_ttl: int = 1800
    cache_embedding_ttl: int = 86400

    # ---- Worker ---------------------------------------------
    worker_queues: str = "crawl,document,embedding,default"
    worker_concurrency: int = 2

    # ---- Crawling -------------------------------------------
    crawl_allowed_domains: str = "mitaoe.ac.in,www.mitaoe.ac.in"
    crawl_start_url: str = "https://mitaoe.ac.in"
    crawl_max_depth: int = 5
    crawl_max_pages: int = 5000
    crawl_concurrency: int = 5
    crawl_delay_seconds: float = 1.0
    crawl_request_timeout: int = 30
    crawl_max_retries: int = 3
    crawl_user_agent: str = (
        "VEDANTA-Crawler/0.1 (MITAOE Knowledge Platform; +https://mitaoe.ac.in)"
    )
    crawl_respect_robots: bool = True

    # ---- Document Processing --------------------------------
    document_storage_path: str = "./data/documents"
    document_max_size_mb: int = 50
    document_ocr_engine: str = "tesseract"
    document_ocr_language: str = "eng"
    document_tesseract_cmd: Optional[str] = None
    tesseract_cmd: Optional[str] = None
    document_paddle_ocr: bool = False

    # ---- AI / Embeddings ------------------------------------
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32
    embedding_device: str = "cpu"
    reranker_enabled: bool = False
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ---- FAISS ----------------------------------------------
    faiss_index_path: str = "./data/indexes"
    faiss_index_type: str = "flat_ip"
    faiss_nprobe: int = 10

    # ---- Retrieval ------------------------------------------
    retrieval_top_k: int = 20
    retrieval_rerank_top_k: int = 5
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    rrf_k: int = 60
    bm25_weight: float = 0.4
    semantic_weight: float = 0.6

    # ---- Security -------------------------------------------
    api_key_admin: str = "change-this-admin-api-key"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # ---- Computed properties --------------------------------

    @property
    def allowed_domains_list(self) -> List[str]:
        return [d.strip() for d in self.crawl_allowed_domains.split(",") if d.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def worker_queues_list(self) -> List[str]:
        return [q.strip() for q in self.worker_queues.split(",") if q.strip()]

    @property
    def document_storage_dir(self) -> Path:
        p = Path(self.document_storage_path)
        if not p.is_absolute():
            base_dir = Path(__file__).resolve().parents[3]
            p = (base_dir / p).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def faiss_index_dir(self) -> Path:
        p = Path(self.faiss_index_path)
        if not p.is_absolute():
            base_dir = Path(__file__).resolve().parents[3]
            p = (base_dir / p).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


# Convenience export
settings = get_settings()
