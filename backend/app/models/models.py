"""
VEDANTA — SQLAlchemy Database Models
Complete normalized schema for the institutional knowledge platform.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ============================================================
# Enumerations
# ============================================================

class CrawlStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PageStatus(str, enum.Enum):
    PENDING = "pending"
    CRAWLED = "crawled"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    OCR_PENDING = "ocr_pending"
    OCR_RUNNING = "ocr_running"
    OCR_COMPLETE = "ocr_complete"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    IMAGE = "image"
    HTML = "html"
    OTHER = "other"


class VerificationStatus(str, enum.Enum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNCERTAIN = "uncertain"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONFLICTING_SOURCES = "conflicting_sources"
    OUTDATED_SOURCE = "outdated_source"


class EntityType(str, enum.Enum):
    PERSON = "person"
    DEPARTMENT = "department"
    POSITION = "position"
    COMMITTEE = "committee"
    PROGRAM = "program"
    FACILITY = "facility"
    EVENT = "event"
    OTHER = "other"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


# ============================================================
# Institution and Domain
# ============================================================

class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    website: Mapped[str] = mapped_column(String(512), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="India")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    domains: Mapped[List["Domain"]] = relationship(back_populates="institution")
    departments: Mapped[List["Department"]] = relationship(back_populates="institution")
    academic_years: Mapped[List["AcademicYear"]] = relationship(back_populates="institution")


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_allowed_crawl: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    institution: Mapped["Institution"] = relationship(back_populates="domains")


# ============================================================
# Crawling
# ============================================================

class CrawlJob(Base):
    __tablename__ = "crawl_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    start_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[CrawlStatus] = mapped_column(Enum(CrawlStatus), default=CrawlStatus.PENDING)
    max_depth: Mapped[int] = mapped_column(Integer, default=5)
    max_pages: Mapped[int] = mapped_column(Integer, default=5000)
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0)
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    pages_failed: Mapped[int] = mapped_column(Integer, default=0)
    pages_skipped: Mapped[int] = mapped_column(Integer, default=0)
    documents_found: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    config: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    pages: Mapped[List["Page"]] = relationship(back_populates="crawl_job")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    crawl_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("crawl_jobs.id"))
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[Optional[str]] = mapped_column(String(2048))
    title: Mapped[Optional[str]] = mapped_column(String(1024))
    content: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))
    content_type: Mapped[Optional[str]] = mapped_column(String(255))
    etag: Mapped[Optional[str]] = mapped_column(String(255))
    last_modified: Mapped[Optional[str]] = mapped_column(String(255))
    http_status: Mapped[Optional[int]] = mapped_column(Integer)
    crawl_depth: Mapped[int] = mapped_column(Integer, default=0)
    parent_url: Mapped[Optional[str]] = mapped_column(String(2048))
    status: Mapped[PageStatus] = mapped_column(Enum(PageStatus), default=PageStatus.PENDING)
    outgoing_links: Mapped[Optional[list]] = mapped_column(JSONB)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    processing_version: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("institution_id", "url", name="uq_pages_institution_url"),
    )

    institution: Mapped["Institution"] = relationship()
    crawl_job: Mapped[Optional["CrawlJob"]] = relationship(back_populates="pages")
    chunks: Mapped[List["ContentChunk"]] = relationship(back_populates="page")


# ============================================================
# Documents
# ============================================================

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(1024))
    file_name: Mapped[Optional[str]] = mapped_column(String(512))
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), default=DocumentType.PDF)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    is_scanned: Mapped[Optional[bool]] = mapped_column(Boolean)
    ocr_engine: Mapped[Optional[str]] = mapped_column(String(50))
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float)
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(String(1024))
    author: Mapped[Optional[str]] = mapped_column(String(512))
    academic_year: Mapped[Optional[str]] = mapped_column(String(20))
    publication_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    document_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    processing_version: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    doc_pages: Mapped[List["DocumentPage"]] = relationship(back_populates="document")
    doc_tables: Mapped[List["DocumentTable"]] = relationship(back_populates="document")
    chunks: Mapped[List["ContentChunk"]] = relationship(back_populates="document")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[Optional[str]] = mapped_column(Text)
    ocr_text: Mapped[Optional[str]] = mapped_column(Text)
    ocr_confidence: Mapped[Optional[float]] = mapped_column(Float)
    is_scanned: Mapped[bool] = mapped_column(Boolean, default=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(1024))
    page_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    document: Mapped["Document"] = relationship(back_populates="doc_pages")


class DocumentTable(Base):
    __tablename__ = "document_tables"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    table_index: Mapped[int] = mapped_column(Integer, default=0)
    headers: Mapped[Optional[list]] = mapped_column(JSONB)
    rows: Mapped[Optional[list]] = mapped_column(JSONB)
    table_type: Mapped[Optional[str]] = mapped_column(String(100))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    table_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    document: Mapped["Document"] = relationship(back_populates="doc_tables")


# ============================================================
# Content Chunks and Embeddings
# ============================================================

class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    page_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("pages.id"))
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("documents.id"))
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(2048))
    source_title: Mapped[Optional[str]] = mapped_column(String(1024))
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    char_start: Mapped[Optional[int]] = mapped_column(Integer)
    char_end: Mapped[Optional[int]] = mapped_column(Integer)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    academic_year: Mapped[Optional[str]] = mapped_column(String(20))
    chunk_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    embedding_model_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("model_registry.id"))
    embedding_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    faiss_index_id: Mapped[Optional[int]] = mapped_column(Integer)
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    page: Mapped[Optional["Page"]] = relationship(back_populates="chunks")
    document: Mapped[Optional["Document"]] = relationship(back_populates="chunks")


# ============================================================
# Model Registry
# ============================================================

class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(100))
    model_type: Mapped[str] = mapped_column(String(50))  # embedding, reranker, ocr
    embedding_dimension: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    model_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# Entities
# ============================================================

class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    entity_type: Mapped[EntityType] = mapped_column(Enum(EntityType), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    entity_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    aliases: Mapped[List["EntityAlias"]] = relationship(back_populates="entity")
    relationships_as_source: Mapped[List["EntityRelationship"]] = relationship(
        back_populates="source_entity", foreign_keys="EntityRelationship.source_entity_id"
    )


class EntityAlias(Base):
    __tablename__ = "entity_aliases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(512), nullable=False)
    alias_type: Mapped[Optional[str]] = mapped_column(String(50))  # abbreviation, alternate_name
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entity: Mapped["Entity"] = relationship(back_populates="aliases")


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), nullable=False)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("entities.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(100))  # heads, works_in, member_of, etc.
    effective_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    academic_year: Mapped[Optional[str]] = mapped_column(String(20))
    source_url: Mapped[Optional[str]] = mapped_column(String(2048))
    source_chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("content_chunks.id"))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source_entity: Mapped["Entity"] = relationship(
        back_populates="relationships_as_source", foreign_keys=[source_entity_id]
    )
    target_entity: Mapped["Entity"] = relationship(foreign_keys=[target_entity_id])


# ============================================================
# Departments and Academic Years
# ============================================================

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(50))
    abbreviation: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    institution: Mapped["Institution"] = relationship(back_populates="departments")
    placement_records: Mapped[List["PlacementRecord"]] = relationship(back_populates="department")
    fee_records: Mapped[List["FeeRecord"]] = relationship(back_populates="department")


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    year_label: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "2024-25"
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    institution: Mapped["Institution"] = relationship(back_populates="academic_years")

    __table_args__ = (
        UniqueConstraint("institution_id", "year_label", name="uq_academic_year"),
    )


# ============================================================
# Institutional Facts
# ============================================================

class InstitutionalFact(Base):
    __tablename__ = "institutional_facts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    fact_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(512))
    predicate: Mapped[str] = mapped_column(String(255), nullable=False)
    object_text: Mapped[Optional[str]] = mapped_column(Text)
    object_value: Mapped[Optional[float]] = mapped_column(Float)
    academic_year: Mapped[Optional[str]] = mapped_column(String(20))
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source_url: Mapped[Optional[str]] = mapped_column(String(2048))
    source_chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("content_chunks.id"))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.UNCERTAIN
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ============================================================
# Placement and Fee Records
# ============================================================

class PlacementRecord(Base):
    __tablename__ = "placement_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("departments.id"))
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    record_type: Mapped[str] = mapped_column(String(50))  # full_time, internship, aggregate
    total_students: Mapped[Optional[int]] = mapped_column(Integer)
    students_placed: Mapped[Optional[int]] = mapped_column(Integer)
    companies_visited: Mapped[Optional[int]] = mapped_column(Integer)
    offers_made: Mapped[Optional[int]] = mapped_column(Integer)
    highest_package_lpa: Mapped[Optional[float]] = mapped_column(Float)
    average_package_lpa: Mapped[Optional[float]] = mapped_column(Float)
    median_package_lpa: Mapped[Optional[float]] = mapped_column(Float)
    package_distribution: Mapped[Optional[dict]] = mapped_column(JSONB)
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("documents.id"))
    source_url: Mapped[Optional[str]] = mapped_column(String(2048))
    source_page_number: Mapped[Optional[int]] = mapped_column(Integer)
    data_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    department: Mapped[Optional["Department"]] = relationship(back_populates="placement_records")


class FeeRecord(Base):
    __tablename__ = "fee_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("departments.id"))
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    admission_category: Mapped[Optional[str]] = mapped_column(String(100))
    fee_type: Mapped[str] = mapped_column(String(100))  # tuition, development, total
    amount_inr: Mapped[Optional[float]] = mapped_column(Float)
    per_year: Mapped[bool] = mapped_column(Boolean, default=True)
    additional_charges: Mapped[Optional[dict]] = mapped_column(JSONB)
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("documents.id"))
    source_url: Mapped[Optional[str]] = mapped_column(String(2048))
    source_page_number: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    department: Mapped[Optional["Department"]] = relationship(back_populates="fee_records")


# ============================================================
# Evidence
# ============================================================

class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_history_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("query_history.id"))
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("content_chunks.id"))
    source_url: Mapped[Optional[str]] = mapped_column(String(2048))
    source_title: Mapped[Optional[str]] = mapped_column(String(1024))
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("documents.id"))
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    passage: Mapped[Optional[str]] = mapped_column(Text)
    academic_year: Mapped[Optional[str]] = mapped_column(String(20))
    retrieval_score: Mapped[Optional[float]] = mapped_column(Float)
    retrieval_rank: Mapped[Optional[int]] = mapped_column(Integer)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.UNCERTAIN
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    query_history: Mapped[Optional["QueryHistory"]] = relationship(back_populates="evidence_records")


# ============================================================
# Query History
# ============================================================

class QueryHistory(Base):
    __tablename__ = "query_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("institutions.id"), nullable=False)
    raw_query: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_query: Mapped[Optional[str]] = mapped_column(Text)
    query_intent: Mapped[Optional[str]] = mapped_column(String(100))
    query_entities: Mapped[Optional[list]] = mapped_column(JSONB)
    answer_text: Mapped[Optional[str]] = mapped_column(Text)
    answer_confidence: Mapped[Optional[float]] = mapped_column(Float)
    verification_status: Mapped[Optional[VerificationStatus]] = mapped_column(Enum(VerificationStatus))
    retrieval_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    total_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    is_answerable: Mapped[Optional[bool]] = mapped_column(Boolean)
    session_id: Mapped[Optional[str]] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence_records: Mapped[List["EvidenceRecord"]] = relationship(back_populates="query_history")


# ============================================================
# Processing Jobs
# ============================================================

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.QUEUED)
    queue_name: Mapped[Optional[str]] = mapped_column(String(50))
    rq_job_id: Mapped[Optional[str]] = mapped_column(String(255))
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
