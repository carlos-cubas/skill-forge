"""
Skill loader for discovering and loading skills from configured directories.

The SkillLoader discovers skills by scanning directories matching configured
glob patterns. Each directory containing a SKILL.md file is parsed into a
Skill object.

Usage:
    loader = SkillLoader(["./skills/*", "./agents/**/skills/*"])
    skills = loader.discover()
    skill = loader.get("rapid-interviewing")
"""

import glob
import logging
from pathlib import Path
from typing import Iterator, Optional

from skillforge.core.skill import Skill
from skillforge.utils.markdown import SkillParseError, parse_skill_md


logger = logging.getLogger(__name__)


class SkillNotFoundError(Exception):
    """Raised when a requested skill is not found."""

    pass


class SkillLoader:
    """Discovers and loads skills from configured directories.

    The loader scans directories matching the provided glob patterns,
    looking for directories containing SKILL.md files. Each valid skill
    directory is parsed into a Skill object.

    Attributes:
        skill_paths: List of glob patterns for skill discovery
        skills: Dictionary of loaded skills (populated after discover())

    Example:
        >>> loader = SkillLoader(["./skills/*"])
        >>> skills = loader.discover()
        >>> print(list(skills.keys()))
        ['rapid-interviewing', 'goal-extraction']

        >>> skill = loader.get("rapid-interviewing")
        >>> print(skill.description)
        'Conduct rapid discovery interviews'
    """

    def __init__(
        self,
        skill_paths: list[str],
        base_path: Optional[Path] = None,
    ) -> None:
        """Initialize the SkillLoader.

        Args:
            skill_paths: List of glob patterns for discovering skill directories.
                        Each pattern should match directories containing SKILL.md.
                        Example: ["./skills/*", "./agents/**/skills/*"]
            base_path: Base path for resolving relative glob patterns.
                      Defaults to current working directory.
        """
        self.skill_paths = skill_paths
        self.base_path = base_path or Path.cwd()
        self._skills: dict[str, Skill] = {}
        self._discovered = False

    @property
    def skills(self) -> dict[str, Skill]:
        """Get the dictionary of discovered skills.

        Returns:
            Dictionary mapping skill names to Skill objects.
            Empty if discover() hasn't been called yet.
        """
        return self._skills

    def _glob_skill_dirs(self, pattern: str) -> Iterator[Path]:
        """Scan for directories matching a glob pattern.

        Only yields directories that contain a SKILL.md file.

        Args:
            pattern: Glob pattern to match directories.

        Yields:
            Paths to directories containing SKILL.md files.
        """
        # Make pattern absolute if relative
        if not Path(pattern).is_absolute():
            full_pattern = str(self.base_path / pattern)
        else:
            full_pattern = pattern

        # Use glob to find matching paths
        for match in glob.glob(full_pattern, recursive=True):
            path = Path(match)
            if path.is_dir():
                skill_md = path / "SKILL.md"
                if skill_md.exists():
                    yield path
                else:
                    logger.debug(
                        f"Directory {path} matched pattern but has no SKILL.md"
                    )

    def discover(self) -> dict[str, Skill]:
        """Scan and load all skills matching configured patterns.

        This method scans all directories matching the skill_paths patterns,
        parses each SKILL.md file found, and stores the resulting Skill
        objects. Duplicate skill names log a warning and keep the first found.

        Returns:
            Dictionary mapping skill names to Skill objects.

        Example:
            >>> loader = SkillLoader(["./skills/*"])
            >>> skills = loader.discover()
            >>> len(skills)
            3
        """
        self._skills.clear()
        errors: list[str] = []

        for pattern in self.skill_paths:
            logger.debug(f"Scanning for skills matching pattern: {pattern}")

            for skill_dir in self._glob_skill_dirs(pattern):
                try:
                    skill = parse_skill_md(skill_dir)

                    if skill.name in self._skills:
                        logger.warning(
                            f"Duplicate skill name '{skill.name}' found at "
                            f"{skill_dir}. Keeping first occurrence at "
                            f"{self._skills[skill.name].path}"
                        )
                        continue

                    self._skills[skill.name] = skill
                    logger.debug(f"Loaded skill: {skill.name} from {skill_dir}")

                except SkillParseError as e:
                    errors.append(str(e))
                    logger.warning(f"Failed to parse skill at {skill_dir}: {e}")

        self._discovered = True

        if errors:
            logger.warning(
                f"Skill discovery completed with {len(errors)} error(s). "
                f"Loaded {len(self._skills)} skill(s)."
            )
        else:
            logger.debug(f"Skill discovery completed. Loaded {len(self._skills)} skill(s).")

        return self._skills

    def get(self, name: str) -> Skill:
        """Get a skill by name.

        If discover() hasn't been called yet, it will be called automatically.

        Args:
            name: The name of the skill to retrieve.

        Returns:
            The Skill object with the given name.

        Raises:
            SkillNotFoundError: If no skill with the given name exists.

        Example:
            >>> loader = SkillLoader(["./skills/*"])
            >>> skill = loader.get("rapid-interviewing")
            >>> print(skill.name)
            'rapid-interviewing'
        """
        if not self._discovered:
            self.discover()

        if name not in self._skills:
            available = ", ".join(sorted(self._skills.keys())) or "(none)"
            raise SkillNotFoundError(
                f"Skill '{name}' not found. Available skills: {available}"
            )

        return self._skills[name]

    def list_skills(self) -> list[str]:
        """List all discovered skill names.

        If discover() hasn't been called yet, it will be called automatically.

        Returns:
            Sorted list of skill names.
        """
        if not self._discovered:
            self.discover()

        return sorted(self._skills.keys())

    def reload(self) -> dict[str, Skill]:
        """Re-discover skills, clearing the cache.

        This is useful if skills have been added or modified on disk.

        Returns:
            Dictionary mapping skill names to Skill objects.
        """
        self._discovered = False
        return self.discover()
