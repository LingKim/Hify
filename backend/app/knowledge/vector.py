"""pgvector helpers for knowledge retrieval."""

from collections.abc import Sequence

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

SAFE_IDENTIFIER_CHARS = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "_"
)


def build_vector_literal(vector: Sequence[float]) -> str:
    """Serialize numbers into pgvector's '[1,2,3]' input format."""
    return "[" + ",".join(str(float(value)) for value in vector) + "]"


def validate_identifier(identifier: str) -> str:
    """Return a trusted SQL identifier or raise for unsafe input."""
    has_unsafe_char = any(
        char not in SAFE_IDENTIFIER_CHARS
        for char in identifier
    )
    if not identifier or has_unsafe_char:
        raise ValueError(f"Unsafe SQL identifier: {identifier}")
    return identifier


def cosine_search_sql(
    table_name: str,
    embedding_column: str,
    *,
    selected_columns: Sequence[str] = ("title", "content"),
) -> TextClause:
    """Build a pgvector cosine-distance nearest-neighbor query."""
    table = validate_identifier(table_name)
    embedding = validate_identifier(embedding_column)
    columns = [
        validate_identifier(column)
        for column in selected_columns
    ]
    selected = ",\n            ".join(columns)

    return text(
        f"""
        SELECT
            {selected},
            1 - ({embedding} <=> CAST(:query_embedding AS vector)) AS similarity
        FROM {table}
        ORDER BY {embedding} <=> CAST(:query_embedding AS vector)
        LIMIT :limit
        """
    )
