"""Tests for Keycloak authentication module."""

from typing import Any
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from src.keycloak.keycloak_auth import (
    _required_env,
    _verify_and_decode,
    get_current_principal,
)


class TestRequiredEnv:
    """Tests for the _required_env helper function."""

    def test_raises_runtime_error_when_env_var_is_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that RuntimeError is raised when env var is not set."""
        monkeypatch.delenv("MISSING_VAR", raising=False)

        with pytest.raises(RuntimeError, match="MISSING_VAR is not set"):
            _required_env("MISSING_VAR")


class TestVerifyAndDecode:
    """Tests for the _verify_and_decode function."""

    @pytest.fixture
    def mock_jwks_client(self) -> MagicMock:
        """Create a mock JWKS client."""
        mock_key = MagicMock()
        mock_key.key = "mock-signing-key"
        mock_client = MagicMock()
        mock_client.get_signing_key_from_jwt.return_value = mock_key
        return mock_client

    @pytest.fixture
    def valid_claims(self) -> dict[str, Any]:
        """Create valid token claims."""
        return {
            "sub": "user-123",
            "email": "user@example.com",
            "azp": "dish-booking-agent-api",
            "realm_access": {"roles": ["user"]},
        }

    def test_decodes_valid_token(
        self, mock_jwks_client: MagicMock, valid_claims: dict[str, Any]
    ) -> None:
        """Test successful token decode when azp matches allowed client."""
        with (
            patch("src.keycloak.keycloak_auth._jwks_client", mock_jwks_client),
            patch("src.keycloak.keycloak_auth.jwt.decode", return_value=valid_claims),
        ):
            result = _verify_and_decode("valid-token")

        assert result == valid_claims

    def test_raises_401_for_invalid_jwt(self, mock_jwks_client: MagicMock) -> None:
        """Test that HTTPException 401 is raised for invalid JWT."""
        with (
            patch("src.keycloak.keycloak_auth._jwks_client", mock_jwks_client),
            patch(
                "src.keycloak.keycloak_auth.jwt.decode",
                side_effect=jwt.PyJWTError("Invalid token"),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            _verify_and_decode("invalid-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid or expired token"

    def test_raises_401_for_expired_token(self, mock_jwks_client: MagicMock) -> None:
        """Test that HTTPException 401 is raised for expired token."""
        with (
            patch("src.keycloak.keycloak_auth._jwks_client", mock_jwks_client),
            patch(
                "src.keycloak.keycloak_auth.jwt.decode",
                side_effect=jwt.ExpiredSignatureError("Token expired"),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            _verify_and_decode("expired-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_raises_401_when_token_not_for_this_client(self, mock_jwks_client: MagicMock) -> None:
        """Test that HTTPException 401 is raised when token is not for this client."""
        claims_wrong_client = {
            "sub": "user-123",
            "azp": "other-client",
            "aud": ["account", "another-service"],
        }

        with (
            patch("src.keycloak.keycloak_auth._jwks_client", mock_jwks_client),
            patch("src.keycloak.keycloak_auth.jwt.decode", return_value=claims_wrong_client),
            pytest.raises(HTTPException) as exc_info,
        ):
            _verify_and_decode("wrong-client-token")

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Token not issued for this client"


class TestGetCurrentPrincipal:
    """Tests for the get_current_principal FastAPI dependency."""

    @pytest.fixture
    def mock_jwks_client(self) -> MagicMock:
        """Create a mock JWKS client."""
        mock_key = MagicMock()
        mock_key.key = "mock-signing-key"
        mock_client = MagicMock()
        mock_client.get_signing_key_from_jwt.return_value = mock_key
        return mock_client

    @pytest.fixture
    def valid_claims(self) -> dict[str, Any]:
        """Create valid token claims with all fields."""
        return {
            "sub": "user-123",
            "email": "user@example.com",
            "preferred_username": "testuser",
            "azp": "dish-booking-agent-api",
            "realm_access": {"roles": ["admin", "user"]},
        }

    @pytest.fixture
    def bearer_credentials(self) -> HTTPAuthorizationCredentials:
        """Create valid bearer credentials."""
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid-token")

    def test_returns_principal_for_valid_token(
        self,
        mock_jwks_client: MagicMock,
        valid_claims: dict[str, Any],
        bearer_credentials: HTTPAuthorizationCredentials,
    ) -> None:
        """Test that a valid token returns a properly populated KeycloakPrincipal."""
        with (
            patch("src.keycloak.keycloak_auth._jwks_client", mock_jwks_client),
            patch("src.keycloak.keycloak_auth.jwt.decode", return_value=valid_claims),
        ):
            principal = get_current_principal(bearer_credentials)

        assert principal.sub == "user-123"
        assert principal.email == "user@example.com"
        assert principal.preferred_username == "testuser"
        assert principal.roles == ["admin", "user"]

    def test_returns_empty_roles_when_realm_access_missing(
        self,
        mock_jwks_client: MagicMock,
        bearer_credentials: HTTPAuthorizationCredentials,
    ) -> None:
        """Test that missing realm_access results in empty roles list."""
        claims_no_realm_access = {
            "sub": "user-123",
            "azp": "dish-booking-agent-api",
        }

        with (
            patch("src.keycloak.keycloak_auth._jwks_client", mock_jwks_client),
            patch("src.keycloak.keycloak_auth.jwt.decode", return_value=claims_no_realm_access),
        ):
            principal = get_current_principal(bearer_credentials)

        assert principal.roles == []

    def test_raises_401_when_no_credentials(self) -> None:
        """Test that HTTPException 401 is raised when no credentials provided."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_principal(None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Missing bearer token"

    def test_raises_401_when_scheme_not_bearer(self) -> None:
        """Test that HTTPException 401 is raised for non-bearer auth scheme."""
        basic_creds = HTTPAuthorizationCredentials(scheme="Basic", credentials="user:pass")

        with pytest.raises(HTTPException) as exc_info:
            get_current_principal(basic_creds)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_raises_401_when_token_has_no_subject(
        self,
        mock_jwks_client: MagicMock,
        bearer_credentials: HTTPAuthorizationCredentials,
    ) -> None:
        """Test that HTTPException 401 is raised when token has no sub claim."""
        claims_no_sub = {
            "azp": "dish-booking-agent-api",
            "email": "user@example.com",
        }

        with (
            patch("src.keycloak.keycloak_auth._jwks_client", mock_jwks_client),
            patch("src.keycloak.keycloak_auth.jwt.decode", return_value=claims_no_sub),
            pytest.raises(HTTPException) as exc_info,
        ):
            get_current_principal(bearer_credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Token missing subject"
