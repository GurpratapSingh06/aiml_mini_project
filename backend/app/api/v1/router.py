"""VEDANTA — API v1 Router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    search,
    crawl,
    documents,
    entities,
    statistics,
    jobs,
    admin,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(search.router, prefix="/search", tags=["Search & Q&A"])
api_router.include_router(crawl.router, prefix="/crawl", tags=["Crawling"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(entities.router, prefix="/entities", tags=["Entities"])
api_router.include_router(statistics.router, prefix="/statistics", tags=["Statistics"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
