"""Supabase JWT verification (brief Stage 2: user accounts).

The browser authenticates against Supabase Auth and sends the resulting access
token as ``Authorization: Bearer <jwt>``. This module verifies that token and
exposes the caller's identity as a FastAPI dependency. Every ``/api/analyses``
route depends on ``get_current_user`` so data is always scoped to one user.

Verification handles both Supabase signing schemes:
- **HS256** (the legacy/default shared "JWT Secret") — verified locally.
- **Asymmetric** (ES256/RS256 "signing keys") — verified against the project's
  JWKS endpoint, fetched and cached by ``PyJWKClient``.

Tests override this dependency (see ``tests/test_api.py``) so the suite needs no
Supabase project.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Header, HTTPException
from jwt import PyJWKClient

from .config import SUPABASE_JWT_SECRET, SUPABASE_URL

# Supabase stamps user access tokens with this audience.
_AUDIENCE = "authenticated"


@dataclass(frozen=True)
class CurrentUser:
    id: str  # Supabase user UUID (the JWT "sub" claim)
    email: str


_jwks_client: PyJWKClient | None = None


def _jwks() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json")
    return _jwks_client


def _decode(token: str) -> dict:
    """Verify ``token`` and return its claims, picking the scheme by header alg."""
    alg = jwt.get_unverified_header(token).get("alg", "")
    if alg == "HS256":
        if not SUPABASE_JWT_SECRET:
            raise HTTPException(status_code=500, detail="Auth not configured (SUPABASE_JWT_SECRET)")
        return jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience=_AUDIENCE)
    # Asymmetric signing keys → verify against the project JWKS.
    if not SUPABASE_URL:
        raise HTTPException(status_code=500, detail="Auth not configured (SUPABASE_URL)")
    key = _jwks().get_signing_key_from_jwt(token).key
    return jwt.decode(token, key, algorithms=["ES256", "RS256"], audience=_AUDIENCE)


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = _decode(token)
    except HTTPException:
        raise
    except Exception as e:  # signature/expiry/audience failures
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e

    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing subject")
    return CurrentUser(id=sub, email=claims.get("email", ""))
