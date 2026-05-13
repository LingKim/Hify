"""Knowledge module ORM models."""

from __future__ import annotations

from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampSoftDeleteMixin
from app.knowledge.vector import PgVector


class KnowledgeBase(TimestampSoftDeleteMixin, Base):
    """A document collection that can be retrieved by agents."""

    __tablename__: ClassVar[str] = "knowledge_bases"
    __table_args__ = (
        CheckConstraint("name <> ''", name="ck_knowledge_bases_name_non_empty"),
        CheckConstraint(
            "status <> ''",
            name="ck_knowledge_bases_status_non_empty",
        ),
        CheckConstraint(
            "visibility <> ''",
            name="ck_knowledge_bases_visibility_non_empty",
        ),
        CheckConstraint(
            "embedding_dimensions > 0",
            name="ck_knowledge_bases_embedding_dimensions_positive",
        ),
        CheckConstraint(
            "chunk_size > 0",
            name="ck_knowledge_bases_chunk_size_positive",
        ),
        CheckConstraint(
            "chunk_overlap >= 0",
            name="ck_knowledge_bases_chunk_overlap_non_negative",
        ),
        CheckConstraint(
            "chunk_overlap < chunk_size",
            name="ck_knowledge_bases_chunk_overlap_lt_size",
        ),
        CheckConstraint(
            "default_top_k > 0",
            name="ck_knowledge_bases_default_top_k_positive",
        ),
        CheckConstraint(
            "default_score_threshold >= 0",
            name="ck_knowledge_bases_score_threshold_min",
        ),
        CheckConstraint(
            "default_score_threshold <= 1",
            name="ck_knowledge_bases_score_threshold_max",
        ),
        CheckConstraint(
            "document_count >= 0",
            name="ck_knowledge_bases_document_count_non_negative",
        ),
        CheckConstraint(
            "chunk_count >= 0",
            name="ck_knowledge_bases_chunk_count_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_knowledge_bases_version_positive",
        ),
        Index("ix_knowledge_bases_owner_user_id", "owner_user_id"),
        Index("ix_knowledge_bases_status", "status"),
        Index("ix_knowledge_bases_updated_at", "updated_at"),
        Index("ix_knowledge_bases_deleted_at", "deleted_at"),
        Index(
            "ux_knowledge_bases_owner_user_id_name_active",
            "owner_user_id",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    owner_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="draft",
        server_default="draft",
    )
    visibility: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="private",
        server_default="private",
    )
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    embedding_dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=800,
        server_default="800",
    )
    chunk_overlap: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=120,
        server_default="120",
    )
    default_top_k: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        server_default="5",
    )
    default_score_threshold: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=0.65,
        server_default="0.6500",
    )
    document_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_indexed_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )


class KnowledgeDocument(TimestampSoftDeleteMixin, Base):
    """An uploaded source document inside one knowledge base."""

    __tablename__: ClassVar[str] = "knowledge_documents"
    __table_args__ = (
        CheckConstraint(
            "filename <> ''",
            name="ck_knowledge_documents_filename_non_empty",
        ),
        CheckConstraint(
            "status <> ''",
            name="ck_knowledge_documents_status_non_empty",
        ),
        CheckConstraint(
            "process_stage <> ''",
            name="ck_knowledge_documents_process_stage_non_empty",
        ),
        CheckConstraint(
            "file_size_bytes > 0",
            name="ck_knowledge_documents_file_size_positive",
        ),
        CheckConstraint(
            "chunk_count >= 0",
            name="ck_knowledge_documents_chunk_count_non_negative",
        ),
        CheckConstraint(
            "token_count >= 0",
            name="ck_knowledge_documents_token_count_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_knowledge_documents_version_positive",
        ),
        Index("ix_knowledge_documents_knowledge_base_id", "knowledge_base_id"),
        Index("ix_knowledge_documents_uploader_user_id", "uploader_user_id"),
        Index("ix_knowledge_documents_status", "status"),
        Index("ix_knowledge_documents_content_hash", "content_hash"),
        Index("ix_knowledge_documents_created_at", "created_at"),
        Index("ix_knowledge_documents_deleted_at", "deleted_at"),
    )

    knowledge_base_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_bases.id"),
        nullable=False,
    )
    uploader_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_ext: Mapped[str] = mapped_column(String(16), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
    )
    process_stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="uploaded",
        server_default="uploaded",
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Any | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )


