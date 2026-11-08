"""VEDANTA — Document storage."""
from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import select
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models import Document

logger = get_logger(__name__)


def _doc_to_dict(doc: Document) -> dict:
    return {
        "id": str(doc.id),
        "source_url": doc.source_url,
        "file_name": doc.file_name,
        "document_type": doc.document_type.value if doc.document_type else None,
        "status": doc.status.value if doc.status else None,
        "page_count": doc.page_count,
        "academic_year": doc.academic_year,
        "ocr_confidence": doc.ocr_confidence,
        "is_scanned": doc.is_scanned,
        "title": doc.title,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


async def get_documents(limit=50, offset=0, status=None, doc_type=None) -> List[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
            if status:
                stmt = stmt.where(Document.status == status)
            if doc_type:
                stmt = stmt.where(Document.document_type == doc_type)
            result = await db.execute(stmt)
            return [_doc_to_dict(d) for d in result.scalars().all()]
        except Exception as e:
            logger.error("get_documents failed", error=str(e))
            return []


async def get_document_by_id(doc_id: str) -> Optional[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(Document).where(Document.id == uuid.UUID(doc_id))
            result = await db.execute(stmt)
            doc = result.scalar_one_or_none()
            return _doc_to_dict(doc) if doc else None
        except Exception as e:
            return None


async def get_document_by_hash(file_hash: str) -> Optional[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(Document).where(Document.file_hash == file_hash)
            result = await db.execute(stmt)
            doc = result.scalar_one_or_none()
            return _doc_to_dict(doc) if doc else None
        except Exception as e:
            return None


async def create_document(data: dict) -> Optional[str]:
    async with get_db_context() as db:
        try:
            doc = Document(id=uuid.uuid4(), **{k: v for k, v in data.items() if hasattr(Document, k)})
            db.add(doc)
            await db.flush()
            return str(doc.id)
        except Exception as e:
            logger.error("create_document failed", error=str(e))
            return None


async def update_document_status(doc_id: str, status: str, updates: dict = None) -> None:
    async with get_db_context() as db:
        try:
            stmt = select(Document).where(Document.id == uuid.UUID(doc_id))
            result = await db.execute(stmt)
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = status
                if updates:
                    for k, v in updates.items():
                        if hasattr(doc, k):
                            setattr(doc, k, v)
                db.add(doc)
        except Exception as e:
            logger.error("update_document_status failed", error=str(e))
