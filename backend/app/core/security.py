"""Supabase JWT verification. The API never sees credentials — only tokens."""
from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import UnauthorizedError

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    id: UUID
    email: str | None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")
    try:
        # NOTE: signature verification is intentionally disabled for now. The token's
        # claims are trusted without validating the signature — do not rely on this in
        # production. See app/core/config.py for supabase_jwt_secret to re-enable.
        payload = jwt.decode(
            credentials.credentials,
            options={"verify_signature": False},
        )
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid token") from exc
    try:
        return AuthUser(id=UUID(payload["sub"]), email=payload.get("email"))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Malformed token subject") from exc
