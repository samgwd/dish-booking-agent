"""Google OAuth flow for Calendar integration."""

import json
import os
from datetime import datetime, timezone

from fastapi import HTTPException
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_credentials_path() -> str:
    """Get the path to Google OAuth credentials file.

    Returns:
        Path to the credentials JSON file.

    Raises:
        RuntimeError: If GOOGLE_OAUTH_CREDENTIALS is not set.
    """
    credentials_path = os.environ.get("GOOGLE_OAUTH_CREDENTIALS")
    if not credentials_path:
        raise RuntimeError("GOOGLE_OAUTH_CREDENTIALS environment variable not set")
    return credentials_path


def _get_redirect_uri() -> str:
    """Get the OAuth redirect URI.

    Returns:
        The redirect URI for OAuth callbacks.
    """
    return os.environ.get(
        "GOOGLE_OAUTH_REDIRECT_URI",
        "http://localhost:3000/auth/google/callback",
    )


def get_oauth_flow() -> Flow:
    """Create and return a Google OAuth flow instance.

    Returns:
        Configured OAuth flow.

    Raises:
        RuntimeError: If GOOGLE_OAUTH_CREDENTIALS is not set.
    """
    credentials_path = _get_credentials_path()

    flow = Flow.from_client_secrets_file(
        credentials_path,
        scopes=SCOPES,
        redirect_uri=_get_redirect_uri(),
    )
    return flow


def get_authorization_url(state: str) -> str:
    """Generate Google OAuth authorization URL.

    Args:
        state: State parameter for CSRF protection (typically user ID).

    Returns:
        Authorization URL.
    """
    flow = get_oauth_flow()
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
        prompt="consent",  # Force consent to get refresh token
    )
    return str(authorization_url)


def exchange_code_for_tokens(authorization_code: str) -> dict[str, str]:
    """Exchange authorization code for access and refresh tokens.

    Args:
        authorization_code: The authorization code from Google callback.

    Returns:
        Dictionary with access_token, refresh_token, and expiry_date.

    Raises:
        HTTPException: If token exchange fails.
    """
    try:
        flow = get_oauth_flow()
        flow.fetch_token(code=authorization_code)

        credentials = flow.credentials

        # Calculate expiry date in milliseconds (Unix timestamp)
        expiry_ms = 0
        if credentials.expiry:
            expiry_ms = int(credentials.expiry.timestamp() * 1000)

        return {
            "access_token": credentials.token or "",
            "refresh_token": credentials.refresh_token or "",
            "expiry_date": str(expiry_ms),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {e!s}") from e


def refresh_access_token(refresh_token: str) -> dict[str, str]:
    """Refresh an expired access token using the refresh token.

    Args:
        refresh_token: The refresh token.

    Returns:
        Dictionary with new access_token and expiry_date.

    Raises:
        HTTPException: If token refresh fails.
    """
    try:
        credentials_path = _get_credentials_path()

        with open(credentials_path) as f:
            client_config = json.load(f)

        if "web" in client_config:
            client_data = client_config["web"]
        elif "installed" in client_config:
            client_data = client_config["installed"]
        else:
            raise ValueError("Invalid credentials file format")

        client_id = client_data["client_id"]
        client_secret = client_data["client_secret"]

        credentials = Credentials(  # nosec B106 - token_uri is not a password
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )

        credentials.refresh(Request())

        expiry_ms = 0
        if credentials.expiry:
            expiry_ms = int(credentials.expiry.timestamp() * 1000)

        return {
            "access_token": credentials.token or "",
            "expiry_date": str(expiry_ms),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to refresh token: {e!s}") from e


def is_token_expired(expiry_date_ms: int, buffer_seconds: int = 300) -> bool:
    """Check if a token is expired or about to expire.

    Args:
        expiry_date_ms: Token expiry as Unix timestamp in milliseconds.
        buffer_seconds: Buffer time in seconds before actual expiry.

    Returns:
        True if token is expired or will expire within buffer_seconds.
    """
    if expiry_date_ms <= 0:
        return True

    now_ms = int(datetime.now(tz=timezone.utc).timestamp() * 1000)
    buffer_ms = buffer_seconds * 1000

    return now_ms >= (expiry_date_ms - buffer_ms)
