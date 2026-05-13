"""create knowledge tables

Revision ID: 20260513_0009
Revises: 20260512_0008
Create Date: 2026-05-13 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260513_0009"
down_revision: str | None = "20260512_0008"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("1"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_bases",
        sa.Column("owner_user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column(
            "visibility",
            sa.String(length=32),
            server_default=sa.text("'private'"),
            nullable=False,
        ),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("embedding_dimensions", sa.Integer(), nullable=False),
        sa.Column(
            "chunk_size",
            sa.Integer(),
            server_default=sa.text("800"),
            nullable=False,
        ),
        sa.Column(
            "chunk_overlap",
            sa.Integer(),
            server_default=sa.text("120"),
            nullable=False,
        ),
        sa.Column(
            "default_top_k",
            sa.Integer(),
            server_default=sa.text("5"),
            nullable=False,
        ),
        sa.Column(
            "default_score_threshold",
            sa.Numeric(5, 4),
            server_default=sa.text("0.6500"),
            nullable=False,
        ),
        sa.Column(
            "document_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "chunk_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "name <> ''",
            name=op.f("ck_knowledge_bases_name_non_empty"),
        ),
        sa.CheckConstraint(
            "status <> ''",
            name=op.f("ck_knowledge_bases_status_non_empty"),
        ),
        sa.CheckConstraint(
            "visibility <> ''",
            name=op.f("ck_knowledge_bases_visibility_non_empty"),
        ),
        sa.CheckConstraint(
            "embedding_dimensions > 0",
            name=op.f("ck_knowledge_bases_embedding_dimensions_positive"),
        ),
        sa.CheckConstraint(
            "chunk_size > 0",
            name=op.f("ck_knowledge_bases_chunk_size_positive"),
        ),
        sa.CheckConstraint(
            "chunk_overlap >= 0",
            name=op.f("ck_knowledge_bases_chunk_overlap_non_negative"),
        ),
        sa.CheckConstraint(
            "chunk_overlap < chunk_size",
            name=op.f("ck_knowledge_bases_chunk_overlap_lt_size"),
        ),
        sa.CheckConstraint(
            "default_top_k > 0",
            name=op.f("ck_knowledge_bases_default_top_k_positive"),
        ),
        sa.CheckConstraint(
            "default_score_threshold >= 0",
            name=op.f("ck_knowledge_bases_score_threshold_min"),
        ),
        sa.CheckConstraint(
            "default_score_threshold <= 1",
            name=op.f("ck_knowledge_bases_score_threshold_max"),
        ),
        sa.CheckConstraint(
            "document_count >= 0",
            name=op.f("ck_knowledge_bases_document_count_non_negative"),
        ),
        sa.CheckConstraint(
            "chunk_count >= 0",
            name=op.f("ck_knowledge_bases_chunk_count_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_knowledge_bases_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["users.id"],
            name=op.f("fk_knowledge_bases_owner_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_bases")),
    )
    op.create_index(
        op.f("ix_knowledge_bases_deleted_at"),
        "knowledge_bases",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_knowledge_bases_owner_user_id"),
        "knowledge_bases",
        ["owner_user_id"],
    )
    op.create_index(
        op.f("ix_knowledge_bases_status"),
        "knowledge_bases",
        ["status"],
    )
    op.create_index(
        op.f("ix_knowledge_bases_updated_at"),
        "knowledge_bases",
        ["updated_at"],
    )
    op.create_index(
        "ux_knowledge_bases_owner_user_id_name_active",
        "knowledge_bases",
        ["owner_user_id", "name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("knowledge_base_id", sa.BigInteger(), nullable=False),
        sa.Column("uploader_user_id", sa.BigInteger(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_ext", sa.String(length=16), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'uploaded'"),
            nullable=False,
        ),
        sa.Column(
            "process_stage",
            sa.String(length=32),
            server_default=sa.text("'uploaded'"),
            nullable=False,
        ),
        sa.Column(
            "chunk_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "token_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "filename <> ''",
            name=op.f("ck_knowledge_documents_filename_non_empty"),
        ),
        sa.CheckConstraint(
            "status <> ''",
            name=op.f("ck_knowledge_documents_status_non_empty"),
        ),
        sa.CheckConstraint(
            "process_stage <> ''",
            name=op.f("ck_knowledge_documents_process_stage_non_empty"),
        ),
        sa.CheckConstraint(
            "file_size_bytes > 0",
            name=op.f("ck_knowledge_documents_file_size_positive"),
        ),
        sa.CheckConstraint(
            "chunk_count >= 0",
            name=op.f("ck_knowledge_documents_chunk_count_non_negative"),
        ),
        sa.CheckConstraint(
            "token_count >= 0",
            name=op.f("ck_knowledge_documents_token_count_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_knowledge_documents_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_bases.id"],
            name=op.f(
                "fk_knowledge_documents_knowledge_base_id_knowledge_bases"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["uploader_user_id"],
            ["users.id"],
            name=op.f("fk_knowledge_documents_uploader_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_documents")),
    )
    op.create_index(
        op.f("ix_knowledge_documents_content_hash"),
        "knowledge_documents",
        ["content_hash"],
    )
    op.create_index(
        op.f("ix_knowledge_documents_created_at"),
        "knowledge_documents",
        ["created_at"],
    )
    op.create_index(
        op.f("ix_knowledge_documents_deleted_at"),
        "knowledge_documents",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_knowledge_documents_knowledge_base_id"),
        "knowledge_documents",
        ["knowledge_base_id"],
    )
    op.create_index(
        op.f("ix_knowledge_documents_status"),
        "knowledge_documents",
        ["status"],
    )
    op.create_index(
        op.f("ix_knowledge_documents_uploader_user_id"),
        "knowledge_documents",
        ["uploader_user_id"],
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("knowledge_base_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "token_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("source_location_json", sa.JSON(), nullable=True),
        sa.Column("embedding_model", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "chunk_index >= 1",
            name=op.f("ck_knowledge_chunks_chunk_index_positive"),
        ),
        sa.CheckConstraint(
            "content <> ''",
            name=op.f("ck_knowledge_chunks_content_non_empty"),
        ),
        sa.CheckConstraint(
            "token_count >= 0",
            name=op.f("ck_knowledge_chunks_token_count_non_negative"),
        ),
        sa.CheckConstraint(
            "embedding_model <> ''",
            name=op.f("ck_knowledge_chunks_embedding_model_non_empty"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_knowledge_chunks_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["knowledge_documents.id"],
            name=op.f("fk_knowledge_chunks_document_id_knowledge_documents"),
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_bases.id"],
            name=op.f(
                "fk_knowledge_chunks_knowledge_base_id_knowledge_bases"
            ),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_chunks")),
    )
    op.execute(
        "ALTER TABLE knowledge_chunks "
        "ADD COLUMN embedding vector(1024) NOT NULL"
    )
    op.create_index(
        op.f("ix_knowledge_chunks_deleted_at"),
        "knowledge_chunks",
        ["deleted_at"],
    )
    op.create_index(
        op.f("ix_knowledge_chunks_document_id"),
        "knowledge_chunks",
        ["document_id"],
    )
    op.create_index(
        op.f("ix_knowledge_chunks_knowledge_base_id"),
        "knowledge_chunks",
        ["knowledge_base_id"],
    )
    op.create_index(
        "ux_knowledge_chunks_document_id_chunk_index_active",
        "knowledge_chunks",
        ["document_id", "chunk_index"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "knowledge_retrieval_logs",
        sa.Column("knowledge_base_id", sa.BigInteger(), nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("run_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("score_threshold", sa.Numeric(5, 4), nullable=False),
        sa.Column(
            "hit_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("hits_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        *_audit_columns(),
        sa.CheckConstraint(
            "source <> ''",
            name=op.f("ck_knowledge_retrieval_logs_source_non_empty"),
        ),
        sa.CheckConstraint(
            "query_text <> ''",
            name=op.f("ck_knowledge_retrieval_logs_query_text_non_empty"),
        ),
        sa.CheckConstraint(
            "top_k > 0",
            name=op.f("ck_knowledge_retrieval_logs_top_k_positive"),
        ),
        sa.CheckConstraint(
            "score_threshold >= 0",
            name=op.f("ck_knowledge_retrieval_logs_score_threshold_min"),
        ),
        sa.CheckConstraint(
            "score_threshold <= 1",
            name=op.f("ck_knowledge_retrieval_logs_score_threshold_max"),
        ),
        sa.CheckConstraint(
            "hit_count >= 0",
            name=op.f("ck_knowledge_retrieval_logs_hit_count_non_negative"),
        ),
        sa.CheckConstraint(
            "latency_ms >= 0",
            name=op.f("ck_knowledge_retrieval_logs_latency_ms_non_negative"),
        ),
        sa.CheckConstraint(
            "version >= 1",
            name=op.f("ck_knowledge_retrieval_logs_version_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation_sessions.id"],
            name=op.f(
                "fk_knowledge_retrieval_logs_conversation_id_"
                "conversation_sessions"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_base_id"],
            ["knowledge_bases.id"],
            name=op.f(
                "fk_knowledge_retrieval_logs_knowledge_base_id_"
                "knowledge_bases"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["conversation_runs.id"],
            name=op.f("fk_knowledge_retrieval_logs_run_id_conversation_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_knowledge_retrieval_logs_user_id_users"),
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_knowledge_retrieval_logs"),
        ),
    )
    op.create_index(
        op.f("ix_knowledge_retrieval_logs_conversation_id"),
        "knowledge_retrieval_logs",
        ["conversation_id"],
    )
    op.create_index(
        op.f("ix_knowledge_retrieval_logs_created_at"),
        "knowledge_retrieval_logs",
        ["created_at"],
    )
    op.create_index(
        op.f("ix_knowledge_retrieval_logs_knowledge_base_id"),
        "knowledge_retrieval_logs",
        ["knowledge_base_id"],
    )
    op.create_index(
        op.f("ix_knowledge_retrieval_logs_run_id"),
        "knowledge_retrieval_logs",
        ["run_id"],
    )
    op.create_index(
        op.f("ix_knowledge_retrieval_logs_source"),
        "knowledge_retrieval_logs",
        ["source"],
    )
    op.create_index(
        op.f("ix_knowledge_retrieval_logs_user_id"),
        "knowledge_retrieval_logs",
        ["user_id"],
    )

    op.execute(
        """
        DELETE FROM agent_knowledge_bindings akb
        WHERE NOT EXISTS (
            SELECT 1
            FROM knowledge_bases kb
            WHERE kb.id = akb.knowledge_base_id
        )
        """
    )
    op.create_foreign_key(
        op.f(
            "fk_agent_knowledge_bindings_knowledge_base_id_knowledge_bases"
        ),
        "agent_knowledge_bindings",
        "knowledge_bases",
        ["knowledge_base_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f(
            "fk_agent_knowledge_bindings_knowledge_base_id_knowledge_bases"
        ),
        "agent_knowledge_bindings",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_knowledge_retrieval_logs_user_id"),
        table_name="knowledge_retrieval_logs",
    )
    op.drop_index(
        op.f("ix_knowledge_retrieval_logs_source"),
        table_name="knowledge_retrieval_logs",
    )
    op.drop_index(
        op.f("ix_knowledge_retrieval_logs_run_id"),
        table_name="knowledge_retrieval_logs",
    )
    op.drop_index(
        op.f("ix_knowledge_retrieval_logs_knowledge_base_id"),
        table_name="knowledge_retrieval_logs",
    )
    op.drop_index(
        op.f("ix_knowledge_retrieval_logs_created_at"),
        table_name="knowledge_retrieval_logs",
    )
    op.drop_index(
        op.f("ix_knowledge_retrieval_logs_conversation_id"),
        table_name="knowledge_retrieval_logs",
    )
    op.drop_table("knowledge_retrieval_logs")

    op.drop_index(
        "ux_knowledge_chunks_document_id_chunk_index_active",
        table_name="knowledge_chunks",
    )
    op.drop_index(
        op.f("ix_knowledge_chunks_knowledge_base_id"),
        table_name="knowledge_chunks",
    )
    op.drop_index(
        op.f("ix_knowledge_chunks_document_id"),
        table_name="knowledge_chunks",
    )
    op.drop_index(
        op.f("ix_knowledge_chunks_deleted_at"),
        table_name="knowledge_chunks",
    )
    op.drop_table("knowledge_chunks")

    op.drop_index(
        op.f("ix_knowledge_documents_uploader_user_id"),
        table_name="knowledge_documents",
    )
    op.drop_index(
        op.f("ix_knowledge_documents_status"),
        table_name="knowledge_documents",
    )
    op.drop_index(
        op.f("ix_knowledge_documents_knowledge_base_id"),
        table_name="knowledge_documents",
    )
    op.drop_index(
        op.f("ix_knowledge_documents_deleted_at"),
        table_name="knowledge_documents",
    )
    op.drop_index(
        op.f("ix_knowledge_documents_created_at"),
        table_name="knowledge_documents",
    )
    op.drop_index(
        op.f("ix_knowledge_documents_content_hash"),
        table_name="knowledge_documents",
    )
    op.drop_table("knowledge_documents")

    op.drop_index(
        "ux_knowledge_bases_owner_user_id_name_active",
        table_name="knowledge_bases",
    )
    op.drop_index(
        op.f("ix_knowledge_bases_updated_at"),
        table_name="knowledge_bases",
    )
    op.drop_index(
        op.f("ix_knowledge_bases_status"),
        table_name="knowledge_bases",
    )
    op.drop_index(
        op.f("ix_knowledge_bases_owner_user_id"),
        table_name="knowledge_bases",
    )
    op.drop_index(
        op.f("ix_knowledge_bases_deleted_at"),
        table_name="knowledge_bases",
    )
    op.drop_table("knowledge_bases")
