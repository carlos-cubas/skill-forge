"""
SkillForge CLI - Command-line interface for skill management.

This module provides the main CLI entry point for SkillForge commands:
- skillforge version - Show version information
- skillforge marketplace - Marketplace management (future)
- skillforge install - Install skills from marketplaces (future)
- skillforge read - Load skill content for agents (future)
"""

import typer
from rich.console import Console

app = typer.Typer(
    name="skillforge",
    help="Equip agents with domain-specific skills using Anthropic's skill format.",
    no_args_is_help=True,
)

console = Console()


@app.command()
def version() -> None:
    """Show SkillForge version information."""
    from skillforge import __version__

    console.print(f"[bold]skillforge[/bold] {__version__}")


@app.callback()
def main_callback() -> None:
    """
    SkillForge - A toolkit for equipping CrewAI and LangChain agents with skills.

    Use 'skillforge --help' to see available commands.
    """
    pass


if __name__ == "__main__":
    app()
