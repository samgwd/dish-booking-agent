import asyncio
import os
import sys
from dataclasses import dataclass
from typing import Optional, List, Any, Dict
from datetime import datetime
import traceback
import inspect
from typing import get_type_hints

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext, capture_run_messages
from pydantic_ai.messages import ModelMessage
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()


@dataclass
class AgentDeps:
    sessions: dict[str, ClientSession]


agent = Agent(
    "openai:gpt-5.1",
    deps_type=AgentDeps,
    system_prompt=(
        "You manage both office room bookings (Dish MCP) and Google Calendar for the user. "
        "Use Dish tools for room availability and booking; use Google Calendar tools to list events, "
        "check calendar availability, and create/update/delete meetings. "
        "Google Calendar is the source of truth for calendar events—only create/update/delete when "
        "explicitly asked or clearly implied (e.g., “Reschedule that meeting to 3pm tomorrow”); "
        "confirm before destructive actions if instructions are ambiguous. "
        "Coordinate room bookings with calendar availability whenever scheduling meetings. "
        "Convert user time suggestions to the format expected by each tool. "
        "Only ask clarifying questions if its really necessary. Make reasonable assumptions. "
        "When checking availability, summarize the results clearly. "
        "Today's date is " + datetime.now().strftime("%Y-%m-%d") + "."
    ),
)


def create_mcp_tool_wrapper(
    tool_name: str,
    tool_schema: Dict[str, Any],
    session: ClientSession,
    tool_namespace: Optional[str] = None,
):
    """Dynamically create a wrapper function for an MCP tool.

    Args:
        tool_name: The name of the tool to wrap.
        tool_schema: The schema of the tool to wrap.
        session: The MCP session the tool should use.
        tool_namespace: Optional namespace to disambiguate tool names.
    """

    async def wrapper(ctx: RunContext[AgentDeps], **kwargs: Any) -> str:
        """Dynamically generated wrapper for MCP tool."""
        # Filter out None values and add cookie if not present (Dish tools only)
        filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if tool_namespace == "dish" and "cookie" not in filtered_kwargs:
            cookie = os.environ.get("DISH_COOKIE")
            if cookie:
                filtered_kwargs["cookie"] = cookie

        result = await session.call_tool(tool_name, arguments=filtered_kwargs)
        return result.content[0].text

    # Set the function name and docstring from the tool schema
    namespace_prefix = f"{tool_namespace}__" if tool_namespace else ""
    wrapper.__name__ = (namespace_prefix + tool_name).replace("-", "_")

    namespace_label = tool_namespace or "default"
    description_prefix = (
        f"{namespace_label.upper()} MCP tool for {tool_name}. "
        if tool_namespace
        else ""
    )
    wrapper.__doc__ = description_prefix + tool_schema.get(
        "description", f"Call MCP tool: {tool_name}"
    )

    return wrapper


async def register_mcp_tools(session: ClientSession, namespace: Optional[str] = None):
    """Dynamically register all tools from the MCP server.

    Args:
        session: The MCP session to register the tools with.
        namespace: Optional namespace to prefix tool names with.
    """
    tools_response = await session.list_tools()

    registered_names: list[str] = []
    for mcp_tool in tools_response.tools:
        # Create a wrapper function for this tool
        wrapper = create_mcp_tool_wrapper(
            mcp_tool.name,
            {
                "description": mcp_tool.description or "",
                "inputSchema": mcp_tool.inputSchema,
            },
            session=session,
            tool_namespace=namespace,
        )

        registered_name = (
            f"{namespace}__{mcp_tool.name}" if namespace else mcp_tool.name
        )

        # Register it with the agent
        agent.tool(wrapper)

        registered_names.append(registered_name.replace("-", "_"))
        print(f"Registered tool: {registered_name}")

    return registered_names


async def main():
    # Configuration for the MCP server
    # Assuming the user runs: uv run fastmcp run src/mcp_server.py --transport sse
    # Default FastMCP SSE port is 8000
    dish_sse_url = os.getenv("DISH_MCP_SSE_URL", "http://127.0.0.1:8000/sse")

    gcal_http_url = os.getenv("GCAL_MCP_HTTP_URL")
    if not gcal_http_url:
        gcal_http_url = os.getenv("GCAL_MCP_SSE_URL", "http://127.0.0.1:3000")
        if gcal_http_url.endswith("/sse"):
            gcal_http_url = gcal_http_url[: -len("/sse")]

    print(f"Connecting to Dish MCP server at {dish_sse_url}...")
    print(f"Connecting to Google Calendar MCP server at {gcal_http_url}...")

    try:
        async with sse_client(dish_sse_url) as dish_streams, streamablehttp_client(
            gcal_http_url, terminate_on_close=False
        ) as gcal_streams:
            dish_read_stream, dish_write_stream = dish_streams
            gcal_read_stream, gcal_write_stream, _ = gcal_streams

            async with ClientSession(
                dish_read_stream, dish_write_stream
            ) as dish_session, ClientSession(
                gcal_read_stream, gcal_write_stream
            ) as gcal_session:
                await dish_session.initialize()
                await gcal_session.initialize()

                # Register Dish tools
                dish_registered = await register_mcp_tools(
                    dish_session, namespace="dish"
                )
                print(
                    f"Connected to Dish MCP. Registered {len(dish_registered)} tools: {dish_registered}"
                )

                # Register Google Calendar tools
                gcal_registered = await register_mcp_tools(
                    gcal_session, namespace="gcal"
                )
                print(
                    f"Connected to Google Calendar MCP. Registered {len(gcal_registered)} tools: {gcal_registered}"
                )

                deps = AgentDeps(sessions={"dish": dish_session, "gcal": gcal_session})

                print("\nAgent is ready! Type 'quit' to exit.")
                print("Type 'reset' to clear the conversation history.")
                print("-" * 50)

                message_history: List[ModelMessage] = []

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
                                deps=deps,
                                message_history=message_history,
                            )
                        message_history = list(captured_messages)
                        print(f"Agent: {result.output}")
                    except Exception as e:
                        print(f"Error: {e}")
                        traceback.print_exc()

    except Exception as e:
        print(f"\nFailed to connect to MCP servers: {e}")
        traceback.print_exc()
        print(
            "Make sure the Dish and Google Calendar MCP servers are running with their SSE transports."
        )


if __name__ == "__main__":
    asyncio.run(main())
