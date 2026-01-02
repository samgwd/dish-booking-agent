"""Type definitions for the Dish Booking Agent."""

from dataclasses import dataclass


@dataclass
class DishCredentials:
    """Credentials for DiSH room booking."""

    cookie: str
    team_id: str
    member_id: str


@dataclass
class GoogleCalendarTokens:
    """OAuth tokens for Google Calendar API."""

    access_token: str
    refresh_token: str
    expiry_date: int  # Unix timestamp in milliseconds


@dataclass
class AgentDeps:
    """Dependencies for the Dish Booking Agent."""

    dish: DishCredentials | None = None
    google_calendar: GoogleCalendarTokens | None = None
