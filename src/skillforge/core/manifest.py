"""
Manifest manager for tracking installed skills.

This module provides the Manifest class that handles:
- Tracking installed skills in .skillforge/manifest.json
- Adding/removing skills from the manifest
- Listing and querying installed skills

The manifest file is stored in the project root under .skillforge/manifest.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class SkillNotInstalledError(Exception):
    """Raised when trying to access a skill that is not installed."""

    pass


class SkillAlreadyInstalledError(Exception):
    """Raised when trying to install a skill that is already installed."""

    pass


class Manifest:
    """Manages installed skills manifest (.skillforge/manifest.json).

    The manifest tracks which skills have been installed, their locations,
    source marketplaces, and versions. It persists this information to
    a JSON file in the project's .skillforge directory.

    Attributes:
        project_root: Root directory of the project.
        manifest_dir: Directory containing the manifest (.skillforge/).
        manifest_file: Path to the manifest.json file.

    Example:
        >>> manifest = Manifest()
        >>> manifest.add(
        ...     name="rapid-interviewing",
        ...     path="./agents/coach/skills/rapid-interviewing",
        ...     marketplace="dearmarkus/event-skills",
        ...     version="1.0.0"
        ... )
        >>> skill = manifest.get("rapid-interviewing")
        >>> print(skill["path"])
        './agents/coach/skills/rapid-interviewing'
    """

    MANIFEST_DIRNAME = ".skillforge"
    MANIFEST_FILENAME = "manifest.json"

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """Initialize the Manifest manager.

        Args:
            project_root: Root directory of the project.
                         Defaults to current working directory.
        """
        self.project_root = project_root or Path.cwd()
        self.manifest_dir = self.project_root / self.MANIFEST_DIRNAME
        self.manifest_file = self.manifest_dir / self.MANIFEST_FILENAME
        self._skills: dict[str, dict] = {}
        self._load()

    def _ensure_manifest_dir(self) -> None:
        """Ensure the manifest directory exists."""
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load the manifest from disk."""
        if not self.manifest_file.exists():
            logger.debug(f"No manifest found at {self.manifest_file}")
            return

        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._skills = data.get("skills", {})
            logger.debug(f"Loaded manifest with {len(self._skills)} skill(s)")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse manifest file: {e}")
        except Exception as e:
            logger.warning(f"Failed to load manifest: {e}")

    def _save(self) -> None:
        """Save the manifest to disk."""
        self._ensure_manifest_dir()

        data = {
            "version": "1.0",
            "skills": self._skills,
        }

        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved manifest with {len(self._skills)} skill(s)")

    def add(
        self,
        name: str,
        path: str,
        marketplace: str,
        version: Optional[str] = None,
    ) -> None:
        """Add a skill to the manifest.

        Args:
            name: Unique skill identifier.
            path: Relative path to the installed skill directory.
            marketplace: Name of the source marketplace.
            version: Semantic version string (optional).

        Raises:
            SkillAlreadyInstalledError: If a skill with this name is already installed.
        """
        if name in self._skills:
            existing = self._skills[name]
            raise SkillAlreadyInstalledError(
                f"Skill '{name}' is already installed at '{existing['path']}'. "
                f"Uninstall it first with 'skillforge uninstall {name}'."
            )

        self._skills[name] = {
            "path": path,
            "marketplace": marketplace,
            "version": version,
        }
        self._save()

        logger.info(f"Added skill '{name}' to manifest")

    def remove(self, name: str) -> dict:
        """Remove a skill from the manifest.

        Args:
            name: Name of the skill to remove.

        Returns:
            The skill entry that was removed.

        Raises:
            SkillNotInstalledError: If the skill is not in the manifest.
        """
        if name not in self._skills:
            available = ", ".join(self._skills.keys()) or "(none)"
            raise SkillNotInstalledError(
                f"Skill '{name}' is not installed. "
                f"Installed skills: {available}"
            )

        skill = self._skills.pop(name)
        self._save()

        logger.info(f"Removed skill '{name}' from manifest")
        return skill

    def get(self, name: str) -> dict:
        """Get a skill's manifest entry.

        Args:
            name: Name of the skill to retrieve.

        Returns:
            Dictionary with skill metadata (path, marketplace, version).

        Raises:
            SkillNotInstalledError: If the skill is not in the manifest.
        """
        if name not in self._skills:
            available = ", ".join(self._skills.keys()) or "(none)"
            raise SkillNotInstalledError(
                f"Skill '{name}' is not installed. "
                f"Installed skills: {available}"
            )

        return self._skills[name].copy()

    def list(self) -> dict[str, dict]:
        """List all installed skills.

        Returns:
            Dictionary mapping skill names to their metadata.
        """
        return self._skills.copy()

    def has(self, name: str) -> bool:
        """Check if a skill is installed.

        Args:
            name: Name of the skill to check.

        Returns:
            True if the skill is installed, False otherwise.
        """
        return name in self._skills

    def clear(self) -> None:
        """Clear all skills from the manifest (useful for testing)."""
        self._skills.clear()
        self._save()
        logger.info("Cleared all skills from manifest")
