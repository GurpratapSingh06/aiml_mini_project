"""
VEDANTA — URL Validator
SSRF protection and domain allowlist enforcement.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse

from app.core.logging import get_logger

logger = get_logger(__name__)

# Private/reserved IP ranges that must never be crawled
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / cloud metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "169.254.169.254",
}

_ALLOWED_SCHEMES = {"http", "https"}


@dataclass
class UrlValidationResult:
    is_valid: bool
    reason: str = ""
    normalized_url: str = ""


def _is_private_ip(hostname: str) -> bool:
    """Return True if the hostname resolves to a private/reserved IP."""
    try:
        addrs = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        for _, _, _, _, sockaddr in addrs:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)
            for network in _BLOCKED_NETWORKS:
                if ip in network:
                    return True
        return False
    except (socket.gaierror, ValueError):
        # Cannot resolve — treat as invalid
        return True


def validate_crawl_url(url: str, allowed_domains: List[str]) -> UrlValidationResult:
    """
    Validate a URL for crawling eligibility.

    Checks:
    1. URL scheme is http or https
    2. Hostname is in the allowed domains list
    3. Hostname does not resolve to a private/reserved IP (SSRF protection)
    4. Hostname is not in the blocked hostname list
    """
    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        return UrlValidationResult(is_valid=False, reason=f"URL parse error: {e}")

    # Scheme check
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return UrlValidationResult(
            is_valid=False,
            reason=f"Scheme '{parsed.scheme}' not allowed. Only http/https permitted.",
        )

    hostname = parsed.hostname or ""
    if not hostname:
        return UrlValidationResult(is_valid=False, reason="URL has no hostname")

    hostname_lower = hostname.lower()

    # Blocked hostname check
    if hostname_lower in _BLOCKED_HOSTNAMES:
        return UrlValidationResult(
            is_valid=False,
            reason=f"Hostname '{hostname}' is explicitly blocked",
        )

    # Allowed domain check
    is_allowed_domain = any(
        hostname_lower == d.lower() or hostname_lower.endswith("." + d.lower())
        for d in allowed_domains
    )
    if not is_allowed_domain:
        return UrlValidationResult(
            is_valid=False,
            reason=f"Domain '{hostname}' not in allowed list: {allowed_domains}",
        )

    # SSRF protection: resolve and check IP
    if _is_private_ip(hostname):
        logger.warning("SSRF attempt blocked", hostname=hostname, url=url)
        return UrlValidationResult(
            is_valid=False,
            reason=f"Hostname '{hostname}' resolves to a private/reserved IP address",
        )

    return UrlValidationResult(is_valid=True, normalized_url=url)
