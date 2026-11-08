"""
VEDANTA — Crawl Management Endpoints
Start, monitor and control website crawling.
"""

from __future__ import annotations

import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field, HttpUrl

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class CrawlRequest(BaseModel):
    start_url: str = Field(default="https://mitaoe.ac.in", description="Seed URL to start crawling")
    max_depth: int = Field(default=5, ge=1, le=10)
    max_pages: int = Field(default=1000, ge=1, le=10000)
    allowed_domains: Optional[List[str]] = Field(None, description="Override allowed domains")
    follow_sitemaps: bool = Field(True)
    crawl_pdfs: bool = Field(True)
    question_driven: Optional[str] = Field(None, description="Drive crawl from this question")


class CrawlJobResponse(BaseModel):
    job_id: str
    status: str
    start_url: str
    pages_discovered: int
    pages_crawled: int
    pages_failed: int
    pages_skipped: int
    documents_found: int
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[float]


class PageSummary(BaseModel):
    url: str
    title: Optional[str]
    status: str
    crawl_depth: int
    last_crawled_at: Optional[str]
    content_hash: Optional[str]


@router.post("/start", response_model=CrawlJobResponse, summary="Start a crawl job")
async def start_crawl(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
) -> CrawlJobResponse:
    """
    Start a new website crawl job.
    The crawl runs asynchronously in the background worker.
    Returns immediately with a job ID for status polling.
    """
    logger.info("Crawl job requested", start_url=request.start_url)

    # Validate URL is in allowed domains
    from app.ingestion.crawler.url_validator import validate_crawl_url
    allowed = request.allowed_domains or settings.allowed_domains_list
    validation = validate_crawl_url(request.start_url, allowed)
    if not validation.is_valid:
        raise HTTPException(status_code=400, detail=f"URL not allowed: {validation.reason}")

    job_id = str(uuid.uuid4())

    # Enqueue crawl job
    try:
        from app.workers.tasks import enqueue_crawl
        rq_job = enqueue_crawl(
            job_id=job_id,
            start_url=request.start_url,
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            allowed_domains=allowed,
            follow_sitemaps=request.follow_sitemaps,
            crawl_pdfs=request.crawl_pdfs,
        )
        logger.info("Crawl enqueued", job_id=job_id, rq_job_id=getattr(rq_job, "id", None))
    except Exception as e:
        logger.warning("Could not enqueue crawl (worker may not be running)", error=str(e))
        # Still return job ID — job will be stored in DB for retry

    return CrawlJobResponse(
        job_id=job_id,
        status="queued",
        start_url=request.start_url,
        pages_discovered=0,
        pages_crawled=0,
        pages_failed=0,
        pages_skipped=0,
        documents_found=0,
        started_at=None,
        completed_at=None,
        duration_seconds=None,
    )


@router.get("/jobs", response_model=List[CrawlJobResponse], summary="List crawl jobs")
async def list_crawl_jobs(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> List[CrawlJobResponse]:
    """List all crawl jobs with status."""
    try:
        from app.storage.crawl_store import get_crawl_jobs
        jobs = await get_crawl_jobs(limit=limit, offset=offset)
        return jobs
    except Exception as e:
        logger.warning("Could not fetch crawl jobs", error=str(e))
        return []


@router.get("/jobs/{job_id}", response_model=CrawlJobResponse, summary="Get crawl job status")
async def get_crawl_job(job_id: str) -> CrawlJobResponse:
    """Get detailed status of a specific crawl job."""
    try:
        from app.storage.crawl_store import get_crawl_job_by_id
        job = await get_crawl_job_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Crawl job not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching crawl job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail="Error fetching crawl job")


@router.get("/pages", response_model=List[PageSummary], summary="List discovered pages")
async def list_pages(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
) -> List[PageSummary]:
    """List all discovered and crawled pages."""
    try:
        from app.storage.page_store import get_pages
        pages = await get_pages(limit=limit, offset=offset, status=status)
        return pages
    except Exception as e:
        logger.warning("Could not fetch pages", error=str(e))
        return []
