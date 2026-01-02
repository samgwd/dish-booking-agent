"""Tests for streaming event processing."""

from typing import Any
from unittest.mock import MagicMock, patch

from pydantic_ai import AgentRunResultEvent
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    ModelMessage,
    PartStartEvent,
    TextPart,
    TextPartDelta,
)
from src.agent.streaming import (
    StreamingEvent,
    StreamState,
    handle_tool_call,
    process_event,
)

EXPECTED_PRINT_CALLS_WITH_PREFIX = 2
EXPECTED_HISTORY_LENGTH = 2


class TestStreamState:
    """Tests for the StreamState class."""

    def test_initial_state(self) -> None:
        """Test that StreamState initialises with correct defaults."""
        state = StreamState()

        assert state.text_started is False
        assert state.updated_history == []

    def test_emit_text_first_call_sets_text_started(self) -> None:
        """Test that first emit_text call sets text_started to True."""
        state = StreamState()

        with patch("builtins.print"):
            state.emit_text("Hello")

        assert state.text_started is True

    def test_emit_text_returns_streaming_event(self) -> None:
        """Test that emit_text returns correct streaming event tuple."""
        state = StreamState()

        with patch("builtins.print"):
            result = state.emit_text("Hello world")

        assert result == ("text", "Hello world", [])

    def test_emit_text_prints_prefix_on_first_call(self) -> None:
        """Test that 'Agent: ' prefix is printed on first text emission."""
        state = StreamState()

        with patch("builtins.print") as mock_print:
            state.emit_text("Test")

            assert mock_print.call_count == EXPECTED_PRINT_CALLS_WITH_PREFIX
            mock_print.assert_any_call("Agent: ", end="", flush=True)
            mock_print.assert_any_call("Test", end="", flush=True)

    def test_emit_text_no_prefix_on_subsequent_calls(self) -> None:
        """Test that prefix is not printed on subsequent text emissions."""
        state = StreamState()

        with patch("builtins.print"):
            state.emit_text("First")

        with patch("builtins.print") as mock_print:
            state.emit_text("Second")

            mock_print.assert_called_once_with("Second", end="", flush=True)

    def test_emit_text_with_empty_string(self) -> None:
        """Test emit_text with empty string."""
        state = StreamState()

        with patch("builtins.print"):
            result = state.emit_text("")

        assert result == ("text", "", [])


class TestHandleToolCall:
    """Tests for the handle_tool_call function."""

    def test_returns_tool_call_event(self) -> None:
        """Test that handle_tool_call returns a tool_call event tuple."""
        mock_event = MagicMock(spec=FunctionToolCallEvent)
        mock_event.part = MagicMock()
        mock_event.part.tool_name = "dish_mcp_book_room"
        mock_event.part.args_as_dict.return_value = {"room": "A1"}

        with (
            patch("builtins.print"),
            patch(
                "src.agent.streaming.describe_tool_call",
                return_value="Booking room A1",
            ),
        ):
            result = handle_tool_call(mock_event)

        assert result[0] == "tool_call"
        assert result[1] == "Booking room A1"
        assert result[2] == []

    def test_prints_tool_call_description(self) -> None:
        """Test that handle_tool_call prints the tool call description."""
        mock_event = MagicMock(spec=FunctionToolCallEvent)
        mock_event.part = MagicMock()
        mock_event.part.tool_name = "google_calendar_list-events"
        mock_event.part.args_as_dict.return_value = {}

        with (
            patch("builtins.print") as mock_print,
            patch(
                "src.agent.streaming.describe_tool_call",
                return_value="Checking calendar",
            ),
        ):
            handle_tool_call(mock_event)

            mock_print.assert_called_once_with("\n[MCP] Checking calendar", flush=True)


