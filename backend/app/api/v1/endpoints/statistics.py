"""VEDANTA — Statistics endpoints."""
from fastapi import APIRouter, Query
from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class PlacementStats(BaseModel):
    department: Optional[str] = None
    academic_year: str
    total_students: Optional[int] = None
    students_placed: Optional[int] = None
    highest_package_lpa: Optional[float] = None
    average_package_lpa: Optional[float] = None
    source_url: Optional[str] = None
    record_type: Optional[str] = None
    package_distribution: Optional[Any] = None
    companies_visited: Optional[int] = None
    offers_made: Optional[int] = None


@router.get("/placements", response_model=List[PlacementStats], summary="Placement statistics")
async def get_placement_stats(
    department: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
):
    """Retrieve structured placement statistics from the knowledge base."""
    try:
        from app.storage.stats_store import get_placement_records
        return await get_placement_records(department=department, academic_year=academic_year)
    except Exception as e:
        logger.warning("Could not fetch placement stats", error=str(e))
        return []


@router.get("/fees", summary="Fee structure")
async def get_fee_structure(
    department: Optional[str] = Query(None),
    academic_year: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    """Retrieve structured fee information from the knowledge base."""
    try:
        from app.storage.stats_store import get_fee_records
        return await get_fee_records(department=department, academic_year=academic_year, category=category)
    except Exception as e:
        logger.warning("Could not fetch fee records", error=str(e))
        return []
