"""Shared FastAPI dependencies."""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import AccessTokenPayload, decode_access_token
from app.core.context import (
    RequestContext,
    bind_request_user,
    get_request_context,
)
from app.core.errors import CommonErrorCode
from app.core.exceptions import BizException

bearer_scheme = HTTPBearer(auto_error=False)


def require_request_context() -> RequestContext:
    """Return the active request context or fail fast if missing."""
    context = get_request_context()
    if context is None:
        raise BizException(
            code=CommonErrorCode.UNKNOWN_ERROR,
            message="请求上下文缺失",
            http_status=500,
        )
    return context


def _decode_credentials(
    credentials: HTTPAuthorizationCredentials | None,
) -> AccessTokenPayload | None:
    if credentials is None:
        return None
    if credentials.scheme.lower() != "bearer":
        raise BizException(
            code=CommonErrorCode.UNAUTHORIZED,
            message="未登录或登录已过期",
            http_status=401,
        )
    try:
        user = decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise BizException(
            code=CommonErrorCode.UNAUTHORIZED,
            message="未登录或登录已过期",
            http_status=401,
        ) from exc
    bind_request_user(user.sub)
    return user


def get_optional_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> AccessTokenPayload | None:
    """Decode the current user when an Authorization header is present."""
    return _decode_credentials(credentials)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> AccessTokenPayload:
    """Return the authenticated user or raise a 401 business error."""
    current_user = _decode_credentials(credentials)
    if current_user is None:
        raise BizException(
            code=CommonErrorCode.UNAUTHORIZED,
            message="未登录或登录已过期",
            http_status=401,
        )
    return current_user
