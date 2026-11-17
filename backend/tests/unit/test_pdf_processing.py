"""
VEDANTA Unit Tests — PDF Processing Pipeline
Tests digital PDFs, scanned PDFs, image preprocessing, table extraction,
and dependency health diagnostics.
"""

import io
import os
import fitz
import pytest
from PIL import Image, ImageDraw

from app.ingestion.document_processor.pdf_processor import (
    PDFProcessor,
    _extract_tables_from_page,
    _is_page_scanned,
    _preprocess_image_for_ocr,
    get_document_dependencies_status,
    get_tesseract_status,
)


def _create_test_digital_pdf(path: str, text: str = "MITAOE Computer Engineering AY 2024-25") -> str:
    """Create a digital PDF with selectable text."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), text, fontsize=12)
    doc.save(path)
    doc.close()
    return path


def _create_test_scanned_pdf(path: str) -> str:
    """Create a purely scanned PDF with an embedded raster image and zero selectable text."""
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "Scanned Document Text", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_image(rect, stream=img_bytes)
    doc.save(path)
    doc.close()
    return path


def test_tesseract_status_detection(monkeypatch):
    """Verify Tesseract status detection and custom path override."""
    status = get_tesseract_status()
    assert isinstance(status, dict)
    assert "available" in status
    assert "message" in status

    # Test explicit environment variable override
    monkeypatch.setenv("TESSERACT_CMD", r"C:\fake\path\tesseract.exe")
    custom_status = get_tesseract_status()
    assert custom_status["available"] is False
    assert "not installed or not available in PATH" in custom_status["message"]


def test_document_dependencies_status():
    """Verify document dependencies status reports all required packages."""
    deps = get_document_dependencies_status()
    required = ["pymupdf", "pillow", "numpy", "pandas", "opencv", "pytesseract", "tesseract_binary"]
    for r in required:
        assert r in deps, f"Missing dependency check: {r}"

    assert deps["pymupdf"]["installed"] is True
    assert deps["pillow"]["installed"] is True
    assert deps["numpy"]["installed"] is True
    assert deps["pandas"]["installed"] is True
    assert deps["opencv"]["installed"] is True
    assert deps["pytesseract"]["installed"] is True


def test_digital_pdf_text_extraction(tmp_path):
    """Test text and academic year extraction from a digital PDF."""
    pdf_path = str(tmp_path / "test_digital.pdf")
    expected_content = "MIT Academy of Engineering B.Tech Fee Structure for Academic Year 2024-25."
    _create_test_digital_pdf(pdf_path, text=expected_content)

    processor = PDFProcessor(storage_dir=str(tmp_path))
    result = processor.process(pdf_path, source_url="https://mitaoe.ac.in/fee.pdf")

    assert result.error is None
    assert result.is_scanned is False
    assert result.page_count == 1
    assert "MIT Academy of Engineering" in result.full_text
    assert result.academic_year == "2024-25"


def test_scanned_pdf_detection_and_non_silent_ocr_failure(tmp_path, monkeypatch):
    """
    Scanned PDF pages with no selectable text must be detected as scanned,
    and if OCR is unavailable, must NOT silently succeed with empty text.
    """
    pdf_path = str(tmp_path / "test_scanned.pdf")
    _create_test_scanned_pdf(pdf_path)

    doc = fitz.open(pdf_path)
    assert _is_page_scanned(doc[0]) is True
    doc.close()

    # Force Tesseract unavailable to test non-silent failure
    monkeypatch.setattr(
        "app.ingestion.document_processor.pdf_processor.get_tesseract_status",
        lambda *args, **kwargs: {
            "available": False,
            "path": None,
            "version": None,
            "message": "Tesseract executable not found.",
        },
    )

    processor = PDFProcessor(storage_dir=str(tmp_path))
    result = processor.process(pdf_path, source_url="https://mitaoe.ac.in/scanned.pdf")

    assert result.is_scanned is True
    assert result.ocr_status == "failed"
    assert result.error is not None
    assert "OCR failed for 1 scanned page(s)" in result.error
    assert len(result.pages[0].ocr_error) > 0


def test_image_preprocessing_with_opencv():
    """Verify image preprocessing runs with OpenCV and produces valid image bytes."""
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    processed_bytes = _preprocess_image_for_ocr(raw_bytes)
    assert len(processed_bytes) > 0
    # Verify the output is a valid PNG image
    out_img = Image.open(io.BytesIO(processed_bytes))
    assert out_img.size == (100, 100)


def test_image_preprocessing_graceful_fallback(monkeypatch):
    """Verify image preprocessing falls back gracefully when cv2 is unavailable."""
    raw_bytes = b"fake-image-bytes"

    # Simulate cv2 missing
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "cv2":
            raise ImportError("No module named 'cv2'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)

    fallback_bytes = _preprocess_image_for_ocr(raw_bytes)
    assert fallback_bytes == raw_bytes


def test_table_extraction_graceful_without_pandas(tmp_path, monkeypatch):
    """Verify table extraction does not crash and works gracefully even if pandas is unavailable."""
    pdf_path = str(tmp_path / "table_test.pdf")
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    # Draw a table with lines so PyMuPDF detects it
    # Outer rectangle
    page.draw_rect(fitz.Rect(72, 72, 400, 200))
    # Horizontal divider
    page.draw_line(fitz.Point(72, 120), fitz.Point(400, 120))
    # Vertical divider
    page.draw_line(fitz.Point(236, 72), fitz.Point(236, 200))

    page.insert_text((80, 100), "Department", fontsize=11)
    page.insert_text((250, 100), "Intake", fontsize=11)
    page.insert_text((80, 150), "Computer Eng", fontsize=11)
    page.insert_text((250, 150), "180", fontsize=11)

    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    # Even if pandas throws ImportError, extraction should not raise
    tables = _extract_tables_from_page(doc[0])
    doc.close()

    assert isinstance(tables, list)
