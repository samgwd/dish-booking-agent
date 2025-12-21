"""Dish Booking Agent."""

import asyncio
import traceback
from collections.abc import AsyncIterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic_ai import Agent, AgentRunResultEvent, capture_run_messages
from pydantic_ai.mcp import CallToolFunc, ToolResult
from pydantic_ai.messages import (
    AgentStreamEvent,
    FunctionToolCallEvent,
    ModelMessage,
    PartDeltaEvent,
    TextPartDelta,
)
from pydantic_ai.tools import RunContext

from src.mcp_formatting import describe_tool_call
from src.mcp_loader import load_mcp_servers_with_env

# Load .env from project root (three levels up from this file)
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")


@dataclass
class DishCredentials:
    """Credentials for DiSH room booking."""

    cookie: str
    team_id: str
    member_id: str


@dataclass
class GoogleCalendarTokens:
    """OAuth tokens for Google Calendar API."""

    access_token: str
    refresh_token: str
    expiry_date: int  # Unix timestamp in milliseconds


@dataclass
class AgentDeps:
    """Dependencies for the Dish Booking Agent."""

    dish: DishCredentials | None = None
    google_calendar: GoogleCalendarTokens | None = None


async def inject_dish_credentials(
    ctx: RunContext[AgentDeps],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """Inject user credentials into DiSH MCP tool calls.

    This is a process_tool_call hook that intercepts MCP tool calls and
    automatically injects the user's DiSH credentials from AgentDeps.

    Args:
        ctx: The run context containing AgentDeps with credentials.
        call_tool: The function to call the underlying MCP tool.
        name: The name of the tool being called.
        tool_args: The arguments for the tool call.

    Returns:
        The result from the MCP tool call.
    """
    # Inject credentials for all dish-mcp tools
    # NOTE: Tool names include the prefix (e.g., "dish_mcp_book_room")
    if ctx.deps and ctx.deps.dish:
        tool_args["cookie"] = ctx.deps.dish.cookie
        # Only inject user_info for tools that accept it (book_room)
        # check_availability_and_list_bookings and cancel_booking don't accept user_info
        if name.endswith("_book_room"):
            tool_args["user_info"] = {
                "team_id": ctx.deps.dish.team_id,
                "member_id": ctx.deps.dish.member_id,
            }
    return await call_tool(name, tool_args, {})


async def inject_google_calendar_credentials(
    ctx: RunContext[AgentDeps],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """Inject OAuth credentials into Google Calendar MCP tool calls.

    This is a process_tool_call hook that intercepts MCP tool calls and
    automatically injects the user's Google Calendar OAuth tokens from AgentDeps.

    Args:
        ctx: The run context containing AgentDeps with credentials.
        call_tool: The function to call the underlying MCP tool.
        name: The name of the tool being called.
        tool_args: The arguments for the tool call.

    Returns:
        The result from the MCP tool call.
    """
    if ctx.deps and ctx.deps.google_calendar:
        tool_args["oauth_credentials"] = {
            "access_token": ctx.deps.google_calendar.access_token,
            "refresh_token": ctx.deps.google_calendar.refresh_token,
            "expiry_date": ctx.deps.google_calendar.expiry_date,
        }

    return await call_tool(name, tool_args, {})


async def log_mcp_activity(
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


project_root = Path(__file__).resolve().parent.parent
config_path = project_root / "mcp_config.json"
mcp_toolsets = load_mcp_servers_with_env(
    str(config_path),
    tool_processors={
        "dish-mcp": inject_dish_credentials,
        "google-calendar": inject_google_calendar_credentials,
    },
)

agent = Agent(
    "openai:gpt-5-nano",
    deps_type=AgentDeps,
    toolsets=mcp_toolsets,
    event_stream_handler=log_mcp_activity,
    system_prompt=(
        "You manage both office room bookings (Dish MCP) and Google Calendar for the user. "
        "Use Dish tools for room availability and booking; use Google Calendar tools to list "
        "events, check calendar availability, and create/update/delete meetings. "
        "Google Calendar is the source of truth for calendar events—only create/update/delete when "
        "explicitly asked or clearly implied (e.g., 'Reschedule that meeting to 3pm tomorrow'); "
        "confirm before destructive actions if instructions are ambiguous. "
        "Coordinate room bookings with calendar availability whenever scheduling meetings. "
        "Convert user time suggestions to the format expected by each tool. "
        "Only ask clarifying questions if its really necessary. Make reasonable assumptions. "
        "When checking availability, summarise the results clearly. "
        "Today's date is " + datetime.now().strftime("%Y-%m-%d") + "."
    ),
)


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


StreamingEvent = tuple[str, str, list[ModelMessage]]


class _StreamState:
    """Mutable state container for streaming events."""

    def __init__(self) -> None:
        self.text_started = False
        self.updated_history: list[ModelMessage] = []


def _process_event(
    event: AgentStreamEvent | AgentRunResultEvent[str],
    state: _StreamState,
    message_history: list[ModelMessage],
    captured_messages: list[ModelMessage],
) -> StreamingEvent | None:
    """Process a single agent stream event and return a streaming event if applicable.

    Arguments:
        event: The agent stream event to process.
        state: The mutable state container for streaming events.
        message_history: The history of messages between the user and the agent.
        captured_messages: The captured messages from the agent run.

    Returns:
        A streaming event if applicable, otherwise None.
    """
    if isinstance(event, AgentRunResultEvent):
        state.updated_history = [*message_history, *captured_messages]
        return None

    if isinstance(event, FunctionToolCallEvent):
        desc = describe_tool_call(event.part.tool_name, event.part.args_as_dict())
        print(f"\n[MCP] {desc}", flush=True)
        return ("tool_call", desc, [])

    if isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
        if not state.text_started:
            print("Agent: ", end="", flush=True)
            state.text_started = True
        print(event.delta.content_delta, end="", flush=True)
        return ("text", event.delta.content_delta, [])

    return None


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
        state = _StreamState()
        with capture_run_messages() as captured_messages:
            async for event in agent.run_stream_events(
                user_input, message_history=message_history, deps=deps or AgentDeps()
            ):
                result = _process_event(event, state, message_history, list(captured_messages))
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
