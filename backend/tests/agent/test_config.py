"""Tests for agent configuration."""

from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import yaml
from src.agent.config import AgentConfig, load_config


class TestAgentConfig:
    """Tests for the AgentConfig class."""

    def test_default_model_name(self) -> None:
        """Test that model_name has correct default value."""
        config = AgentConfig()

        assert config.model_name == "openai:gpt-5-mini"

    def test_default_mcp_config_path(self) -> None:
        """Test that mcp_config_path has correct default value."""
        config = AgentConfig()

        assert config.mcp_config_path == "backend/mcp_config.json"

    def test_custom_model_name(self) -> None:
        """Test creating config with custom model name."""
        config = AgentConfig(model_name="anthropic:claude-3-opus")

        assert config.model_name == "anthropic:claude-3-opus"

    def test_custom_mcp_config_path(self) -> None:
        """Test creating config with custom MCP config path."""
        config = AgentConfig(mcp_config_path="/custom/path/mcp.json")

        assert config.mcp_config_path == "/custom/path/mcp.json"

    def test_extra_fields_are_ignored(self) -> None:
        """Test that extra fields are ignored (not raising errors)."""
        config = AgentConfig(
            model_name="test:model",
            unknown_field="should be ignored",  # type: ignore[call-arg]
        )

        assert config.model_name == "test:model"
        assert not hasattr(config, "unknown_field")


class TestAgentConfigGetMcpConfigPath:
    """Tests for AgentConfig.get_mcp_config_path method."""

    def test_absolute_path_returned_as_is(self) -> None:
        """Test that absolute paths are returned unchanged."""
        config = AgentConfig(mcp_config_path="/absolute/path/mcp.json")
        project_root = Path("/some/project")

        result = config.get_mcp_config_path(project_root)

        assert result == Path("/absolute/path/mcp.json")

    def test_relative_path_resolved_to_project_root(self) -> None:
        """Test that relative paths are resolved relative to project root."""
        config = AgentConfig(mcp_config_path="config/mcp.json")
        project_root = Path("/project/root")

        result = config.get_mcp_config_path(project_root)

        assert result == Path("/project/root/config/mcp.json")

    def test_default_path_resolved_correctly(self) -> None:
        """Test that default path is resolved correctly."""
        config = AgentConfig()
        project_root = Path("/my/project")

        result = config.get_mcp_config_path(project_root)

        assert result == Path("/my/project/backend/mcp_config.json")

    def test_path_object_input(self) -> None:
        """Test that Path objects are handled correctly."""
        config = AgentConfig(mcp_config_path=Path("relative/path.json"))
        project_root = Path("/root")

        result = config.get_mcp_config_path(project_root)

        assert result == Path("/root/relative/path.json")


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_from_yaml_file(self) -> None:
        """Test loading configuration from a YAML file."""
        config_data = {
            "model_name": "custom:model-v1",
            "mcp_config_path": "custom/path.json",
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)

            assert config.model_name == "custom:model-v1"
            assert config.mcp_config_path == "custom/path.json"
        finally:
            config_path.unlink()

    def test_load_from_empty_yaml_file(self) -> None:
        """Test loading from an empty YAML file uses defaults."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            config_path = Path(f.name)

        try:
            config = load_config(config_path)

            assert config.model_name == "openai:gpt-5-mini"
            assert config.mcp_config_path == "backend/mcp_config.json"
        finally:
            config_path.unlink()

    def test_load_from_nonexistent_file_uses_defaults(self) -> None:
        """Test that loading from a nonexistent file uses defaults."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.yaml"

            config = load_config(config_path)

            assert config.model_name == "openai:gpt-5-mini"
            assert config.mcp_config_path == "backend/mcp_config.json"

    def test_partial_yaml_uses_defaults_for_missing(self) -> None:
        """Test that partial YAML uses defaults for missing fields."""
        config_data = {"model_name": "only-model-specified"}

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)

            assert config.model_name == "only-model-specified"
            assert config.mcp_config_path == "backend/mcp_config.json"
        finally:
            config_path.unlink()

    def test_relative_config_path_resolved(self) -> None:
        """Test that relative config paths are resolved to project root."""
        with TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"
            config_dir.mkdir()
            config_path = config_dir / "test.yaml"

            config_data = {"model_name": "test:model"}
            with open(config_path, "w") as f:
                yaml.safe_dump(config_data, f)

            config = load_config(config_path)

            assert config.model_name == "test:model"
