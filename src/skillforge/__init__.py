"""
SkillForge - A Python toolkit for equipping agents with domain-specific skills.

This package enables CrewAI and LangChain agents to be equipped with
skills using Anthropic's proven skill format.
"""

from skillforge.core.config import SkillForgeConfig, load_config, find_config_file

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "SkillForgeConfig",
    "load_config",
    "find_config_file",
]
