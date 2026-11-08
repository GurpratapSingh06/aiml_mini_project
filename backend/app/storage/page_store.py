"""
VEDANTA — Page Storage
CRUD operations for crawled web pages.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, update, func
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models import Page, PageStatus

logger = get_logger(__name__)


def _page_to_dict(page: Page) -> dict:
    return {
        "id": str(page.id),
        "url": page.url,
        "canonical_url": page.canonical_url,
        "title": page.title,
        "status": page.status.value if page.status else None,
        "content_hash": page.content_hash,
        "content_type": page.content_type,
        "http_status": page.http_status,
        "crawl_depth": page.crawl_depth,
        "parent_url": page.parent_url,
        "last_crawled_at": page.last_crawled_at.isoformat() if page.last_crawled_at else None,
        "created_at": page.created_at.isoformat() if page.created_at else None,
    }


async def get_pages(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
) -> List[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(Page).order_by(Page.created_at.desc()).limit(limit).offset(offset)
            if status:
                stmt = stmt.where(Page.status == status)
            result = await db.execute(stmt)
            pages = result.scalars().all()
            return [_page_to_dict(p) for p in pages]
        except Exception as e:
            logger.error("get_pages failed", error=str(e))
            return []


async def get_page_by_url(url: str) -> Optional[dict]:
    async with get_db_context() as db:
        try:
            stmt = select(Page).where(Page.url == url)
            result = await db.execute(stmt)
            page = result.scalar_one_or_none()
            return _page_to_dict(page) if page else None
        except Exception as e:
            logger.error("get_page_by_url failed", url=url, error=str(e))
            return None


async def upsert_page(data: dict) -> Optional[str]:
    """Insert or update a page. Returns page_id."""
    import uuid
    from datetime import datetime, timezone

    async with get_db_context() as db:
        try:
            # Check if exists
            stmt = select(Page).where(Page.url == data["url"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update
                for key, value in data.items():
                    if hasattr(existing, key) and key not in ("id", "created_at"):
                        setattr(existing, key, value)
                db.add(existing)
                return str(existing.id)
            else:
                # Insert
                page = Page(
                    id=uuid.uuid4(),
                    **{k: v for k, v in data.items() if hasattr(Page, k)}
                )
                db.add(page)
                await db.flush()
                return str(page.id)
        except Exception as e:
            logger.error("upsert_page failed", url=data.get("url"), error=str(e))
            return None


async def update_page_status(page_id: str, status: str, updates: dict = None) -> None:
    async with get_db_context() as db:
        try:
            import uuid
            from datetime import datetime, timezone
            stmt = select(Page).where(Page.id == uuid.UUID(page_id))
            result = await db.execute(stmt)
            page = result.scalar_one_or_none()
            if page:
                page.status = status
                if updates:
                    for k, v in updates.items():
                        if hasattr(page, k):
                            setattr(page, k, v)
                db.add(page)
        except Exception as e:
            logger.error("update_page_status failed", page_id=page_id, error=str(e))


async def get_page_count() -> int:
    async with get_db_context() as db:
        try:
            result = await db.execute(select(func.count(Page.id)))
            return result.scalar() or 0
        except Exception as e:
            logger.error("get_page_count failed", error=str(e))
            return 0
