"""Dish Booking Agent - core agent logic."""

import asyncio
import traceback
from collections.abc import AsyncIterable
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent, capture_run_messages
from pydantic_ai.messages import AgentStreamEvent, FunctionToolCallEvent, ModelMessage
from pydantic_ai.tools import RunContext

from src.agent.hooks import inject_dish_credentials, inject_google_calendar_credentials
from src.agent.streaming import StreamingEvent, StreamState, process_event
from src.agent.types import AgentDeps
from src.mcp.formatting import describe_tool_call
from src.mcp.loader import load_mcp_servers_with_env

# Load .env from project root (four levels up from this file)
_project_root = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(_project_root / ".env")

SYSTEM_PROMPT = """\
You manage both office room bookings (Dish MCP) and Google Calendar for the user. \
Use Dish tools for room availability and booking; use Google Calendar tools to list \
events, check calendar availability, and create/update/delete meetings. \
Google Calendar is the source of truth for calendar events—only create/update/delete when \
explicitly asked or clearly implied (e.g., 'Reschedule that meeting to 3pm tomorrow'); \
confirm before destructive actions if instructions are ambiguous. \
Coordinate room bookings with calendar availability whenever scheduling meetings. \
Convert user time suggestions to the format expected by each tool. \
Only ask clarifying questions if its really necessary. Make reasonable assumptions. \
When checking availability, summarise the results clearly. \
Today's date is {date}."""


async def _log_mcp_activity(
    _run_ctx: RunContext[AgentDeps], events: AsyncIterable[AgentStreamEvent]
) -> None:
    """Event handler that logs whenever the agent triggers an MCP tool.

    Args:
        _run_ctx: The run context containing AgentDeps.
        events: The events to log.
    """
    async for event in events:
        if isinstance(event, FunctionToolCallEvent) and (
            message := describe_tool_call(event.part.tool_name, event.part.args_as_dict())
        ):
            print(f"\n[MCP] {message}", flush=True)


def _create_agent() -> Agent[AgentDeps, str]:
    """Create and configure the agent with MCP toolsets.

    Returns:
        The configured agent instance.
    """
    config_path = Path(__file__).resolve().parent.parent.parent / "mcp_config.json"
    mcp_toolsets = load_mcp_servers_with_env(
        str(config_path),
        tool_processors={
            "dish-mcp": inject_dish_credentials,
            "google-calendar": inject_google_calendar_credentials,
        },
    )
    return Agent(
        "openai:gpt-4o-mini",
        deps_type=AgentDeps,
        toolsets=mcp_toolsets,
        event_stream_handler=_log_mcp_activity,
        system_prompt=SYSTEM_PROMPT.format(date=datetime.now().strftime("%Y-%m-%d")),
    )


agent = _create_agent()


async def process_message(
    user_input: str,
    message_history: list[ModelMessage],
    deps: AgentDeps | None = None,
) -> list[ModelMessage]:
    """Process a user message and return updated message history.

    Args:
        user_input: The user's input message.
        message_history: The history of messages between the user and the agent.
        deps: Optional agent dependencies containing user credentials.

    Returns:
        The updated message history.
    """
    try:
        with capture_run_messages() as captured_messages:
            async with agent.run_stream(
                user_input,
                message_history=message_history,
                deps=deps or AgentDeps(),
            ) as result:
                text_started = False
                async for text in result.stream_text(delta=True):
                    if not text_started:
                        print("Agent: ", end="", flush=True)
                        text_started = True
                    print(text, end="", flush=True)
        if text_started:
            print()
        new_messages = list(captured_messages)
        return [*message_history, *new_messages]
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return message_history


async def process_message_streaming(
    user_input: str,
    message_history: list[ModelMessage],
    deps: AgentDeps | None = None,
) -> AsyncIterable[StreamingEvent]:
    """Process a user message and yield streaming events.

    This is designed for Server-Sent Events (SSE) streaming to keep the
    connection alive during long-running agent operations.

    Args:
        user_input: The user's input message.
        message_history: The history of messages between the user and the agent.
        deps: Optional agent dependencies containing user credentials.

    Yields:
        Tuples of (event_type, data, updated_history) where:
        - event_type: "text", "tool_call", "done", or "error"
        - data: The text chunk, tool description, or error message
        - updated_history: The updated message history (only populated on "done")
    """
    try:
        state = StreamState()
        with capture_run_messages() as captured_messages:
            async for event in agent.run_stream_events(
                user_input, message_history=message_history, deps=deps or AgentDeps()
            ):
                result = process_event(event, state, message_history, list(captured_messages))
                if result:
                    yield result

        if state.text_started:
            print()
        yield ("done", "", state.updated_history)

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        yield ("error", str(e), message_history)


async def main() -> None:
    """Main function for the Dish Booking Agent."""
    message_history: list[ModelMessage] = []

    async with agent:
        print("\nAgent is ready! Type 'quit' to exit.")
        print("Type 'reset' to clear the conversation history.")
        print("-" * 50)
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["quit", "exit"]:
                break

            if user_input.lower() == "reset":
                message_history = []
                print("Agent: Conversation history cleared.")
                continue

            message_history = await process_message(user_input, message_history)


if __name__ == "__main__":
    asyncio.run(main())
