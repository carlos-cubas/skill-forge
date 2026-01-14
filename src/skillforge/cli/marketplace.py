"""
CLI commands for managing skill marketplaces.

This module provides the 'skillforge marketplace' commands for:
- Adding marketplaces from GitHub, Git URLs, or local paths
- Listing configured marketplaces
- Updating marketplace metadata
- Removing marketplaces

Usage:
    skillforge marketplace add <source>      # Add marketplace
    skillforge marketplace list              # List marketplaces
    skillforge marketplace update [name]     # Update metadata
    skillforge marketplace remove <name>     # Remove marketplace
"""

import typer
from rich.console import Console
from rich.table import Table

from skillforge.core.marketplace_registry import (
    MarketplaceRegistry,
    MarketplaceNotFoundError,
    MarketplaceExistsError,
)

console = Console()
app = typer.Typer(help="Manage skill marketplaces")


@app.command()
def add(
    source: str = typer.Argument(
        ..., help="Marketplace source (owner/repo, URL, or path)"
    ),
) -> None:
    """Add a skill marketplace.

    Supports multiple source formats:
    - owner/repo (GitHub shorthand)
    - github:owner/repo (explicit GitHub)
    - https://github.com/org/repo.git (Git URL)
    - ./local-path (local directory)

    After adding, run 'skillforge marketplace update <name>' to fetch skills.
    """
    registry = MarketplaceRegistry()

    try:
        marketplace = registry.add(source)
        console.print(f"[green]Added marketplace:[/green] {marketplace.name}")
        console.print(f"  Source: {marketplace.source}")
        console.print(f"  Type: {marketplace.source_type.value}")

        if marketplace.skills:
            console.print(f"  Skills: {len(marketplace.skills)}")
            console.print("\n  Available skills:")
            for skill in marketplace.skills[:5]:
                console.print(f"    - {skill.name}: {skill.description}")
            if len(marketplace.skills) > 5:
                console.print(f"    ... and {len(marketplace.skills) - 5} more")
        else:
            console.print(
                "\n  [dim]No skills loaded yet. "
                "Run 'skillforge marketplace update' to fetch skills.[/dim]"
            )

    except MarketplaceExistsError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command(name="list")
def list_marketplaces() -> None:
    """List configured marketplaces.

    Shows all marketplaces that have been added, along with their
    source type and number of available skills.
    """
    registry = MarketplaceRegistry()
    marketplaces = registry.list()

    if not marketplaces:
        console.print("[dim]No marketplaces configured.[/dim]")
        console.print(
            "\nAdd one with: [bold]skillforge marketplace add <source>[/bold]"
        )
        console.print("Example: [bold]skillforge marketplace add dearmarkus/event-skills[/bold]")
        return

    table = Table(title="Configured Marketplaces")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Skills", justify="right", style="green")
    table.add_column("Source", style="dim")

    for mp in marketplaces:
        skills_count = str(len(mp.skills)) if mp.skills else "-"
        table.add_row(mp.name, mp.source_type.value, skills_count, mp.source)

    console.print(table)


@app.command()
def update(
    name: str = typer.Argument(
        None, help="Marketplace name (or omit to update all)"
    ),
) -> None:
    """Update marketplace metadata.

    Fetches the latest skill information from the marketplace source.
    If no name is provided, updates all configured marketplaces.
    """
    registry = MarketplaceRegistry()

    # Check if we have any marketplaces
    if not registry.list():
        console.print("[dim]No marketplaces configured.[/dim]")
        console.print(
            "\nAdd one with: [bold]skillforge marketplace add <source>[/bold]"
        )
        raise typer.Exit(code=0)

    try:
        if name:
            # Update specific marketplace
            console.print(f"Updating marketplace: [cyan]{name}[/cyan]...")
            marketplace = registry.get(name)
            registry.update(name)
            updated = registry.get(name)
            console.print(
                f"[green]Updated![/green] Found {len(updated.skills)} skill(s)"
            )

            if updated.skills:
                console.print("\nAvailable skills:")
                for skill in updated.skills:
                    desc = skill.description or "(no description)"
                    version = f" v{skill.version}" if skill.version else ""
                    console.print(f"  - [cyan]{skill.name}[/cyan]{version}: {desc}")
        else:
            # Update all marketplaces
            marketplaces = registry.list()
            console.print(f"Updating {len(marketplaces)} marketplace(s)...")

            for mp in marketplaces:
                console.print(f"\n[cyan]{mp.name}[/cyan]:")
                try:
                    registry.update(mp.name)
                    updated = registry.get(mp.name)
                    console.print(
                        f"  [green]Updated![/green] Found {len(updated.skills)} skill(s)"
                    )
                except Exception as e:
                    console.print(f"  [yellow]Warning:[/yellow] {e}")

            console.print("\n[green]All marketplaces updated.[/green]")

    except MarketplaceNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command()
def remove(
    name: str = typer.Argument(..., help="Marketplace name to remove"),
    force: bool = typer.Option(
        False, "--force", "-f", help="Remove without confirmation"
    ),
) -> None:
    """Remove a marketplace.

    Removes a marketplace from the configuration. This does not delete
    any installed skills, only removes the marketplace reference.
    """
    registry = MarketplaceRegistry()

    try:
        # Verify marketplace exists before prompting
        marketplace = registry.get(name)

        if not force:
            confirmed = typer.confirm(
                f"Remove marketplace '{name}'? "
                f"({len(marketplace.skills)} skills)"
            )
            if not confirmed:
                console.print("[dim]Cancelled.[/dim]")
                return

        registry.remove(name)
        console.print(f"[green]Removed marketplace:[/green] {name}")

    except MarketplaceNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
    except typer.Exit:
        # Re-raise typer exits (e.g., from confirmation abort)
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
