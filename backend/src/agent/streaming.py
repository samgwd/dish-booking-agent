"""Streaming event processing for the agent."""

from pydantic_ai import AgentRunResultEvent
from pydantic_ai.messages import (
    AgentStreamEvent,
    FunctionToolCallEvent,
    ModelMessage,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
)

from src.mcp.formatting import describe_tool_call

StreamingEvent = tuple[str, str, list[ModelMessage]]


class StreamState:
    """Mutable state container for streaming events."""

    def __init__(self) -> None:
        """Initialise the stream state."""
        self.text_started = False
        self.updated_history: list[ModelMessage] = []

    def emit_text(self, content: str) -> StreamingEvent:
        """Print text content and return the corresponding streaming event.

        Args:
            content: The text content to emit.

        Returns:
            A streaming event tuple for the text content.
        """
        if not self.text_started:
            print("Agent: ", end="", flush=True)
            self.text_started = True
        print(content, end="", flush=True)
        return ("text", content, [])


def handle_tool_call(event: FunctionToolCallEvent) -> StreamingEvent:
    """Handle a function tool call event.

    Args:
        event: The function tool call event to handle.

    Returns:
        A streaming event tuple for the tool call.
    """
    desc = describe_tool_call(event.part.tool_name, event.part.args_as_dict())
    print(f"\n[MCP] {desc}", flush=True)
    return ("tool_call", desc, [])


def process_event(
    event: AgentStreamEvent | AgentRunResultEvent[str],
    state: StreamState,
    message_history: list[ModelMessage],
    captured_messages: list[ModelMessage],
) -> StreamingEvent | None:
    """Process a single agent stream event and return a streaming event if applicable.

    Args:
        event: The agent stream event to process.
        state: The mutable state container for streaming events.
        message_history: The history of messages between the user and the agent.
        captured_messages: The captured messages from the agent run.

    Returns:
        A streaming event if applicable, otherwise None.
    """
    if isinstance(event, AgentRunResultEvent):
        state.updated_history = [*message_history, *captured_messages]
        return None

    if isinstance(event, FunctionToolCallEvent):
        return handle_tool_call(event)

    if isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
        return state.emit_text(event.part.content) if event.part.content else None

    if isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
        return state.emit_text(event.delta.content_delta)

    return None
