"""Tests for MCP tool call formatting utilities."""

from src.mcp.formatting import (
    _describe_dish,
    _describe_google_calendar,
    _format_date_range,
    _format_event_summary,
    _format_room_name,
    describe_tool_call,
)


class TestFormatDateRange:
    """Tests for the _format_date_range function."""

    def test_returns_none_when_no_time_min(self) -> None:
        """Returns None when timeMin and start_datetime are missing."""
        result = _format_date_range({})
        assert result is None

    def test_returns_none_when_time_min_is_none(self) -> None:
        """Returns None when timeMin is explicitly None."""
        result = _format_date_range({"timeMin": None})
        assert result is None

    def test_formats_single_date_without_time_max(self) -> None:
        """Formats a single date when only timeMin is provided."""
        result = _format_date_range({"timeMin": "2025-01-15T10:00:00Z"})
        assert result == "Wed 15 Jan"

    def test_formats_same_day_range_with_times(self) -> None:
        """Formats a same-day range showing times."""
        result = _format_date_range(
            {
                "timeMin": "2025-01-15T10:00:00Z",
                "timeMax": "2025-01-15T11:30:00Z",
            }
        )
        assert result == "Wed 15 Jan, 10:00–11:30"

    def test_formats_multi_day_range(self) -> None:
        """Formats a range spanning multiple days."""
        result = _format_date_range(
            {
                "timeMin": "2025-01-15T10:00:00Z",
                "timeMax": "2025-01-20T11:30:00Z",
            }
        )
        assert result == "Wed 15 Jan to Mon 20 Jan"

    def test_handles_dish_datetime_format(self) -> None:
        """Handles DiSH-style start_datetime and end_datetime keys."""
        result = _format_date_range(
            {
                "start_datetime": "2025-01-15T10:00:00",
                "end_datetime": "2025-01-15T11:30:00",
            }
        )
        assert result == "Wed 15 Jan, 10:00–11:30"

    def test_prefers_time_min_over_start_datetime(self) -> None:
        """Uses timeMin when both timeMin and start_datetime are present."""
        result = _format_date_range(
            {
                "timeMin": "2025-01-15T10:00:00Z",
                "start_datetime": "2025-02-20T14:00:00",
                "timeMax": "2025-01-15T11:00:00Z",
            }
        )
        assert result is not None
        assert "Jan" in result

    def test_handles_timezone_offset(self) -> None:
        """Handles datetime strings with timezone offsets."""
        result = _format_date_range(
            {
                "timeMin": "2025-01-15T10:00:00+00:00",
                "timeMax": "2025-01-15T11:30:00+00:00",
            }
        )
        assert result == "Wed 15 Jan, 10:00–11:30"

    def test_returns_none_for_invalid_datetime(self) -> None:
        """Returns None when datetime parsing fails."""
        result = _format_date_range({"timeMin": "not-a-date"})
        assert result is None

    def test_returns_none_for_non_string_time_min(self) -> None:
        """Returns None when timeMin is not a string."""
        result = _format_date_range({"timeMin": 12345})
        assert result is None


class TestFormatRoomName:
    """Tests for the _format_room_name function."""

    def test_extracts_meeting_room_name(self) -> None:
        """Extracts room name from meeting_room_name key."""
        result = _format_room_name({"meeting_room_name": "Conference Room A"})
        assert result == "Conference Room A"

    def test_extracts_room_name(self) -> None:
        """Extracts room name from room_name key."""
        result = _format_room_name({"room_name": "Meeting Room B"})
        assert result == "Meeting Room B"

    def test_prefers_meeting_room_name_over_room_name(self) -> None:
        """Uses meeting_room_name when both keys are present."""
        result = _format_room_name(
            {
                "meeting_room_name": "Primary Room",
                "room_name": "Secondary Room",
            }
        )
        assert result == "Primary Room"

    def test_returns_none_when_no_room_name(self) -> None:
        """Returns None when no room name keys are present."""
        result = _format_room_name({"other_arg": "value"})
        assert result is None

    def test_returns_none_for_empty_room_name(self) -> None:
        """Returns None when room name is empty string."""
        result = _format_room_name({"meeting_room_name": ""})
        assert result is None

    def test_returns_none_for_none_room_name(self) -> None:
        """Returns None when room name is None."""
        result = _format_room_name({"meeting_room_name": None})
        assert result is None


