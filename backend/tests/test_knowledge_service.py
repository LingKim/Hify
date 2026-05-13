import pytest
from pydantic import ValidationError

from app.knowledge.processor import split_text
from app.knowledge.schema import KnowledgeBaseCreateReq


def test_split_text_keeps_overlap_between_chunks() -> None:
    chunks = split_text("abcdefghijklmnopqrstuvwxyz", chunk_size=10, overlap=3)

    assert chunks == [
        "abcdefghij",
        "hijklmnopq",
        "opqrstuvwx",
        "vwxyz",
    ]


def test_knowledge_base_create_requires_overlap_less_than_chunk_size() -> None:
    with pytest.raises(ValidationError) as exc_info:
        KnowledgeBaseCreateReq(
            name="产品资料库",
            chunkSize=100,
            chunkOverlap=100,
        )

    assert "切片重叠长度必须小于切片长度" in str(exc_info.value)
