"""VEDANTA — Entity, stats, and job stores."""
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import select, or_
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models import Entity, EntityAlias, PlacementRecord, FeeRecord, ProcessingJob

logger = get_logger(__name__)

# ---- Entity Store ----------------------------------------

async def get_entities(entity_type: Optional[str] = None, limit: int = 50) -> List[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(Entity).limit(limit)
            if entity_type:
                stmt = stmt.where(Entity.entity_type == entity_type)
            result = await db.execute(stmt)
            entities = result.scalars().all()
            return [
                {
                    "id": str(e.id),
                    "entity_type": e.entity_type.value if e.entity_type else None,
                    "canonical_name": e.canonical_name,
                    "description": e.description,
                    "aliases": [],
                }
                for e in entities
            ]
        except Exception as e:
            logger.error("get_entities failed", error=str(e))
            return []


async def search_entities_by_name(query: str) -> List[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(Entity).where(
                or_(
                    Entity.canonical_name.ilike(f"%{query}%"),
                )
            ).limit(20)
            result = await db.execute(stmt)
            return [
                {"id": str(e.id), "canonical_name": e.canonical_name, "entity_type": e.entity_type.value if e.entity_type else None}
                for e in result.scalars().all()
            ]
        except Exception as e:
            return []


async def upsert_entity(data: dict) -> Optional[str]:
    async with get_db_context() as db:
        try:
            entity = Entity(id=uuid.uuid4(), **{k: v for k, v in data.items() if hasattr(Entity, k)})
            db.add(entity)
            await db.flush()
            return str(entity.id)
        except Exception as e:
            logger.error("upsert_entity failed", error=str(e))
            return None


# ---- Stats Store -----------------------------------------

async def get_placement_records(department=None, academic_year=None) -> List[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(PlacementRecord)
            if department:
                stmt = stmt.where(PlacementRecord.academic_year == academic_year)
            if academic_year:
                stmt = stmt.where(PlacementRecord.academic_year == academic_year)
            result = await db.execute(stmt)
            return [
                {
                    "department": str(r.department_id) if r.department_id else None,
                    "academic_year": r.academic_year,
                    "total_students": r.total_students,
                    "students_placed": r.students_placed,
                    "highest_package_lpa": r.highest_package_lpa,
                    "average_package_lpa": r.average_package_lpa,
                    "source_url": r.source_url,
                }
                for r in result.scalars().all()
            ]
        except Exception as e:
            logger.error("get_placement_records failed", error=str(e))
            return []


async def get_fee_records(department=None, academic_year=None, category=None) -> List[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(FeeRecord)
            if academic_year:
                stmt = stmt.where(FeeRecord.academic_year == academic_year)
            if category:
                stmt = stmt.where(FeeRecord.admission_category == category)
            result = await db.execute(stmt)
            return [
                {
                    "department": str(r.department_id) if r.department_id else None,
                    "academic_year": r.academic_year,
                    "fee_type": r.fee_type,
                    "admission_category": r.admission_category,
                    "amount_inr": r.amount_inr,
                    "source_url": r.source_url,
                }
                for r in result.scalars().all()
            ]
        except Exception as e:
            return []


# ---- Job Store -------------------------------------------

async def get_jobs(status=None, job_type=None, limit=50) -> List[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(ProcessingJob).order_by(ProcessingJob.created_at.desc()).limit(limit)
            if status:
                stmt = stmt.where(ProcessingJob.status == status)
            if job_type:
                stmt = stmt.where(ProcessingJob.job_type == job_type)
            result = await db.execute(stmt)
            return [
                {
                    "id": str(j.id),
                    "job_type": j.job_type,
                    "status": j.status.value if j.status else None,
                    "queue_name": j.queue_name,
                    "attempts": j.attempts,
                    "created_at": j.created_at.isoformat() if j.created_at else None,
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                    "error_message": j.error_message,
                }
                for j in result.scalars().all()
            ]
        except Exception as e:
            return []


async def create_job(data: dict) -> Optional[str]:
    async with get_db_context() as db:
        try:
            job = ProcessingJob(id=uuid.uuid4(), **{k: v for k, v in data.items() if hasattr(ProcessingJob, k)})
            db.add(job)
            await db.flush()
            return str(job.id)
        except Exception as e:
            return None


async def update_job_status(job_id: str, status: str, updates: dict = None) -> None:
    async with get_db_context() as db:
        try:
            stmt = select(ProcessingJob).where(ProcessingJob.id == uuid.UUID(job_id))
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                job.status = status
                if updates:
                    for k, v in updates.items():
                        if hasattr(job, k):
                            setattr(job, k, v)
                db.add(job)
        except Exception as e:
            logger.error("update_job_status failed", error=str(e))
