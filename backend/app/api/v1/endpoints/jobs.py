"""VEDANTA — Processing jobs endpoints."""
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class JobResponse(BaseModel):
    id: str
    job_type: str
    status: str
    queue_name: Optional[str]
    attempts: int
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]


@router.get("", response_model=List[JobResponse], summary="List processing jobs")
async def list_jobs(
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List all background processing jobs."""
    try:
        from app.storage.job_store import get_jobs
        return await get_jobs(status=status, job_type=job_type, limit=limit)
    except Exception as e:
        logger.warning("Could not fetch jobs", error=str(e))
        return []
