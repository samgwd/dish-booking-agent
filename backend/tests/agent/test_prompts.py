"""Tests for agent prompts."""

from datetime import datetime

from src.agent.prompts import SYSTEM_PROMPT


class TestSystemPrompt:
    """Tests for the SYSTEM_PROMPT constant."""

    def test_prompt_is_non_empty_string(self) -> None:
        """Test that SYSTEM_PROMPT is a non-empty string."""
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 0

    def test_prompt_contains_date_placeholder(self) -> None:
        """Test that SYSTEM_PROMPT contains the date placeholder."""
        assert "{date}" in SYSTEM_PROMPT

    def test_prompt_can_be_formatted_with_date(self) -> None:
        """Test that the prompt can be formatted with a date."""
        test_date = "2025-01-15"

        formatted = SYSTEM_PROMPT.format(date=test_date)

        assert test_date in formatted
        assert "{date}" not in formatted

    def test_prompt_mentions_dish_mcp(self) -> None:
        """Test that the prompt mentions Dish MCP for room bookings."""
        assert "Dish" in SYSTEM_PROMPT or "room" in SYSTEM_PROMPT.lower()

    def test_prompt_mentions_google_calendar(self) -> None:
        """Test that the prompt mentions Google Calendar."""
        assert "Google Calendar" in SYSTEM_PROMPT

    def test_prompt_mentions_calendar_as_source_of_truth(self) -> None:
        """Test that the prompt identifies Google Calendar as source of truth."""
        assert "source of truth" in SYSTEM_PROMPT.lower()

    def test_prompt_formatted_with_current_date(self) -> None:
        """Test formatting prompt with the current date format used in core.py."""
        current_date = datetime.now().strftime("%Y-%m-%d")

        formatted = SYSTEM_PROMPT.format(date=current_date)

        assert current_date in formatted
        assert f"Today's date is {current_date}" in formatted

    def test_prompt_mentions_room_availability(self) -> None:
        """Test that the prompt mentions room availability checking."""
        assert "availability" in SYSTEM_PROMPT.lower()

    def test_prompt_mentions_booking(self) -> None:
        """Test that the prompt mentions booking functionality."""
        assert "booking" in SYSTEM_PROMPT.lower()
