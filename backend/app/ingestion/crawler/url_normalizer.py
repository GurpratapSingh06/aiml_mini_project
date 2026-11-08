"""
VEDANTA — URL Normalizer
Converts raw URLs into canonical, deduplicated forms.
"""

from __future__ import annotations

import re
from urllib.parse import (
    ParseResult,
    parse_qs,
    urlencode,
    urljoin,
    urlparse,
    urlunparse,
)

# Query parameters that add no semantic value and should be removed
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "msclkid", "ref", "source", "_ga", "mc_cid", "mc_eid",
}


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normalize a URL to a canonical form for deduplication.

    Operations performed:
    - Resolve relative URLs against base_url
    - Lowercase scheme and hostname
    - Remove default ports (80 for http, 443 for https)
    - Remove URL fragments (#...)
    - Remove known tracking query parameters
    - Sort remaining query parameters for stability
    - Normalize trailing slash (keep for root, remove for paths with extensions)
    """
    try:
        # Resolve relative URLs
        if base_url and not url.startswith(("http://", "https://")):
            url = urljoin(base_url, url)

        parsed = urlparse(url.strip())

        # Lowercase scheme and netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default ports
        if ":" in netloc:
            host, port_str = netloc.rsplit(":", 1)
            try:
                port = int(port_str)
                if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
                    netloc = host
            except ValueError:
                pass

        # Clean path
        path = parsed.path
        # Normalize multiple slashes
        path = re.sub(r"/+", "/", path)

        # Remove tracking query params
        if parsed.query:
            params = parse_qs(parsed.query, keep_blank_values=False)
            cleaned = {k: v for k, v in params.items() if k.lower() not in _TRACKING_PARAMS}
            query = urlencode(sorted(cleaned.items()), doseq=True)
        else:
            query = ""

        # Remove fragment entirely
        fragment = ""

        normalized = urlunparse((scheme, netloc, path, parsed.params, query, fragment))
        return normalized

    except Exception:
        return url


def is_internal_link(url: str, allowed_domains: list[str]) -> bool:
    """Return True if the URL belongs to one of the allowed domains."""
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        return any(
            hostname == d.lower() or hostname.endswith("." + d.lower())
            for d in allowed_domains
        )
    except Exception:
        return False


def is_pdf_url(url: str) -> bool:
    """Return True if the URL likely points to a PDF file."""
    path = urlparse(url).path.lower()
    return path.endswith(".pdf")


def should_skip_url(url: str) -> bool:
    """Return True for URLs that should never be crawled (binary assets, mailto, etc.)."""
    skip_extensions = {
        ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", ".webp",
        ".mp4", ".mp3", ".avi", ".mov", ".zip", ".tar", ".gz",
        ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
        ".xls", ".xlsx", ".ppt", ".pptx", ".doc", ".docx",
    }
    skip_schemes = {"mailto:", "tel:", "javascript:", "ftp:", "#"}

    url_lower = url.lower().strip()

    for scheme in skip_schemes:
        if url_lower.startswith(scheme):
            return True

    path = urlparse(url_lower).path
    _, ext = path.rsplit(".", 1) if "." in path else ("", "")
    return f".{ext}" in skip_extensions
