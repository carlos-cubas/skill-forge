"""
SkillForge configuration loading and management.

This module provides configuration handling for SkillForge, including:
- SkillForgeConfig dataclass for type-safe configuration
- Configuration file discovery (.skillforge.yaml)
- Default configuration values
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class SkillForgeConfig:
    """Configuration for SkillForge skill loading and management.

    Attributes:
        skill_paths: Glob patterns for discovering skills (e.g., ["./skills/*"])
        meta_skill: Path to custom meta-skill, or None for default
        skill_mode: Loading mode - "progressive" (lazy) or "eager" (immediate)
    """

    skill_paths: list[str] = field(default_factory=lambda: ["./skills/*"])
    meta_skill: Optional[str] = None
    skill_mode: str = "progressive"

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        valid_modes = {"progressive", "eager"}
        if self.skill_mode not in valid_modes:
            raise ValueError(
                f"Invalid skill_mode '{self.skill_mode}'. "
                f"Must be one of: {', '.join(valid_modes)}"
            )


def find_config_file(start_path: Optional[Path] = None) -> Optional[Path]:
    """Search for .skillforge.yaml in current and parent directories.

    Args:
        start_path: Directory to start searching from. Defaults to cwd.

    Returns:
        Path to config file if found, None otherwise.
    """
    current = start_path or Path.cwd()
    current = current.resolve()

    # Search up to filesystem root
    while True:
        config_path = current / ".skillforge.yaml"
        if config_path.exists():
            return config_path

        # Also check for .skillforge.yml variant
        config_path_yml = current / ".skillforge.yml"
        if config_path_yml.exists():
            return config_path_yml

        parent = current.parent
        if parent == current:
            # Reached filesystem root
            break
        current = parent

    return None


def load_config(config_path: Optional[Path] = None) -> SkillForgeConfig:
    """Load SkillForge configuration from file or return defaults.

    Args:
        config_path: Explicit path to config file. If None, searches
                    current and parent directories for .skillforge.yaml

    Returns:
        SkillForgeConfig instance with loaded or default values.

    Example:
        >>> config = load_config()
        >>> print(config.skill_paths)
        ['./skills/*']

        >>> config = load_config(Path("./my-config.yaml"))
        >>> print(config.skill_mode)
        'progressive'
    """
    # Find config file if not explicitly provided
    if config_path is None:
        config_path = find_config_file()

    # Return defaults if no config file found
    if config_path is None or not config_path.exists():
        return SkillForgeConfig()

    # Load and parse YAML config
    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)

    # Handle empty config file
    if raw_config is None:
        return SkillForgeConfig()

    # Extract known fields, ignore unknown ones
    return SkillForgeConfig(
        skill_paths=raw_config.get("skill_paths", ["./skills/*"]),
        meta_skill=raw_config.get("meta_skill"),
        skill_mode=raw_config.get("skill_mode", "progressive"),
    )
