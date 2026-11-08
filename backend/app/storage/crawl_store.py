"""
VEDANTA — Crawl Job Storage
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models import CrawlJob, CrawlStatus

logger = get_logger(__name__)


def _job_to_dict(job: CrawlJob) -> dict:
    duration = None
    if job.started_at and job.completed_at:
        duration = (job.completed_at - job.started_at).total_seconds()

    return {
        "job_id": str(job.id),
        "status": job.status.value if job.status else None,
        "start_url": job.start_url,
        "pages_discovered": job.pages_discovered,
        "pages_crawled": job.pages_crawled,
        "pages_failed": job.pages_failed,
        "pages_skipped": job.pages_skipped,
        "documents_found": job.documents_found,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "duration_seconds": duration,
    }


async def get_crawl_jobs(limit: int = 20, offset: int = 0) -> List[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(CrawlJob).order_by(CrawlJob.created_at.desc()).limit(limit).offset(offset)
            result = await db.execute(stmt)
            jobs = result.scalars().all()
            return [_job_to_dict(j) for j in jobs]
        except Exception as e:
            logger.error("get_crawl_jobs failed", error=str(e))
            return []


async def get_crawl_job_by_id(job_id: str) -> Optional[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(CrawlJob).where(CrawlJob.id == uuid.UUID(job_id))
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            return _job_to_dict(job) if job else None
        except Exception as e:
            logger.error("get_crawl_job_by_id failed", job_id=job_id, error=str(e))
            return None


async def create_crawl_job(data: dict) -> Optional[str]:
    async with get_db_context() as db:
        try:
            job = CrawlJob(id=uuid.uuid4(), **{k: v for k, v in data.items() if hasattr(CrawlJob, k)})
            db.add(job)
            await db.flush()
            return str(job.id)
        except Exception as e:
            logger.error("create_crawl_job failed", error=str(e))
            return None


async def update_crawl_job(job_id: str, updates: dict) -> None:
    async with get_db_context() as db:
        try:
            stmt = select(CrawlJob).where(CrawlJob.id == uuid.UUID(job_id))
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                for k, v in updates.items():
                    if hasattr(job, k):
                        setattr(job, k, v)
                db.add(job)
        except Exception as e:
            logger.error("update_crawl_job failed", job_id=job_id, error=str(e))
