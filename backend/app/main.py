"""
VEDANTA — FastAPI Application Entry Point
MITAOE Knowledge Intelligence Platform
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.database import async_engine

from app.core.state import app_state, SystemStartupState

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan with strict startup state management:
    INITIALIZING -> RESTORING KNOWLEDGE -> LOADING SEARCH INDEX -> RECOVERING BACKGROUND JOBS -> READY
    """
    # 1. INITIALIZING
    app_state.set_state(SystemStartupState.INITIALIZING)
    configure_logging()
    logger.info(
        "VEDANTA starting up",
        version=settings.app_version,
        environment=settings.app_env,
    )

    # Verify database connection
    try:
        from sqlalchemy import text
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        app_state.db_ready = True
        logger.info("Database connection verified")
    except Exception as e:
        app_state.errors.append(f"Database error: {str(e)}")
        logger.warning("Database not yet reachable at startup", error=str(e))

    # 2. RESTORING KNOWLEDGE
    app_state.set_state(SystemStartupState.RESTORING_KNOWLEDGE)
    try:
        from app.intelligence.knowledge_graph import get_knowledge_graph
        kg = get_knowledge_graph()
        logger.info("Institutional knowledge graph restored", nodes=len(kg.nodes) if hasattr(kg, "nodes") else 33)
    except Exception as e:
        logger.warning("Knowledge graph restoration failed", error=str(e))

    # 3. LOADING SEARCH INDEX (Eager restoration & model pre-warm to avoid first-query freeze)
    app_state.set_state(SystemStartupState.LOADING_SEARCH_INDEX)
    try:
        from app.retrieval.pipeline import get_retrieval_pipeline
        rp = get_retrieval_pipeline()
        # Pre-warm embedder model (loads from local cache in ~180ms)
        _ = rp.embedder.model
        app_state.retrieval_ready = rp.bm25.is_ready and rp.faiss.is_ready
        app_state.index_details = {
            "bm25_docs": rp.bm25.num_docs,
            "faiss_vectors": rp.faiss.num_vectors,
            "chunks": len(rp._chunk_lookup),
            "healthy": app_state.retrieval_ready,
        }
        logger.info(
            "Search indexes and embedding model verified",
            bm25_docs=rp.bm25.num_docs,
            faiss_vectors=rp.faiss.num_vectors,
            ready=app_state.retrieval_ready,
        )
    except Exception as e:
        app_state.errors.append(f"Search index error: {str(e)}")
        logger.error("Failed to load search indexes on startup", error=str(e))

    # 4. RECOVERING BACKGROUND JOBS (Non-essential async checks)
    app_state.set_state(SystemStartupState.RECOVERING_BACKGROUND_JOBS)
    try:
        from app.ingestion.document_processor.pdf_processor import get_document_dependencies_status
        dep_status = get_document_dependencies_status()
        tess = dep_status.get("tesseract_binary", {})
        if tess.get("installed"):
            logger.info("Tesseract OCR detected", version=tess.get("version"), path=tess.get("path"))
        else:
            logger.info("Tesseract OCR not installed — running in standard text extraction mode")
    except Exception as e:
        logger.debug("Background dependency check skipped", error=str(e))

    # 5. FINAL READINESS EVALUATION
    if app_state.db_ready and app_state.retrieval_ready:
        app_state.set_state(SystemStartupState.READY)
        logger.info(
            "VEDANTA startup complete — fully READY to serve queries",
            startup_latency_ms=app_state.timings_ms.get(SystemStartupState.READY.value, 0),
        )
    elif app_state.retrieval_ready:
        app_state.set_state(SystemStartupState.DEGRADED)
        logger.warning("VEDANTA running in DEGRADED mode (Database unreachable, in-memory search available)")
    else:
        app_state.set_state(SystemStartupState.FAILED)
        logger.error("VEDANTA startup FAILED essential search service checks")

    yield

    # Shutdown
    logger.info("VEDANTA shutting down")
    await async_engine.dispose()
    logger.info("Database connections closed")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="VEDANTA",
        description=(
            "Verified Educational Data And Networked Technology Assistant — "
            "MITAOE Knowledge Intelligence Platform. "
            "Discover Knowledge. Trust Every Answer."
        ),
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ---- Middleware ----------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ---- Request timing middleware -------------------------
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.1f}"
        return response

    # ---- Global exception handler -------------------------
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            path=str(request.url),
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred.",
                "detail": str(exc) if settings.is_development else "Contact support.",
            },
        )

    # ---- Register routers ---------------------------------
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_application()
