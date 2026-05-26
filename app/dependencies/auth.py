"""FastAPI dependency for admin JWT authentication."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.security import decode_admin_token

_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
) -> str:
    """Validate the Bearer JWT in the ``Authorization`` header.

    Returns the admin login string on success.

    Raises:
        HTTPException 401: when the token is missing, expired, or invalid.
    """
    try:
        admin_login = decode_admin_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin_login
