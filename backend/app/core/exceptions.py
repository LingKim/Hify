"""Application exceptions and global exception handlers."""

import logging
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import CommonErrorCode
from app.core.responses import Result

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BizException(Exception):
    """Business exception with explicit response metadata."""

    code: int
    message: str
    http_status: int = status.HTTP_400_BAD_REQUEST

    def __str__(self) -> str:
        """Return the exception message for logging."""
        return self.message


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(BizException)
    async def handle_biz_exception(
        request: Request,
        exc: BizException,
    ) -> JSONResponse:
        del request
        payload = Result[Any].failure(code=exc.code, message=exc.message)
        return JSONResponse(
            status_code=exc.http_status,
            content=payload.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        del request
        payload = Result[Any].failure(
            code=CommonErrorCode.VALIDATION_ERROR,
            message="参数校验失败",
            data={"detail": exc.errors()},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=payload.model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception: method=%s path=%s",
            request.method,
            request.url.path,
            exc_info=exc,
        )
        payload = Result[Any].failure(
            code=CommonErrorCode.UNKNOWN_ERROR,
            message="未知错误",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(),
        )
