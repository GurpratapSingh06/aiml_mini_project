"""
VEDANTA — Robots.txt Cache
Fetches and caches robots.txt rules for crawled domains.
"""

from __future__ import annotations

import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

_CACHE_TTL = 3600  # 1 hour per domain


class RobotsCache:
    """Thread-safe cache for robots.txt rules."""

    def __init__(self, user_agent: str = "VEDANTA-Crawler"):
        self.user_agent = user_agent
        self._cache: dict[str, tuple[RobotFileParser, float]] = {}

    async def _fetch_robots(self, base_url: str) -> RobotFileParser:
        """Fetch and parse robots.txt for the given domain."""
        robots_url = f"{base_url}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(robots_url)
                if response.status_code == 200:
                    rp.parse(response.text.splitlines())
                else:
                    # No robots.txt — allow everything
                    rp.parse([])
        except Exception as e:
            logger.warning("Could not fetch robots.txt", url=robots_url, error=str(e))
            rp.parse([])

        return rp

    def _get_base_url(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def is_allowed(self, url: str) -> bool:
        """Return True if the URL is allowed by robots.txt."""
        base_url = self._get_base_url(url)
        now = time.time()

        # Check cache
        if base_url in self._cache:
            rp, cached_at = self._cache[base_url]
            if now - cached_at < _CACHE_TTL:
                return rp.can_fetch(self.user_agent, url)

        # Fetch and cache
        rp = await self._fetch_robots(base_url)
        self._cache[base_url] = (rp, now)
        return rp.can_fetch(self.user_agent, url)

    def clear(self) -> None:
        self._cache.clear()
