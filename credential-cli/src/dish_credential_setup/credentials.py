"""Automated cookie retrieval for Dish using Playwright."""

from __future__ import annotations

import asyncio
import subprocess  # nosec B404 - only used with hardcoded args
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# playwright doesn't ship type stubs
from playwright.async_api import (  # type: ignore[import-not-found]
    Page,
    Request,
    async_playwright,
)
from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]


@dataclass
class DishCredentials:
    """Container for Dish authentication credentials."""

    cookie: str
    team_id: str | None = None
    member_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Convert credentials to a dictionary of secret keys to values."""
        result = {"DISH_COOKIE": self.cookie}
        if self.team_id:
            result["TEAM_ID"] = self.team_id
        if self.member_id:
            result["MEMBER_ID"] = self.member_id
        return result


def _extract_ids_from_url(url: str) -> tuple[str | None, str | None]:
    """Extract team_id and member_id from URL query parameters.

    Args:
        url: The full request URL

    Returns:
        Tuple of (team_id, member_id), either may be None
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return params.get("team", [None])[0], params.get("member", [None])[0]


def ensure_playwright_browsers() -> None:
    """Ensure Playwright browsers are installed."""
    try:
        with sync_playwright() as p:
            # This will fail if browsers aren't installed
            _ = p.chromium.executable_path
    except Exception:
        print("📦 Installing browser for first-time setup...")
        subprocess.run(  # nosec B603 - hardcoded trusted args
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
        )


async def get_dish_credentials_interactive() -> DishCredentials:
    """Launch browser for user to login, then extract cookie, team_id, and member_id.

    This opens a browser window where the user can complete the login
    (including any SSO/2FA), then waits for confirmation before extracting credentials.

    Returns:
        DishCredentials containing cookie, team_id, and member_id
    """
    async with async_playwright() as p:
        user_data_dir = Path.home() / ".dish-credential-setup" / "browser-data"
        user_data_dir.mkdir(parents=True, exist_ok=True)

        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        captured_ids: dict[str, str | None] = {"team_id": None, "member_id": None}

        def handle_request(request: Request) -> None:
            if "occurrences" in request.url and "team=" in request.url:
                team_id, member_id = _extract_ids_from_url(request.url)
                if team_id:
                    captured_ids["team_id"] = team_id
                if member_id:
                    captured_ids["member_id"] = member_id

        page.on("request", handle_request)

        await page.goto("https://dish-manchester.officernd.com/")

        await _wait_for_dashboard(page)

        await asyncio.sleep(2)

        credentials = await _build_credentials(page, captured_ids)
        await browser.close()
        return credentials


async def _wait_for_dashboard(page: Page, timeout_seconds: int = 300) -> None:
    """Wait for the page URL to contain /dashboard, indicating successful login.

    Args:
        page: The playwright page object
        timeout_seconds: Maximum time to wait (default 5 minutes)

    Raises:
        TimeoutError: If dashboard is not reached within timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        current_url = page.url
        if "/dashboard" in current_url:
            return
        await asyncio.sleep(0.5)

    raise TimeoutError(
        f"Login did not complete within {timeout_seconds} seconds. Please try again."
    )


async def _extract_session_cookie(page: Page) -> str | None:
    """Extract the connect.sid cookie from the current page context.

    Args:
        page: The playwright page object

    Returns:
        The value of the connect.sid cookie, or None if not found
    """
    cookies = await page.context.cookies()

    for cookie in cookies:
        if cookie["name"] == "connect.sid":
            return str(cookie["value"])

    return None


async def _build_credentials(page: Page, captured_ids: dict[str, str | None]) -> DishCredentials:
    """Extract cookie and build DishCredentials object.

    Args:
        page: The playwright page object
        captured_ids: Dict containing captured team_id and member_id

    Returns:
        DishCredentials with all available credentials

    Raises:
        RuntimeError: If cookie extraction fails
    """
    cookie_value = await _extract_session_cookie(page)

    if not cookie_value:
        raise RuntimeError(
            "Could not find connect.sid cookie. Make sure you completed the login successfully."
        )

    return DishCredentials(
        cookie=f"connect.sid={cookie_value}",
        team_id=captured_ids["team_id"],
        member_id=captured_ids["member_id"],
    )
