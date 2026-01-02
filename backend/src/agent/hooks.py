"""MCP tool call hooks for credential injection."""

from typing import Any

from pydantic_ai.mcp import CallToolFunc, ToolResult
from pydantic_ai.tools import RunContext

from src.agent.types import AgentDeps


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
