# Dish Credential Setup CLI

A command-line tool to retrieve your Dish booking credentials.

## What It Does

This tool automates the process of:

1. **Launching a browser** for you to log in to Dish (supports SSO/2FA)
2. **Extracting** your session cookie, team ID, and member ID
3. **Displaying** the credentials for you to copy into the application

## Installation

### Option 1: Install from Git

```bash
pipx install git+https://github.com/samgwd/dish-booking-agent.git#subdirectory=credential-cli
```

Or with pip:

```bash
pip install git+https://github.com/samgwd/dish-booking-agent.git#subdirectory=credential-cli
```

### Option 2: Install Locally (Development)

```bash
cd credential-cli
pip install -e .
```

## Usage

Simply run:

```bash
dish-setup
```

The tool will:

1. Open a browser window
2. Wait for you to complete the Dish login (SSO supported)
3. Display your credentials once you reach the dashboard

### Example Output

```
┌───────────────────────────────────────────┐
│ ✓ Credentials Retrieved Successfully!    │
└───────────────────────────────────────────┘

       Your Dish Credentials
┌─────────────┬────────────────────┬────────┐
│ Key         │ Value              │ Status │
├─────────────┼────────────────────┼────────┤
│ DISH_COOKIE │ connect.sid=s%3... │   ✓    │
│ TEAM_ID     │ abc123def456       │   ✓    │
│ MEMBER_ID   │ xyz789             │   ✓    │
└─────────────┴────────────────────┴────────┘

Copy these values to the application:

DISH_COOKIE:
connect.sid=s%3A...

TEAM_ID:
abc123def456

MEMBER_ID:
xyz789
```

Copy these values into the Dish Booking Agent settings page.

### First Run

On first run, the tool will automatically install the Chromium browser needed for automation. This is a one-time setup.

## Requirements

- Python 3.10+
- A Dish account (with SSO access if applicable)

## How It Works

1. **Browser Automation**: Using Playwright, the tool opens a browser window where you complete the Dish login. This supports any authentication method Dish uses (including SSO and 2FA).

2. **Credential Capture**: Once you reach the Dish dashboard, the tool extracts:
   - `DISH_COOKIE`: Your session cookie
   - `TEAM_ID`: Your team identifier (captured from API requests)
   - `MEMBER_ID`: Your member identifier (captured from API requests)

3. **Display**: The credentials are displayed in the terminal for you to copy.

## Troubleshooting

### "Could not capture team_id/member_id"

If the tool captures the cookie but not the team/member IDs:

1. Run the tool again
2. After logging in, navigate around the Dish dashboard before it finishes
3. Click on "Book a Room" or view the calendar
4. The IDs are captured from API requests, which may not fire on initial page load

### Browser doesn't open

Ensure Playwright browsers are installed:

```bash
playwright install chromium
```

## Security Notes

- Your Dish password is never stored or transmitted
- Only the session cookie is captured (not your login credentials)
- Credentials are only displayed locally in your terminal
