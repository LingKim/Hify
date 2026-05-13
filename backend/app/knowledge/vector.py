"""pgvector helpers for knowledge retrieval."""

from collections.abc import Sequence

from sqlalchemy import cast, text
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.types import UserDefinedType

SAFE_IDENTIFIER_CHARS = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "_"
)


class PgVector(UserDefinedType):
    """SQLAlchemy binding for pgvector values stored as vector literals."""

    cache_ok = True

    def get_col_spec(self, **kwargs: object) -> str:
        del kwargs
        return "public.vector"

    def bind_expression(self, bindvalue: object) -> object:
        return cast(bindvalue, self)


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
    distance = f"{embedding} <=> CAST(:query_embedding AS public.vector)"

    return text(
        f"""
        SELECT
            {selected},
            1 - ({distance}) AS similarity
        FROM {table}
        ORDER BY {distance}
        LIMIT :limit
        """
    )
