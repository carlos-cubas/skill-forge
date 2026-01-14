"""
SkillForge CLI - Command-line interface for skill management.

This module provides the main CLI entry point for SkillForge commands:
- skillforge version - Show version information
- skillforge marketplace - Marketplace management
- skillforge install - Install skills from marketplaces (future)
- skillforge read - Load skill content for agents
"""

import typer
from rich.console import Console

from skillforge.cli import marketplace
from skillforge.cli.read import read_skill

app = typer.Typer(
    name="skillforge",
    help="Equip agents with domain-specific skills using Anthropic's skill format.",
    no_args_is_help=True,
)

console = Console()

# Register the read command
app.command(name="read")(read_skill)

# Register marketplace subcommands
app.add_typer(marketplace.app, name="marketplace")


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
