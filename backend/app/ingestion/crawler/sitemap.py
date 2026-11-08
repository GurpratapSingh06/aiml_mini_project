"""
VEDANTA — Sitemap Parser
Discovers URLs from XML sitemaps and sitemap indexes.
"""

from __future__ import annotations

import gzip
import io
from typing import AsyncGenerator
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree as ET

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

_SITEMAP_NAMESPACES = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
}

_COMMON_SITEMAP_PATHS = [
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/sitemaps/sitemap.xml",
    "/wp-sitemap.xml",
]


class SitemapUrl:
    """Represents a single URL entry from a sitemap."""

    def __init__(self, loc: str, lastmod: str = "", priority: float = 0.5, changefreq: str = ""):
        self.loc = loc.strip()
        self.lastmod = lastmod
        self.priority = priority
        self.changefreq = changefreq

    def __repr__(self) -> str:
        return f"SitemapUrl(loc={self.loc!r}, priority={self.priority})"


class SitemapParser:
    """Discovers and parses XML sitemaps for institutional websites."""

    def __init__(self, user_agent: str = "VEDANTA-Crawler/0.1"):
        self.user_agent = user_agent
        self._client_kwargs = {
            "timeout": httpx.Timeout(30.0),
            "follow_redirects": True,
            "headers": {"User-Agent": user_agent},
        }

    async def _fetch(self, url: str) -> bytes | None:
        """Fetch a URL and return raw bytes, or None on failure."""
        try:
            async with httpx.AsyncClient(**self._client_kwargs) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.content
                logger.debug("Sitemap fetch non-200", url=url, status=resp.status_code)
                return None
        except Exception as e:
            logger.debug("Sitemap fetch error", url=url, error=str(e))
            return None

    def _decompress_if_needed(self, content: bytes, url: str) -> bytes:
        """Decompress gzip content if needed."""
        if url.endswith(".gz") or content[:2] == b"\x1f\x8b":
            try:
                return gzip.decompress(content)
            except Exception:
                pass
        return content

    def _parse_sitemap_xml(self, content: bytes) -> tuple[list[str], list[SitemapUrl]]:
        """
        Parse sitemap XML.
        Returns (sub_sitemap_urls, page_urls).
        """
        sub_sitemaps: list[str] = []
        pages: list[SitemapUrl] = []

        try:
            root = ET.fromstring(content)
            tag = root.tag.lower()

            # Sitemap index
            if "sitemapindex" in tag:
                for sitemap in root.iter():
                    if sitemap.tag.endswith("}loc") or sitemap.tag == "loc":
                        loc = sitemap.text
                        if loc:
                            sub_sitemaps.append(loc.strip())

            # Regular sitemap
            elif "urlset" in tag:
                for url_elem in root.iter():
                    ns = ""
                    local = url_elem.tag
                    if "}" in local:
                        _, local = local.split("}", 1)

                    if local == "url":
                        loc = ""
                        lastmod = ""
                        priority = 0.5
                        changefreq = ""
                        for child in url_elem:
                            child_local = child.tag.split("}")[-1]
                            if child_local == "loc" and child.text:
                                loc = child.text.strip()
                            elif child_local == "lastmod" and child.text:
                                lastmod = child.text.strip()
                            elif child_local == "priority" and child.text:
                                try:
                                    priority = float(child.text.strip())
                                except ValueError:
                                    pass
                            elif child_local == "changefreq" and child.text:
                                changefreq = child.text.strip()
                        if loc:
                            pages.append(SitemapUrl(loc, lastmod, priority, changefreq))

        except ET.ParseError as e:
            logger.warning("Sitemap XML parse error", error=str(e))

        return sub_sitemaps, pages

    async def discover_urls(self, base_url: str) -> AsyncGenerator[SitemapUrl, None]:
        """
        Discover all URLs from sitemaps for a given base URL.
        Tries common sitemap paths and follows sitemap indexes recursively.
        """
        parsed = urlparse(base_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        # Try to find a sitemap
        discovered_sitemap = None
        for path in _COMMON_SITEMAP_PATHS:
            sitemap_url = origin + path
            content = await self._fetch(sitemap_url)
            if content:
                discovered_sitemap = (sitemap_url, content)
                logger.info("Sitemap found", url=sitemap_url)
                break

        # Also check robots.txt for Sitemap: directive
        robots_content = await self._fetch(origin + "/robots.txt")
        if robots_content:
            for line in robots_content.decode("utf-8", errors="ignore").splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()
                    if discovered_sitemap is None:
                        content = await self._fetch(sitemap_url)
                        if content:
                            discovered_sitemap = (sitemap_url, content)
                            logger.info("Sitemap from robots.txt", url=sitemap_url)
                            break

        if not discovered_sitemap:
            logger.info("No sitemap found for base_url", base_url=base_url)
            return

        # Process sitemaps recursively
        queue = [discovered_sitemap]
        seen_sitemaps: set[str] = set()

        while queue:
            sitemap_url, content = queue.pop(0)
            if sitemap_url in seen_sitemaps:
                continue
            seen_sitemaps.add(sitemap_url)

            content = self._decompress_if_needed(content, sitemap_url)
            sub_sitemaps, pages = self._parse_sitemap_xml(content)

            # Yield pages
            for page in pages:
                yield page

            # Fetch and queue sub-sitemaps
            for sub_url in sub_sitemaps:
                if sub_url not in seen_sitemaps:
                    sub_content = await self._fetch(sub_url)
                    if sub_content:
                        queue.append((sub_url, sub_content))
