"""
CLI command for listing installed skills.

This module provides the 'skillforge list' command for displaying
all installed skills tracked in the manifest.

Usage:
    skillforge list

Example:
    skillforge list
"""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from skillforge.core.manifest import Manifest


console = Console()


def list_skills(
    project_root: Optional[Path] = typer.Option(
        None,
        "--project-root",
        help="Project root directory (default: current directory)",
        hidden=True,
    ),
) -> None:
    """List installed skills.

    Shows all skills that have been installed and tracked in the
    project's manifest file (.skillforge/manifest.json).

    Example:
        skillforge list
    """
    # Get project root
    root = project_root or Path.cwd()

    # Initialize manifest
    manifest = Manifest(project_root=root)

    # Get all installed skills
    skills = manifest.list()

    if not skills:
        console.print("[dim]No skills installed.[/dim]")
        console.print(
            "\nInstall skills with: [bold]skillforge install <skill>@<marketplace> --to <path>[/bold]"
        )
        console.print(
            "Example: [bold]skillforge install rapid-interviewing@dearmarkus/event-skills --to ./skills/[/bold]"
        )
        return

    # Create table
    table = Table(title="Installed Skills")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Path", style="dim")
    table.add_column("Marketplace", style="magenta")
    table.add_column("Version", style="green")

    # Sort by name and add rows
    for name in sorted(skills.keys()):
        info = skills[name]
        version = info.get("version") or "-"
        marketplace = info.get("marketplace") or "-"
        path = info.get("path") or "-"

        table.add_row(name, path, marketplace, version)

    console.print(table)
    console.print(f"\n[dim]Total: {len(skills)} skill(s)[/dim]")
