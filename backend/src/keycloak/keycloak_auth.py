"""Keycloak (OIDC) authentication for FastAPI.

This module validates Bearer access tokens issued by Keycloak and exposes a FastAPI dependency
that returns a normalised "principal" object for request handlers.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient


@dataclass(frozen=True)
class KeycloakPrincipal:
    """Authenticated identity extracted from a Keycloak access token."""

    sub: str
    email: str | None
    preferred_username: str | None
    roles: list[str]
    claims: dict[str, Any]


def _required_env(name: str) -> str:
    """Read a required env var.

    Args:
        name: The environment variable name.

    Returns:
        The non-empty environment variable value.

    Raises:
        RuntimeError: If the variable is missing or empty.
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


KEYCLOAK_BASE_URL = _required_env("KEYCLOAK_BASE_URL")
KEYCLOAK_REALM = _required_env("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_ID = _required_env("KEYCLOAK_CLIENT_ID")
# Optional: frontend client ID whose tokens the backend should also accept
KEYCLOAK_FRONTEND_CLIENT_ID = os.environ.get("KEYCLOAK_FRONTEND_CLIENT_ID")

# Build a set of allowed client IDs for token validation
_ALLOWED_CLIENTS: set[str] = {KEYCLOAK_CLIENT_ID}
if KEYCLOAK_FRONTEND_CLIENT_ID:
    _ALLOWED_CLIENTS.add(KEYCLOAK_FRONTEND_CLIENT_ID)

ISSUER = f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}"
JWKS_URL = f"{ISSUER}/protocol/openid-connect/certs"
_ALGORITHMS = ["RS256"]

_bearer = HTTPBearer(auto_error=False)
_jwks_client = PyJWKClient(JWKS_URL)


def _verify_and_decode(token: str) -> dict[str, Any]:
    """Verify a JWT using Keycloak JWKS and return decoded claims.

    We verify:
    - Signature (RS256)
    - Expiry (exp)
    - Issuer (iss)

    We then enforce that the token is intended for this service using `aud` and/or `azp`.
    Keycloak frequently uses:
    - `azp` (authorised party): the client that requested the token
    - `aud` (audience): may require an Audience mapper to include an API client id

    Args:
        token: Raw JWT access token.

    Returns:
        Decoded JWT claims.

    Raises:
        HTTPException: If token is invalid/expired/not intended for this service.
    """
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token).key
        claims: dict[str, Any] = jwt.decode(
            token,
            signing_key,
            algorithms=_ALGORITHMS,
            issuer=ISSUER,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": False,  # handled manually below
            },
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    aud = claims.get("aud")
    aud_list: list[str] = []
    if isinstance(aud, list):
        aud_list = [str(a) for a in aud]
    elif isinstance(aud, str):
        aud_list = [aud]

    azp = claims.get("azp")
    # Check if token is for an allowed client (either via aud or azp)
    aud_matches = bool(_ALLOWED_CLIENTS & set(aud_list))
    azp_matches = azp in _ALLOWED_CLIENTS
    if not aud_matches and not azp_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not issued for this client",
        )

    return claims


def get_current_principal(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> KeycloakPrincipal:
    """FastAPI dependency that authenticates the request via Keycloak access token.

    Args:
        creds: Parsed HTTP Bearer credentials.

    Returns:
        KeycloakPrincipal extracted from the token.

    Raises:
        HTTPException: If the token is missing/invalid.
    """
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    claims = _verify_and_decode(creds.credentials)

    realm_roles = claims.get("realm_access", {}).get("roles", [])
    roles = realm_roles if isinstance(realm_roles, list) else []

    sub = claims.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    return KeycloakPrincipal(
        sub=str(sub),
        email=claims.get("email"),
        preferred_username=claims.get("preferred_username"),
        roles=[str(r) for r in roles],
        claims=claims,
    )
