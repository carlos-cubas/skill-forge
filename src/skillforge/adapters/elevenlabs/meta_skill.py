"""
Meta-skill rendering for ElevenLabs conversational AI agents.

This module provides functions to render the using-skillforge-elevenlabs meta-skill
with dynamically populated available skills list. The meta-skill teaches ElevenLabs
agents how to discover and use SkillForge skills via Knowledge Base RAG retrieval
instead of CLI commands.
"""

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from skillforge.core.skill import Skill


# Path to the ElevenLabs meta-skill template
META_SKILL_PATH = (
    Path(__file__).parent.parent.parent / "meta" / "using-skillforge-elevenlabs" / "SKILL.md"
)

# Template variable placeholder
AVAILABLE_SKILLS_PLACEHOLDER = "{available_skills}"


def get_elevenlabs_meta_skill_content() -> str:
    """Get raw ElevenLabs meta-skill template content.

    Reads the using-skillforge-elevenlabs SKILL.md file and returns its raw content,
    including the {available_skills} template placeholder.

    Returns:
        The raw content of the ElevenLabs meta-skill template file.

    Raises:
        FileNotFoundError: If the meta-skill SKILL.md file is not found.

    Example:
        >>> content = get_elevenlabs_meta_skill_content()
        >>> "{available_skills}" in content
        True
    """
    if not META_SKILL_PATH.exists():
        raise FileNotFoundError(
            f"ElevenLabs meta-skill template not found at {META_SKILL_PATH}. "
            "This may indicate a corrupted SkillForge installation."
        )

    return META_SKILL_PATH.read_text(encoding="utf-8")


def format_skills_for_rag(skills: list["Skill"]) -> str:
    """Format skills with RAG query instructions.

    Creates a formatted markdown list of skills with their names,
    descriptions, and Knowledge Base query instructions for ElevenLabs agents.

    Args:
        skills: List of Skill objects to format.

    Returns:
        A markdown-formatted string listing all skills with query instructions.
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
        >>> print(format_skills_for_rag(skills))
        - **rapid-interviewing**: Conduct rapid discovery interviews Query: "SKILL: rapid-interviewing"
    """
    if not skills:
        return "(No skills available)"

    lines = []
    for skill in skills:
        description = skill.description or "(no description)"
        lines.append(
            f"- **{skill.name}**: {description} "
            f'Query: "SKILL: {skill.name}"'
        )

    return "\n".join(lines)


def render_elevenlabs_meta_skill(available_skills: list["Skill"]) -> str:
    """Render the ElevenLabs meta-skill with available skills list.

    Loads the ElevenLabs meta-skill template and replaces the {available_skills}
    placeholder with a formatted list of the provided skills, including
    RAG query instructions for each skill.

    Args:
        available_skills: List of Skill objects to include in the rendered output.

    Returns:
        The fully rendered ElevenLabs meta-skill content with the available skills
        list populated and RAG query instructions.

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
        >>> rendered = render_elevenlabs_meta_skill(skills)
        >>> "rapid-interviewing" in rendered
        True
        >>> 'Query: "SKILL: rapid-interviewing"' in rendered
        True
        >>> "{available_skills}" in rendered
        False
    """
    template = get_elevenlabs_meta_skill_content()
    skills_list = format_skills_for_rag(available_skills)

    return template.replace(AVAILABLE_SKILLS_PLACEHOLDER, skills_list)
