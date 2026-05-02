"""JWT helpers shared by authentication dependencies."""

from datetime import UTC, datetime, timedelta

import jwt
from pydantic import BaseModel

from app.core.config import get_settings


class AccessTokenPayload(BaseModel):
    """Authenticated user claims carried in access tokens."""

    sub: str
    username: str
    role: str
    iss: str | None = None
    iat: int | None = None
    exp: int | None = None


def create_access_token(
    payload: AccessTokenPayload,
    *,
    expires_in_seconds: int | None = None,
) -> str:
    """Sign a JWT access token for the given authenticated user."""
    settings = get_settings()
    issued_at = datetime.now(tz=UTC)
    ttl_seconds = expires_in_seconds or settings.jwt_access_token_ttl_seconds
    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    claims = payload.model_dump(exclude={"iss", "iat", "exp"})
    claims.update(
        {
            "iss": settings.jwt_issuer,
            "iat": int(issued_at.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
    )
    return jwt.encode(
        claims,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> AccessTokenPayload:
    """Decode and validate a JWT access token."""
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
    )
    return AccessTokenPayload.model_validate(payload)
