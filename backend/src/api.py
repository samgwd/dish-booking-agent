"""API for the Dish Booking Agent."""

from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelResponse

from src.agent import agent, process_message
from src.keycloak.keycloak_auth import KeycloakPrincipal, get_current_principal


class UserCredentials(BaseModel):
    """Request body for user authentication endpoints."""

    email: str
    password: str


class UserIdRequest(BaseModel):
    """Request body for endpoints requiring a user ID."""

    user_id: UUID


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
