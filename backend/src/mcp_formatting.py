"""Helpers for formatting MCP tool usage and arguments."""

import json
from typing import Any, Final

mcp_name_map: Final[dict[str, str]] = {
    "dish-mcp": "DiSH MCP",
    "google-calendar": "Google Calendar MCP",
}


def format_mcp_usage(tool_name: str) -> str | None:
    """Return a human friendly description for recognised MCP tools.

    Args:
        tool_name: The name of the tool to format.

    Returns:
        A human friendly description for recognised MCP tools.
    """
    if "_" not in tool_name:
        return None
    prefix, action = tool_name.split("_", 1)
    if (friendly := mcp_name_map.get(prefix)) is None:
        return None
    action_text = action.replace("_", " ").strip()
    return f"Using {friendly} to {action_text}"


def summarise_args(args: dict[str, Any]) -> str:
    """Create a concise, readable summary of tool arguments.

    Args:
        args: The arguments to summarise.

    Returns:
        A concise, readable summary of tool arguments.
    """
    if not args:
        return "with no arguments"

    try:
        preview = json.dumps(args, default=str)
    except TypeError:
        preview = repr(args)

    max_chars = 200
    if len(preview) > max_chars:
        preview = preview[: max_chars - 3] + "..."
    return f"with args {preview}"


def describe_tool_call(tool_name: str, args: dict[str, Any]) -> str:
    """Build a descriptive sentence for a tool call.

    Args:
        tool_name: The name of the tool to describe.
        args: The arguments to describe.

    Returns:
        A descriptive sentence for a tool call.
    """
    args_summary = summarise_args(args)
    base = format_mcp_usage(tool_name)
    if base:
        return f"{base} ({args_summary})"
    return f"Calling {tool_name} ({args_summary})"
