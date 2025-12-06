# DiSH & Calendar Booking Agent

Pydantic AI agent that brokers room bookings (DiSH MCP) and calendar actions (Google Calendar MCP) with MCP over stdio. It can co‑ordinate room reservations with your calendar availability.

## Prerequisites
- Python 3.12+ with [`uv`](https://docs.astral.sh/uv/) installed.
- Docker available for the Google Calendar MCP container.
- Access to the DiSH MCP repository (set `DISH_MCP_PATH` to its root; it must have a `.venv` with `fastmcp` installed via `uv sync`).

## Setup
1) Install this project’s dependencies:
   ```bash
   uv sync
   ```
2) Prepare DiSH MCP locally (in the repo pointed to by `DISH_MCP_PATH`):
   ```bash
   uv sync
   ```
3) Ensure the Google Calendar MCP Docker image `calendar-mcp` is available (build or pull from its source) and you have OAuth credentials JSON on disk.
4) Copy `example.env` to `.env` and fill in values:
   - `OPENAI_API_KEY`
   - `DISH_MCP_PATH` (absolute path to the DiSH MCP repo)
   - `DISH_COOKIE`
   - `TEAM_ID`
   - `MEMBER_ID`
   - `GOOGLE_OAUTH_CREDENTIALS` (absolute path to your Google OAuth JSON for the Calendar MCP mount)

`mcp_config.json` uses these variables for runtime substitution; the agent launches both MCP servers automatically via stdio.

## Running

### CLI agent
```bash
uv run src/agent.py
```
You will see `[MCP] ...` lines whenever the agent invokes an MCP tool.

### HTTP API (FastAPI)
```bash
uv run uvicorn src.api:app --reload --port 8000
```
Endpoints:
- `GET /health`
- `GET /send-message`

`session` lets you keep separate conversational histories.

## Example prompts
- "List my calendar events tomorrow morning."
- "Book a room from 14:00–15:00 tomorrow and create a calendar invite for it."
- "Reschedule the 13:00 sync to 15:00 and keep the same attendees."

## Manual test flow
1) Start the CLI or API as above (no separate SSE servers needed).
2) Ask for upcoming events on a given day.
3) Book a DiSH room and ask for a matching Google Calendar invite at the same time.
4) Reschedule or cancel a calendar event and confirm the change. If the model blurs DiSH vs Calendar responsibilities, adjust prompts or tool prefixes in `mcp_config.json`.
