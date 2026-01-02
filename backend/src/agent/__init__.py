"""Agent package - public API for the Dish Booking Agent."""

from src.agent.core import agent, main, process_message, process_message_streaming
from src.agent.hooks import inject_dish_credentials, inject_google_calendar_credentials
from src.agent.streaming import StreamingEvent, StreamState, process_event
from src.agent.types import AgentDeps, DishCredentials, GoogleCalendarTokens

__all__ = [
    "AgentDeps",
    "DishCredentials",
    "GoogleCalendarTokens",
    "StreamingEvent",
    "StreamState",
    "agent",
    "inject_dish_credentials",
    "inject_google_calendar_credentials",
    "main",
    "process_event",
    "process_message",
    "process_message_streaming",
]
