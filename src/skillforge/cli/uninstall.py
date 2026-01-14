"""
CLI command for uninstalling skills.

This module provides the 'skillforge uninstall' command for removing
installed skills and updating the manifest.

Usage:
    skillforge uninstall <skill-name>
    skillforge uninstall <skill-name> --keep-files

Example:
    skillforge uninstall rapid-interviewing
    skillforge uninstall rapid-interviewing --keep-files
"""

import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from skillforge.core.manifest import (
    Manifest,
    SkillNotInstalledError,
)


console = Console()


def uninstall(
    skill_name: str = typer.Argument(
        ...,
        help="Name of the skill to uninstall",
    ),
    keep_files: bool = typer.Option(
        False,
        "--keep-files",
        help="Keep the skill files on disk (only remove from manifest)",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Uninstall without confirmation",
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        "--project-root",
        help="Project root directory (default: current directory)",
        hidden=True,
    ),
) -> None:
    """Uninstall an installed skill.

    Removes a skill from the manifest and optionally deletes its files
    from the filesystem. By default, both the manifest entry and files
    are removed. Use --keep-files to only remove the manifest entry.

    Examples:
        skillforge uninstall rapid-interviewing

        skillforge uninstall rapid-interviewing --keep-files

        skillforge uninstall rapid-interviewing --force
    """
    # Get project root
    root = project_root or Path.cwd()

    # Initialize manifest
    manifest = Manifest(project_root=root)

    # Check if skill is installed
    try:
        skill_info = manifest.get(skill_name)
    except SkillNotInstalledError:
        console.print(
            f"[red]Error:[/red] Skill '{skill_name}' is not installed.\n"
            f"Run 'skillforge list' to see installed skills."
        )
        raise typer.Exit(code=1)

    skill_path = skill_info["path"]
    marketplace = skill_info.get("marketplace", "unknown")

    # Confirm uninstall unless force
    if not force:
        console.print(f"Skill: [cyan]{skill_name}[/cyan]")
        console.print(f"  Path: {skill_path}")
        console.print(f"  Marketplace: {marketplace}")

        if keep_files:
            message = f"\nRemove '{skill_name}' from manifest (files will be kept)?"
        else:
            message = f"\nRemove '{skill_name}' and delete its files?"

        confirmed = typer.confirm(message)
        if not confirmed:
            console.print("[dim]Cancelled.[/dim]")
            raise typer.Exit(code=0)

    # Delete files if not keeping
    files_deleted = False
    if not keep_files:
        # Resolve the skill path
        path = Path(skill_path)
        if not path.is_absolute():
            # Handle relative paths like ./agents/coach/skills/skill-name
            if skill_path.startswith("./"):
                path = root / skill_path[2:]
            else:
                path = root / skill_path

        if path.exists():
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                files_deleted = True
                console.print(f"[green]Deleted[/green] {path}")
            except Exception as e:
                console.print(
                    f"[yellow]Warning:[/yellow] Could not delete files at {path}: {e}\n"
                    f"Removing from manifest anyway."
                )
        else:
            console.print(
                f"[yellow]Warning:[/yellow] Skill directory not found at {path}\n"
                f"Removing from manifest anyway."
            )

    # Remove from manifest
    try:
        manifest.remove(skill_name)

        if keep_files:
            console.print(
                f"[green]Uninstalled![/green] Skill '{skill_name}' removed from manifest (files kept at {skill_path})"
            )
        elif files_deleted:
            console.print(
                f"[green]Uninstalled![/green] Skill '{skill_name}' removed completely."
            )
        else:
            console.print(
                f"[green]Uninstalled![/green] Skill '{skill_name}' removed from manifest."
            )

    except SkillNotInstalledError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
