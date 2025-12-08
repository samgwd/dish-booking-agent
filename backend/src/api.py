"""API for the Dish Booking Agent."""

from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic_ai.messages import ModelMessage, ModelResponse

from src.agent import agent, process_message


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

    # Collapse streamed assistant parts into a single reply so the UI renders one response per send.
    response_parts: list[str] = []
    for msg in updated_history[prior_length:]:
        if isinstance(msg, ModelResponse):
            response_parts.extend(getattr(part, "content", "") for part in msg.parts)

    combined_response = "".join(response_parts).strip()
    return [combined_response] if combined_response else []
