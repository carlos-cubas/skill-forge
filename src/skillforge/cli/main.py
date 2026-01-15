"""
SkillForge CLI - Command-line interface for skill management.

This module provides the main CLI entry point for SkillForge commands:
- skillforge version - Show version information
- skillforge marketplace - Marketplace management
- skillforge install - Install skills from marketplaces
- skillforge uninstall - Uninstall skills
- skillforge list - List installed skills
- skillforge read - Load skill content for agents
- skillforge elevenlabs - ElevenLabs integration commands
"""

import typer
from rich.console import Console

from skillforge.cli import marketplace
from skillforge.cli import elevenlabs
from skillforge.cli.read import read_skill
from skillforge.cli.install import install
from skillforge.cli.uninstall import uninstall
from skillforge.cli.list_cmd import list_skills

app = typer.Typer(
    name="skillforge",
    help="Equip agents with domain-specific skills using Anthropic's skill format.",
    no_args_is_help=True,
)

console = Console()

# Register the read command
app.command(name="read")(read_skill)

# Register install command
app.command(name="install")(install)

# Register uninstall command
app.command(name="uninstall")(uninstall)

# Register list command
app.command(name="list")(list_skills)

# Register marketplace subcommands
app.add_typer(marketplace.app, name="marketplace")

# Register elevenlabs subcommands
app.add_typer(elevenlabs.app, name="elevenlabs")


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
