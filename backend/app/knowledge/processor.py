"""Document processing helpers for knowledge ingestion."""

from __future__ import annotations

from hashlib import sha256
from html import unescape
from pathlib import Path
from re import sub
from zipfile import ZipFile

SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx", ".pdf"}


def content_hash(content: bytes | str) -> str:
    """Return a stable SHA-256 hash for document or chunk content."""
    raw = content.encode("utf-8") if isinstance(content, str) else content
    return sha256(raw).hexdigest()


def normalize_text(text: str) -> str:
    """Collapse noisy whitespace while preserving paragraph boundaries."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = sub(r"[ \t]+", " ", normalized)
    normalized = sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def split_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks."""
    normalized = normalize_text(text)
    if not normalized:
        return []
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = end - overlap
    return chunks


def extract_text_from_file(path: Path, file_ext: str) -> str:
    """Extract plain text from one supported file."""
    normalized_ext = file_ext.lower()
    if normalized_ext in {".txt", ".md"}:
        return normalize_text(path.read_text(encoding="utf-8", errors="ignore"))
    if normalized_ext == ".docx":
        return extract_docx_text(path)
    if normalized_ext == ".pdf":
        raise ValueError("当前 PDF 仅支持可解析文本版本，解析器尚未启用")
    raise ValueError(f"不支持的文档格式: {file_ext}")


def extract_docx_text(path: Path) -> str:
    """Extract text from a docx file using the zipped XML payload."""
    with ZipFile(path) as archive:
        raw = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    raw = sub(r"</w:p>", "\n", raw)
    raw = sub(r"<[^>]+>", "", raw)
    return normalize_text(unescape(raw))
