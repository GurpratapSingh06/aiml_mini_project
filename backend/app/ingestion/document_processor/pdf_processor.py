"""
VEDANTA — PDF Document Processor
Handles digital PDFs, scanned PDFs, OCR, and table extraction.
Provides robust fallback when OCR or optional libraries are unavailable.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PageContent:
    page_number: int
    text: str
    is_scanned: bool
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_error: Optional[str] = None
    image_path: Optional[str] = None
    tables: List[dict] = field(default_factory=list)


@dataclass
class ProcessedDocument:
    source_url: str
    file_path: str
    file_hash: str
    file_size_bytes: int
    document_type: str = "pdf"
    is_scanned: bool = False
    is_mixed: bool = False
    page_count: int = 0
    title: Optional[str] = None
    author: Optional[str] = None
    academic_year: Optional[str] = None
    ocr_engine: Optional[str] = None
    overall_ocr_confidence: Optional[float] = None
    ocr_status: Optional[str] = None  # None | "success" | "partial" | "failed" | "skipped"
    ocr_error: Optional[str] = None
    pages: List[PageContent] = field(default_factory=list)
    full_text: str = ""
    tables: List[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    error: Optional[str] = None


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_tesseract_status(custom_cmd: Optional[str] = None) -> Dict[str, Any]:
    """
    Detect Tesseract availability and configure pytesseract executable path.
    Supports explicit configuration via TESSERACT_CMD environment variable,
    config settings, PATH lookup, and common Windows install directories.
    """
    # 1. Candidate paths in order of preference
    candidates: List[str] = []

    if custom_cmd and custom_cmd.strip():
        candidates = [custom_cmd.strip()]
    elif os.environ.get("TESSERACT_CMD") and os.environ.get("TESSERACT_CMD").strip():
        candidates = [os.environ.get("TESSERACT_CMD").strip()]
    else:
        settings_cmd = getattr(settings, "document_tesseract_cmd", None)
        if settings_cmd and settings_cmd.strip() and settings_cmd.strip().lower() != "tesseract":
            candidates.append(settings_cmd.strip())

        # System PATH
        which_cmd = shutil.which("tesseract")
        if which_cmd:
            candidates.append(which_cmd)

        # Standard Windows install locations
        win_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for wp in win_paths:
            if os.path.isfile(wp):
                candidates.append(wp)

    # Try candidates
    resolved_path: Optional[str] = None
    for cand in candidates:
        if os.path.isfile(cand) or shutil.which(cand):
            resolved_path = cand
            break

    # If an explicit candidate was provided but not found, retain it to test against pytesseract
    if not resolved_path:
        resolved_path = candidates[0] if candidates else "tesseract"

    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = resolved_path

        version = str(pytesseract.get_tesseract_version())
        return {
            "available": True,
            "path": resolved_path,
            "version": version,
            "message": f"Tesseract OCR {version} detected at '{resolved_path}'",
        }
    except Exception as e:
        return {
            "available": False,
            "path": None,
            "version": None,
            "message": (
                "Tesseract OCR executable is not installed or not available in PATH. "
                "Scanned PDF pages will fail OCR gracefully. To enable OCR on Windows, "
                "install Tesseract (e.g., 'winget install UB-Mannheim.TesseractOCR') and "
                "set the TESSERACT_CMD environment variable."
            ),
        }


def get_document_dependencies_status() -> Dict[str, Any]:
    """
    Check the installation status of all document processing dependencies.
    """
    status: Dict[str, Any] = {}

    # PyMuPDF
    try:
        import fitz
        status["pymupdf"] = {
            "installed": True,
            "version": getattr(fitz, "__version__", getattr(fitz, "VersionBind", "unknown")),
            "status": "ok",
        }
    except ImportError as e:
        status["pymupdf"] = {"installed": False, "version": None, "status": "missing", "error": str(e)}

    # Pillow
    try:
        import PIL
        status["pillow"] = {
            "installed": True,
            "version": getattr(PIL, "__version__", "unknown"),
            "status": "ok",
        }
    except ImportError as e:
        status["pillow"] = {"installed": False, "version": None, "status": "missing", "error": str(e)}

    # NumPy
    try:
        import numpy as np
        status["numpy"] = {
            "installed": True,
            "version": getattr(np, "__version__", "unknown"),
            "status": "ok",
        }
    except ImportError as e:
        status["numpy"] = {"installed": False, "version": None, "status": "missing", "error": str(e)}

    # Pandas
    try:
        import pandas as pd
        status["pandas"] = {
            "installed": True,
            "version": getattr(pd, "__version__", "unknown"),
            "status": "ok",
        }
    except ImportError as e:
        status["pandas"] = {"installed": False, "version": None, "status": "missing", "error": str(e)}

    # OpenCV
    try:
        import cv2
        status["opencv"] = {
            "installed": True,
            "version": getattr(cv2, "__version__", "unknown"),
            "status": "ok",
        }
    except ImportError as e:
        status["opencv"] = {"installed": False, "version": None, "status": "missing", "error": str(e)}

    # Pytesseract Python package
    try:
        import pytesseract
        status["pytesseract"] = {
            "installed": True,
            "version": getattr(pytesseract, "__version__", "unknown"),
            "status": "ok",
        }
    except ImportError as e:
        status["pytesseract"] = {"installed": False, "version": None, "status": "missing", "error": str(e)}

    # Tesseract system binary
    tess_info = get_tesseract_status()
    status["tesseract_binary"] = {
        "installed": tess_info["available"],
        "path": tess_info["path"],
        "version": tess_info["version"],
        "status": "ok" if tess_info["available"] else "missing",
        "message": tess_info["message"],
    }

    return status


def _is_page_scanned(page) -> bool:
    """
    Detect if a PyMuPDF page is scanned (image-based) rather than digital text.
    A page is considered scanned if it has very little selectable text
    but contains images.
    """
    text = page.get_text("text").strip()
    images = page.get_images(full=False)
    # If less than 50 chars of text but has images → scanned
    return len(text) < 50 and len(images) > 0


def _extract_tables_from_page(page) -> List[dict]:
    """
    Extract tables from a PyMuPDF page using the table detection API.
    Returns a list of table dicts with 'headers', 'rows', 'row_count', 'col_count'.
    Natively extracts using tab.extract() and fails gracefully if pandas is unavailable.
    """
    tables = []
    try:
        tab_finder = page.find_tables()
        for i, tab in enumerate(tab_finder.tables):
            try:
                # Primary extraction: tab.extract() works with or without pandas
                extracted = tab.extract()
                if not extracted or len(extracted) == 0:
                    continue

                raw_headers = extracted[0]
                raw_rows = extracted[1:] if len(extracted) > 1 else []

                headers = [str(h).strip() if h is not None else "" for h in raw_headers]
                rows = [
                    [str(cell).strip() if cell is not None else "" for cell in row]
                    for row in raw_rows
                ]

                tables.append({
                    "table_index": i,
                    "headers": headers,
                    "rows": rows,
                    "row_count": len(rows),
                    "col_count": len(headers),
                })
            except Exception as table_err:
                logger.debug("Single table extraction failed", index=i, error=str(table_err))
                continue
    except Exception as e:
        logger.debug("Table extraction failed on page", error=str(e))

    return tables


def _preprocess_image_for_ocr(image_bytes: bytes) -> bytes:
    """
    Apply preprocessing to improve OCR accuracy.
    Fails gracefully to raw image bytes if cv2, numpy, or PIL are unavailable.
    """
    try:
        import cv2
        import numpy as np
        from PIL import Image
    except ImportError as e:
        logger.debug("Image preprocessing skipped (missing dependency)", error=str(e))
        return image_bytes

    try:
        img_array = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return image_bytes

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Deskew using moments
        coords = np.column_stack(np.where(gray < 200))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            if abs(angle) > 0.5:
                (h, w) = gray.shape
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC,
                                       borderMode=cv2.BORDER_REPLICATE)

        # Denoise
        gray = cv2.fastNlMeansDenoising(gray, h=10)

        # Contrast enhancement (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # Convert back to PIL and encode
        pil_img = Image.fromarray(gray)
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        return buf.getvalue()

    except Exception as e:
        logger.debug("Image preprocessing failed, using raw", error=str(e))
        return image_bytes


def _ocr_page_tesseract(page, lang: str = "eng", tesseract_cmd: Optional[str] = None) -> Tuple[str, float, Optional[str]]:
    """
    Run Tesseract OCR on a PyMuPDF page.
    Returns (text, confidence, error_message).
    Does not raise exceptions; returns explicit error message when Tesseract is missing.
    """
    tess_status = get_tesseract_status(custom_cmd=tesseract_cmd)
    if not tess_status["available"]:
        return "", 0.0, tess_status["message"]

    try:
        import pytesseract
        from PIL import Image

        # Render page to image at 300 DPI
        mat = page.get_pixmap(dpi=300)
        img_bytes = mat.tobytes("png")
        img_bytes = _preprocess_image_for_ocr(img_bytes)

        img = Image.open(io.BytesIO(img_bytes))

        # Get OCR with confidence data
        config = "--oem 3 --psm 1"
        data = pytesseract.image_to_data(
            img, lang=lang, config=config, output_type=pytesseract.Output.DICT
        )

        # Compute mean confidence (excluding -1 values)
        confs = [c for c in data["conf"] if c != -1]
        mean_conf = sum(confs) / len(confs) / 100.0 if confs else 0.0

        # Reconstruct text
        words = [
            w for w, c in zip(data["text"], data["conf"])
            if w.strip() and c != -1
        ]
        text = " ".join(words)

        return text, mean_conf, None

    except ImportError:
        return "", 0.0, "pytesseract Python package is not installed."
    except Exception as e:
        logger.debug("Tesseract OCR execution error", error=str(e))
        return "", 0.0, f"Tesseract OCR execution failed: {str(e)}"


class PDFProcessor:
    """
    Processes PDF documents: extracts text, detects scanned pages,
    runs OCR where needed, extracts tables.
    """

    def __init__(
        self,
        ocr_engine: str = "tesseract",
        ocr_language: str = "eng",
        storage_dir: Optional[str] = None,
        tesseract_cmd: Optional[str] = None,
    ):
        self.ocr_engine = ocr_engine
        self.ocr_language = ocr_language
        self.tesseract_cmd = tesseract_cmd or os.environ.get("TESSERACT_CMD") or getattr(settings, "document_tesseract_cmd", None)
        self.storage_dir = Path(storage_dir or settings.document_storage_path)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def process(self, file_path: str, source_url: str) -> ProcessedDocument:
        """
        Process a PDF file and return structured content.
        Automatically detects whether pages are digital or scanned
        and applies OCR only where needed.
        Never silently marks failed OCR as successful extraction.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error("PyMuPDF (fitz) not installed")
            return ProcessedDocument(
                source_url=source_url,
                file_path=file_path,
                file_hash="",
                file_size_bytes=0,
                error="PyMuPDF not installed",
            )

        try:
            file_hash = _file_hash(file_path)
            file_size = os.path.getsize(file_path)

            doc = fitz.open(file_path)
            page_count = doc.page_count

            # Extract document metadata
            meta = doc.metadata or {}
            title = meta.get("title", "").strip() or None
            author = meta.get("author", "").strip() or None

            pages: List[PageContent] = []
            all_text_parts: List[str] = []
            all_tables: List[dict] = []
            scanned_count = 0
            ocr_confidences: List[float] = []
            ocr_errors: List[str] = []

            for page_num in range(page_count):
                page = doc[page_num]
                is_scanned = _is_page_scanned(page)

                if is_scanned:
                    scanned_count += 1

                # Extract digital text
                digital_text = page.get_text("text").strip()

                # Extract tables (works for digital pages)
                page_tables = []
                if not is_scanned:
                    page_tables = _extract_tables_from_page(page)
                    for t in page_tables:
                        t["page_number"] = page_num + 1
                    all_tables.extend(page_tables)

                # OCR if scanned
                ocr_text = None
                ocr_confidence = None
                ocr_error = None
                if is_scanned and self.ocr_engine == "tesseract":
                    ocr_text, ocr_confidence, ocr_error = _ocr_page_tesseract(
                        page, self.ocr_language, tesseract_cmd=self.tesseract_cmd
                    )
                    if ocr_confidence is not None and ocr_confidence > 0:
                        ocr_confidences.append(ocr_confidence)
                    if ocr_error:
                        ocr_errors.append(f"Page {page_num + 1}: {ocr_error}")

                effective_text = (ocr_text or "") if is_scanned else digital_text
                if effective_text:
                    all_text_parts.append(effective_text)

                pages.append(PageContent(
                    page_number=page_num + 1,
                    text=digital_text,
                    is_scanned=is_scanned,
                    ocr_text=ocr_text,
                    ocr_confidence=ocr_confidence,
                    ocr_error=ocr_error,
                    tables=page_tables,
                ))

            doc.close()

            is_scanned = (scanned_count == page_count) if page_count > 0 else False
            is_mixed = (0 < scanned_count < page_count)
            full_text = "\n\n".join(all_text_parts)
            overall_ocr_confidence = (
                sum(ocr_confidences) / len(ocr_confidences) if ocr_confidences else None
            )

            # Determine OCR status and error
            ocr_status: Optional[str] = None
            doc_error: Optional[str] = None

            if scanned_count > 0:
                if len(all_text_parts) > 0 and len(ocr_confidences) == scanned_count:
                    ocr_status = "success"
                elif len(all_text_parts) > 0:
                    ocr_status = "partial"
                    if ocr_errors:
                        doc_error = f"Partial extraction: {len(ocr_errors)} page(s) failed OCR."
                else:
                    ocr_status = "failed"
                    first_err = ocr_errors[0] if ocr_errors else "OCR produced no text"
                    doc_error = f"OCR failed for {scanned_count} scanned page(s): {first_err}"

            # Detect academic year from text
            academic_year = self._detect_academic_year(full_text)

            logger.info(
                "PDF processed",
                source_url=source_url,
                pages=page_count,
                scanned=scanned_count,
                text_chars=len(full_text),
                tables=len(all_tables),
                ocr_status=ocr_status,
            )

            return ProcessedDocument(
                source_url=source_url,
                file_path=file_path,
                file_hash=file_hash,
                file_size_bytes=file_size,
                document_type="pdf",
                is_scanned=is_scanned,
                is_mixed=is_mixed,
                page_count=page_count,
                title=title,
                author=author,
                academic_year=academic_year,
                ocr_engine=self.ocr_engine if scanned_count > 0 else None,
                overall_ocr_confidence=overall_ocr_confidence,
                ocr_status=ocr_status,
                ocr_error="; ".join(ocr_errors[:3]) if ocr_errors else None,
                pages=pages,
                full_text=full_text,
                tables=all_tables,
                metadata={"source_metadata": meta, "ocr_errors": ocr_errors[:5]},
                error=doc_error,
            )

        except Exception as e:
            logger.error("PDF processing failed", file_path=file_path, error=str(e))
            return ProcessedDocument(
                source_url=source_url,
                file_path=file_path,
                file_hash="",
                file_size_bytes=0,
                error=str(e),
            )

    def _detect_academic_year(self, text: str) -> Optional[str]:
        """Detect academic year patterns like 2024-25 or 2024-2025."""
        import re
        patterns = [
            r"\b(20\d{2}[-–]\d{2,4})\b",
            r"\bAY\s+(20\d{2}[-–]\d{2,4})\b",
            r"\bacademic\s+year\s+(20\d{2}[-–]\d{2,4})\b",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                year = matches[0]
                parts = re.split(r"[-–]", year)
                if len(parts) == 2:
                    start = parts[0].strip()
                    end = parts[1].strip()
                    if len(end) == 4:
                        end = end[2:]
                    return f"{start}-{end}"
        return None

    async def download_and_process(self, url: str, source_url: str) -> ProcessedDocument:
        """Download a PDF from URL and process it."""
        import httpx

        try:
            async with httpx.AsyncClient(
                timeout=60.0,
                follow_redirects=True,
                headers={"User-Agent": settings.crawl_user_agent},
            ) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return ProcessedDocument(
                        source_url=source_url,
                        file_path="",
                        file_hash="",
                        file_size_bytes=0,
                        error=f"HTTP {response.status_code}",
                    )

                # Save to disk
                file_hash_prefix = hashlib.md5(url.encode()).hexdigest()[:12]
                file_name = f"doc_{file_hash_prefix}.pdf"
                file_path = str(self.storage_dir / file_name)

                with open(file_path, "wb") as f:
                    f.write(response.content)

                return self.process(file_path, source_url)

        except Exception as e:
            logger.error("PDF download failed", url=url, error=str(e))
            return ProcessedDocument(
                source_url=source_url,
                file_path="",
                file_hash="",
                file_size_bytes=0,
                error=str(e),
            )
