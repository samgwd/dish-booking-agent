"""Tests for MCP configuration loader utilities."""

import json
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.mcp.loader import (
    ProcessToolCallFunc,
    create_mcp_toolsets,
    load_mcp_config_with_env,
    load_mcp_servers_with_env,
)


class TestLoadMcpConfigWithEnv:
    """Tests for the load_mcp_config_with_env function."""

    def test_loads_config_from_file(self, tmp_path: Any) -> None:
        """Loads and parses JSON config from file."""
        config_file = tmp_path / "mcp_config.json"
        config_data = {"mcpServers": {"test": {"command": "npx"}}}
        config_file.write_text(json.dumps(config_data))

        result = load_mcp_config_with_env(str(config_file))

        assert result == config_data

    def test_substitutes_single_env_variable(self, tmp_path: Any) -> None:
        """Substitutes a single environment variable in config."""
        config_file = tmp_path / "mcp_config.json"
        config_data = {
            "mcpServers": {
                "test": {
                    "command": "npx",
                    "env": {"API_KEY": "${TEST_API_KEY}"},
                }
            }
        }
        config_file.write_text(json.dumps(config_data))

        with patch.dict("os.environ", {"TEST_API_KEY": "secret-key-123"}):
            result = load_mcp_config_with_env(str(config_file))

        assert result["mcpServers"]["test"]["env"]["API_KEY"] == "secret-key-123"

    def test_substitutes_multiple_env_variables(self, tmp_path: Any) -> None:
        """Substitutes multiple environment variables in config."""
        config_file = tmp_path / "mcp_config.json"
        config_data = {
            "mcpServers": {
                "test": {
                    "command": "npx",
                    "env": {
                        "API_KEY": "${TEST_API_KEY}",
                        "SECRET": "${TEST_SECRET}",
                    },
                }
            }
        }
        config_file.write_text(json.dumps(config_data))

        with patch.dict("os.environ", {"TEST_API_KEY": "key-123", "TEST_SECRET": "secret-456"}):
            result = load_mcp_config_with_env(str(config_file))

        assert result["mcpServers"]["test"]["env"]["API_KEY"] == "key-123"
        assert result["mcpServers"]["test"]["env"]["SECRET"] == "secret-456"

    def test_replaces_unset_env_var_with_empty_string(
        self, tmp_path: Any, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Replaces unset environment variables with empty string and prints warning."""
        config_file = tmp_path / "mcp_config.json"
        config_data = {
            "mcpServers": {
                "test": {
                    "command": "npx",
                    "env": {"MISSING_VAR": "${UNSET_VARIABLE}"},
                }
            }
        }
        config_file.write_text(json.dumps(config_data))

        with patch.dict("os.environ", {}, clear=True):
            result = load_mcp_config_with_env(str(config_file))

        assert result["mcpServers"]["test"]["env"]["MISSING_VAR"] == ""
        captured = capsys.readouterr()
        assert "UNSET_VARIABLE is not set" in captured.out

    def test_preserves_non_env_var_values(self, tmp_path: Any) -> None:
        """Preserves values that are not environment variable placeholders."""
        config_file = tmp_path / "mcp_config.json"
        config_data = {
            "mcpServers": {
                "test": {
                    "command": "npx",
                    "args": ["-y", "test-package"],
                    "cwd": "/path/to/dir",
                }
            }
        }
        config_file.write_text(json.dumps(config_data))

        result = load_mcp_config_with_env(str(config_file))

        assert result["mcpServers"]["test"]["command"] == "npx"
        assert result["mcpServers"]["test"]["args"] == ["-y", "test-package"]
        assert result["mcpServers"]["test"]["cwd"] == "/path/to/dir"

    def test_raises_file_not_found_for_missing_file(self) -> None:
        """Raises FileNotFoundError when config file does not exist."""
        with pytest.raises(FileNotFoundError):
            load_mcp_config_with_env("/nonexistent/path/config.json")

    def test_raises_json_decode_error_for_invalid_json(self, tmp_path: Any) -> None:
        """Raises JSONDecodeError when config file contains invalid JSON."""
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text("not valid json {")

        with pytest.raises(json.JSONDecodeError):
            load_mcp_config_with_env(str(config_file))

    def test_handles_env_var_in_args_list(self, tmp_path: Any) -> None:
        """Substitutes environment variables in args array."""
        config_file = tmp_path / "mcp_config.json"
        config_data = {
            "mcpServers": {
                "test": {
                    "command": "python",
                    "args": ["-m", "${MODULE_NAME}"],
                }
            }
        }
        config_file.write_text(json.dumps(config_data))

        with patch.dict("os.environ", {"MODULE_NAME": "my_module"}):
            result = load_mcp_config_with_env(str(config_file))

        assert result["mcpServers"]["test"]["args"] == ["-m", "my_module"]


class TestCreateMcpToolsets:
    """Tests for the create_mcp_toolsets function."""

    @patch("src.mcp.loader.MCPServerStdio")
    def test_creates_toolset_for_each_server(
        self, mock_mcp_server: MagicMock, sample_mcp_config: dict[str, Any]
    ) -> None:
        """Creates an MCPServerStdio instance for each server in config."""
        result = create_mcp_toolsets(sample_mcp_config)

        expected_server_count = len(sample_mcp_config["mcpServers"])
        assert len(result) == expected_server_count
        assert mock_mcp_server.call_count == expected_server_count

    @patch("src.mcp.loader.MCPServerStdio")
    def test_passes_correct_command_and_args(
        self, mock_mcp_server: MagicMock, sample_mcp_config: dict[str, Any]
    ) -> None:
        """Passes correct command and args to MCPServerStdio."""
        create_mcp_toolsets(sample_mcp_config)

        calls = mock_mcp_server.call_args_list
        call_commands = [call[0][0] for call in calls]
        assert "npx" in call_commands
        assert "python" in call_commands

    @patch("src.mcp.loader.MCPServerStdio")
    def test_passes_env_and_cwd_when_present(
        self, mock_mcp_server: MagicMock, sample_mcp_config: dict[str, Any]
    ) -> None:
        """Passes env and cwd parameters when present in config."""
        create_mcp_toolsets(sample_mcp_config)

        calls = mock_mcp_server.call_args_list

        google_call = next(c for c in calls if c.kwargs.get("tool_prefix") == "google_calendar")
        assert google_call.kwargs["env"] == {"API_KEY": "test-key"}

        dish_call = next(c for c in calls if c.kwargs.get("tool_prefix") == "dish_mcp")
        assert dish_call.kwargs["cwd"] == "/path/to/dish"

    @patch("src.mcp.loader.MCPServerStdio")
    def test_converts_hyphen_to_underscore_in_tool_prefix(
        self, mock_mcp_server: MagicMock, sample_mcp_config: dict[str, Any]
    ) -> None:
        """Converts hyphens to underscores in tool_prefix for valid Python identifiers."""
        create_mcp_toolsets(sample_mcp_config)

        calls = mock_mcp_server.call_args_list
        tool_prefixes = [call.kwargs["tool_prefix"] for call in calls]

        assert "google_calendar" in tool_prefixes
        assert "dish_mcp" in tool_prefixes
        assert "google-calendar" not in tool_prefixes

    @patch("src.mcp.loader.MCPServerStdio")
    def test_returns_empty_list_for_empty_config(
        self, mock_mcp_server: MagicMock, empty_mcp_config: dict[str, Any]
    ) -> None:
        """Returns empty list when config has no servers."""
        result = create_mcp_toolsets(empty_mcp_config)

        assert result == []
        mock_mcp_server.assert_not_called()

    @patch("src.mcp.loader.MCPServerStdio")
    def test_passes_tool_processor_when_provided(
        self, mock_mcp_server: MagicMock, sample_mcp_config: dict[str, Any]
    ) -> None:
        """Passes process_tool_call callback when provided for server."""
        mock_processor = AsyncMock()
        tool_processors: dict[str, ProcessToolCallFunc] = {
            "google-calendar": cast(ProcessToolCallFunc, mock_processor)
        }

        create_mcp_toolsets(sample_mcp_config, tool_processors)

        calls = mock_mcp_server.call_args_list
        google_call = next(c for c in calls if c.kwargs.get("tool_prefix") == "google_calendar")
        assert google_call.kwargs["process_tool_call"] == mock_processor

    @patch("src.mcp.loader.MCPServerStdio")
    def test_passes_none_processor_when_not_provided(
        self, mock_mcp_server: MagicMock, sample_mcp_config: dict[str, Any]
    ) -> None:
        """Passes None for process_tool_call when no processor provided for server."""
        create_mcp_toolsets(sample_mcp_config)

        calls = mock_mcp_server.call_args_list
        for call in calls:
            assert call.kwargs["process_tool_call"] is None

    @patch("src.mcp.loader.MCPServerStdio")
    def test_defaults_args_to_empty_list(self, mock_mcp_server: MagicMock) -> None:
        """Defaults args to empty list when not specified in config."""
        config = {"mcpServers": {"test": {"command": "npx"}}}

        create_mcp_toolsets(config)

        call = mock_mcp_server.call_args_list[0]
        assert call[0][1] == []


class TestLoadMcpServersWithEnv:
    """Tests for the load_mcp_servers_with_env function."""

    @patch("src.mcp.loader.create_mcp_toolsets")
    @patch("src.mcp.loader.load_mcp_config_with_env")
    def test_combines_load_and_create(
        self,
        mock_load_config: MagicMock,
        mock_create_toolsets: MagicMock,
    ) -> None:
        """Combines load_mcp_config_with_env and create_mcp_toolsets."""
        mock_config = {"mcpServers": {"test": {"command": "npx"}}}
        mock_load_config.return_value = mock_config
        mock_toolsets = [MagicMock()]
        mock_create_toolsets.return_value = mock_toolsets

        result = load_mcp_servers_with_env("/path/to/config.json")

        mock_load_config.assert_called_once_with("/path/to/config.json")
        mock_create_toolsets.assert_called_once_with(mock_config, None)
        assert result == mock_toolsets

    @patch("src.mcp.loader.create_mcp_toolsets")
    @patch("src.mcp.loader.load_mcp_config_with_env")
    def test_passes_tool_processors_to_create_toolsets(
        self,
        mock_load_config: MagicMock,
        mock_create_toolsets: MagicMock,
    ) -> None:
        """Passes tool_processors argument to create_mcp_toolsets."""
        mock_load_config.return_value = {"mcpServers": {}}
        mock_processor = AsyncMock()
        tool_processors: dict[str, ProcessToolCallFunc] = {
            "test-server": cast(ProcessToolCallFunc, mock_processor)
        }

        load_mcp_servers_with_env("/path/to/config.json", tool_processors)

        mock_create_toolsets.assert_called_once_with({"mcpServers": {}}, tool_processors)

    def test_integration_with_real_file(self, tmp_path: Any) -> None:
        """Integration test with real file and mocked MCPServerStdio."""
        config_file = tmp_path / "mcp_config.json"
        config_data = {
            "mcpServers": {
                "test-server": {
                    "command": "npx",
                    "args": ["-y", "test-package"],
                    "env": {"KEY": "${TEST_KEY}"},
                }
            }
        }
        config_file.write_text(json.dumps(config_data))

        with (
            patch.dict("os.environ", {"TEST_KEY": "test-value"}),
            patch("src.mcp.loader.MCPServerStdio") as mock_mcp_server,
        ):
            mock_mcp_server.return_value = MagicMock()
            result = load_mcp_servers_with_env(str(config_file))

        assert len(result) == 1
        call = mock_mcp_server.call_args
        assert call[0][0] == "npx"
        assert call[0][1] == ["-y", "test-package"]
        assert call.kwargs["env"] == {"KEY": "test-value"}
        assert call.kwargs["tool_prefix"] == "test_server"
