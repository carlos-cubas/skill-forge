"""
Skill data class representing a loaded SkillForge skill.

This module defines the core Skill dataclass that represents a parsed and loaded
skill from a SKILL.md file. It follows Anthropic's skill format specification.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Skill:
    """Represents a loaded skill.

    A Skill is parsed from a SKILL.md file and its associated directory.
    The skill format follows Anthropic's specification:
    - SKILL.md (required) - Instructions + YAML frontmatter metadata
    - tools.py (optional) - Skill-specific tool implementations
    - resources/, scripts/ (optional) - Supporting files

    Attributes:
        name: Unique skill identifier (from frontmatter or directory name)
        description: Human-readable description of what the skill does
        instructions: The markdown content (without frontmatter)
        path: Path to the skill directory
        allowed_tools: List of tool names the skill is allowed to use
        version: Semantic version string (e.g., "1.0.0")
        author: Skill author name or organization

    Example:
        >>> from pathlib import Path
        >>> skill = Skill(
        ...     name="rapid-interviewing",
        ...     description="Conduct rapid discovery interviews",
        ...     instructions="# Rapid Interviewing\\n\\n...",
        ...     path=Path("./skills/rapid-interviewing"),
        ...     allowed_tools=["Bash", "Read"],
        ...     version="1.0.0",
        ...     author="SkillForge Team"
        ... )
        >>> skill.has_tools
        False
    """

    name: str
    description: str
    instructions: str  # The markdown content (without frontmatter)
    path: Path
    allowed_tools: list[str] = field(default_factory=list)
    version: Optional[str] = None
    author: Optional[str] = None

    @property
    def has_tools(self) -> bool:
        """Check if skill has bundled tools.py.

        Returns:
            True if a tools.py file exists in the skill directory.
        """
        return (self.path / "tools.py").exists()

    @property
    def tools_module_path(self) -> Optional[Path]:
        """Return path to tools.py if it exists.

        Returns:
            Path to tools.py if it exists, None otherwise.
        """
        tools_path = self.path / "tools.py"
        return tools_path if tools_path.exists() else None

    def __repr__(self) -> str:
        """Return a concise string representation of the skill."""
        return (
            f"Skill(name={self.name!r}, description={self.description!r}, "
            f"path={self.path!r})"
        )
