"""API for the Dish Booking Agent."""

from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelResponse

from src.agent import agent, process_message
from src.keycloak.keycloak_auth import KeycloakPrincipal, get_current_principal
from src.user_db.user_db_utilities import (
    delete_user_secret,
    ensure_user_exists,
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


@app.get("/send-message")
async def send_message(
    message: str,
    session: str = "default",
    principal: KeycloakPrincipal = Depends(get_current_principal),
) -> list[str]:
    """Send a message to the API.

    Args:
        message: The message to send.
        session: The session to use.
        principal: The authenticated Keycloak principal (derived from the Bearer token).

    Returns:
        A list of strings representing the response messages.
    """
    session_key = f"{principal.sub}:{session}"
    history = message_histories[session_key]
    prior_length = len(history)
    updated_history = await process_message(message, history)
    message_histories[session_key] = updated_history

    new_messages = updated_history[prior_length:]
    latest_response = next(
        (msg for msg in reversed(new_messages) if isinstance(msg, ModelResponse)),
        None,
    )

    if not latest_response:
        return []

    combined_response = "".join(
        getattr(part, "content", "") for part in latest_response.parts
    ).strip()
    return [combined_response] if combined_response else []
