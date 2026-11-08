"""
VEDANTA Unit Tests — URL Validator and SSRF Guard
"""

import pytest
from app.ingestion.crawler.url_validator import validate_crawl_url


def test_allowed_domain_valid():
    res = validate_crawl_url("https://mitaoe.ac.in/academics/computer.php", ["mitaoe.ac.in"])
    assert res.is_valid is True
    assert res.reason == ""


def test_disallowed_external_domain_blocked():
    res = validate_crawl_url("https://google.com/search", ["mitaoe.ac.in"])
    assert res.is_valid is False
    assert "not in allowed list" in res.reason


def test_ssrf_localhost_blocked():
    res = validate_crawl_url("http://localhost:8000/admin", ["mitaoe.ac.in", "localhost"])
    assert res.is_valid is False
    assert "blocked" in res.reason.lower() or "private" in res.reason.lower()


def test_ssrf_cloud_metadata_blocked():
    res = validate_crawl_url("http://169.254.169.254/latest/meta-data/", ["169.254.169.254"])
    assert res.is_valid is False
    assert "blocked" in res.reason.lower() or "private" in res.reason.lower()


def test_unsupported_scheme_blocked():
    res = validate_crawl_url("file:///etc/passwd", ["mitaoe.ac.in"])
    assert res.is_valid is False
    assert "scheme" in res.reason.lower()
