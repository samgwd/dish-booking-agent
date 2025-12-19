"""CLI entry point for Dish Credential Setup."""

from __future__ import annotations

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .credentials import (
    DishCredentials,
    ensure_playwright_browsers,
    get_dish_credentials_interactive,
)

console = Console()

_MAX_DISPLAY_LEN = 50


def print_banner() -> None:
    """Print the welcome banner."""
    console.print(
        Panel.fit(
            "[bold cyan]🍽️  Dish Credential Setup[/bold cyan]\n\n"
            "This tool will help you retrieve your Dish booking credentials.\n"
            "A browser window will open for you to log in.",
            border_style="cyan",
        )
    )


def print_credentials(credentials: DishCredentials) -> None:
    """Print the retrieved credentials in a copyable format.

    Args:
        credentials: The Dish credentials to display
    """
    console.print("\n")
    console.print(
        Panel.fit(
            "[bold green]✓ Credentials Retrieved Successfully![/bold green]",
            border_style="green",
        )
    )

    table = Table(title="Your Dish Credentials", show_header=True, header_style="bold cyan")
    table.add_column("Key", style="dim")
    table.add_column("Value", style="green")
    table.add_column("Status", justify="center")

    creds_dict = credentials.to_dict()

    for key in ["DISH_COOKIE", "TEAM_ID", "MEMBER_ID"]:
        value = creds_dict.get(key)
        if value:
            display_value = (
                value if len(value) <= _MAX_DISPLAY_LEN else f"{value[:_MAX_DISPLAY_LEN - 3]}..."
            )
            table.add_row(key, display_value, "[green]✓[/green]")
        else:
            table.add_row(key, "[dim]Not captured[/dim]", "[yellow]⚠[/yellow]")

    console.print(table)

    console.print("\n[bold]Copy these values to the application:[/bold]\n")

    for key, value in creds_dict.items():
        console.print(f"[cyan]{key}:[/cyan]")
        console.print(f"[green]{value}[/green]\n")

    if not credentials.team_id or not credentials.member_id:
        console.print(
            Panel(
                "[yellow]⚠ team_id and/or member_id were not captured.[/yellow]\n\n"
                "These are captured from API requests when you navigate around Dish.\n"
                "Try running the tool again and clicking on 'Book a Room' or similar\n"
                "features before the dashboard fully loads.",
                title="Missing Credentials",
                border_style="yellow",
            )
        )


async def get_dish_credentials() -> DishCredentials | None:
    """Launch browser to get Dish credentials.

    Returns:
        DishCredentials if successful, None if failed
    """
    console.print("\n[bold]Dish Login[/bold]")
    console.print(
        "A browser window will open. Please log in to Dish.\n"
        "The tool will automatically detect when you reach the dashboard."
    )

    input("\nPress Enter to open the browser...")

    try:
        with console.status("[bold green]Waiting for login..."):
            credentials = await get_dish_credentials_interactive()
        return credentials
    except TimeoutError:
        console.print("\n[red]✗[/red] Login timed out. Please try again.")
        return None
    except Exception as e:
        console.print(f"\n[red]✗[/red] Failed to get credentials: {e}")
        return None


async def run_setup() -> int:
    """Run the credential retrieval flow.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_banner()

    ensure_playwright_browsers()

    credentials = await get_dish_credentials()

    if not credentials:
        return 1

    print_credentials(credentials)

    return 0


def main() -> None:
    """CLI entry point."""
    try:
        sys.exit(asyncio.run(run_setup()))
    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted by user.[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
