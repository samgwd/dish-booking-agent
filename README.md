# DiSH & Calendar Booking Agent

Pydantic AI agent that connects to both the DiSH room-booking MCP and the Google Calendar MCP. It can coordinate room bookings with your calendar availability.

## Setup

1. Install Dish MCP dependencies:
    ```bash
    cd ../dish-mcp
    uv sync
    ```
2. Install the agent dependencies:
    ```bash
    cd ../dish-booking-agent
    uv sync
    ```
3. Environment variables (e.g., in `.env`):
    - `OPENAI_API_KEY`
    - `DISH_COOKIE`
    - `TEAM_ID`
    - `MEMBER_ID`
    - `DISH_MCP_SSE_URL` (default `http://127.0.0.1:8000/sse`)
    - `GCAL_MCP_SSE_URL` (default `http://127.0.0.1:3000/sse`)
    - `GOOGLE_OAUTH_CREDENTIALS` (path to your Google OAuth JSON for the calendar MCP)


## Running the Agent

```bash
cd ../dish-booking-agent
uv run agent.py
```
The agent logs which servers and tools it connects to. Override `DISH_MCP_SSE_URL` or `GCAL_MCP_SSE_URL` to match your ports if needed.

## Usage

Example prompts:
- "List my calendar events tomorrow morning."
- "Book a room from 2–3pm tomorrow and create a calendar invite for it."
- "Reschedule the 1pm sync to 3pm and keep the same attendees."

## Manual Test Flows

1) Start Dish MCP on :8000 and Google Calendar MCP on :3000 (or your configured ports), then run the agent.
2) Ask the agent to list upcoming events for a specific day.
3) Ask it to book a room in Dish and create a matching Google Calendar event with the same time and title.
4) Ask it to reschedule or cancel a calendar event and confirm the change.
If the model confuses Dish vs. Calendar responsibilities, tweak the namespaces or prompts as needed.
