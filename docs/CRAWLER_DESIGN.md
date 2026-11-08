# VEDANTA — Intelligent Website Crawler Architecture

**Product:** VEDANTA Crawler Engine  
**Module:** `backend/app/ingestion/crawler/`  
**Target Root:** `https://mitaoe.ac.in`

---

## 1. Design Overview

The VEDANTA crawler is built for institutional domain exploration. It prevents denial-of-service, respects webmaster policies, defends against Server-Side Request Forgery (SSRF), and eliminates duplicate processing through SHA-256 hash diffing.

```
                           [ SEED URL / SITEMAP ]
                                     |
                                     v
                        +--------------------------+
                        |   SSRF & Domain Guard    |  <-- Checks RFC 1918 Private IPs,
                        |   (url_validator.py)     |      Cloud Metadata (169.254.169.254)
                        +--------------------------+      Domain Allowlist (mitaoe.ac.in)
                                     |
                                     v
                        +--------------------------+
                        |     Robots.txt Cache     |  <-- In-Memory 1hr TTL Cache
                        |       (robots.py)        |      Urllib RobotFileParser
                        +--------------------------+
                                     |
                                     v
                        +--------------------------+
                        |  Polite Rate Limiter     |  <-- Asyncio Semaphore (concurrency=5)
                        |    (HTTPX AsyncClient)   |      Polite 1.0s Sleep Delay
                        +--------------------------+
                                     |
                                     v
                        +--------------------------+
                        |  Conditional GET (304)   |  <-- If-None-Match (ETag)
                        |    & SHA-256 Hash Diff   |      If-Modified-Since
                        +--------------------------+
                                     |
                 +-------------------+-------------------+
                 |                                       |
           [ HTML Content ]                         [ PDF File ]
                 |                                       |
                 v                                       v
      +----------------------+               +-----------------------+
      |  Trafilatura Parser  |               |  PyMuPDF & Tesseract  |
      |   & Content Chunker  |               |  Document Processor   |
      +----------------------+               +-----------------------+
```

---

## 2. Security & SSRF Protection (`url_validator.py`)

Any URL provided to the crawler must pass:
1. **Scheme Validation:** Only `http` and `https` schemes are permitted. Schemes like `file://`, `ftp://`, `gopher://`, and `javascript:` are rejected.
2. **Blocked Network Filtering:** Resolves DNS before request dispatch and blocks private IP ranges:
   - `10.0.0.0/8`
   - `172.16.0.0/12`
   - `192.168.0.0/16`
   - `127.0.0.0/8` (Localhost)
   - `169.254.0.0/16` (AWS/GCP/Azure link-local metadata)
   - `::1/128`, `fc00::/7`, `fe80::/10` (IPv6 loopback & private)
3. **Domain Strict Scope:** Hostnames must end in `.mitaoe.ac.in` or match `mitaoe.ac.in`. External links are cataloged but never fetched.

---

## 3. Incremental Crawling & Hash Diffing

VEDANTA persists the SHA-256 hash of extracted content. On subsequent visits:
1. HTTP headers `ETag` and `Last-Modified` are sent as conditional headers.
2. If the server returns HTTP 304 (Not Modified), processing is bypassed.
3. If content is returned, the new SHA-256 hash is compared against the database.
4. If identical, re-embedding and re-indexing are skipped, preserving CPU cycles and disk bandwidth.
