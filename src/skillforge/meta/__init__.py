"""SkillForge meta-skills - default skills that teach agents how to use SkillForge."""

from pathlib import Path

# Path to the default meta-skill
DEFAULT_META_SKILL_PATH = Path(__file__).parent / "using-skillforge" / "SKILL.md"

__all__ = ["DEFAULT_META_SKILL_PATH"]
