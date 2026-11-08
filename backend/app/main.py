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

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    # Startup
    configure_logging()
    logger.info(
        "VEDANTA starting up",
        version=settings.app_version,
        environment=settings.app_env,
    )

    # Verify database connection
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(lambda c: c.execute(c.connection.cursor().connection.cursor().__class__.__mro__[0].__subclasses__()[0] if False else None) if False else None)
        logger.info("Database connection verified")
    except Exception as e:
        logger.warning("Database not yet reachable at startup", error=str(e))

    # Load models in background (non-blocking)
    logger.info("VEDANTA startup complete — ready to serve requests")

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
