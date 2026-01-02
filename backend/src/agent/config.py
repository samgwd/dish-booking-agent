"""Agent configuration settings."""

from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseSettings):
    """Configuration settings for the agent.

    Settings are loaded from a YAML file (default: backend/agent_config.yaml).
    Environment variable overrides are disabled - configuration must come from the YAML file.
    """

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding=None,
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
    )

    model_name: str = Field(
        default="openai:gpt-5-mini",
        description="The model identifier to use for the agent (e.g., 'openai:gpt-5-mini')",
    )

    mcp_config_path: str | Path = Field(
        default="backend/mcp_config.json",
        description="Path to the MCP configuration file (relative to project root or absolute)",
    )

    def get_mcp_config_path(self, project_root: Path) -> Path:
        """Resolve the MCP config path relative to project root if needed.

        Args:
            project_root: The project root directory.

        Returns:
            The resolved absolute path to the MCP config file.
        """
        config_path = Path(self.mcp_config_path)
        if config_path.is_absolute():
            return config_path
        return project_root / config_path


def load_config(config_path: Path | None = None) -> AgentConfig:
    """Load agent configuration from YAML file.

    Args:
        config_path: Optional path to the config YAML file. If not provided,
            defaults to backend/agent_config.yaml relative to project root.

    Returns:
        The loaded AgentConfig instance.
    """
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    if config_path is None:
        config_path = project_root / "backend" / "agent_config.yaml"

    config_path = Path(config_path)
    if not config_path.is_absolute():
        config_path = project_root / config_path

    if config_path.exists():
        with open(config_path) as f:
            yaml_data = yaml.safe_load(f) or {}
    else:
        yaml_data = {}

    return AgentConfig(**yaml_data)


config = load_config()
