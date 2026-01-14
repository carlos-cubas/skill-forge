"""
Meta-skill rendering for SkillForge.

This module provides functions to render the using-skillforge meta-skill
with dynamically populated available skills list. The meta-skill teaches
agents how to discover and use SkillForge skills at runtime.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skillforge.core.skill import Skill


# Path to the meta-skill template
META_SKILL_PATH = Path(__file__).parent.parent / "meta" / "using-skillforge" / "SKILL.md"

# Template variable placeholder
AVAILABLE_SKILLS_PLACEHOLDER = "{available_skills}"


def get_meta_skill_content() -> str:
    """Get raw meta-skill template content.

    Reads the using-skillforge SKILL.md file and returns its raw content,
    including the {available_skills} template placeholder.

    Returns:
        The raw content of the meta-skill template file.

    Raises:
        FileNotFoundError: If the meta-skill SKILL.md file is not found.

    Example:
        >>> content = get_meta_skill_content()
        >>> "{available_skills}" in content
        True
    """
    if not META_SKILL_PATH.exists():
        raise FileNotFoundError(
            f"Meta-skill template not found at {META_SKILL_PATH}. "
            "This may indicate a corrupted SkillForge installation."
        )

    return META_SKILL_PATH.read_text(encoding="utf-8")


def format_skills_list(skills: list["Skill"]) -> str:
    """Format skills as a markdown list.

    Creates a formatted markdown list of skills with their names,
    descriptions, and paths for easy reference by agents.

    Args:
        skills: List of Skill objects to format.

    Returns:
        A markdown-formatted string listing all skills.
        Returns "(No skills available)" if the list is empty.

    Example:
        >>> from skillforge.core.skill import Skill
        >>> from pathlib import Path
        >>> skills = [
        ...     Skill(
        ...         name="rapid-interviewing",
        ...         description="Conduct rapid discovery interviews",
        ...         instructions="...",
        ...         path=Path("./skills/rapid-interviewing")
        ...     )
        ... ]
        >>> print(format_skills_list(skills))
        - **rapid-interviewing**: Conduct rapid discovery interviews (`./skills/rapid-interviewing`)
    """
    if not skills:
        return "(No skills available)"

    lines = []
    for skill in skills:
        description = skill.description or "(no description)"
        lines.append(f"- **{skill.name}**: {description} (`{skill.path}`)")

    return "\n".join(lines)


def render_meta_skill(available_skills: list["Skill"]) -> str:
    """Render the meta-skill with available skills list.

    Loads the meta-skill template and replaces the {available_skills}
    placeholder with a formatted list of the provided skills.

    Args:
        available_skills: List of Skill objects to include in the rendered output.

    Returns:
        The fully rendered meta-skill content with the available skills
        list populated.

    Raises:
        FileNotFoundError: If the meta-skill template is not found.

    Example:
        >>> from skillforge.core.skill import Skill
        >>> from pathlib import Path
        >>> skills = [
        ...     Skill(
        ...         name="rapid-interviewing",
        ...         description="Conduct rapid discovery interviews",
        ...         instructions="...",
        ...         path=Path("./skills/rapid-interviewing")
        ...     )
        ... ]
        >>> rendered = render_meta_skill(skills)
        >>> "rapid-interviewing" in rendered
        True
        >>> "{available_skills}" in rendered
        False
    """
    template = get_meta_skill_content()
    skills_list = format_skills_list(available_skills)

    return template.replace(AVAILABLE_SKILLS_PLACEHOLDER, skills_list)
