"""Shared fixtures for MCP package tests."""

from typing import Any

import pytest


@pytest.fixture
def sample_mcp_config() -> dict[str, Any]:
    """Create a sample MCP configuration for testing."""
    return {
        "mcpServers": {
            "google-calendar": {
                "command": "npx",
                "args": ["-y", "@anthropic/google-calendar-mcp"],
                "env": {"API_KEY": "test-key"},
            },
            "dish_mcp": {
                "command": "python",
                "args": ["-m", "dish_mcp"],
                "cwd": "/path/to/dish",
            },
        }
    }


@pytest.fixture
def sample_mcp_config_with_env_vars() -> str:
    """Create a sample MCP config string with environment variable placeholders."""
    return """{
    "mcpServers": {
        "test-server": {
            "command": "npx",
            "args": ["-y", "test-package"],
            "env": {
                "API_KEY": "${TEST_API_KEY}",
                "SECRET": "${TEST_SECRET}"
            }
        }
    }
}"""


@pytest.fixture
def empty_mcp_config() -> dict[str, Any]:
    """Create an empty MCP configuration."""
    return {"mcpServers": {}}


@pytest.fixture
def sample_datetime_args() -> dict[str, str]:
    """Create sample args with datetime values."""
    return {
        "timeMin": "2025-01-15T10:00:00Z",
        "timeMax": "2025-01-15T11:30:00Z",
    }


@pytest.fixture
def sample_dish_datetime_args() -> dict[str, str]:
    """Create sample args with DiSH datetime format."""
    return {
        "start_datetime": "2025-01-15T10:00:00",
        "end_datetime": "2025-01-15T11:30:00",
    }