class TestFormatEventSummary:
    """Tests for the _format_event_summary function."""

    def test_extracts_summary(self) -> None:
        """Extracts event summary from summary key."""
        result = _format_event_summary({"summary": "Team Meeting"})
        assert result == "Team Meeting"

    def test_extracts_title(self) -> None:
        """Extracts event summary from title key."""
        result = _format_event_summary({"title": "Project Review"})
        assert result == "Project Review"

    def test_prefers_summary_over_title(self) -> None:
        """Uses summary when both summary and title are present."""
        result = _format_event_summary(
            {
                "summary": "Primary Title",
                "title": "Secondary Title",
            }
        )
        assert result == "Primary Title"

    def test_returns_none_when_no_summary(self) -> None:
        """Returns None when no summary keys are present."""
        result = _format_event_summary({"other_arg": "value"})
        assert result is None

    def test_returns_none_for_empty_summary(self) -> None:
        """Returns None for empty summary string."""
        result = _format_event_summary({"summary": ""})
        assert result is None


class TestDescribeGoogleCalendar:
    """Tests for the _describe_google_calendar function."""

    def test_simple_action_get_event(self) -> None:
        """Returns predefined description for get-event action."""
        result = _describe_google_calendar("get-event", {})
        assert result == "Looking up event details"

    def test_simple_action_delete_event(self) -> None:
        """Returns predefined description for delete-event action."""
        result = _describe_google_calendar("delete-event", {})
        assert result == "Removing calendar event"

    def test_simple_action_list_calendars(self) -> None:
        """Returns predefined description for list-calendars action."""
        result = _describe_google_calendar("list-calendars", {})
        assert result == "Fetching your calendars"

    def test_list_events_with_date_info(self) -> None:
        """Describes list-events with date range information."""
        result = _describe_google_calendar(
            "list-events",
            {
                "timeMin": "2025-01-15T10:00:00Z",
                "timeMax": "2025-01-15T18:00:00Z",
            },
        )
        assert result == "Checking your calendar for Wed 15 Jan, 10:00–18:00"

    def test_list_events_without_date_info(self) -> None:
        """Falls back to generic description when no date info."""
        result = _describe_google_calendar("list-events", {})
        assert result == "Checking your calendar"

    def test_create_event_with_summary_and_date(self) -> None:
        """Describes create-event with event summary and date."""
        result = _describe_google_calendar(
            "create-event",
            {
                "summary": "Team Meeting",
                "timeMin": "2025-01-15T10:00:00Z",
                "timeMax": "2025-01-15T11:00:00Z",
            },
        )
        assert result == "Creating 'Team Meeting' on Wed 15 Jan, 10:00–11:00"

    def test_create_event_with_summary_only(self) -> None:
        """Describes create-event with only event summary."""
        result = _describe_google_calendar("create-event", {"summary": "Team Meeting"})
        assert result == "Creating 'Team Meeting'"

    def test_create_event_without_context(self) -> None:
        """Falls back to generic description when no context available."""
        result = _describe_google_calendar("create-event", {})
        assert result == "Creating a new calendar event"

    def test_update_event_with_summary(self) -> None:
        """Describes update-event with event summary."""
        result = _describe_google_calendar("update-event", {"summary": "Updated Meeting"})
        assert result == "Updating 'Updated Meeting'"

    def test_update_event_without_summary(self) -> None:
        """Falls back to generic description when no summary."""
        result = _describe_google_calendar("update-event", {})
        assert result == "Updating calendar event"

    def test_unknown_action_generic_fallback(self) -> None:
        """Uses generic fallback for unknown actions."""
        result = _describe_google_calendar("some-new-action", {})
        assert result == "Accessing Google Calendar (some new action)"


