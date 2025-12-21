"""MCP configuration loader with environment variable substitution."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Awaitable, Callable
from typing import Any, cast

from pydantic_ai.mcp import MCPServerStdio, ToolResult

# Type alias for process_tool_call callbacks
ProcessToolCallFunc = Callable[..., Awaitable[ToolResult]]


def load_mcp_config_with_env(config_path: str) -> dict[str, Any]:
    """Load MCP config and substitute environment variables.

    Replaces ${VAR_NAME} patterns with the corresponding environment variable values.

    Args:
        config_path: Path to the MCP config file.

    Returns:
        MCP config with environment variables substituted.
    """
    with open(config_path) as f:
        config_str = f.read()

    def replace_env_var(match: re.Match[str]) -> str:
        """Replace environment variable with its value.

        Args:
            match: Match object from regex substitution.

        Returns:
            Value of the environment variable.
        """
        var_name = match.group(1)
        value = os.environ.get(var_name, "")
        if not value:
            print(f"Warning: Environment variable {var_name} is not set")
        return value

    config_str = re.sub(r"\$\{(\w+)\}", replace_env_var, config_str)

    return cast(dict[str, Any], json.loads(config_str))


def create_mcp_toolsets(
    config: dict[str, Any],
    tool_processors: dict[str, ProcessToolCallFunc] | None = None,
) -> list[MCPServerStdio]:
    """Create MCP toolsets from config dict.

    Args:
        config: The MCP configuration dictionary.
        tool_processors: Optional dict mapping server names to process_tool_call callbacks.
            This allows injecting credentials into tool calls for specific servers.

    Returns:
        A list of MCPServerStdio instances.
    """
    tool_processors = tool_processors or {}
    toolsets = []
    for name, server_config in config.get("mcpServers", {}).items():
        processor = tool_processors.get(name)
        # Use underscores in tool_prefix for valid Python identifiers
        tool_prefix = name.replace("-", "_")
        toolset = MCPServerStdio(
            server_config["command"],
            server_config.get("args", []),
            cwd=server_config.get("cwd"),
            env=server_config.get("env"),
            tool_prefix=tool_prefix,
            process_tool_call=processor,
        )
        toolsets.append(toolset)
    return toolsets


def load_mcp_servers_with_env(
    config_path: str,
    tool_processors: dict[str, ProcessToolCallFunc] | None = None,
) -> list[MCPServerStdio]:
    """Load MCP servers from config file with environment variable substitution.

    This is a drop-in replacement for pydantic_ai.mcp.load_mcp_servers that
    supports ${VAR_NAME} syntax for environment variable substitution.

    Args:
        config_path: Path to the MCP config file.
        tool_processors: Optional dict mapping server names to process_tool_call callbacks.

    Returns:
        A list of MCPServerStdio instances.
    """
    config = load_mcp_config_with_env(config_path)
    return create_mcp_toolsets(config, tool_processors)
