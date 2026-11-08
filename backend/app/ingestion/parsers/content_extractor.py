"""
VEDANTA — Content Extractor
Extracts clean text, title, and metadata from HTML pages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedContent:
    url: str
    title: str
    text: str
    description: Optional[str] = None
    keywords: Optional[str] = None
    author: Optional[str] = None
    language: str = "en"
    word_count: int = 0
    metadata: dict = field(default_factory=dict)


class ContentExtractor:
    """
    Extracts structured content from HTML using trafilatura + BeautifulSoup.
    """

    def extract(self, html: str, url: str) -> ExtractedContent:
        """
        Extract clean text and metadata from raw HTML.

        Strategy:
        1. Use trafilatura for main body text (best quality)
        2. Use BeautifulSoup for title, meta tags, fallback text
        """
        title = ""
        text = ""
        description = None
        keywords = None
        author = None

        # --- Trafilatura for main text ---
        try:
            import trafilatura
            extracted = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_recall=True,
            )
            if extracted and len(extracted.strip()) > 50:
                text = extracted.strip()
        except Exception as e:
            logger.debug("Trafilatura extraction failed", url=url, error=str(e))

        # --- BeautifulSoup for metadata and fallback ---
        try:
            soup = BeautifulSoup(html, "lxml")

            # Title
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            if not title:
                h1 = soup.find("h1")
                if h1:
                    title = h1.get_text(strip=True)

            # Meta tags
            for meta in soup.find_all("meta"):
                name = (meta.get("name") or meta.get("property") or "").lower()
                content = meta.get("content", "")
                if name in ("description", "og:description") and not description:
                    description = content[:500]
                elif name in ("keywords",) and not keywords:
                    keywords = content[:200]
                elif name in ("author", "og:author") and not author:
                    author = content[:200]

            # Fallback text if trafilatura returned nothing
            if not text:
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                raw_text = soup.get_text(separator="\n", strip=True)
                # Clean up excessive blank lines
                text = re.sub(r"\n{3,}", "\n\n", raw_text).strip()

        except Exception as e:
            logger.debug("BeautifulSoup extraction failed", url=url, error=str(e))

        # Detect language (simple heuristic — could use langdetect)
        language = "en"
        try:
            from langdetect import detect
            if text and len(text) > 100:
                language = detect(text[:1000])
        except Exception:
            pass

        word_count = len(text.split()) if text else 0

        return ExtractedContent(
            url=url,
            title=title,
            text=text,
            description=description,
            keywords=keywords,
            author=author,
            language=language,
            word_count=word_count,
            metadata={
                "domain": urlparse(url).netloc,
                "has_description": bool(description),
            },
        )
