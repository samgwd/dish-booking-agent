"""Shared fixtures for agent package tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.agent.types import AgentDeps, DishCredentials, GoogleCalendarTokens

SAMPLE_EXPIRY_TIMESTAMP = 1735689600000


@pytest.fixture
def dish_credentials() -> DishCredentials:
    """Create sample DiSH credentials for testing."""
    return DishCredentials(
        cookie="test-cookie-value",
        team_id="test-team-123",
        member_id="test-member-456",
    )


@pytest.fixture
def google_calendar_tokens() -> GoogleCalendarTokens:
    """Create sample Google Calendar tokens for testing."""
    return GoogleCalendarTokens(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expiry_date=SAMPLE_EXPIRY_TIMESTAMP,
    )


@pytest.fixture
def agent_deps(
    dish_credentials: DishCredentials,
    google_calendar_tokens: GoogleCalendarTokens,
) -> AgentDeps:
    """Create AgentDeps with all credentials populated."""
    return AgentDeps(
        dish=dish_credentials,
        google_calendar=google_calendar_tokens,
    )


@pytest.fixture
def agent_deps_dish_only(dish_credentials: DishCredentials) -> AgentDeps:
    """Create AgentDeps with only DiSH credentials."""
    return AgentDeps(dish=dish_credentials)


@pytest.fixture
def agent_deps_google_only(google_calendar_tokens: GoogleCalendarTokens) -> AgentDeps:
    """Create AgentDeps with only Google Calendar tokens."""
    return AgentDeps(google_calendar=google_calendar_tokens)


@pytest.fixture
def agent_deps_empty() -> AgentDeps:
    """Create AgentDeps with no credentials."""
    return AgentDeps()


@pytest.fixture
def mock_run_context() -> MagicMock:
    """Create a mock RunContext for testing hooks."""
    return MagicMock()


@pytest.fixture
def mock_call_tool() -> AsyncMock:
    """Create a mock call_tool function for testing hooks."""
    mock = AsyncMock()
    mock.return_value = {"success": True}
    return mock
