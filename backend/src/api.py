"""API for the Dish Booking Agent."""

from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelResponse
from sqlalchemy.exc import IntegrityError

from src.agent import agent, process_message
from src.user_db.user_db_utilities import (
    authenticate,
    create_user,
    delete_user,
    logout_user,
)


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


@app.post("/register")
async def register(credentials: UserCredentials) -> dict[str, str]:
    """Register a new user.

    Args:
        credentials: The user credentials containing email and password.

    Raises:
        HTTPException: If the email is already registered.
    """
    try:
        user = create_user(credentials.email, credentials.password)
    except IntegrityError as exc:
        # Most commonly: unique constraint violation on users.email.
        raise HTTPException(status_code=409, detail="Email already registered") from exc

    return {"status": "ok", "user_id": str(user.id)}


@app.post("/login")
async def login(credentials: UserCredentials) -> dict[str, str]:
    """Login a user.

    Args:
        credentials: The user credentials containing email and password.

    Raises:
        HTTPException: If the credentials are invalid.
    """
    user = authenticate(credentials.email, credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"status": "ok", "user_id": str(user.id)}


@app.post("/logout")
async def logout(request: UserIdRequest) -> dict[str, str]:
    """Logout a user.

    Args:
        request: The request containing the user ID to logout.

    Raises:
        HTTPException: If the user is not found.
    """
    if not logout_user(request.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@app.post("/delete-user")
async def delete_user_account(request: UserIdRequest) -> dict[str, str]:
    """Delete a user.

    Args:
        request: The request containing the user ID to delete.

    Raises:
        HTTPException: If the user is not found.
    """
    if not delete_user(request.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@app.get("/send-message")
async def send_message(message: str, session: str = "default") -> list[str]:
    """Send a message to the API.

    Args:
        message: The message to send.
        session: The session to use.

    Returns:
        A list of strings representing the response messages.
    """
    history = message_histories[session]
    prior_length = len(history)
    updated_history = await process_message(message, history)
    message_histories[session] = updated_history

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
