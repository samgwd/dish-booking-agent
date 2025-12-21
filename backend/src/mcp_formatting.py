"""Helpers for formatting MCP tool usage and arguments."""

from datetime import datetime
from typing import Any


def _format_date_range(args: dict[str, Any]) -> str | None:
    """Extract and format a human-readable date range from args.

    Args:
        args: The arguments passed to the tool.

    Returns:
        A human-readable date range.
    """
    time_min = args.get("timeMin") or args.get("start_datetime")
    time_max = args.get("timeMax") or args.get("end_datetime")

    if not time_min:
        return None

    try:
        start = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
        start_str = start.strftime("%a %d %b")

        if time_max:
            end = datetime.fromisoformat(time_max.replace("Z", "+00:00"))
            if start.date() == end.date():
                return f"{start_str}, {start.strftime('%H:%M')}–{end.strftime('%H:%M')}"
            else:
                return f"{start_str} to {end.strftime('%a %d %b')}"
        return start_str
    except (ValueError, AttributeError):
        return None


def _format_room_name(args: dict[str, Any]) -> str | None:
    """Extract room name from args.

    Args:
        args: The arguments passed to the tool.

    Returns:
        A human-readable room name.
    """
    room = args.get("meeting_room_name") or args.get("room_name")
    return room if room else None


def _format_event_summary(args: dict[str, Any]) -> str | None:
    """Extract event summary/title from args.

    Args:
        args: The arguments passed to the tool.

    Returns:
        A human-readable event summary.
    """
    return args.get("summary") or args.get("title")


_GCAL_SIMPLE_ACTIONS: dict[str, str] = {
    "get-event": "Looking up event details",
    "delete-event": "Removing calendar event",
    "list-calendars": "Fetching your calendars",
}


def _describe_google_calendar(action: str, args: dict[str, Any]) -> str:
    """Create a friendly description for Google Calendar actions.

    Args:
        action: The action being performed.
        args: The arguments passed to the tool.

    Returns:
        A human-readable description of the action.
    """
    if action in _GCAL_SIMPLE_ACTIONS:
        return _GCAL_SIMPLE_ACTIONS[action]

    date_info = _format_date_range(args)
    event_summary = _format_event_summary(args)

    descriptions: dict[str, tuple[str, str]] = {
        "list-events": (f"Checking your calendar for {date_info}", "Checking your calendar"),
        "create-event": (
            f"Creating '{event_summary}'" + (f" on {date_info}" if date_info else ""),
            "Creating a new calendar event",
        ),
        "update-event": (f"Updating '{event_summary}'", "Updating calendar event"),
    }

    if action in descriptions:
        with_context, fallback = descriptions[action]
        return with_context if (event_summary or date_info) else fallback

    return f"Accessing Google Calendar ({action.replace('-', ' ')})"


def _describe_dish(action: str, args: dict[str, Any]) -> str:
    """Create a friendly description for DiSH room booking actions.

    Args:
        action: The action being performed.
        args: The arguments passed to the tool.

    Returns:
        A human-readable description of the action.
    """
    if action == "cancel_booking":
        return "Cancelling room booking"

    date_info = _format_date_range(args)
    room_name = _format_room_name(args)

    if action == "check_availability_and_list_bookings":
        base = "Checking room availability"
        return f"{base} for {date_info}" if date_info else base

    if action == "book_room":
        base = room_name or "a meeting room"
        return f"Booking {base} for {date_info}" if date_info else f"Booking {base}"

    return f"Accessing room bookings ({action.replace('_', ' ')})"


def describe_tool_call(tool_name: str, args: dict[str, Any]) -> str:
    """Build a user-friendly description for a tool call.

    Args:
        tool_name: The name of the tool being called.
        args: The arguments passed to the tool.

    Returns:
        A friendly, human-readable description of what the tool is doing.
    """
    if tool_name.startswith("google_calendar_"):
        action = tool_name.replace("google_calendar_", "")
        return _describe_google_calendar(action, args)

    if tool_name.startswith("dish_mcp_"):
        action = tool_name.replace("dish_mcp_", "")
        return _describe_dish(action, args)

    # Generic fallback for unknown tools
    action_text = tool_name.replace("_", " ").replace("-", " ")
    return f"Processing: {action_text}"
