"""API for the Dish Booking Agent."""

import json
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage

from src.agent import (
    AgentDeps,
    DishCredentials,
    GoogleCalendarTokens,
    agent,
    process_message_streaming,
)
from src.google_oauth import exchange_code_for_tokens, get_authorization_url
from src.keycloak.keycloak_auth import KeycloakPrincipal, get_current_principal
from src.user_db.user_db_utilities import (
    delete_user_secret,
    ensure_user_exists,
    get_all_user_secrets,
    get_user_secret,
    list_user_secret_keys,
    set_user_secret,
)


class SecretRequest(BaseModel):
    """Request body for storing a user secret."""

    key: str
    value: str


class SecretKeyRequest(BaseModel):
    """Request body for retrieving or deleting a specific secret."""

    key: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan for the FastAPI app.

    Args:
        app: The FastAPI app.

    Returns:
        An asynchronous generator that yields None.
    """
    async with agent:  # keeps MCP server connections open once
        yield


app = FastAPI(lifespan=lifespan)
message_histories: defaultdict[str, list[ModelMessage]] = defaultdict(list)


@app.get("/health")
def health() -> dict[str, str]:
    """Check the health of the API.

    Returns:
        A tuple containing a dictionary with the status and an integer representing the HTTP status
        code.
    """
    return {"status": "ok"}


@app.post("/secrets")
async def store_secret(
    request: SecretRequest,
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> dict[str, str]:
    """Store or update an encrypted secret for the authenticated user.

    Args:
        request: The request containing key and value.
        principal: The authenticated Keycloak principal (derived from the Bearer token).

    Returns:
        Status confirmation.
    """
    # Auto-provision user in local DB if this is their first interaction
    ensure_user_exists(principal.sub, email=principal.email)
    set_user_secret(principal.sub, request.key, request.value)
    return {"status": "ok"}


@app.get("/secrets")
async def list_secrets(
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> dict[str, list[str]]:
    """List all secret keys for the authenticated user (values are not returned).

    Args:
        principal: The authenticated Keycloak principal (derived from the Bearer token).

    Returns:
        A dict with a 'keys' list of secret key names.
    """
    keys = list_user_secret_keys(principal.sub)
    return {"keys": keys}


@app.post("/secrets/get")
async def retrieve_secret(
    request: SecretKeyRequest,
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> dict[str, str | None]:
    """Retrieve a specific secret for the authenticated user.

    Args:
        request: The request containing the key.
        principal: The authenticated Keycloak principal (derived from the Bearer token).

    Returns:
        The decrypted secret value, or null if not found.
    """
    value = get_user_secret(principal.sub, request.key)
    return {"key": request.key, "value": value}


@app.delete("/secrets")
async def remove_secret(
    request: SecretKeyRequest,
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> dict[str, str]:
    """Delete a specific secret for the authenticated user.

    Args:
        request: The request containing the key.
        principal: The authenticated Keycloak principal (derived from the Bearer token).

    Raises:
        HTTPException: If the secret is not found.
    """
    if not delete_user_secret(principal.sub, request.key):
        raise HTTPException(status_code=404, detail="Secret not found")
    return {"status": "ok"}


def _build_agent_deps(secrets: dict[str, str]) -> AgentDeps:
    """Build AgentDeps from user secrets.

    Args:
        secrets: Dictionary of user secrets.

    Returns:
        AgentDeps with credentials populated from secrets.
    """
    dish_creds = None
    if all(secrets.get(k) for k in ("DISH_COOKIE", "TEAM_ID", "MEMBER_ID")):
        dish_creds = DishCredentials(
            cookie=secrets["DISH_COOKIE"],
            team_id=secrets["TEAM_ID"],
            member_id=secrets["MEMBER_ID"],
        )

    gcal_tokens = None
    gcal_access = secrets.get("GOOGLE_CALENDAR_ACCESS_TOKEN")
    if gcal_access:
        gcal_refresh = secrets.get("GOOGLE_CALENDAR_REFRESH_TOKEN", "")
        gcal_expiry = secrets.get("GOOGLE_CALENDAR_EXPIRY_DATE", "0")
        gcal_tokens = GoogleCalendarTokens(
            access_token=gcal_access,
            refresh_token=gcal_refresh,
            expiry_date=int(gcal_expiry) if gcal_expiry else 0,
        )

    return AgentDeps(dish=dish_creds, google_calendar=gcal_tokens)


GOOGLE_CALENDAR_SECRET_KEYS = [
    "GOOGLE_CALENDAR_ACCESS_TOKEN",
    "GOOGLE_CALENDAR_REFRESH_TOKEN",
    "GOOGLE_CALENDAR_EXPIRY_DATE",
]


@app.get("/oauth/google/authorize")
async def initiate_google_oauth(
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> dict[str, str]:
    """Initiate Google OAuth flow.

    Args:
        principal: The authenticated Keycloak principal.

    Returns:
        Authorization URL for redirecting the user.
    """
    state = principal.sub
    authorization_url = get_authorization_url(state)
    return {"authorization_url": authorization_url}


@app.get("/oauth/google/callback")
async def google_oauth_callback(
    code: str,
    state: str,
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> dict[str, str]:
    """Handle Google OAuth callback and store tokens.

    Args:
        code: Authorization code from Google.
        state: State parameter (should match user's sub).
        principal: The authenticated Keycloak principal.

    Returns:
        Success status.

    Raises:
        HTTPException: If state doesn't match or token exchange fails.
    """
    if state != principal.sub:
        raise HTTPException(status_code=403, detail="Invalid state parameter")

    tokens = exchange_code_for_tokens(code)

    ensure_user_exists(principal.sub, email=principal.email)

    set_user_secret(principal.sub, "GOOGLE_CALENDAR_ACCESS_TOKEN", tokens["access_token"])
    set_user_secret(principal.sub, "GOOGLE_CALENDAR_REFRESH_TOKEN", tokens["refresh_token"])
    set_user_secret(principal.sub, "GOOGLE_CALENDAR_EXPIRY_DATE", tokens["expiry_date"])

    return {"status": "ok", "message": "Google Calendar connected successfully"}


@app.post("/oauth/google/disconnect")
async def disconnect_google_oauth(
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> dict[str, str]:
    """Disconnect Google Calendar by removing stored tokens.

    Args:
        principal: The authenticated Keycloak principal.

    Returns:
        Success status.
    """
    for key in GOOGLE_CALENDAR_SECRET_KEYS:
        delete_user_secret(principal.sub, key)

    return {"status": "ok", "message": "Google Calendar disconnected"}


@app.get("/oauth/google/status")
async def google_oauth_status(
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> dict[str, bool]:
    """Check if Google Calendar is connected.

    Args:
        principal: The authenticated Keycloak principal.

    Returns:
        Connection status.
    """
    access_token = get_user_secret(principal.sub, "GOOGLE_CALENDAR_ACCESS_TOKEN")
    return {"connected": access_token is not None and len(access_token) > 0}


def _format_sse_event(event_type: str, data: str | None = None) -> str:
    """Format an SSE event as a JSON string.

    Args:
        event_type: The type of event (text, tool_call, done, error).
        data: Optional data payload for the event.

    Returns:
        Formatted SSE event string.
    """
    payload: dict[str, str] = {"type": event_type}
    if event_type == "text":
        payload["content"] = data or ""
    elif event_type == "tool_call":
        payload["tool"] = data or ""
    elif event_type == "error":
        payload["message"] = data or ""
    return f"data: {json.dumps(payload)}\n\n"


async def _stream_agent_events(
    message: str,
    session_key: str,
    history: list[ModelMessage],
    deps: AgentDeps,
) -> AsyncGenerator[str, None]:
    """Generate SSE events from the agent's streaming response.

    Args:
        message: The user message to process.
        session_key: The session key for storing history.
        history: The current message history.
        deps: Agent dependencies.

    Yields:
        Formatted SSE event strings.
    """
    try:
        async for event_type, data, updated_history in process_message_streaming(
            message, history, deps=deps
        ):
            yield _format_sse_event(event_type, data)
            if event_type == "done":
                message_histories[session_key] = updated_history
    except Exception as e:
        yield _format_sse_event("error", str(e))


@app.get("/send-message")
async def send_message(
    message: str,
    session: str = "default",
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> StreamingResponse:
    """Send a message to the API using Server-Sent Events (SSE).

    Args:
        message: The message to send.
        session: The session to use.
        principal: The authenticated Keycloak principal (derived from the Bearer token).

    Returns:
        A StreamingResponse with SSE events containing the agent's response.
    """
    secrets = get_all_user_secrets(principal.sub)
    deps = _build_agent_deps(secrets)
    session_key = f"{principal.sub}:{session}"
    history = message_histories[session_key]

    return StreamingResponse(
        _stream_agent_events(message, session_key, history, deps),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
