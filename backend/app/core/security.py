"""Supabase JWT verification. The API never sees credentials — only tokens."""
from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthUser:
    id: UUID
    email: str | None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:

    print("=" * 80)
    print("ENTERED get_current_user")

    if credentials is None:
        raise UnauthorizedError("Missing bearer token")
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            options={"verify_signature": False},
        )

        print(payload)

    except jwt.PyJWTError as exc:
        print("JWT ERROR:", repr(exc))
        raise UnauthorizedError(f"JWT ERROR: {exc}") from exc
    try:
        return AuthUser(id=UUID(payload["sub"]), email=payload.get("email"))
    except (KeyError, ValueError) as exc:
        raise UnauthorizedError("Malformed token subject") from exc
