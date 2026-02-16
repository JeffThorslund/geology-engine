import os
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

_bearer_scheme = HTTPBearer()


@dataclass
class SupabaseUser:
    """Decoded claims from a verified Supabase JWT."""

    id: str
    email: str | None = None
    role: str | None = None


async def get_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> SupabaseUser:
    """FastAPI dependency that verifies a Supabase access token.

    Raises 401 if the token is missing, expired, or otherwise invalid.
    """
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET is not configured",
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return SupabaseUser(
        id=payload["sub"],
        email=payload.get("email"),
        role=payload.get("role"),
    )
