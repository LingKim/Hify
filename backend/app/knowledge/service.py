"""Knowledge module business services."""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from fastapi import status
from sqlalchemy import func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.model import Agent, AgentKnowledgeBinding
from app.core.config import get_settings
from app.core.database import utc_now
from app.core.exceptions import BizException
from app.core.responses import PageResult
from app.knowledge.embedding import SiliconFlowEmbeddingClient
from app.knowledge.errors import KnowledgeErrorCode
from app.knowledge.model import (
    KnowledgeBase,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeRetrievalLog,
)
from app.knowledge.processor import (
    SUPPORTED_EXTENSIONS,
    content_hash,
    extract_text_from_file,
    split_text,
)
from app.knowledge.schema import (
    ConversationRetrievalResp,
    KnowledgeBaseCreateReq,
    KnowledgeBaseDetailResp,
    KnowledgeBaseListParams,
    KnowledgeBaseOptionResp,
    KnowledgeBaseSummaryResp,
    KnowledgeBaseUpdateReq,
    KnowledgeBoundAgentResp,
    KnowledgeDocumentListParams,
    KnowledgeDocumentResp,
    KnowledgeHealthResp,
    KnowledgeRetrievalPreviewResp,
    RetrievalHitResp,
    RetrievalTestReq,
    RetrievalTestResp,
)
from app.knowledge.vector import build_vector_literal

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
DEFAULT_STORAGE_DIR = (
    Path(__file__).resolve().parents[2] / "storage" / "knowledge"
)