class KnowledgeChunk(TimestampSoftDeleteMixin, Base):
    """One retrievable text chunk with an embedding vector."""

    __tablename__: ClassVar[str] = "knowledge_chunks"
    __table_args__ = (
        CheckConstraint(
            "chunk_index >= 1",
            name="ck_knowledge_chunks_chunk_index_positive",
        ),
        CheckConstraint(
            "content <> ''",
            name="ck_knowledge_chunks_content_non_empty",
        ),
        CheckConstraint(
            "token_count >= 0",
            name="ck_knowledge_chunks_token_count_non_negative",
        ),
        CheckConstraint(
            "embedding_model <> ''",
            name="ck_knowledge_chunks_embedding_model_non_empty",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_knowledge_chunks_version_positive",
        ),
        Index("ix_knowledge_chunks_knowledge_base_id", "knowledge_base_id"),
        Index("ix_knowledge_chunks_document_id", "document_id"),
        Index("ix_knowledge_chunks_deleted_at", "deleted_at"),
        Index(
            "ux_knowledge_chunks_document_id_chunk_index_active",
            "document_id",
            "chunk_index",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    knowledge_base_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_bases.id"),
        nullable=False,
    )
    document_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_documents.id"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    source_location_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    embedding: Mapped[str] = mapped_column(PgVector(), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )


class KnowledgeRetrievalLog(TimestampSoftDeleteMixin, Base):
    """A retrieval test or conversation retrieval audit record."""

    __tablename__: ClassVar[str] = "knowledge_retrieval_logs"
    __table_args__ = (
        CheckConstraint(
            "source <> ''",
            name="ck_knowledge_retrieval_logs_source_non_empty",
        ),
        CheckConstraint(
            "query_text <> ''",
            name="ck_knowledge_retrieval_logs_query_text_non_empty",
        ),
        CheckConstraint(
            "top_k > 0",
            name="ck_knowledge_retrieval_logs_top_k_positive",
        ),
        CheckConstraint(
            "score_threshold >= 0",
            name="ck_knowledge_retrieval_logs_score_threshold_min",
        ),
        CheckConstraint(
            "score_threshold <= 1",
            name="ck_knowledge_retrieval_logs_score_threshold_max",
        ),
        CheckConstraint(
            "hit_count >= 0",
            name="ck_knowledge_retrieval_logs_hit_count_non_negative",
        ),
        CheckConstraint(
            "latency_ms >= 0",
            name="ck_knowledge_retrieval_logs_latency_ms_non_negative",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_knowledge_retrieval_logs_version_positive",
        ),
        Index(
            "ix_knowledge_retrieval_logs_knowledge_base_id",
            "knowledge_base_id",
        ),
        Index("ix_knowledge_retrieval_logs_conversation_id", "conversation_id"),
        Index("ix_knowledge_retrieval_logs_run_id", "run_id"),
        Index("ix_knowledge_retrieval_logs_user_id", "user_id"),
        Index("ix_knowledge_retrieval_logs_source", "source"),
        Index("ix_knowledge_retrieval_logs_created_at", "created_at"),
    )

    knowledge_base_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_bases.id"),
        nullable=False,
    )
    conversation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("conversation_sessions.id"),
        nullable=True,
    )
    run_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("conversation_runs.id"),
        nullable=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    score_threshold: Mapped[float] = mapped_column(
        Numeric(5, 4),
        nullable=False,
    )
    hit_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hits_json: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
