"""Knowledge module routes."""

from __future__ import annotations

from json import loads
from typing import Any

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile

from app.auth.deps import get_current_active_user
from app.auth.model import User
from app.core.database import get_db_session
from app.core.responses import PageResult, Result
from app.knowledge.schema import (
    KnowledgeBaseCreateReq,
    KnowledgeBaseDetailResp,
    KnowledgeBaseListParams,
    KnowledgeBaseOptionResp,
    KnowledgeBaseSummaryResp,
    KnowledgeBaseUpdateReq,
    KnowledgeDocumentListParams,
    KnowledgeDocumentResp,
    KnowledgeRetrievalPreviewResp,
    RetrievalTestReq,
    RetrievalTestResp,
)
from app.knowledge.service import KnowledgeService

router = APIRouter(prefix="/api/v1/knowledge-bases", tags=["knowledge"])


@router.get(
    "/retrieval-preview",
    response_model=Result[KnowledgeRetrievalPreviewResp],
)
async def retrieval_preview(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[KnowledgeRetrievalPreviewResp]:
    """Return the knowledge module preview endpoint response."""
    del current_user
    service = KnowledgeService(db)
    return Result.success(data=await service.preview())


@router.get("", response_model=Result[PageResult[KnowledgeBaseSummaryResp]])
async def list_knowledge_bases(
    params: KnowledgeBaseListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[PageResult[KnowledgeBaseSummaryResp]]:
    """Return visible knowledge bases."""
    service = KnowledgeService(db)
    return Result.success(
        data=await service.list_knowledge_bases(
            params,
            user_id=current_user.id,
        )
    )


@router.get(
    "/options",
    response_model=Result[list[KnowledgeBaseOptionResp]],
)
async def list_knowledge_base_options(
    keyword: str | None = None,
    status_value: str | None = "enabled",
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[list[KnowledgeBaseOptionResp]]:
    """Return knowledge-base options for forms."""
    service = KnowledgeService(db)
    return Result.success(
        data=await service.list_options(
            user_id=current_user.id,
            keyword=keyword,
            status_value=status_value,
        )
    )


@router.post(
    "",
    response_model=Result[KnowledgeBaseDetailResp],
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_base(
    payload: KnowledgeBaseCreateReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[KnowledgeBaseDetailResp]:
    """Create one knowledge base."""
    service = KnowledgeService(db)
    data = await service.create_knowledge_base(
        payload,
        user_id=current_user.id,
    )
    return Result.success(data=data, code=status.HTTP_201_CREATED)


@router.get(
    "/{knowledge_base_id}",
    response_model=Result[KnowledgeBaseDetailResp],
)
async def get_knowledge_base(
    knowledge_base_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[KnowledgeBaseDetailResp]:
    """Return one knowledge-base workbench detail."""
    service = KnowledgeService(db)
    return Result.success(
        data=await service.get_knowledge_base(
            knowledge_base_id,
            user_id=current_user.id,
        )
    )


@router.patch(
    "/{knowledge_base_id}",
    response_model=Result[KnowledgeBaseDetailResp],
)
async def update_knowledge_base(
    knowledge_base_id: int,
    payload: KnowledgeBaseUpdateReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[KnowledgeBaseDetailResp]:
    """Update one knowledge base."""
    service = KnowledgeService(db)
    return Result.success(
        data=await service.update_knowledge_base(
            knowledge_base_id,
            payload,
            user_id=current_user.id,
        )
    )


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    knowledge_base_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Soft-delete one knowledge base."""
    service = KnowledgeService(db)
    await service.delete_knowledge_base(
        knowledge_base_id,
        user_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{knowledge_base_id}/documents",
    response_model=Result[KnowledgeDocumentResp],
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    knowledge_base_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[KnowledgeDocumentResp]:
    """Upload and process one document."""
    form = await request.form()
    file = form.get("file")
    if not isinstance(file, UploadFile):
        raise ValueError("缺少上传文件")
    metadata = parse_metadata(form.get("metadata"))
    content = await file.read()
    service = KnowledgeService(db)
    data = await service.upload_document(
        knowledge_base_id,
        user_id=current_user.id,
        filename=file.filename or "untitled",
        content=content,
        mime_type=file.content_type,
        metadata=metadata,
    )
    return Result.success(data=data, code=status.HTTP_201_CREATED)


@router.get(
    "/{knowledge_base_id}/documents",
    response_model=Result[PageResult[KnowledgeDocumentResp]],
)
async def list_documents(
    knowledge_base_id: int,
    params: KnowledgeDocumentListParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[PageResult[KnowledgeDocumentResp]]:
    """Return documents under one knowledge base."""
    service = KnowledgeService(db)
    return Result.success(
        data=await service.list_documents(
            knowledge_base_id,
            params,
            user_id=current_user.id,
        )
    )


@router.get(
    "/{knowledge_base_id}/documents/{document_id}",
    response_model=Result[KnowledgeDocumentResp],
)
async def get_document(
    knowledge_base_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[KnowledgeDocumentResp]:
    """Return one document detail."""
    service = KnowledgeService(db)
    return Result.success(
        data=await service.get_document(
            knowledge_base_id,
            document_id,
            user_id=current_user.id,
        )
    )


@router.delete(
    "/{knowledge_base_id}/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    knowledge_base_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """Soft-delete one document."""
    service = KnowledgeService(db)
    await service.delete_document(
        knowledge_base_id,
        document_id,
        user_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{knowledge_base_id}/documents/{document_id}/reprocess",
    response_model=Result[KnowledgeDocumentResp],
)
async def reprocess_document(
    knowledge_base_id: int,
    document_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[KnowledgeDocumentResp]:
    """Reprocess one document."""
    service = KnowledgeService(db)
    return Result.success(
        data=await service.reprocess_document(
            knowledge_base_id,
            document_id,
            user_id=current_user.id,
        )
    )


@router.post(
    "/{knowledge_base_id}/retrieval-test",
    response_model=Result[RetrievalTestResp],
)
async def retrieval_test(
    knowledge_base_id: int,
    payload: RetrievalTestReq,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user),
) -> Result[RetrievalTestResp]:
    """Run a retrieval test for one knowledge base."""
    service = KnowledgeService(db)
    return Result.success(
        data=await service.retrieval_test(
            knowledge_base_id,
            payload,
            user_id=current_user.id,
        )
    )


def parse_metadata(raw_metadata: Any) -> dict[str, Any] | None:
    """Parse optional multipart metadata."""
    if raw_metadata is None or raw_metadata == "":
        return None
    if isinstance(raw_metadata, str):
        parsed = loads(raw_metadata)
        return parsed if isinstance(parsed, dict) else None
    return None
