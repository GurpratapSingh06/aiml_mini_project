"""
VEDANTA — Institutional Website Crawler
Polite, incremental, SSRF-safe crawler for institutional websites.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Set
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.logging import get_logger
from app.ingestion.crawler.robots import RobotsCache
from app.ingestion.crawler.sitemap import SitemapParser
from app.ingestion.crawler.url_normalizer import (
    is_internal_link,
    is_pdf_url,
    normalize_url,
    should_skip_url,
)
from app.ingestion.crawler.url_validator import validate_crawl_url

logger = get_logger(__name__)


@dataclass
class CrawlResult:
    url: str
    title: str
    content: str
    content_hash: str
    links: List[str]
    pdf_links: List[str]
    http_status: int
    content_type: str
    crawl_depth: int
    parent_url: Optional[str]
    etag: Optional[str]
    last_modified: Optional[str]
    crawled_at: float
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class CrawlerConfig:
    allowed_domains: List[str]
    max_depth: int = 5
    max_pages: int = 5000
    concurrency: int = 5
    delay_seconds: float = 1.0
    request_timeout: int = 30
    max_retries: int = 3
    user_agent: str = settings.crawl_user_agent
    respect_robots: bool = True
    crawl_pdfs: bool = True
    follow_sitemaps: bool = True


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def _extract_text_from_html(html: str, url: str) -> tuple[str, str]:
    """
    Extract title and main text from HTML using trafilatura first,
    then BeautifulSoup as fallback.
    """
    title = ""
    text = ""

    # Try trafilatura for clean text extraction
    try:
        import trafilatura
        extracted = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )
        if extracted:
            text = extracted
    except Exception as e:
        logger.debug("Trafilatura failed, using BS4 fallback", error=str(e))

    # BeautifulSoup for title and fallback text
    try:
        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title_tag = (
            soup.find("title")
            or soup.find("h1")
            or soup.find(attrs={"property": "og:title"})
        )
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Fallback text extraction
        if not text:
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)

    except Exception as e:
        logger.debug("BeautifulSoup extraction error", error=str(e))

    return title, text


def _extract_links(html: str, page_url: str) -> tuple[List[str], List[str]]:
    """Extract all internal links and PDF links from an HTML page."""
    links: List[str] = []
    pdf_links: List[str] = []

    try:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href:
                continue
            abs_url = normalize_url(href, base_url=page_url)
            if should_skip_url(abs_url):
                continue
            if is_pdf_url(abs_url):
                pdf_links.append(abs_url)
            else:
                links.append(abs_url)
    except Exception as e:
        logger.debug("Link extraction error", url=page_url, error=str(e))

    return links, pdf_links


class InstitutionalCrawler:
    """
    Polite, BFS-based institutional website crawler.

    Features:
    - Respects robots.txt
    - Rate-limited with configurable delay
    - SSRF protection via URL validator
    - Incremental (checks content hash before reprocessing)
    - Discovers PDFs
    - Sitemap-aware
    """

    def __init__(self, config: CrawlerConfig):
        self.config = config
        self._robots = RobotsCache(user_agent=config.user_agent)
        self._sitemap = SitemapParser(user_agent=config.user_agent)
        self._semaphore = asyncio.Semaphore(config.concurrency)
        self._visited: Set[str] = set()
        self._results: List[CrawlResult] = []

    async def _fetch_page(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> tuple[int, str, str, dict]:
        """
        Fetch a single page and return (status, content_type, body, headers).
        Returns (304, "", "", {}) if content unchanged.
        """
        headers = {"User-Agent": self.config.user_agent}
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        async with httpx.AsyncClient(
            timeout=self.config.request_timeout,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = await client.get(url)
            content_type = response.headers.get("content-type", "")
            resp_etag = response.headers.get("etag", "")
            resp_last_modified = response.headers.get("last-modified", "")
            resp_headers = {
                "etag": resp_etag,
                "last_modified": resp_last_modified,
                "content_type": content_type,
            }
            return response.status_code, content_type, response.text, resp_headers

    async def _process_url(
        self,
        url: str,
        depth: int,
        parent_url: Optional[str],
        existing_hash: Optional[str] = None,
        existing_etag: Optional[str] = None,
        existing_last_modified: Optional[str] = None,
    ) -> Optional[CrawlResult]:
        """Fetch and process a single URL."""
        async with self._semaphore:
            # Polite delay
            await asyncio.sleep(self.config.delay_seconds)

            # Validate URL
            validation = validate_crawl_url(url, self.config.allowed_domains)
            if not validation.is_valid:
                logger.debug("URL failed validation", url=url, reason=validation.reason)
                return None

            # Robots.txt check
            if self.config.respect_robots:
                if not await self._robots.is_allowed(url):
                    logger.debug("Blocked by robots.txt", url=url)
                    return None

            try:
                status, content_type, body, resp_headers = await self._fetch_page(
                    url,
                    etag=existing_etag,
                    last_modified=existing_last_modified,
                )

                if status == 304:
                    logger.debug("Content unchanged (304)", url=url)
                    return CrawlResult(
                        url=url,
                        title="",
                        content="",
                        content_hash=existing_hash or "",
                        links=[],
                        pdf_links=[],
                        http_status=304,
                        content_type=content_type,
                        crawl_depth=depth,
                        parent_url=parent_url,
                        etag=resp_headers.get("etag"),
                        last_modified=resp_headers.get("last_modified"),
                        crawled_at=time.time(),
                        metadata={"unchanged": True},
                    )

                if status != 200:
                    return CrawlResult(
                        url=url,
                        title="",
                        content="",
                        content_hash="",
                        links=[],
                        pdf_links=[],
                        http_status=status,
                        content_type=content_type,
                        crawl_depth=depth,
                        parent_url=parent_url,
                        etag=None,
                        last_modified=None,
                        crawled_at=time.time(),
                        error=f"HTTP {status}",
                    )

                # Only process HTML
                if "text/html" not in content_type.lower():
                    return None

                content_hash = _sha256(body)

                # Skip if content unchanged (hash comparison)
                if existing_hash and content_hash == existing_hash:
                    logger.debug("Content hash unchanged", url=url)
                    return CrawlResult(
                        url=url,
                        title="",
                        content="",
                        content_hash=content_hash,
                        links=[],
                        pdf_links=[],
                        http_status=status,
                        content_type=content_type,
                        crawl_depth=depth,
                        parent_url=parent_url,
                        etag=resp_headers.get("etag"),
                        last_modified=resp_headers.get("last_modified"),
                        crawled_at=time.time(),
                        metadata={"unchanged": True},
                    )

                title, text = _extract_text_from_html(body, url)
                links, pdf_links = _extract_links(body, url)

                # Filter links to allowed domains only
                links = [
                    l for l in links
                    if is_internal_link(l, self.config.allowed_domains)
                ]

                logger.info(
                    "Page crawled",
                    url=url,
                    depth=depth,
                    links=len(links),
                    pdfs=len(pdf_links),
                    text_chars=len(text),
                )

                return CrawlResult(
                    url=url,
                    title=title,
                    content=text,
                    content_hash=content_hash,
                    links=links,
                    pdf_links=pdf_links,
                    http_status=status,
                    content_type=content_type,
                    crawl_depth=depth,
                    parent_url=parent_url,
                    etag=resp_headers.get("etag"),
                    last_modified=resp_headers.get("last_modified"),
                    crawled_at=time.time(),
                )

            except httpx.TimeoutException:
                logger.warning("Request timed out", url=url)
                return CrawlResult(
                    url=url, title="", content="", content_hash="",
                    links=[], pdf_links=[], http_status=0,
                    content_type="", crawl_depth=depth, parent_url=parent_url,
                    etag=None, last_modified=None, crawled_at=time.time(),
                    error="Timeout",
                )
            except Exception as e:
                logger.error("Crawl error", url=url, error=str(e))
                return CrawlResult(
                    url=url, title="", content="", content_hash="",
                    links=[], pdf_links=[], http_status=0,
                    content_type="", crawl_depth=depth, parent_url=parent_url,
                    etag=None, last_modified=None, crawled_at=time.time(),
                    error=str(e),
                )

    async def crawl(
        self,
        start_url: str,
        job_id: str = "",
        progress_callback=None,
    ) -> dict:
        """
        Main crawl loop using BFS.

        Args:
            start_url: Seed URL
            job_id: Job tracking ID
            progress_callback: Optional async callable(stats) for progress updates

        Returns:
            dict with crawl statistics
        """
        logger.info("Crawl started", start_url=start_url, job_id=job_id)
        start_time = time.time()

        # BFS queue: (url, depth, parent_url)
        queue: deque[tuple[str, int, Optional[str]]] = deque()
        norm_start = normalize_url(start_url)
        queue.append((norm_start, 0, None))
        self._visited.add(norm_start)

        stats = {
            "job_id": job_id,
            "start_url": start_url,
            "pages_discovered": 1,
            "pages_crawled": 0,
            "pages_failed": 0,
            "pages_skipped": 0,
            "pages_unchanged": 0,
            "documents_found": 0,
            "pdf_urls": [],
        }

        # Seed from sitemap first
        if self.config.follow_sitemaps:
            logger.info("Discovering URLs from sitemap", base_url=start_url)
            async for sitemap_url in self._sitemap.discover_urls(start_url):
                loc = normalize_url(sitemap_url.loc)
                if (
                    loc not in self._visited
                    and is_internal_link(loc, self.config.allowed_domains)
                    and not should_skip_url(loc)
                    and len(self._visited) < self.config.max_pages
                ):
                    if is_pdf_url(loc):
                        stats["pdf_urls"].append(loc)
                        stats["documents_found"] += 1
                    else:
                        queue.append((loc, 1, start_url))
                        self._visited.add(loc)
                        stats["pages_discovered"] += 1

        # BFS loop
        while queue and stats["pages_crawled"] < self.config.max_pages:
            url, depth, parent = queue.popleft()

            if depth > self.config.max_depth:
                stats["pages_skipped"] += 1
                continue

            result = await self._process_url(url, depth, parent)
            if result is None:
                stats["pages_skipped"] += 1
                continue

            if result.error:
                stats["pages_failed"] += 1
            elif result.metadata.get("unchanged"):
                stats["pages_unchanged"] += 1
                stats["pages_crawled"] += 1
            else:
                stats["pages_crawled"] += 1
                # Add discovered links
                for link in result.links:
                    norm_link = normalize_url(link)
                    if (
                        norm_link not in self._visited
                        and stats["pages_discovered"] < self.config.max_pages * 2
                    ):
                        self._visited.add(norm_link)
                        queue.append((norm_link, depth + 1, url))
                        stats["pages_discovered"] += 1

                # Track PDF links
                for pdf_url in result.pdf_links:
                    norm_pdf = normalize_url(pdf_url)
                    if norm_pdf not in stats["pdf_urls"]:
                        stats["pdf_urls"].append(norm_pdf)
                        stats["documents_found"] += 1

            self._results.append(result)

            if progress_callback and stats["pages_crawled"] % 10 == 0:
                await progress_callback(stats)

        stats["duration_seconds"] = round(time.time() - start_time, 2)
        logger.info("Crawl completed", **{k: v for k, v in stats.items() if k != "pdf_urls"})
        return stats

    @property
    def results(self) -> List[CrawlResult]:
        return self._results