class TestProcessEvent:
    """Tests for the process_event function."""

    def test_agent_run_result_event_updates_history(self) -> None:
        """Test that AgentRunResultEvent updates the state's updated_history."""
        state = StreamState()
        message_history: list[ModelMessage] = []
        captured_messages: list[ModelMessage] = [MagicMock(spec=ModelMessage)]

        mock_event: Any = MagicMock(spec=AgentRunResultEvent)
        mock_event.__class__ = AgentRunResultEvent

        with patch.object(AgentRunResultEvent, "__instancecheck__", return_value=True):
            process_event(mock_event, state, message_history, captured_messages)

    def test_function_tool_call_event_handled(self) -> None:
        """Test that FunctionToolCallEvent is handled correctly."""
        mock_part = MagicMock()
        mock_part.tool_name = "test_tool"
        mock_part.args_as_dict.return_value = {}

        with (
            patch("builtins.print"),
            patch(
                "src.agent.streaming.describe_tool_call",
                return_value="Test description",
            ),
        ):
            event: Any = MagicMock()
            event.__class__ = FunctionToolCallEvent
            event.part = mock_part

            result = handle_tool_call(event)

        assert result[0] == "tool_call"
        assert result[1] == "Test description"

    def test_part_start_event_with_text_part(self) -> None:
        """Test handling PartStartEvent with TextPart."""
        state = StreamState()

        text_part = TextPart(content="Hello")
        mock_event = MagicMock(spec=PartStartEvent)
        mock_event.part = text_part

        with patch("builtins.print"):
            result = None
            if isinstance(mock_event.part, TextPart) and mock_event.part.content:
                result = state.emit_text(mock_event.part.content)

        assert result is not None
        assert result[0] == "text"
        assert result[1] == "Hello"

    def test_part_start_event_with_empty_content(self) -> None:
        """Test handling PartStartEvent with empty TextPart content."""
        state = StreamState()
        text_part = TextPart(content="")

        result = None
        if text_part.content:
            with patch("builtins.print"):
                result = state.emit_text(text_part.content)

        assert result is None

    def test_part_delta_event_with_text_delta(self) -> None:
        """Test handling PartDeltaEvent with TextPartDelta."""
        state = StreamState()
        text_delta = TextPartDelta(content_delta=" world")

        with patch("builtins.print"):
            result = state.emit_text(text_delta.content_delta)

        assert result[0] == "text"
        assert result[1] == " world"

    def test_unknown_event_returns_none(self) -> None:
        """Test that unknown event types return None."""
        state = StreamState()
        message_history: list[ModelMessage] = []
        captured_messages: list[ModelMessage] = []

        unknown_event: Any = MagicMock()
        unknown_event.__class__ = type("UnknownEvent", (), {})

        result = process_event(unknown_event, state, message_history, captured_messages)

        assert result is None

    def test_updated_history_persists_across_events(self) -> None:
        """Test that updated_history is correctly set on state."""
        state = StreamState()
        message1 = MagicMock(spec=ModelMessage)
        message2 = MagicMock(spec=ModelMessage)
        message_history = [message1]
        captured_messages = [message2]

        state.updated_history = [*message_history, *captured_messages]

        assert len(state.updated_history) == EXPECTED_HISTORY_LENGTH
        assert state.updated_history[0] == message1
        assert state.updated_history[1] == message2


class TestStreamingEventType:
    """Tests for the StreamingEvent type alias."""

    def test_streaming_event_structure(self) -> None:
        """Test that StreamingEvent has correct structure."""
        event: StreamingEvent = ("text", "content", [])

        assert event[0] == "text"
        assert event[1] == "content"
        assert event[2] == []

    def test_streaming_event_with_message_history(self) -> None:
        """Test StreamingEvent with populated message history."""
        mock_message = MagicMock(spec=ModelMessage)
        history: list[ModelMessage] = [mock_message]

        event: StreamingEvent = ("done", "", history)

        assert event[0] == "done"
        assert event[1] == ""
        assert len(event[2]) == 1

    def test_streaming_event_types(self) -> None:
        """Test various StreamingEvent type combinations."""
        text_event: StreamingEvent = ("text", "Hello", [])
        tool_event: StreamingEvent = ("tool_call", "Booking room", [])
        done_event: StreamingEvent = ("done", "", [])
        error_event: StreamingEvent = ("error", "Something went wrong", [])

        assert text_event[0] == "text"
        assert tool_event[0] == "tool_call"
        assert done_event[0] == "done"
        assert error_event[0] == "error"
