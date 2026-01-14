"""
CLI command for installing skills from marketplaces.

This module provides the 'skillforge install' command for downloading
and installing skills from configured marketplaces.

Usage:
    skillforge install <skill>@<marketplace> --to <destination>

Example:
    skillforge install rapid-interviewing@dearmarkus/event-skills --to ./agents/coach/skills/
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from skillforge.core.fetcher import FetchError, MarketplaceFetcher
from skillforge.core.manifest import (
    Manifest,
    SkillAlreadyInstalledError,
)
from skillforge.core.marketplace_registry import (
    MarketplaceNotFoundError,
    MarketplaceRegistry,
    SkillNotInMarketplaceError,
)


console = Console()


def parse_skill_spec(skill_spec: str) -> tuple[str, str]:
    """Parse a skill specification in the format skill@marketplace.

    Args:
        skill_spec: Skill specification string (e.g., "rapid-interviewing@dearmarkus/event-skills")

    Returns:
        Tuple of (skill_name, marketplace_name).

    Raises:
        typer.BadParameter: If the format is invalid.
    """
    if "@" not in skill_spec:
        raise typer.BadParameter(
            f"Invalid skill specification: '{skill_spec}'. "
            f"Expected format: skill@marketplace (e.g., 'rapid-interviewing@dearmarkus/event-skills')"
        )

    parts = skill_spec.split("@", 1)
    skill_name = parts[0].strip()
    marketplace_name = parts[1].strip()

    if not skill_name:
        raise typer.BadParameter(
            f"Invalid skill specification: '{skill_spec}'. Skill name cannot be empty."
        )

    if not marketplace_name:
        raise typer.BadParameter(
            f"Invalid skill specification: '{skill_spec}'. Marketplace name cannot be empty."
        )

    return skill_name, marketplace_name


def install(
    skill_spec: str = typer.Argument(
        ...,
        help="Skill to install (format: skill@marketplace, e.g., 'rapid-interviewing@dearmarkus/event-skills')",
    ),
    to: Path = typer.Option(
        ...,
        "--to",
        help="Destination directory for the installed skill",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite if skill already installed",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        "--project-root",
        help="Project root directory (default: current directory)",
        hidden=True,
    ),
) -> None:
    """Install a skill from a marketplace.

    Downloads a skill from a configured marketplace and installs it
    to the specified destination directory. The skill is tracked in
    the project's manifest file (.skillforge/manifest.json).

    The skill specification must be in the format: skill@marketplace

    Examples:
        skillforge install rapid-interviewing@dearmarkus/event-skills --to ./skills/

        skillforge install example-skill@local-marketplace --to ./agents/coach/skills/
    """
    # Parse skill specification
    try:
        skill_name, marketplace_name = parse_skill_spec(skill_spec)
    except typer.BadParameter as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise typer.Exit(code=1)

    console.print(f"Installing [cyan]{skill_name}[/cyan] from [cyan]{marketplace_name}[/cyan]...")

    # Get project root
    root = project_root or Path.cwd()

    # Initialize manifest
    manifest = Manifest(project_root=root)

    # Check if already installed (unless force)
    if manifest.has(skill_name) and not force:
        existing = manifest.get(skill_name)
        console.print(
            f"[red]Error:[/red] Skill '{skill_name}' is already installed at '{existing['path']}'.\n"
            f"Use --force to reinstall, or run 'skillforge uninstall {skill_name}' first."
        )
        raise typer.Exit(code=1)

    # Get marketplace from registry
    registry = MarketplaceRegistry()

    try:
        marketplace = registry.get(marketplace_name)
    except MarketplaceNotFoundError:
        console.print(
            f"[red]Error:[/red] Marketplace '{marketplace_name}' not found.\n"
            f"Add it first with: skillforge marketplace add {marketplace_name}"
        )
        raise typer.Exit(code=1)

    # Ensure marketplace has skill metadata
    if not marketplace.skills:
        console.print(f"[dim]Updating marketplace metadata...[/dim]")
        try:
            registry.update(marketplace_name)
            marketplace = registry.get(marketplace_name)
        except Exception as e:
            console.print(f"[red]Error:[/red] Failed to update marketplace: {e}")
            raise typer.Exit(code=1)

    # Find skill in marketplace
    try:
        skill = registry.find_skill(skill_name, marketplace_name)
    except SkillNotInMarketplaceError:
        available = ", ".join(s.name for s in marketplace.skills) or "(none - run 'skillforge marketplace update' first)"
        console.print(
            f"[red]Error:[/red] Skill '{skill_name}' not found in marketplace '{marketplace_name}'.\n"
            f"Available skills: {available}"
        )
        raise typer.Exit(code=1)

    # Download the skill
    fetcher = MarketplaceFetcher()

    try:
        # Ensure destination directory exists
        destination = Path(to)
        if not destination.is_absolute():
            destination = root / destination

        installed_path = fetcher.download_skill(marketplace, skill, destination)
        console.print(f"[green]Downloaded[/green] to {installed_path}")

    except FetchError as e:
        console.print(f"[red]Error:[/red] Failed to download skill: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)

    # Update manifest
    try:
        # Calculate relative path from project root
        try:
            relative_path = installed_path.relative_to(root)
            path_str = f"./{relative_path}"
        except ValueError:
            # Path is not relative to root, use absolute
            path_str = str(installed_path)

        # Remove from manifest first if force reinstalling
        if force and manifest.has(skill_name):
            manifest.remove(skill_name)

        manifest.add(
            name=skill_name,
            path=path_str,
            marketplace=marketplace_name,
            version=skill.version,
        )

        console.print(f"[green]Installed![/green] Skill '{skill_name}' is now available.")
        console.print(f"  Path: {path_str}")
        console.print(f"  Marketplace: {marketplace_name}")
        if skill.version:
            console.print(f"  Version: {skill.version}")

    except SkillAlreadyInstalledError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
