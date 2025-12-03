"""Dish Booking Agent."""

import asyncio
import traceback
from collections.abc import AsyncIterable
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv
from mcp import ClientSession
from mcp_formatting import describe_tool_call
from mcp_loader import load_mcp_servers_with_env
from pydantic_ai import Agent, capture_run_messages
from pydantic_ai.messages import AgentStreamEvent, FunctionToolCallEvent, ModelMessage
from pydantic_ai.tools import RunContext

load_dotenv()


@dataclass
class AgentDeps:
    """Dependencies for the Dish Booking Agent."""

    sessions: dict[str, ClientSession]


async def log_mcp_activity(
    _run_ctx: RunContext[AgentDeps], events: AsyncIterable[AgentStreamEvent]
) -> None:
    """Event handler that logs whenever the agent triggers an MCP tool."""
    async for event in events:
        if isinstance(event, FunctionToolCallEvent) and (
            message := describe_tool_call(event.part.tool_name, event.part.args_as_dict())
        ):
            print(f"\n[MCP] {message}", flush=True)


mcp_toolsets = load_mcp_servers_with_env("mcp_config.json")

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
    user_input: str, message_history: list[ModelMessage]
) -> list[ModelMessage]:
    """Process a user message and return updated message history.

    Args:
        user_input: The user's input message.
        message_history: The history of messages between the user and the agent.

    Returns:
        The updated message history.
    """
    try:
        with capture_run_messages() as captured_messages:
            async with agent.run_stream(
                user_input,
                message_history=message_history,
            ) as result:
                text_started = False
                async for text in result.stream_text(delta=True):
                    if not text_started:
                        print("Agent: ", end="", flush=True)
                        text_started = True
                    print(text, end="", flush=True)
        if text_started:
            print()
        return list(captured_messages)
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
