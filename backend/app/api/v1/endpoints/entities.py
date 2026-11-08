"""VEDANTA — Entity endpoints."""
from fastapi import APIRouter, Query
from typing import List, Optional
from pydantic import BaseModel
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class EntityResponse(BaseModel):
    id: str
    entity_type: str
    canonical_name: str
    description: Optional[str]
    aliases: List[str]


@router.get("", response_model=List[EntityResponse], summary="List entities")
async def list_entities(
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """List extracted institutional entities (people, departments, etc.)."""
    try:
        from app.storage.entity_store import get_entities
        return await get_entities(entity_type=entity_type, limit=limit)
    except Exception as e:
        logger.warning("Could not fetch entities", error=str(e))
        return []


@router.get("/search", summary="Search entities")
async def search_entities(q: str = Query(..., min_length=1)):
    """Search for entities by name or alias."""
    try:
        from app.storage.entity_store import search_entities_by_name
        return await search_entities_by_name(q)
    except Exception as e:
        logger.warning("Entity search failed", error=str(e))
        return []
