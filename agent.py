"""Dish Booking Agent."""

import asyncio
import traceback
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv
from mcp import ClientSession
from pydantic_ai import Agent, capture_run_messages
from pydantic_ai.mcp import load_mcp_servers
from pydantic_ai.messages import ModelMessage

load_dotenv()


@dataclass
class AgentDeps:
    """Dependencies for the Dish Booking Agent."""

    sessions: dict[str, ClientSession]


mcp_toolsets = load_mcp_servers("mcp_config.json")

agent = Agent(
    "openai:gpt-5-nano",
    deps_type=AgentDeps,
    toolsets=mcp_toolsets,
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


async def main() -> None:
    """Main function for the Dish Booking Agent."""
    print("\nAgent is ready! Type 'quit' to exit.")
    print("Type 'reset' to clear the conversation history.")
    print("-" * 50)

    message_history: list[ModelMessage] = []

    # Use async context manager to keep MCP server connections alive
    async with agent:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["quit", "exit"]:
                break

            if user_input.lower() == "reset":
                message_history = []
                print("Agent: Conversation history cleared.")
                continue

            try:
                with capture_run_messages() as captured_messages:
                    result = await agent.run(
                        user_input,
                        message_history=message_history,
                    )
                message_history = list(captured_messages)
                print(f"Agent: {result.output}")
            except Exception as e:
                print(f"Error: {e}")
                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
