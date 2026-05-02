"""Unified API response models."""

from math import ceil
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class Result[T](BaseModel):
    """Standard API response envelope."""

    code: int
    message: str
    data: T | None = None

    @classmethod
    def success(
        cls,
        data: T | None = None,
        message: str = "success",
        code: int = 200,
    ) -> "Result[T]":
        """Create a success response."""
        return cls(code=code, message=message, data=data)

    @classmethod
    def failure(
        cls,
        code: int,
        message: str,
        data: T | None = None,
    ) -> "Result[T]":
        """Create a failure response."""
        return cls(code=code, message=message, data=data)


class PageResult[T](BaseModel):
    """Paginated response payload."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    items: list[T] = Field(alias="list")
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PageResult[T]":
        """Create a paginated payload with computed total pages."""
        total_pages = ceil(total / page_size) if total > 0 else 0
        return cls(
            list=items,
            total=total,
            page=page,
            pageSize=page_size,
            totalPages=total_pages,
        )


class PageParams(BaseModel):
    """Standard pagination parameters for list endpoints."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, alias="pageSize", ge=1, le=100)

    @property
    def offset(self) -> int:
        """Return the SQL offset for the current pagination window."""
        return (self.page - 1) * self.page_size