class KnowledgeService:
    """Knowledge service with CRUD, ingestion, and retrieval operations."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        embedding_client: SiliconFlowEmbeddingClient | None = None,
        storage_dir: Path = DEFAULT_STORAGE_DIR,
    ) -> None:
        """Initialize the knowledge service."""
        self.db = db
        self.embedding_client = embedding_client
        self.storage_dir = storage_dir

    async def preview(self) -> KnowledgeRetrievalPreviewResp:
        """Return the knowledge module preview payload."""
        return KnowledgeRetrievalPreviewResp(
            module="knowledge",
            status="ready",
            capabilities=[
                "知识库管理",
                "文档切片处理",
                "检索增强查询",
            ],
        )

    async def list_knowledge_bases(
        self,
        params: KnowledgeBaseListParams,
        *,
        user_id: int,
    ) -> PageResult[KnowledgeBaseSummaryResp]:
        """Return paginated knowledge-base cards."""
        filters = self._visibility_filters(user_id)
        if params.keyword:
            keyword = f"%{params.keyword.strip()}%"
            filters.append(
                or_(
                    KnowledgeBase.name.ilike(keyword),
                    KnowledgeBase.description.ilike(keyword),
                )
            )
        if params.status is not None:
            filters.append(KnowledgeBase.status == params.status)
        else:
            filters.append(KnowledgeBase.status != "archived")
        if params.visibility is not None:
            filters.append(KnowledgeBase.visibility == params.visibility)

        total_statement = (
            select(func.count()).select_from(KnowledgeBase).where(*filters)
        )
        total = int((await self.db.execute(total_statement)).scalar_one())
        statement = (
            select(KnowledgeBase)
            .where(*filters)
            .order_by(KnowledgeBase.updated_at.desc(), KnowledgeBase.id.desc())
            .offset(params.offset)
            .limit(params.page_size)
        )
        rows = list((await self.db.scalars(statement)).all())
        return PageResult.create(
            items=[self._build_summary(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_knowledge_base(
        self,
        knowledge_base_id: int,
        *,
        user_id: int,
    ) -> KnowledgeBaseDetailResp:
        """Return one workbench detail payload."""
        knowledge_base = await self._get_knowledge_base_or_raise(
            knowledge_base_id,
            user_id=user_id,
        )
        return await self._build_detail(knowledge_base)

    async def create_knowledge_base(
        self,
        payload: KnowledgeBaseCreateReq,
        *,
        user_id: int,
    ) -> KnowledgeBaseDetailResp:
        """Create one knowledge base."""
        await self._ensure_name_unique(payload.name, user_id=user_id)
        settings = get_settings()
        knowledge_base = KnowledgeBase(
            owner_user_id=user_id,
            name=payload.name,
            description=payload.description,
            status=payload.status,
            visibility=payload.visibility,
            embedding_model=settings.embeddings_model,
            embedding_dimensions=settings.embeddings_dimensions,
            chunk_size=payload.chunk_size,
            chunk_overlap=payload.chunk_overlap,
            default_top_k=payload.default_top_k,
            default_score_threshold=payload.default_score_threshold,
            metadata_json=payload.metadata,
        )
        self.db.add(knowledge_base)
        await self.db.commit()
        await self.db.refresh(knowledge_base)
        return await self._build_detail(knowledge_base)

    async def update_knowledge_base(
        self,
        knowledge_base_id: int,
        payload: KnowledgeBaseUpdateReq,
        *,
        user_id: int,
    ) -> KnowledgeBaseDetailResp:
        """Update one knowledge base."""
        knowledge_base = await self._get_knowledge_base_or_raise(
            knowledge_base_id,
            user_id=user_id,
        )
        await self._ensure_name_unique(
            payload.name,
            user_id=user_id,
            exclude_id=knowledge_base.id,
        )
        knowledge_base.name = payload.name
        knowledge_base.description = payload.description
        knowledge_base.status = payload.status
        knowledge_base.visibility = payload.visibility
        knowledge_base.chunk_size = payload.chunk_size
        knowledge_base.chunk_overlap = payload.chunk_overlap
        knowledge_base.default_top_k = payload.default_top_k
        knowledge_base.default_score_threshold = payload.default_score_threshold
        knowledge_base.metadata_json = payload.metadata
        knowledge_base.version += 1
        await self.db.commit()
        await self.db.refresh(knowledge_base)
        return await self._build_detail(knowledge_base)

    async def delete_knowledge_base(
        self,
        knowledge_base_id: int,
        *,
        user_id: int,
    ) -> None:
        """Soft-delete one knowledge base and related rows."""
        knowledge_base = await self._get_knowledge_base_or_raise(
            knowledge_base_id,
            user_id=user_id,
        )
        now = utc_now()
        knowledge_base.deleted_at = now
        knowledge_base.status = "archived"
        knowledge_base.version += 1
        await self.db.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.knowledge_base_id == knowledge_base.id)
            .values(deleted_at=now, version=KnowledgeDocument.version + 1)
        )
        await self.db.execute(
            update(KnowledgeChunk)
            .where(KnowledgeChunk.knowledge_base_id == knowledge_base.id)
            .values(deleted_at=now, version=KnowledgeChunk.version + 1)
        )
        await self.db.execute(
            update(AgentKnowledgeBinding)
            .where(
                AgentKnowledgeBinding.knowledge_base_id == knowledge_base.id,
                AgentKnowledgeBinding.deleted_at.is_(None),
            )
            .values(
                deleted_at=now,
                is_enabled=False,
                version=AgentKnowledgeBinding.version + 1,
            )
        )
        await self.db.commit()

    async def list_options(
        self,
        *,
        user_id: int,
        keyword: str | None = None,
        status_value: str | None = "enabled",
    ) -> list[KnowledgeBaseOptionResp]:
        """Return knowledge-base options for reference fields."""
        filters = self._visibility_filters(user_id)
        if keyword:
            filters.append(KnowledgeBase.name.ilike(f"%{keyword.strip()}%"))
        if status_value:
            filters.append(KnowledgeBase.status == status_value)
        statement = (
            select(KnowledgeBase)
            .where(*filters)
            .order_by(KnowledgeBase.name.asc())
            .limit(50)
        )
        rows = list((await self.db.scalars(statement)).all())
        return [
            KnowledgeBaseOptionResp(
                id=row.id,
                name=row.name,
                status=row.status,
                documentCount=row.document_count,
                chunkCount=row.chunk_count,
            )
            for row in rows
        ]

    async def upload_document(
        self,
        knowledge_base_id: int,
        *,
        user_id: int,
        filename: str,
        content: bytes,
        mime_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocumentResp:
        """Store and process one uploaded document."""
        knowledge_base = await self._get_knowledge_base_or_raise(
            knowledge_base_id,
            user_id=user_id,
        )
        if knowledge_base.status == "archived":
            raise BizException(
                code=KnowledgeErrorCode.DOCUMENT_PROCESS_FAILED,
                message="已归档知识库不能上传文档",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        if len(content) > MAX_UPLOAD_BYTES:
            raise BizException(
                code=KnowledgeErrorCode.FILE_SIZE_EXCEEDED,
                message="文件大小超过限制",
                http_status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )
        file_ext = Path(filename).suffix.lower()
        if file_ext not in SUPPORTED_EXTENSIONS:
            raise BizException(
                code=KnowledgeErrorCode.UNSUPPORTED_DOCUMENT_FORMAT,
                message="不支持的文档格式",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        storage_path = self._write_upload_file(
            knowledge_base_id,
            filename=filename,
            content=content,
        )
        document = KnowledgeDocument(
            knowledge_base_id=knowledge_base.id,
            uploader_user_id=user_id,
            filename=filename,
            file_ext=file_ext,
            mime_type=mime_type,
            file_size_bytes=len(content),
            storage_path=str(storage_path),
            content_hash=content_hash(content),
            status="uploaded",
            process_stage="uploaded",
            metadata_json=metadata,
        )
        self.db.add(document)
        knowledge_base.document_count += 1
        knowledge_base.version += 1
        await self.db.flush()

        await self._process_document(knowledge_base, document)
        await self.db.commit()
        await self.db.refresh(document)
        return self._build_document(document)

    async def list_documents(
        self,
        knowledge_base_id: int,
        params: KnowledgeDocumentListParams,
        *,
        user_id: int,
    ) -> PageResult[KnowledgeDocumentResp]:
        """Return paginated document rows for a knowledge base."""
        await self._get_knowledge_base_or_raise(
            knowledge_base_id,
            user_id=user_id,
        )
        filters = [
            KnowledgeDocument.knowledge_base_id == knowledge_base_id,
            KnowledgeDocument.deleted_at.is_(None),
        ]
        if params.keyword:
            filters.append(
                KnowledgeDocument.filename.ilike(f"%{params.keyword.strip()}%")
            )
        if params.status is not None:
            filters.append(KnowledgeDocument.status == params.status)
        total_statement = (
            select(func.count()).select_from(KnowledgeDocument).where(*filters)
        )
        total = int((await self.db.execute(total_statement)).scalar_one())
        statement = (
            select(KnowledgeDocument)
            .where(*filters)
            .order_by(KnowledgeDocument.created_at.desc())
            .offset(params.offset)
            .limit(params.page_size)
        )
        rows = list((await self.db.scalars(statement)).all())
        return PageResult.create(
            items=[self._build_document(row) for row in rows],
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def get_document(
        self,
        knowledge_base_id: int,
        document_id: int,
        *,
        user_id: int,
    ) -> KnowledgeDocumentResp:
        """Return one document detail."""
        await self._get_knowledge_base_or_raise(
            knowledge_base_id,
            user_id=user_id,
        )
        document = await self._get_document_or_raise(
            knowledge_base_id,
            document_id,
        )
        return self._build_document(document)

    async def delete_document(
        self,
        knowledge_base_id: int,
        document_id: int,
        *,
        user_id: int,
    ) -> None:
        """Soft-delete a document and its chunks."""
        knowledge_base = await self._get_knowledge_base_or_raise(
            knowledge_base_id,
            user_id=user_id,
        )
        document = await self._get_document_or_raise(
            knowledge_base_id,
            document_id,
        )
        now = utc_now()
        document.deleted_at = now
        document.version += 1
        await self.db.execute(
            update(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document.id)
            .values(deleted_at=now, version=KnowledgeChunk.version + 1)
        )
        knowledge_base.document_count = max(
            0,
            knowledge_base.document_count - 1,
        )
        knowledge_base.chunk_count = max(
            0,
            knowledge_base.chunk_count - document.chunk_count,
        )
        knowledge_base.version += 1
        await self.db.commit()

    async def reprocess_document(
        self,
        knowledge_base_id: int,
        document_id: int,
        *,
        user_id: int,
    ) -> KnowledgeDocumentResp:
        """Reprocess an existing document."""
        knowledge_base = await self._get_knowledge_base_or_raise(
            knowledge_base_id,
            user_id=user_id,
        )
        document = await self._get_document_or_raise(
            knowledge_base_id,
            document_id,
        )
        await self._soft_delete_document_chunks(document.id)
        knowledge_base.chunk_count = max(
            0,
            knowledge_base.chunk_count - document.chunk_count,
        )
        document.chunk_count = 0
        document.token_count = 0
        await self._process_document(knowledge_base, document)
        await self.db.commit()
        await self.db.refresh(document)
        return self._build_document(document)

    async def retrieval_test(
        self,
        knowledge_base_id: int,
        payload: RetrievalTestReq,
        *,
        user_id: int,
    ) -> RetrievalTestResp:
        """Run a retrieval test against one knowledge base."""
        knowledge_base = await self._get_knowledge_base_or_raise(
            knowledge_base_id,
            user_id=user_id,
        )
        top_k = payload.top_k or knowledge_base.default_top_k
        threshold = (
            payload.score_threshold
            if payload.score_threshold is not None
            else float(knowledge_base.default_score_threshold)
        )
        started = perf_counter()
        hits = await self._retrieve_hits(
            knowledge_base.id,
            query=payload.query,
            top_k=top_k,
            score_threshold=threshold,
        )
        latency_ms = int((perf_counter() - started) * 1000)
        await self._write_retrieval_log(
            knowledge_base.id,
            user_id=user_id,
            source="test",
            query=payload.query,
            top_k=top_k,
            score_threshold=threshold,
            hits=hits,
            latency_ms=latency_ms,
        )
        await self.db.commit()
        return RetrievalTestResp(
            query=payload.query,
            topK=top_k,
            scoreThreshold=threshold,
            latencyMs=latency_ms,
            hits=hits,
        )

    async def retrieve_for_conversation(
        self,
        *,
        knowledge_base_ids: list[int],
        query: str,
        user_id: int,
        conversation_id: int | None = None,
        run_id: int | None = None,
        retrieval_configs: dict[int, dict[str, Any]] | None = None,
    ) -> ConversationRetrievalResp:
        """Retrieve context for conversation orchestration."""
        all_hits: list[RetrievalHitResp] = []
        configs = retrieval_configs or {}
        for knowledge_base_id in knowledge_base_ids:
            knowledge_base = await self._get_knowledge_base_or_raise(
                knowledge_base_id,
                user_id=user_id,
            )
            if knowledge_base.status != "enabled":
                continue
            config = configs.get(knowledge_base_id) or {}
            top_k = int(config.get("topK") or knowledge_base.default_top_k)
            threshold = float(
                config.get("scoreThreshold")
                or knowledge_base.default_score_threshold
            )
            hits = await self._retrieve_hits(
                knowledge_base_id,
                query=query,
                top_k=top_k,
                score_threshold=threshold,
            )
            await self._write_retrieval_log(
                knowledge_base_id,
                user_id=user_id,
                source="conversation",
                query=query,
                top_k=top_k,
                score_threshold=threshold,
                hits=hits,
                latency_ms=None,
                conversation_id=conversation_id,
                run_id=run_id,
            )
            all_hits.extend(hits)
        context_text = self._build_context_text(all_hits)
        return ConversationRetrievalResp(
            hits=all_hits,
            contextText=context_text,
        )

    def _visibility_filters(self, user_id: int) -> list[Any]:
        return [
            KnowledgeBase.deleted_at.is_(None),
            or_(
                KnowledgeBase.owner_user_id == user_id,
                KnowledgeBase.visibility == "workspace",
            ),
        ]

    async def _get_knowledge_base_or_raise(
        self,
        knowledge_base_id: int,
        *,
        user_id: int,
    ) -> KnowledgeBase:
        statement = select(KnowledgeBase).where(
            KnowledgeBase.id == knowledge_base_id,
            *self._visibility_filters(user_id),
        )
        knowledge_base = await self.db.scalar(statement)
        if knowledge_base is None:
            raise BizException(
                code=KnowledgeErrorCode.KNOWLEDGE_BASE_NOT_FOUND,
                message="知识库不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return knowledge_base

    async def _get_document_or_raise(
        self,
        knowledge_base_id: int,
        document_id: int,
    ) -> KnowledgeDocument:
        statement = select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.knowledge_base_id == knowledge_base_id,
            KnowledgeDocument.deleted_at.is_(None),
        )
        document = await self.db.scalar(statement)
        if document is None:
            raise BizException(
                code=KnowledgeErrorCode.DOCUMENT_NOT_FOUND,
                message="文档不存在",
                http_status=status.HTTP_404_NOT_FOUND,
            )
        return document

    async def _ensure_name_unique(
        self,
        name: str,
        *,
        user_id: int,
        exclude_id: int | None = None,
    ) -> None:
        filters = [
            KnowledgeBase.owner_user_id == user_id,
            KnowledgeBase.name == name,
            KnowledgeBase.deleted_at.is_(None),
        ]
        if exclude_id is not None:
            filters.append(KnowledgeBase.id != exclude_id)
        existing_id = await self.db.scalar(
            select(KnowledgeBase.id).where(*filters)
        )
        if existing_id is not None:
            raise BizException(
                code=KnowledgeErrorCode.DOCUMENT_PROCESS_FAILED,
                message="知识库名称已存在",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

    def _write_upload_file(
        self,
        knowledge_base_id: int,
        *,
        filename: str,
        content: bytes,
    ) -> Path:
        safe_name = Path(filename).name
        target_dir = self.storage_dir / str(knowledge_base_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / f"{content_hash(content)[:16]}-{safe_name}"
        target_path.write_bytes(content)
        return target_path

    async def _process_document(
        self,
        knowledge_base: KnowledgeBase,
        document: KnowledgeDocument,
    ) -> None:
        document.status = "processing"
        document.process_stage = "extracting"
        document.started_at = utc_now()
        document.error_code = None
        document.error_message = None
        try:
            text_content = extract_text_from_file(
                Path(document.storage_path),
                document.file_ext,
            )
            document.process_stage = "chunking"
            chunks = split_text(
                text_content,
                chunk_size=knowledge_base.chunk_size,
                overlap=knowledge_base.chunk_overlap,
            )
            document.process_stage = "embedding"
            await self._create_chunks(knowledge_base, document, chunks)
            document.status = "completed"
            document.process_stage = "indexed"
            document.chunk_count = len(chunks)
            document.token_count = sum(len(chunk) // 2 for chunk in chunks)
            document.completed_at = utc_now()
            knowledge_base.chunk_count += len(chunks)
            knowledge_base.last_indexed_at = utc_now()
        except Exception as exc:
            document.status = "failed"
            document.process_stage = "failed"
            document.error_code = "DOCUMENT_PROCESS_FAILED"
            document.error_message = str(exc)
            document.completed_at = utc_now()

    async def _create_chunks(
        self,
        knowledge_base: KnowledgeBase,
        document: KnowledgeDocument,
        chunks: list[str],
    ) -> None:
        client = self._get_embedding_client()
        for index, chunk in enumerate(chunks, start=1):
            embedding = await client.embed(chunk)
            self.db.add(
                KnowledgeChunk(
                    knowledge_base_id=knowledge_base.id,
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk,
                    content_hash=content_hash(chunk),
                    token_count=len(chunk) // 2,
                    embedding=build_vector_literal(embedding),
                    embedding_model=knowledge_base.embedding_model,
                )
            )

    async def _soft_delete_document_chunks(self, document_id: int) -> None:
        await self.db.execute(
            update(KnowledgeChunk)
            .where(
                KnowledgeChunk.document_id == document_id,
                KnowledgeChunk.deleted_at.is_(None),
            )
            .values(deleted_at=utc_now(), version=KnowledgeChunk.version + 1)
        )

    async def _retrieve_hits(
        self,
        knowledge_base_id: int,
        *,
        query: str,
        top_k: int,
        score_threshold: float,
    ) -> list[RetrievalHitResp]:
        embedding = await self._get_embedding_client().embed(query)
        vector_literal = build_vector_literal(embedding)
        statement = text(
            """
            SELECT
                kc.id AS chunk_id,
                kd.id AS document_id,
                kd.filename AS document_name,
                kc.content AS content,
                1 - (kc.embedding <=> CAST(:query_embedding AS public.vector))
                    AS score,
                kc.page_number AS page_number,
                kc.section_title AS section_title
            FROM knowledge_chunks kc
            JOIN knowledge_documents kd ON kd.id = kc.document_id
            WHERE kc.knowledge_base_id = :knowledge_base_id
              AND kc.deleted_at IS NULL
              AND kd.deleted_at IS NULL
              AND kd.status = 'completed'
              AND 1 - (kc.embedding <=> CAST(:query_embedding AS public.vector))
                  >= :score_threshold
            ORDER BY kc.embedding <=> CAST(:query_embedding AS public.vector)
            LIMIT :top_k
            """
        )
        try:
            result = await self.db.execute(
                statement,
                {
                    "knowledge_base_id": knowledge_base_id,
                    "query_embedding": vector_literal,
                    "score_threshold": score_threshold,
                    "top_k": top_k,
                },
            )
        except Exception as exc:
            raise BizException(
                code=KnowledgeErrorCode.VECTOR_SEARCH_FAILED,
                message="向量检索失败",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from exc
        return [
            RetrievalHitResp(
                chunkId=row.chunk_id,
                documentId=row.document_id,
                documentName=row.document_name,
                content=row.content,
                score=float(row.score),
                pageNumber=row.page_number,
                sectionTitle=row.section_title,
            )
            for row in result
        ]

    async def _write_retrieval_log(
        self,
        knowledge_base_id: int,
        *,
        user_id: int,
        source: str,
        query: str,
        top_k: int,
        score_threshold: float,
        hits: list[RetrievalHitResp],
        latency_ms: int | None,
        conversation_id: int | None = None,
        run_id: int | None = None,
    ) -> None:
        self.db.add(
            KnowledgeRetrievalLog(
                knowledge_base_id=knowledge_base_id,
                conversation_id=conversation_id,
                run_id=run_id,
                user_id=user_id,
                source=source,
                query_text=query,
                top_k=top_k,
                score_threshold=score_threshold,
                hit_count=len(hits),
                latency_ms=latency_ms,
                hits_json=[
                    hit.model_dump(by_alias=True, exclude={"content"})
                    for hit in hits
                ],
            )
        )

    def _get_embedding_client(self) -> SiliconFlowEmbeddingClient:
        if self.embedding_client is not None:
            return self.embedding_client
        settings = get_settings()
        if not settings.embeddings_secret_key:
            raise BizException(
                code=KnowledgeErrorCode.DOCUMENT_PROCESS_FAILED,
                message="Embedding 配置缺失",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        self.embedding_client = SiliconFlowEmbeddingClient(
            api_key=settings.embeddings_secret_key,
            base_url=settings.embeddings_base_url,
            model=settings.embeddings_model,
            dimensions=settings.embeddings_dimensions,
        )
        return self.embedding_client

    async def _build_detail(
        self,
        knowledge_base: KnowledgeBase,
    ) -> KnowledgeBaseDetailResp:
        processing_count = await self._count_documents(
            knowledge_base.id,
            status_value="processing",
        )
        failed_count = await self._count_documents(
            knowledge_base.id,
            status_value="failed",
        )
        return KnowledgeBaseDetailResp(
            **self._build_summary(knowledge_base).model_dump(by_alias=True),
            embeddingModel=knowledge_base.embedding_model,
            embeddingDimensions=knowledge_base.embedding_dimensions,
            chunkSize=knowledge_base.chunk_size,
            chunkOverlap=knowledge_base.chunk_overlap,
            defaultTopK=knowledge_base.default_top_k,
            defaultScoreThreshold=float(
                knowledge_base.default_score_threshold,
            ),
            processingDocumentCount=processing_count,
            failedDocumentCount=failed_count,
            health=self._build_health(knowledge_base, failed_count),
            boundAgents=await self._load_bound_agents(knowledge_base.id),
            metadata=knowledge_base.metadata_json,
        )

    def _build_summary(
        self,
        knowledge_base: KnowledgeBase,
    ) -> KnowledgeBaseSummaryResp:
        return KnowledgeBaseSummaryResp(
            id=knowledge_base.id,
            name=knowledge_base.name,
            description=knowledge_base.description,
            status=knowledge_base.status,
            visibility=knowledge_base.visibility,
            documentCount=knowledge_base.document_count,
            chunkCount=knowledge_base.chunk_count,
            lastIndexedAt=knowledge_base.last_indexed_at,
            createdAt=knowledge_base.created_at,
            updatedAt=knowledge_base.updated_at,
        )

    def _build_document(
        self,
        document: KnowledgeDocument,
    ) -> KnowledgeDocumentResp:
        return KnowledgeDocumentResp(
            id=document.id,
            knowledgeBaseId=document.knowledge_base_id,
            filename=document.filename,
            fileExt=document.file_ext,
            mimeType=document.mime_type,
            fileSizeBytes=document.file_size_bytes,
            status=document.status,
            processStage=document.process_stage,
            chunkCount=document.chunk_count,
            tokenCount=document.token_count,
            errorCode=document.error_code,
            errorMessage=document.error_message,
            startedAt=document.started_at,
            completedAt=document.completed_at,
            createdAt=document.created_at,
            updatedAt=document.updated_at,
            metadata=document.metadata_json,
        )

    def _build_health(
        self,
        knowledge_base: KnowledgeBase,
        failed_count: int,
    ) -> KnowledgeHealthResp:
        if knowledge_base.document_count == 0:
            return KnowledgeHealthResp(
                score=0,
                label="待上传",
                suggestion="上传文档后再进行检索测试",
            )
        failed_ratio = failed_count / max(knowledge_base.document_count, 1)
        score = max(0, int(100 - failed_ratio * 40))
        return KnowledgeHealthResp(
            score=score,
            label="健康" if score >= 70 else "需关注",
            suggestion=None if score >= 70 else "请处理失败文档后再绑定 Agent",
        )

    async def _count_documents(
        self,
        knowledge_base_id: int,
        *,
        status_value: str,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(KnowledgeDocument)
            .where(
                KnowledgeDocument.knowledge_base_id == knowledge_base_id,
                KnowledgeDocument.status == status_value,
                KnowledgeDocument.deleted_at.is_(None),
            )
        )
        return int((await self.db.execute(statement)).scalar_one())

    async def _load_bound_agents(
        self,
        knowledge_base_id: int,
    ) -> list[KnowledgeBoundAgentResp]:
        statement = (
            select(Agent, AgentKnowledgeBinding)
            .join(
                AgentKnowledgeBinding,
                AgentKnowledgeBinding.agent_id == Agent.id,
            )
            .where(
                AgentKnowledgeBinding.knowledge_base_id == knowledge_base_id,
                AgentKnowledgeBinding.deleted_at.is_(None),
                Agent.deleted_at.is_(None),
            )
            .order_by(Agent.name.asc())
        )
        rows = list((await self.db.execute(statement)).all())
        return [
            KnowledgeBoundAgentResp(
                agentId=agent.id,
                agentName=agent.name,
                isEnabled=binding.is_enabled,
                topK=(binding.retrieval_config_json or {}).get("topK"),
                scoreThreshold=(binding.retrieval_config_json or {}).get(
                    "scoreThreshold",
                ),
            )
            for agent, binding in rows
        ]

    def _build_context_text(self, hits: list[RetrievalHitResp]) -> str:
        if not hits:
            return ""
        parts = []
        for hit in hits:
            location = f"第 {hit.page_number} 页" if hit.page_number else "片段"
            parts.append(
                f"【{hit.document_name} / {location}】\n{hit.content}"
            )
        return "\n\n".join(parts)
