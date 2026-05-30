"""JWT creation and verification utilities for admin authentication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings

_ALGORITHM = settings.jwt_algorithm


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_admin_access_token() -> str:
    """Return a signed JWT that is valid for ``jwt_access_token_expire_hours`` hours."""
    expire = _utcnow() + timedelta(hours=settings.jwt_access_token_expire_hours)
    payload: dict[str, object] = {
        "sub": settings.admin_login,
        "type": "admin_access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def create_user_access_token(phone: str) -> str:
    expire = _utcnow() + timedelta(days=30)
    payload: dict[str, object] = {"sub": phone, "type": "user_access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_user_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
    if payload.get("type") != "user_access":
        raise JWTError("Invalid token type")
    sub: str | None = payload.get("sub")
    if sub is None:
        raise JWTError("Token missing subject")
    return sub


def decode_admin_token(token: str) -> str:
    """Decode and validate an admin JWT.

    Returns the ``sub`` claim (admin login) on success.

    Raises:
        JWTError: when the token is invalid, expired, or has an unexpected type.
    """
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
    if payload.get("type") != "admin_access":
        raise JWTError("Invalid token type")
    sub: str | None = payload.get("sub")
    if sub is None:
        raise JWTError("Token missing subject")
    return sub
