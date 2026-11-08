"""
VEDANTA — Document Management Endpoints
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class DocumentSummary(BaseModel):
    id: str
    source_url: str
    file_name: Optional[str]
    document_type: str
    status: str
    page_count: Optional[int]
    academic_year: Optional[str]
    ocr_confidence: Optional[float]
    created_at: str


@router.get("", response_model=List[DocumentSummary], summary="List documents")
async def list_documents(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
) -> List[DocumentSummary]:
    """List all processed documents."""
    try:
        from app.storage.document_store import get_documents
        return await get_documents(limit=limit, offset=offset, status=status, doc_type=document_type)
    except Exception as e:
        logger.warning("Could not fetch documents", error=str(e))
        return []


@router.get("/{document_id}", summary="Get document details")
async def get_document(document_id: str):
    """Get detailed information about a specific document."""
    try:
        from app.storage.document_store import get_document_by_id
        doc = await get_document_by_id(document_id)
        if not doc:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except Exception as e:
        logger.error("Error fetching document", document_id=document_id, error=str(e))
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Error fetching document")