class TestDescribeDish:
    """Tests for the _describe_dish function."""

    def test_cancel_booking_action(self) -> None:
        """Returns predefined description for cancel_booking action."""
        result = _describe_dish("cancel_booking", {})
        assert result == "Cancelling room booking"

    def test_check_availability_with_date_info(self) -> None:
        """Describes check availability with date range."""
        result = _describe_dish(
            "check_availability_and_list_bookings",
            {
                "start_datetime": "2025-01-15T10:00:00",
                "end_datetime": "2025-01-15T18:00:00",
            },
        )
        assert result == "Checking room availability for Wed 15 Jan, 10:00–18:00"

    def test_check_availability_without_date_info(self) -> None:
        """Falls back to generic description when no date info."""
        result = _describe_dish("check_availability_and_list_bookings", {})
        assert result == "Checking room availability"

    def test_book_room_with_room_name_and_date(self) -> None:
        """Describes book_room with room name and date."""
        result = _describe_dish(
            "book_room",
            {
                "meeting_room_name": "Conference Room A",
                "start_datetime": "2025-01-15T10:00:00",
                "end_datetime": "2025-01-15T11:00:00",
            },
        )
        assert result == "Booking Conference Room A for Wed 15 Jan, 10:00–11:00"

    def test_book_room_with_room_name_only(self) -> None:
        """Describes book_room with only room name."""
        result = _describe_dish("book_room", {"meeting_room_name": "Conference Room A"})
        assert result == "Booking Conference Room A"

    def test_book_room_with_date_only(self) -> None:
        """Describes book_room with only date info."""
        result = _describe_dish(
            "book_room",
            {
                "start_datetime": "2025-01-15T10:00:00",
                "end_datetime": "2025-01-15T11:00:00",
            },
        )
        assert result == "Booking a meeting room for Wed 15 Jan, 10:00–11:00"

    def test_book_room_without_context(self) -> None:
        """Falls back to generic description when no context."""
        result = _describe_dish("book_room", {})
        assert result == "Booking a meeting room"

    def test_unknown_action_generic_fallback(self) -> None:
        """Uses generic fallback for unknown actions."""
        result = _describe_dish("some_new_action", {})
        assert result == "Accessing room bookings (some new action)"


class TestDescribeToolCall:
    """Tests for the describe_tool_call function."""

    def test_routes_google_calendar_tools(self) -> None:
        """Routes google_calendar_ prefixed tools to Google Calendar handler."""
        result = describe_tool_call(
            "google_calendar_list-events",
            {
                "timeMin": "2025-01-15T10:00:00Z",
            },
        )
        assert "calendar" in result.lower()

    def test_routes_dish_mcp_tools(self) -> None:
        """Routes dish_mcp_ prefixed tools to DiSH handler."""
        result = describe_tool_call(
            "dish_mcp_book_room",
            {
                "meeting_room_name": "Room A",
            },
        )
        assert "Booking Room A" in result

    def test_generic_fallback_for_unknown_tools(self) -> None:
        """Uses generic fallback for unknown tool prefixes."""
        result = describe_tool_call("some_unknown_tool", {})
        assert result == "Processing: some unknown tool"

    def test_generic_fallback_replaces_underscores(self) -> None:
        """Replaces underscores with spaces in generic fallback."""
        result = describe_tool_call("my_custom_tool_action", {})
        assert result == "Processing: my custom tool action"

    def test_generic_fallback_replaces_hyphens(self) -> None:
        """Replaces hyphens with spaces in generic fallback."""
        result = describe_tool_call("my-custom-tool-action", {})
        assert result == "Processing: my custom tool action"

    def test_google_calendar_strips_prefix(self) -> None:
        """Strips google_calendar_ prefix when routing."""
        result = describe_tool_call("google_calendar_list-calendars", {})
        assert result == "Fetching your calendars"

    def test_dish_mcp_strips_prefix(self) -> None:
        """Strips dish_mcp_ prefix when routing."""
        result = describe_tool_call("dish_mcp_cancel_booking", {})
        assert result == "Cancelling room booking"

    def test_google_calendar_get_event_description(self) -> None:
        """Tests google_calendar_get-event returns correct description."""
        result = describe_tool_call("google_calendar_get-event", {})
        assert "Looking up event details" in result

    def test_google_calendar_delete_event_description(self) -> None:
        """Tests google_calendar_delete-event returns correct description."""
        result = describe_tool_call("google_calendar_delete-event", {})
        assert "Removing calendar event" in result

    def test_dish_mcp_cancel_booking_description(self) -> None:
        """Tests dish_mcp_cancel_booking returns correct description."""
        result = describe_tool_call("dish_mcp_cancel_booking", {})
        assert "Cancelling" in result

    def test_dish_mcp_check_availability_description(self) -> None:
        """Tests dish_mcp_check_availability_and_list_bookings returns correct description."""
        result = describe_tool_call("dish_mcp_check_availability_and_list_bookings", {})
        assert "availability" in result
