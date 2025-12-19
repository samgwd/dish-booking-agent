"""API for the Dish Booking Agent."""

from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelResponse

from src.agent import agent, process_message
from src.keycloak.keycloak_auth import KeycloakPrincipal, get_current_principal
from src.user_db.user_db_utilities import (
    delete_user_secret,
    get_user_secret,
    list_user_secret_keys,
    set_user_secret,
)


class UserCredentials(BaseModel):
    """Request body for user authentication endpoints."""

    email: str
    password: str


class UserIdRequest(BaseModel):
    """Request body for endpoints requiring a user ID."""

    user_id: UUID


class SecretRequest(BaseModel):
    """Request body for storing a user secret."""

    user_id: UUID
    key: str
    value: str


class SecretKeyRequest(BaseModel):
    """Request body for retrieving or deleting a specific secret."""

    user_id: UUID
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
async def store_secret(request: SecretRequest) -> dict[str, str]:
    """Store or update an encrypted secret for a user.

    Args:
        request: The request containing user_id, key, and value.

    Returns:
        Status confirmation.
    """
    set_user_secret(request.user_id, request.key, request.value)
    return {"status": "ok"}


@app.get("/secrets/{user_id}")
async def list_secrets(user_id: UUID) -> dict[str, list[str]]:
    """List all secret keys for a user (values are not returned).

    Args:
        user_id: The user ID to list secrets for.

    Returns:
        A dict with a 'keys' list of secret key names.
    """
    keys = list_user_secret_keys(user_id)
    return {"keys": keys}


@app.post("/secrets/get")
async def retrieve_secret(request: SecretKeyRequest) -> dict[str, str | None]:
    """Retrieve a specific secret for a user.

    Args:
        request: The request containing user_id and key.

    Returns:
        The decrypted secret value, or null if not found.
    """
    value = get_user_secret(request.user_id, request.key)
    return {"key": request.key, "value": value}


@app.delete("/secrets")
async def remove_secret(request: SecretKeyRequest) -> dict[str, str]:
    """Delete a specific secret for a user.

    Args:
        request: The request containing user_id and key.

    Raises:
        HTTPException: If the secret is not found.
    """
    if not delete_user_secret(request.user_id, request.key):
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
