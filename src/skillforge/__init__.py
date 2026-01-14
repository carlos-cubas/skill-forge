"""
SkillForge - A Python toolkit for equipping agents with domain-specific skills.

This package enables CrewAI and LangChain agents to be equipped with
skills using Anthropic's proven skill format.
"""

from skillforge.core.config import SkillForgeConfig, load_config, find_config_file
from skillforge.core.skill import Skill
from skillforge.core.loader import SkillLoader, SkillNotFoundError
from skillforge.utils.markdown import parse_skill_md, SkillParseError

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "SkillForgeConfig",
    "load_config",
    "find_config_file",
    "Skill",
    "SkillLoader",
    "SkillNotFoundError",
    "parse_skill_md",
    "SkillParseError",
]
