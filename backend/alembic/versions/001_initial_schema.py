"""
VEDANTA initial database schema migration.
Revision: 001_initial_schema
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # institutions
    op.create_table(
        "institutions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_name", sa.String(50), nullable=False),
        sa.Column("website", sa.String(512), nullable=False),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(100)),
        sa.Column("country", sa.String(100), server_default="India"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("short_name"),
    )

    # domains
    op.create_table(
        "domains",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="false"),
        sa.Column("is_allowed_crawl", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )

    # crawl_jobs
    op.create_table(
        "crawl_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_url", sa.String(2048), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("max_depth", sa.Integer(), server_default="5"),
        sa.Column("max_pages", sa.Integer(), server_default="5000"),
        sa.Column("pages_discovered", sa.Integer(), server_default="0"),
        sa.Column("pages_crawled", sa.Integer(), server_default="0"),
        sa.Column("pages_failed", sa.Integer(), server_default="0"),
        sa.Column("pages_skipped", sa.Integer(), server_default="0"),
        sa.Column("documents_found", sa.Integer(), server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
        sa.Column("config", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )

    # pages
    op.create_table(
        "pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crawl_job_id", postgresql.UUID(as_uuid=True)),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("canonical_url", sa.String(2048)),
        sa.Column("title", sa.String(1024)),
        sa.Column("content", sa.Text()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("content_type", sa.String(255)),
        sa.Column("etag", sa.String(255)),
        sa.Column("last_modified", sa.String(255)),
        sa.Column("http_status", sa.Integer()),
        sa.Column("crawl_depth", sa.Integer(), server_default="0"),
        sa.Column("parent_url", sa.String(2048)),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("outgoing_links", postgresql.JSONB),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True)),
        sa.Column("last_processed_at", sa.DateTime(timezone=True)),
        sa.Column("processing_version", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "url", name="uq_pages_institution_url"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["crawl_job_id"], ["crawl_jobs.id"]),
    )
    op.create_index("ix_pages_url", "pages", ["url"])
    op.create_index("ix_pages_status", "pages", ["status"])
    op.create_index("ix_pages_institution_id", "pages", ["institution_id"])

    # model_registry
    op.create_table(
        "model_registry",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_version", sa.String(100)),
        sa.Column("model_type", sa.String(50), nullable=False),
        sa.Column("embedding_dimension", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("model_metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )

    # documents
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_url", sa.String(2048), nullable=False),
        sa.Column("file_path", sa.String(1024)),
        sa.Column("file_name", sa.String(512)),
        sa.Column("file_hash", sa.String(64)),
        sa.Column("file_size_bytes", sa.Integer()),
        sa.Column("document_type", sa.String(50), server_default="pdf"),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("is_scanned", sa.Boolean()),
        sa.Column("ocr_engine", sa.String(50)),
        sa.Column("ocr_confidence", sa.Float()),
        sa.Column("page_count", sa.Integer()),
        sa.Column("title", sa.String(1024)),
        sa.Column("author", sa.String(512)),
        sa.Column("academic_year", sa.String(20)),
        sa.Column("publication_date", sa.DateTime(timezone=True)),
        sa.Column("document_metadata", postgresql.JSONB),
        sa.Column("processing_version", sa.String(50)),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )
    op.create_index("ix_documents_file_hash", "documents", ["file_hash"])
    op.create_index("ix_documents_status", "documents", ["status"])

    # document_pages
    op.create_table(
        "document_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text()),
        sa.Column("ocr_text", sa.Text()),
        sa.Column("ocr_confidence", sa.Float()),
        sa.Column("is_scanned", sa.Boolean(), server_default="false"),
        sa.Column("image_path", sa.String(1024)),
        sa.Column("page_metadata", postgresql.JSONB),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
    )

    # document_tables
    op.create_table(
        "document_tables",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("table_index", sa.Integer(), server_default="0"),
        sa.Column("headers", postgresql.JSONB),
        sa.Column("rows", postgresql.JSONB),
        sa.Column("table_type", sa.String(100)),
        sa.Column("confidence", sa.Float()),
        sa.Column("raw_text", sa.Text()),
        sa.Column("table_metadata", postgresql.JSONB),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
    )

    # content_chunks
    op.create_table(
        "content_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True)),
        sa.Column("document_id", postgresql.UUID(as_uuid=True)),
        sa.Column("chunk_index", sa.Integer(), server_default="0"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(64), nullable=False),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("source_title", sa.String(1024)),
        sa.Column("page_number", sa.Integer()),
        sa.Column("char_start", sa.Integer()),
        sa.Column("char_end", sa.Integer()),
        sa.Column("token_count", sa.Integer()),
        sa.Column("academic_year", sa.String(20)),
        sa.Column("chunk_metadata", postgresql.JSONB),
        sa.Column("embedding_model_id", postgresql.UUID(as_uuid=True)),
        sa.Column("embedding_generated_at", sa.DateTime(timezone=True)),
        sa.Column("faiss_index_id", sa.Integer()),
        sa.Column("is_indexed", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["page_id"], ["pages.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["embedding_model_id"], ["model_registry.id"]),
    )
    op.create_index("ix_chunks_institution", "content_chunks", ["institution_id"])
    op.create_index("ix_chunks_is_indexed", "content_chunks", ["is_indexed"])

    # entities
    op.create_table(
        "entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("canonical_name", sa.String(512), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("entity_metadata", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )

    # entity_aliases
    op.create_table(
        "entity_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alias", sa.String(512), nullable=False),
        sa.Column("alias_type", sa.String(50)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"]),
    )

    # entity_relationships
    op.create_table(
        "entity_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(100)),
        sa.Column("effective_from", sa.DateTime(timezone=True)),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.Column("academic_year", sa.String(20)),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("source_chunk_id", postgresql.UUID(as_uuid=True)),
        sa.Column("confidence", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["source_entity_id"], ["entities.id"]),
        sa.ForeignKeyConstraint(["target_entity_id"], ["entities.id"]),
    )

    # departments
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_name", sa.String(50)),
        sa.Column("abbreviation", sa.String(20)),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )

    # academic_years
    op.create_table(
        "academic_years",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("year_label", sa.String(20), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=False),
        sa.Column("end_year", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "year_label", name="uq_academic_year"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )

    # institutional_facts
    op.create_table(
        "institutional_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("fact_type", sa.String(100), nullable=False),
        sa.Column("subject", sa.String(512)),
        sa.Column("predicate", sa.String(255), nullable=False),
        sa.Column("object_text", sa.Text()),
        sa.Column("object_value", sa.Float()),
        sa.Column("academic_year", sa.String(20)),
        sa.Column("effective_date", sa.DateTime(timezone=True)),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("source_chunk_id", postgresql.UUID(as_uuid=True)),
        sa.Column("verification_status", sa.String(50), server_default="uncertain"),
        sa.Column("confidence", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )

    # placement_records
    op.create_table(
        "placement_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True)),
        sa.Column("academic_year", sa.String(20), nullable=False),
        sa.Column("record_type", sa.String(50)),
        sa.Column("total_students", sa.Integer()),
        sa.Column("students_placed", sa.Integer()),
        sa.Column("companies_visited", sa.Integer()),
        sa.Column("offers_made", sa.Integer()),
        sa.Column("highest_package_lpa", sa.Float()),
        sa.Column("average_package_lpa", sa.Float()),
        sa.Column("median_package_lpa", sa.Float()),
        sa.Column("package_distribution", postgresql.JSONB),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("source_page_number", sa.Integer()),
        sa.Column("data_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
    )

    # fee_records
    op.create_table(
        "fee_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True)),
        sa.Column("academic_year", sa.String(20), nullable=False),
        sa.Column("admission_category", sa.String(100)),
        sa.Column("fee_type", sa.String(100)),
        sa.Column("amount_inr", sa.Float()),
        sa.Column("per_year", sa.Boolean(), server_default="true"),
        sa.Column("additional_charges", postgresql.JSONB),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("source_page_number", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
    )

    # query_history
    op.create_table(
        "query_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("raw_query", sa.Text(), nullable=False),
        sa.Column("normalized_query", sa.Text()),
        sa.Column("query_intent", sa.String(100)),
        sa.Column("query_entities", postgresql.JSONB),
        sa.Column("answer_text", sa.Text()),
        sa.Column("answer_confidence", sa.Float()),
        sa.Column("verification_status", sa.String(50)),
        sa.Column("retrieval_latency_ms", sa.Integer()),
        sa.Column("total_latency_ms", sa.Integer()),
        sa.Column("cache_hit", sa.Boolean(), server_default="false"),
        sa.Column("is_answerable", sa.Boolean()),
        sa.Column("session_id", sa.String(100)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )

    # evidence_records
    op.create_table(
        "evidence_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query_history_id", postgresql.UUID(as_uuid=True)),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True)),
        sa.Column("source_url", sa.String(2048)),
        sa.Column("source_title", sa.String(1024)),
        sa.Column("document_id", postgresql.UUID(as_uuid=True)),
        sa.Column("page_number", sa.Integer()),
        sa.Column("passage", sa.Text()),
        sa.Column("academic_year", sa.String(20)),
        sa.Column("retrieval_score", sa.Float()),
        sa.Column("retrieval_rank", sa.Integer()),
        sa.Column("verification_status", sa.String(50), server_default="uncertain"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["query_history_id"], ["query_history.id"]),
    )

    # processing_jobs
    op.create_table(
        "processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), server_default="queued"),
        sa.Column("queue_name", sa.String(50)),
        sa.Column("rq_job_id", sa.String(255)),
        sa.Column("payload", postgresql.JSONB),
        sa.Column("result", postgresql.JSONB),
        sa.Column("error_message", sa.Text()),
        sa.Column("attempts", sa.Integer(), server_default="0"),
        sa.Column("max_attempts", sa.Integer(), server_default="3"),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_status", "processing_jobs", ["status"])
    op.create_index("ix_jobs_type", "processing_jobs", ["job_type"])

    # Seed MITAOE institution
    op.execute("""
        INSERT INTO institutions (id, name, short_name, website, city, state, country, is_active)
        VALUES (
            '00000000-0000-0000-0000-000000000001',
            'MIT Academy of Engineering',
            'MITAOE',
            'https://mitaoe.ac.in',
            'Pune',
            'Maharashtra',
            'India',
            true
        ) ON CONFLICT DO NOTHING;
    """)

    op.execute("""
        INSERT INTO domains (id, institution_id, domain, is_primary, is_allowed_crawl)
        VALUES
            ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'mitaoe.ac.in', true, true),
            ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000001', 'www.mitaoe.ac.in', false, true)
        ON CONFLICT DO NOTHING;
    """)

    # Seed MITAOE departments
    departments = [
        ("00000000-0000-0000-0000-000000000021", "Computer Engineering", "CE", "CE"),
        ("00000000-0000-0000-0000-000000000022", "Computer Science and Engineering", "CSE", "CSE"),
        ("00000000-0000-0000-0000-000000000023", "Artificial Intelligence and Machine Learning", "AIML", "AIML"),
        ("00000000-0000-0000-0000-000000000024", "Information Technology", "IT", "IT"),
        ("00000000-0000-0000-0000-000000000025", "Electronics and Telecommunication Engineering", "ENTC", "ENTC"),
        ("00000000-0000-0000-0000-000000000026", "Mechanical Engineering", "MECH", "MECH"),
        ("00000000-0000-0000-0000-000000000027", "Civil Engineering", "CIVIL", "CIVIL"),
        ("00000000-0000-0000-0000-000000000028", "First Year Engineering", "FY", "FY"),
    ]
    for dept_id, name, short_name, abbrev in departments:
        op.execute(f"""
            INSERT INTO departments (id, institution_id, name, short_name, abbreviation, is_active)
            VALUES ('{dept_id}', '00000000-0000-0000-0000-000000000001', '{name}', '{short_name}', '{abbrev}', true)
            ON CONFLICT DO NOTHING;
        """)

    # Seed model registry
    op.execute("""
        INSERT INTO model_registry (id, model_name, model_type, embedding_dimension, is_active)
        VALUES (
            '00000000-0000-0000-0000-000000000031',
            'sentence-transformers/all-MiniLM-L6-v2',
            'embedding',
            384,
            true
        ) ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    tables = [
        "processing_jobs", "evidence_records", "query_history",
        "fee_records", "placement_records", "institutional_facts",
        "academic_years", "departments", "entity_relationships",
        "entity_aliases", "entities", "content_chunks",
        "document_tables", "document_pages", "documents",
        "model_registry", "pages", "crawl_jobs", "domains", "institutions",
    ]
    for table in tables:
        op.drop_table(table)
