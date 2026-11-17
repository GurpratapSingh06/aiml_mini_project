"""
VEDANTA — Health Check Endpoints
Returns system health status for all dependent services.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

_startup_time = time.time()


class ServiceHealth(BaseModel):
    status: str  # ok | degraded | down
    latency_ms: Optional[float] = None
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    startup_state: str
    version: str
    environment: str
    uptime_seconds: float
    timestamp: str
    services: Dict[str, ServiceHealth]
    index_details: Optional[Dict[str, Any]] = None


async def _check_database() -> ServiceHealth:
    """Check PostgreSQL connectivity."""
    try:
        from app.core.database import async_engine
        t0 = time.perf_counter()
        async with async_engine.begin() as conn:
            await conn.execute(conn.sync_connection.cursor().__class__.__mro__[0].__subclasses__()[0] if False else __import__('sqlalchemy').text("SELECT 1"))
        latency = (time.perf_counter() - t0) * 1000
        return ServiceHealth(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        return ServiceHealth(status="down", detail=str(e))


async def _check_redis() -> ServiceHealth:
    """Check Redis connectivity."""
    try:
        import redis.asyncio as aioredis
        t0 = time.perf_counter()
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=0.15, socket_timeout=0.15)
        await r.ping()
        await r.aclose()
        latency = (time.perf_counter() - t0) * 1000
        return ServiceHealth(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        return ServiceHealth(status="down", detail=str(e))


async def _check_document_pipeline() -> ServiceHealth:
    """Check document processing libraries and OCR engine."""
    try:
        from app.ingestion.document_processor.pdf_processor import get_document_dependencies_status
        deps = get_document_dependencies_status()
        core_ok = (
            deps.get("pymupdf", {}).get("installed", False) and
            deps.get("pillow", {}).get("installed", False) and
            deps.get("numpy", {}).get("installed", False) and
            deps.get("pandas", {}).get("installed", False)
        )
        tess_installed = deps.get("tesseract_binary", {}).get("installed", False)
        if core_ok and tess_installed:
            return ServiceHealth(
                status="ok",
                detail="All PDF processing and Tesseract OCR components operational"
            )
        elif core_ok:
            return ServiceHealth(
                status="degraded",
                detail="Core PDF/table processing ready. Tesseract binary not installed (scanned PDF OCR unavailable)"
            )
        else:
            missing = [k for k, v in deps.items() if not v.get("installed")]
            return ServiceHealth(
                status="down",
                detail=f"Missing required document processing dependencies: {', '.join(missing)}"
            )
    except Exception as e:
        return ServiceHealth(status="down", detail=str(e))


@router.get("", response_model=HealthResponse, summary="System health check")
async def health_check() -> HealthResponse:
    """
    Returns the health status of VEDANTA and all dependent services.
    Use this endpoint for load balancer and monitoring health probes.
    """
    import asyncio
    db_health, redis_health, doc_health = await asyncio.gather(
        _check_database(),
        _check_redis(),
        _check_document_pipeline(),
    )

    from app.core.state import app_state

    # Search index service health
    search_status = "ok" if app_state.retrieval_ready else "degraded"
    search_health = ServiceHealth(
        status=search_status,
        detail=f"BM25 docs: {app_state.index_details.get('bm25_docs', 0)}, FAISS vectors: {app_state.index_details.get('faiss_vectors', 0)}"
    )

    services = {
        "database": db_health,
        "search_index": search_health,
        "document_pipeline": doc_health,
    }
    if getattr(settings, "redis_enabled", False):
        services["redis"] = redis_health

    # Overall status based on essential startup state
    overall = "ok" if app_state.state.value == "READY" else ("degraded" if app_state.state.value == "DEGRADED" else "down")

    return HealthResponse(
        status=overall,
        startup_state=app_state.state.value,
        version=settings.app_version,
        environment=settings.app_env,
        uptime_seconds=round(time.time() - _startup_time, 1),
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
        index_details=app_state.index_details,
    )


@router.get("/ping", summary="Simple ping")
async def ping() -> Dict[str, str]:
    """Lightweight ping for load balancers — no service checks."""
    return {"status": "ok", "app": "vedanta"}


@router.get("/dependencies", summary="Document processing dependencies check")
async def dependencies_check() -> Dict[str, Any]:
    """
    Returns installation status and versions of all PDF processing,
    OCR, and image preprocessing components.
    """
    from app.ingestion.document_processor.pdf_processor import get_document_dependencies_status
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": get_document_dependencies_status(),
    }
