"""Knowledge module error codes."""

from enum import IntEnum


class KnowledgeErrorCode(IntEnum):
    """Knowledge error codes."""

    KNOWLEDGE_BASE_NOT_FOUND = 5001
    DOCUMENT_NOT_FOUND = 5002
    UNSUPPORTED_DOCUMENT_FORMAT = 5003
    FILE_SIZE_EXCEEDED = 5004
    DOCUMENT_PROCESS_FAILED = 5005
    DOCUMENT_PROCESSING = 5006
    VECTOR_SEARCH_FAILED = 5007
