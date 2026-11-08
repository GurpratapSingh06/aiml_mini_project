"""
VEDANTA — Background Worker Tasks
Job functions executed by RQ workers.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_redis_conn():
    import redis
    return redis.from_url(settings.redis_url)


def _get_queue(name: str):
    from rq import Queue
    return Queue(name, connection=_get_redis_conn())


# ---- Enqueue Helpers -------------------------------------

def enqueue_crawl(
    job_id: str,
    start_url: str,
    max_depth: int = 5,
    max_pages: int = 1000,
    allowed_domains: List[str] = None,
    follow_sitemaps: bool = True,
    crawl_pdfs: bool = True,
) -> object:
    """Enqueue a crawl job to the 'crawl' queue."""
    try:
        q = _get_queue("crawl")
        job = q.enqueue(
            run_crawl_job,
            job_id=job_id,
            start_url=start_url,
            max_depth=max_depth,
            max_pages=max_pages,
            allowed_domains=allowed_domains or settings.allowed_domains_list,
            follow_sitemaps=follow_sitemaps,
            crawl_pdfs=crawl_pdfs,
            job_timeout=7200,  # 2 hours
        )
        logger.info("Crawl job enqueued", job_id=job_id, rq_job_id=job.id)
        return job
    except Exception as e:
        logger.error("Failed to enqueue crawl job", error=str(e))
        raise


def enqueue_process_document(document_id: str, source_url: str) -> object:
    """Enqueue document processing to the 'document' queue."""
    try:
        q = _get_queue("document")
        job = q.enqueue(
            run_document_processing,
            document_id=document_id,
            source_url=source_url,
            job_timeout=1800,  # 30 minutes for OCR
        )
        logger.info("Document processing enqueued", document_id=document_id)
        return job
    except Exception as e:
        logger.error("Failed to enqueue document processing", error=str(e))
        raise


def enqueue_generate_embeddings(chunk_ids: List[str]) -> object:
    """Enqueue embedding generation to the 'embedding' queue."""
    try:
        q = _get_queue("embedding")
        job = q.enqueue(
            run_embedding_generation,
            chunk_ids=chunk_ids,
            job_timeout=3600,
        )
        logger.info("Embedding generation enqueued", chunks=len(chunk_ids))
        return job
    except Exception as e:
        logger.error("Failed to enqueue embedding generation", error=str(e))
        raise


def enqueue_reindex() -> object:
    """Enqueue a full FAISS reindex."""
    try:
        q = _get_queue("default")
        job = q.enqueue(run_full_reindex, job_timeout=7200)
        logger.info("Reindex job enqueued")
        return job
    except Exception as e:
        logger.error("Failed to enqueue reindex", error=str(e))
        raise


# ---- Actual Task Functions (called by RQ) ----------------

def run_crawl_job(
    job_id: str,
    start_url: str,
    max_depth: int = 5,
    max_pages: int = 1000,
    allowed_domains: List[str] = None,
    follow_sitemaps: bool = True,
    crawl_pdfs: bool = True,
) -> dict:
    """Execute a full website crawl and persist results."""
    logger.info("Crawl task started", job_id=job_id, start_url=start_url)

    async def _run():
        from app.ingestion.crawler.crawler import InstitutionalCrawler, CrawlerConfig
        from app.ingestion.parsers.chunker import TextChunker
        from app.ingestion.parsers.content_extractor import ContentExtractor

        config = CrawlerConfig(
            allowed_domains=allowed_domains or settings.allowed_domains_list,
            max_depth=max_depth,
            max_pages=max_pages,
            follow_sitemaps=follow_sitemaps,
            crawl_pdfs=crawl_pdfs,
        )

        crawler = InstitutionalCrawler(config)
        stats = await crawler.crawl(start_url=start_url, job_id=job_id)

        # Process results: chunk and index
        chunker = TextChunker()
        all_chunks = []

        for result in crawler.results:
            if not result.content or result.metadata.get("unchanged"):
                continue

            # Persist page to DB
            try:
                from app.storage.page_store import upsert_page
                from datetime import datetime, timezone
                await upsert_page({
                    "url": result.url,
                    "title": result.title,
                    "content": result.content[:100000],  # Limit stored content
                    "content_hash": result.content_hash,
                    "content_type": result.content_type,
                    "http_status": result.http_status,
                    "crawl_depth": result.crawl_depth,
                    "parent_url": result.parent_url,
                    "etag": result.etag,
                    "last_modified": result.last_modified,
                    "last_crawled_at": datetime.now(timezone.utc),
                    "status": "processed",
                    "institution_id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
                })
            except Exception as e:
                logger.error("Failed to persist page", url=result.url, error=str(e))

            # Create chunks
            if result.content:
                chunks = chunker.chunk(
                    text=result.content,
                    source_url=result.url,
                    source_title=result.title,
                )
                for chunk in chunks:
                    all_chunks.append({
                        "chunk_id": str(uuid.uuid4()),
                        "text": chunk.text,
                        "source_url": result.url,
                        "source_title": result.title,
                        "page_number": None,
                    })

        # Add chunks to retrieval index
        if all_chunks:
            logger.info("Adding chunks to retrieval index", count=len(all_chunks))
            from app.retrieval.pipeline import get_retrieval_pipeline
            pipeline = get_retrieval_pipeline()
            pipeline.add_chunks(all_chunks)

        return stats

    result = asyncio.run(_run())
    logger.info("Crawl task completed", job_id=job_id, stats=result)
    return result


def run_document_processing(document_id: str, source_url: str) -> dict:
    """Process a PDF document and add its content to the index."""
    logger.info("Document processing started", document_id=document_id)

    async def _run():
        from app.storage.document_store import get_document_by_id, update_document_status
        from app.ingestion.document_processor.pdf_processor import PDFProcessor
        from app.ingestion.parsers.chunker import TextChunker
        from app.retrieval.pipeline import get_retrieval_pipeline

        # Get document record
        doc = await get_document_by_id(document_id)
        if not doc:
            logger.error("Document not found", document_id=document_id)
            return {"error": "Document not found"}

        await update_document_status(document_id, "processing")

        # Process PDF
        processor = PDFProcessor()
        result = await processor.download_and_process(source_url, source_url)

        if result.error:
            await update_document_status(document_id, "failed", {"error_message": result.error})
            return {"error": result.error}

        # Chunk the content
        chunker = TextChunker()
        all_chunks = []

        for page in result.pages:
            page_text = page.ocr_text if page.is_scanned else page.text
            if not page_text:
                continue
            chunks = chunker.chunk(
                text=page_text,
                source_url=source_url,
                document_id=document_id,
                page_number=page.page_number,
            )
            for chunk in chunks:
                all_chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "text": chunk.text,
                    "source_url": source_url,
                    "source_title": result.title or "",
                    "page_number": page.page_number,
                })

        # Index chunks
        if all_chunks:
            pipeline = get_retrieval_pipeline()
            pipeline.add_chunks(all_chunks)

        await update_document_status(document_id, "processed", {
            "page_count": result.page_count,
            "is_scanned": result.is_scanned,
            "academic_year": result.academic_year,
            "ocr_confidence": result.overall_ocr_confidence,
        })

        return {"chunks_indexed": len(all_chunks), "pages": result.page_count}

    result = asyncio.run(_run())
    logger.info("Document processing completed", document_id=document_id)
    return result


def run_embedding_generation(chunk_ids: List[str]) -> dict:
    """Generate and persist embeddings for a list of chunk IDs."""
    logger.info("Embedding generation started", chunks=len(chunk_ids))
    # This is handled inline by add_chunks in the pipeline
    # This task is a hook for explicit embedding regeneration
    return {"status": "ok", "chunks": len(chunk_ids)}


def run_full_reindex() -> dict:
    """Rebuild all retrieval indexes from the database."""
    logger.info("Full reindex started")

    async def _run():
        # In a real implementation, load all chunks from DB
        # For now, log and return
        from app.retrieval.pipeline import get_retrieval_pipeline
        pipeline = get_retrieval_pipeline()
        logger.info(
            "Reindex: current index state",
            bm25_docs=pipeline.bm25.num_docs,
            faiss_vectors=pipeline.faiss.num_vectors,
        )
        return {"status": "ok"}

    return asyncio.run(_run())
