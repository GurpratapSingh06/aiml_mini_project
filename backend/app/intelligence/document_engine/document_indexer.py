"""
VEDANTA — Document Intelligence Engine
Connects PDF extraction, OCR, table parsing, classification, and page-level citations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.core.logging import get_logger
from app.ingestion.document_processor.pdf_processor import PDFProcessor, ProcessedDocument
from app.ingestion.parsers.chunker import TextChunker, ChunkData

logger = get_logger(__name__)


class DocumentCategory(str, Enum):
    PLACEMENT_REPORT = "placement_report"
    FEE_STRUCTURE = "fee_structure"
    ACADEMIC_CALENDAR = "academic_calendar"
    CIRCULAR_NOTICE = "circular_notice"
    SYLLABUS_CURRICULUM = "syllabus_curriculum"
    ACCREDITATION_REPORT = "accreditation_report"
    EXAMINATION_RULE = "examination_rule"
    GENERAL = "general"


@dataclass
class DocumentIndexResult:
    document_id: str
    category: DocumentCategory
    title: str
    academic_year: Optional[str]
    page_count: int
    is_scanned: bool
    ocr_confidence: Optional[float]
    chunks: List[ChunkData]
    tables_found: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentIntelligenceEngine:
    """
    Classifies institutional documents, extracts page-level text/tables,
    and formats them with accurate page and year citations for retrieval.
    """

    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.chunker = TextChunker()

    def classify_document(self, text: str, file_name: str = "") -> DocumentCategory:
        """
        Classifies document based on content keywords and file naming.
        """
        combined = f"{file_name} {text[:2000]}".lower()

        if any(kw in combined for kw in ["placement report", "placement statistics", "highest package", "campus drive", "recruiters"]):
            return DocumentCategory.PLACEMENT_REPORT
        if any(kw in combined for kw in ["fee structure", "tuition fee", "development fee", "interim fee", "fra"]):
            return DocumentCategory.FEE_STRUCTURE
        if any(kw in combined for kw in ["academic calendar", "term schedule", "instructional days", "commencement"]):
            return DocumentCategory.ACADEMIC_CALENDAR
        if any(kw in combined for kw in ["circular", "notice", "office order", "ref no:"]):
            return DocumentCategory.CIRCULAR_NOTICE
        if any(kw in combined for kw in ["syllabus", "curriculum", "course structure", "scheme of examination"]):
            return DocumentCategory.SYLLABUS_CURRICULUM
        if any(kw in combined for kw in ["naac", "nba", "ssr", "aqar", "accreditation"]):
            return DocumentCategory.ACCREDITATION_REPORT
        if any(kw in combined for kw in ["examination", "revaluation", "malpractice", "grading system"]):
            return DocumentCategory.EXAMINATION_RULE

        return DocumentCategory.GENERAL

    def process_and_index(
        self,
        file_path: str,
        source_url: str,
        document_id: str,
    ) -> DocumentIndexResult:
        """
        Processes document with PyMuPDF/OCR, classifies it,
        and generates page-tracked chunks for vector indexing.
        """
        proc_doc: ProcessedDocument = self.pdf_processor.process(file_path, source_url)

        category = self.classify_document(proc_doc.full_text, Path(file_path).name)
        chunks: List[ChunkData] = []

        # Process per-page to guarantee page citation accuracy
        for page in proc_doc.pages:
            page_text = page.ocr_text if page.is_scanned else page.text
            if not page_text or len(page_text.strip()) < 20:
                continue

            page_chunks = self.chunker.chunk(
                text=page_text,
                source_url=source_url,
                source_title=proc_doc.title or Path(file_path).name,
                document_id=document_id,
                page_number=page.page_number,
            )
            chunks.extend(page_chunks)

        logger.info(
            "Document intelligence indexing completed",
            doc_id=document_id,
            category=category.value,
            pages=proc_doc.page_count,
            chunks=len(chunks),
        )

        return DocumentIndexResult(
            document_id=document_id,
            category=category,
            title=proc_doc.title or Path(file_path).name,
            academic_year=proc_doc.academic_year,
            page_count=proc_doc.page_count,
            is_scanned=proc_doc.is_scanned,
            ocr_confidence=proc_doc.overall_ocr_confidence,
            chunks=chunks,
            tables_found=len(proc_doc.tables),
            metadata={
                "category": category.value,
                "file_hash": proc_doc.file_hash,
                "file_size": proc_doc.file_size_bytes,
            },
        )
