"""MCP configuration loader with environment variable substitution."""

import json
import os
import re
from typing import Any, cast

from pydantic_ai.mcp import MCPServerStdio


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


def create_mcp_toolsets(config: dict[str, Any]) -> list[MCPServerStdio]:
    """Create MCP toolsets from config dict."""
    toolsets = []
    for name, server_config in config.get("mcpServers", {}).items():
        toolset = MCPServerStdio(
            server_config["command"],
            server_config.get("args", []),
            cwd=server_config.get("cwd"),
            env=server_config.get("env"),
            tool_prefix=name,
        )
        toolsets.append(toolset)
    return toolsets


def load_mcp_servers_with_env(config_path: str) -> list[MCPServerStdio]:
    """Load MCP servers from config file with environment variable substitution.

    This is a drop-in replacement for pydantic_ai.mcp.load_mcp_servers that
    supports ${VAR_NAME} syntax for environment variable substitution.
    """
    config = load_mcp_config_with_env(config_path)
    return create_mcp_toolsets(config)
