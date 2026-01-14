"""
CLI command for reading and outputting skill instructions.

This module provides the 'skillforge read' command which loads a skill
from a specified path and outputs only its instructions (no frontmatter).
This is used by agents at runtime to load skill content.

Usage:
    skillforge read rapid-interviewing --from ./skills/
    skillforge read rapid-interviewing -f ./skills/
"""

import typer
from pathlib import Path
from rich.console import Console

from skillforge.core.loader import SkillLoader, SkillNotFoundError

console = Console()


def read_skill(
    skill_name: str = typer.Argument(..., help="Name of the skill to read"),
    from_path: Path = typer.Option(
        ..., "--from", "-f", help="Path to search for skill"
    ),
) -> None:
    """Load and output a skill's instructions.

    Used by agents at runtime to load skill content.
    The output contains only the skill instructions (no frontmatter).
    """
    try:
        loader = SkillLoader(skill_paths=[str(from_path / "*")])
        skill = loader.get(skill_name)
        print(skill.instructions)
    except SkillNotFoundError:
        console.print(f"[red]Error:[/red] Skill '{skill_name}' not found in {from_path}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)
