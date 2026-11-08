"""VEDANTA — Admin endpoints (require API key auth)."""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


def require_admin_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Validate admin API key."""
    if not x_api_key or x_api_key != settings.api_key_admin:
        raise HTTPException(status_code=401, detail="Invalid or missing admin API key")


@router.get("/status", summary="System status (admin)")
async def admin_status(_: None = Depends(require_admin_key)) -> Dict[str, Any]:
    """Full system status including index sizes, model info, etc."""
    return {
        "app": "vedanta",
        "version": settings.app_version,
        "environment": settings.app_env,
        "embedding_model": settings.embedding_model,
        "faiss_index_path": settings.faiss_index_path,
        "crawl_start_url": settings.crawl_start_url,
        "allowed_domains": settings.allowed_domains_list,
    }


@router.post("/reindex", summary="Trigger full reindex (admin)")
async def trigger_reindex(_: None = Depends(require_admin_key)) -> Dict[str, str]:
    """Trigger a full reindex of all content chunks."""
    try:
        from app.workers.tasks import enqueue_reindex
        enqueue_reindex()
        return {"status": "enqueued", "message": "Reindex job has been queued"}
    except Exception as e:
        logger.error("Could not enqueue reindex", error=str(e))
        raise HTTPException(status_code=500, detail=f"Could not enqueue reindex: {e}")


@router.post("/cache/clear", summary="Clear caches (admin)")
async def clear_cache(_: None = Depends(require_admin_key)) -> Dict[str, str]:
    """Clear all Redis caches."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.flushdb()
        await r.aclose()
        return {"status": "ok", "message": "Cache cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {e}")
