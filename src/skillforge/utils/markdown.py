"""
SKILL.md parser for SkillForge.

This module provides utilities for parsing SKILL.md files according to
Anthropic's skill format specification. Skills have YAML frontmatter
followed by markdown instructions.

Example SKILL.md format:
    ---
    name: rapid-interviewing
    description: Conduct rapid discovery interviews
    allowed-tools:
      - Bash
      - Read
    version: 1.0.0
    author: SkillForge Team
    ---

    # Rapid Interviewing Skill

    This skill enables rapid discovery interviews...
"""

from pathlib import Path
from typing import Optional

import yaml

from skillforge.core.skill import Skill


class SkillParseError(Exception):
    """Raised when a SKILL.md file cannot be parsed."""

    pass


def _split_frontmatter(content: str) -> tuple[Optional[str], str]:
    """Split YAML frontmatter from markdown body.

    Frontmatter must be delimited by '---' at the start and end.
    The opening '---' must be at the very beginning of the file.

    Args:
        content: The full content of the SKILL.md file.

    Returns:
        A tuple of (frontmatter_yaml, body_markdown).
        If no frontmatter is found, frontmatter_yaml will be None.

    Example:
        >>> fm, body = _split_frontmatter("---\\nname: test\\n---\\n# Body")
        >>> fm
        'name: test'
        >>> body
        '# Body'
    """
    # Check for frontmatter delimiter at start
    if not content.startswith("---"):
        return None, content

    # Find the closing delimiter
    # Skip the first '---' (3 chars) and newline
    rest = content[3:].lstrip("\n")

    # Handle empty frontmatter case (---\n---\n)
    if rest.startswith("---"):
        body = rest[3:].lstrip("\n")
        return "", body

    end_pos = rest.find("\n---")

    if end_pos == -1:
        # No closing delimiter found - treat entire content as body
        return None, content

    # Extract frontmatter and body
    frontmatter = rest[:end_pos].strip()

    # Body starts after the closing '---' and any following newlines
    body_start = end_pos + 4  # len("\n---")
    body = rest[body_start:].lstrip("\n")

    return frontmatter, body


def parse_skill_md(skill_path: Path) -> Skill:
    """Parse a SKILL.md file and return a Skill object.

    This function reads the SKILL.md file from the given directory,
    parses the YAML frontmatter for metadata, and extracts the
    markdown instructions.

    Args:
        skill_path: Path to the skill directory (not the SKILL.md file).
                   The directory must contain a SKILL.md file.

    Returns:
        A Skill object populated with metadata and instructions.

    Raises:
        SkillParseError: If SKILL.md is not found or cannot be parsed.
        FileNotFoundError: If the skill directory doesn't exist.

    Example:
        >>> from pathlib import Path
        >>> skill = parse_skill_md(Path("./skills/rapid-interviewing"))
        >>> print(skill.name)
        'rapid-interviewing'
    """
    skill_path = Path(skill_path).resolve()

    if not skill_path.exists():
        raise FileNotFoundError(f"Skill directory not found: {skill_path}")

    if not skill_path.is_dir():
        raise SkillParseError(f"Expected directory, got file: {skill_path}")

    skill_md_path = skill_path / "SKILL.md"

    if not skill_md_path.exists():
        raise SkillParseError(f"SKILL.md not found in: {skill_path}")

    # Read the SKILL.md content
    try:
        content = skill_md_path.read_text(encoding="utf-8")
    except OSError as e:
        raise SkillParseError(f"Failed to read SKILL.md: {e}") from e

    # Split frontmatter and body
    frontmatter_yaml, instructions = _split_frontmatter(content)

    # Parse YAML frontmatter
    metadata: dict = {}
    if frontmatter_yaml:
        try:
            metadata = yaml.safe_load(frontmatter_yaml) or {}
        except yaml.YAMLError as e:
            raise SkillParseError(
                f"Invalid YAML frontmatter in {skill_md_path}: {e}"
            ) from e

    # Extract fields from metadata, with defaults
    name = metadata.get("name", skill_path.name)
    description = metadata.get("description", "")

    # Handle allowed-tools (with hyphen) or allowed_tools (with underscore)
    allowed_tools = metadata.get("allowed-tools") or metadata.get("allowed_tools") or []

    # Ensure allowed_tools is a list
    if isinstance(allowed_tools, str):
        allowed_tools = [allowed_tools]

    version = metadata.get("version")
    if version is not None:
        version = str(version)  # Ensure version is a string

    author = metadata.get("author")

    return Skill(
        name=name,
        description=description,
        instructions=instructions,
        path=skill_path,
        allowed_tools=allowed_tools,
        version=version,
        author=author,
    )
