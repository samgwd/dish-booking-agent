"""Tests for MCP tool call hooks."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

from src.agent.hooks import inject_dish_credentials, inject_google_calendar_credentials
from src.agent.types import AgentDeps, DishCredentials, GoogleCalendarTokens


class TestInjectDishCredentials:
    """Tests for the inject_dish_credentials hook."""

    async def test_injects_cookie_when_dish_credentials_present(
        self,
        dish_credentials: DishCredentials,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that cookie is injected when DiSH credentials are present."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(dish=dish_credentials)
        tool_args: dict[str, Any] = {"some_arg": "value"}

        await inject_dish_credentials(ctx, mock_call_tool, "some_tool", tool_args)

        assert tool_args["cookie"] == "test-cookie-value"
        mock_call_tool.assert_called_once_with("some_tool", tool_args, {})

    async def test_injects_user_info_for_book_room_tool(
        self,
        dish_credentials: DishCredentials,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that user_info is injected for book_room tool."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(dish=dish_credentials)
        tool_args: dict[str, Any] = {"meeting_room_name": "Room A"}

        await inject_dish_credentials(ctx, mock_call_tool, "dish_mcp_book_room", tool_args)

        assert tool_args["cookie"] == "test-cookie-value"
        assert tool_args["user_info"] == {
            "team_id": "test-team-123",
            "member_id": "test-member-456",
        }
        mock_call_tool.assert_called_once()

    async def test_does_not_inject_user_info_for_other_tools(
        self,
        dish_credentials: DishCredentials,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that user_info is not injected for non-book_room tools."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(dish=dish_credentials)
        tool_args: dict[str, Any] = {}

        await inject_dish_credentials(ctx, mock_call_tool, "check_availability", tool_args)

        assert tool_args["cookie"] == "test-cookie-value"
        assert "user_info" not in tool_args

    async def test_no_injection_when_deps_is_none(
        self,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that nothing is injected when deps is None."""
        ctx = MagicMock()
        ctx.deps = None
        tool_args: dict[str, Any] = {"existing": "value"}

        await inject_dish_credentials(ctx, mock_call_tool, "some_tool", tool_args)

        assert "cookie" not in tool_args
        assert tool_args == {"existing": "value"}
        mock_call_tool.assert_called_once()

    async def test_no_injection_when_dish_is_none(
        self,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that nothing is injected when dish credentials are None."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(dish=None)
        tool_args: dict[str, Any] = {}

        await inject_dish_credentials(ctx, mock_call_tool, "some_tool", tool_args)

        assert "cookie" not in tool_args
        mock_call_tool.assert_called_once()

    async def test_preserves_existing_tool_args(
        self,
        dish_credentials: DishCredentials,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that existing tool args are preserved."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(dish=dish_credentials)
        tool_args: dict[str, Any] = {
            "datetime_range": {"start": "2025-01-01", "end": "2025-01-02"},
            "summary": "Test meeting",
        }

        await inject_dish_credentials(ctx, mock_call_tool, "some_tool", tool_args)

        assert tool_args["datetime_range"] == {
            "start": "2025-01-01",
            "end": "2025-01-02",
        }
        assert tool_args["summary"] == "Test meeting"
        assert tool_args["cookie"] == "test-cookie-value"

    async def test_returns_call_tool_result(
        self,
        dish_credentials: DishCredentials,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that the result from call_tool is returned."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(dish=dish_credentials)
        tool_args: dict[str, Any] = {}
        expected_result = {"bookings": [], "status": "success"}
        mock_call_tool.return_value = expected_result

        result = await inject_dish_credentials(ctx, mock_call_tool, "some_tool", tool_args)

        assert result == expected_result


class TestInjectGoogleCalendarCredentials:
    """Tests for the inject_google_calendar_credentials hook."""

    async def test_injects_oauth_credentials_when_present(
        self,
        google_calendar_tokens: GoogleCalendarTokens,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that OAuth credentials are injected when present."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(google_calendar=google_calendar_tokens)
        tool_args: dict[str, Any] = {"calendarId": "primary"}

        await inject_google_calendar_credentials(ctx, mock_call_tool, "list-events", tool_args)

        assert tool_args["oauth_credentials"] == {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expiry_date": 1735689600000,
        }
        mock_call_tool.assert_called_once_with("list-events", tool_args, {})

    async def test_no_injection_when_deps_is_none(
        self,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that nothing is injected when deps is None."""
        ctx = MagicMock()
        ctx.deps = None
        tool_args: dict[str, Any] = {"calendarId": "primary"}

        await inject_google_calendar_credentials(ctx, mock_call_tool, "list-events", tool_args)

        assert "oauth_credentials" not in tool_args
        mock_call_tool.assert_called_once()

    async def test_no_injection_when_google_calendar_is_none(
        self,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that nothing is injected when google_calendar is None."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(google_calendar=None)
        tool_args: dict[str, Any] = {}

        await inject_google_calendar_credentials(ctx, mock_call_tool, "list-events", tool_args)

        assert "oauth_credentials" not in tool_args
        mock_call_tool.assert_called_once()

    async def test_preserves_existing_tool_args(
        self,
        google_calendar_tokens: GoogleCalendarTokens,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that existing tool args are preserved."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(google_calendar=google_calendar_tokens)
        tool_args: dict[str, Any] = {
            "calendarId": "primary",
            "timeMin": "2025-01-01T00:00:00Z",
            "timeMax": "2025-01-31T23:59:59Z",
        }

        await inject_google_calendar_credentials(ctx, mock_call_tool, "list-events", tool_args)

        assert tool_args["calendarId"] == "primary"
        assert tool_args["timeMin"] == "2025-01-01T00:00:00Z"
        assert tool_args["timeMax"] == "2025-01-31T23:59:59Z"
        assert "oauth_credentials" in tool_args

    async def test_returns_call_tool_result(
        self,
        google_calendar_tokens: GoogleCalendarTokens,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that the result from call_tool is returned."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(google_calendar=google_calendar_tokens)
        tool_args: dict[str, Any] = {}
        expected_result = {"events": [{"summary": "Meeting"}]}
        mock_call_tool.return_value = expected_result

        result = await inject_google_calendar_credentials(
            ctx, mock_call_tool, "list-events", tool_args
        )

        assert result == expected_result

    async def test_works_for_any_tool_name(
        self,
        google_calendar_tokens: GoogleCalendarTokens,
        mock_call_tool: AsyncMock,
    ) -> None:
        """Test that credentials are injected regardless of tool name."""
        ctx = MagicMock()
        ctx.deps = AgentDeps(google_calendar=google_calendar_tokens)

        tool_names = [
            "list-events",
            "create-event",
            "delete-event",
            "get-freebusy",
            "update-event",
        ]

        for tool_name in tool_names:
            tool_args: dict[str, Any] = {}
            mock_call_tool.reset_mock()

            await inject_google_calendar_credentials(ctx, mock_call_tool, tool_name, tool_args)

            assert "oauth_credentials" in tool_args
            mock_call_tool.assert_called_once()
