"""Dish Booking Agent."""

import asyncio
import traceback
from collections.abc import AsyncIterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic_ai import Agent, capture_run_messages
from pydantic_ai.mcp import CallToolFunc, ToolResult
from pydantic_ai.messages import AgentStreamEvent, FunctionToolCallEvent, ModelMessage
from pydantic_ai.tools import RunContext

from src.mcp_formatting import describe_tool_call
from src.mcp_loader import load_mcp_servers_with_env

# Load .env from project root (one level up from backend/)
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")


@dataclass
class AgentDeps:
    """Dependencies for the Dish Booking Agent."""

    dish_cookie: str | None = None
    team_id: str | None = None
    member_id: str | None = None


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
    # NOTE: This hook is ONLY assigned to the dish-mcp server, so no prefix check needed
    if ctx.deps and ctx.deps.dish_cookie:
        tool_args["cookie"] = ctx.deps.dish_cookie
    # Only inject user_info for tools that accept it (book_room)
    # check_availability_and_list_bookings and cancel_booking don't accept user_info
    if name == "book_room" and ctx.deps and ctx.deps.team_id and ctx.deps.member_id:
        tool_args["user_info"] = {
            "team_id": ctx.deps.team_id,
            "member_id": ctx.deps.member_id,
        }
    return await call_tool(name, tool_args, {})


async def log_mcp_activity(
    _run_ctx: RunContext[AgentDeps], events: AsyncIterable[AgentStreamEvent]
) -> None:
    """Event handler that logs whenever the agent triggers an MCP tool."""
    async for event in events:
        if isinstance(event, FunctionToolCallEvent) and (
            message := describe_tool_call(event.part.tool_name, event.part.args_as_dict())
        ):
            print(f"\n[MCP] {message}", flush=True)


project_root = Path(__file__).resolve().parent.parent
config_path = project_root / "mcp_config.json"
mcp_toolsets = load_mcp_servers_with_env(str(config_path), inject_dish_credentials)

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
        "explicitly asked or clearly implied (e.g., “Reschedule that meeting to 3pm tomorrow”); "
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


async def main() -> None:
    """Main function for the Dish Booking Agent."""
    message_history: list[ModelMessage] = []

    # Use async context manager to keep MCP server connections alive
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
