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
    version: str
    environment: str
    uptime_seconds: float
    timestamp: str
    services: Dict[str, ServiceHealth]


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
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        latency = (time.perf_counter() - t0) * 1000
        return ServiceHealth(status="ok", latency_ms=round(latency, 2))
    except Exception as e:
        return ServiceHealth(status="down", detail=str(e))


@router.get("", response_model=HealthResponse, summary="System health check")
async def health_check() -> HealthResponse:
    """
    Returns the health status of VEDANTA and all dependent services.
    Use this endpoint for load balancer and monitoring health probes.
    """
    db_health = await _check_database()
    redis_health = await _check_redis()

    services = {
        "database": db_health,
        "redis": redis_health,
    }

    # Overall status
    all_ok = all(s.status == "ok" for s in services.values())
    any_down = any(s.status == "down" for s in services.values())

    if all_ok:
        overall = "ok"
    elif any_down:
        overall = "degraded"
    else:
        overall = "degraded"

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        environment=settings.app_env,
        uptime_seconds=round(time.time() - _startup_time, 1),
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services,
    )


@router.get("/ping", summary="Simple ping")
async def ping() -> Dict[str, str]:
    """Lightweight ping for load balancers — no service checks."""
    return {"status": "ok", "app": "vedanta"}
