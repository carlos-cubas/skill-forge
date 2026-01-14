"""
MarketplaceFetcher for fetching marketplace data from various sources.

This module provides the MarketplaceFetcher class that handles:
- Fetching skill metadata from local directories
- Cloning GitHub repositories and extracting skill metadata
- Cloning Git URLs and extracting skill metadata
- Downloading individual skills for installation

Skills are discovered by scanning for directories containing SKILL.md files.
"""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import yaml

from skillforge.core.marketplace import (
    Marketplace,
    MarketplaceSkill,
    MarketplaceSource,
)


logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Raised when fetching marketplace data fails."""

    pass


class MarketplaceFetcher:
    """Fetches marketplace data from various sources.

    The fetcher handles different marketplace source types:
    - Local: Scans the directory directly
    - GitHub: Clones the repo to a cache directory
    - Git URL: Clones the repo to a cache directory

    Attributes:
        cache_dir: Directory for caching cloned repositories.

    Example:
        >>> fetcher = MarketplaceFetcher()
        >>> skills = fetcher.fetch_metadata(marketplace)
        >>> print([s.name for s in skills])
        ['rapid-interviewing', 'goal-extraction']
    """

    DEFAULT_CACHE_DIR = Path.home() / ".skillforge" / "cache"

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """Initialize the MarketplaceFetcher.

        Args:
            cache_dir: Directory for caching cloned repositories.
                      Defaults to ~/.skillforge/cache/
        """
        self.cache_dir = cache_dir or self.DEFAULT_CACHE_DIR

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_metadata(self, marketplace: Marketplace) -> list[MarketplaceSkill]:
        """Fetch skill metadata from a marketplace.

        Dispatches to the appropriate fetch method based on source type.

        Args:
            marketplace: The Marketplace to fetch metadata from.

        Returns:
            List of MarketplaceSkill objects discovered in the marketplace.

        Raises:
            FetchError: If fetching fails.
        """
        if marketplace.source_type == MarketplaceSource.LOCAL:
            return self._fetch_local(marketplace)
        elif marketplace.source_type == MarketplaceSource.GITHUB:
            return self._fetch_github(marketplace)
        elif marketplace.source_type == MarketplaceSource.GIT_URL:
            return self._fetch_git(marketplace)
        else:
            raise FetchError(f"Unknown source type: {marketplace.source_type}")

    def _fetch_local(self, marketplace: Marketplace) -> list[MarketplaceSkill]:
        """Fetch skill metadata from a local directory.

        Args:
            marketplace: Marketplace with LOCAL source type.

        Returns:
            List of MarketplaceSkill objects.

        Raises:
            FetchError: If the local path doesn't exist or isn't a directory.
        """
        if marketplace.local_path is None:
            raise FetchError(f"Local marketplace '{marketplace.name}' has no local_path set")

        local_path = marketplace.local_path
        if not local_path.exists():
            raise FetchError(f"Local marketplace path does not exist: {local_path}")

        if not local_path.is_dir():
            raise FetchError(f"Local marketplace path is not a directory: {local_path}")

        return self._scan_for_skills(local_path, marketplace)

    def _fetch_github(self, marketplace: Marketplace) -> list[MarketplaceSkill]:
        """Fetch skill metadata from a GitHub repository.

        Clones the repository to the cache directory and scans for skills.

        Args:
            marketplace: Marketplace with GITHUB source type.

        Returns:
            List of MarketplaceSkill objects.

        Raises:
            FetchError: If cloning or scanning fails.
        """
        if marketplace.remote_url is None:
            raise FetchError(f"GitHub marketplace '{marketplace.name}' has no remote_url set")

        return self._clone_and_scan(marketplace)

    def _fetch_git(self, marketplace: Marketplace) -> list[MarketplaceSkill]:
        """Fetch skill metadata from a Git URL.

        Clones the repository to the cache directory and scans for skills.

        Args:
            marketplace: Marketplace with GIT_URL source type.

        Returns:
            List of MarketplaceSkill objects.

        Raises:
            FetchError: If cloning or scanning fails.
        """
        if marketplace.remote_url is None:
            raise FetchError(f"Git marketplace '{marketplace.name}' has no remote_url set")

        return self._clone_and_scan(marketplace)

    def _clone_and_scan(self, marketplace: Marketplace) -> list[MarketplaceSkill]:
        """Clone a remote repository and scan for skills.

        Args:
            marketplace: Marketplace with a remote_url set.

        Returns:
            List of MarketplaceSkill objects.

        Raises:
            FetchError: If cloning fails.
        """
        self._ensure_cache_dir()

        # Create a safe directory name from marketplace name
        safe_name = marketplace.name.replace("/", "_").replace("\\", "_")
        clone_path = self.cache_dir / safe_name

        # Remove existing clone to get fresh data
        if clone_path.exists():
            shutil.rmtree(clone_path)

        # Clone the repository
        try:
            logger.info(f"Cloning {marketplace.remote_url} to {clone_path}")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", marketplace.remote_url, str(clone_path)],
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
            )

            if result.returncode != 0:
                raise FetchError(
                    f"Git clone failed for {marketplace.remote_url}: {result.stderr}"
                )

        except subprocess.TimeoutExpired:
            raise FetchError(f"Git clone timed out for {marketplace.remote_url}")
        except FileNotFoundError:
            raise FetchError("Git is not installed or not in PATH")
        except Exception as e:
            raise FetchError(f"Failed to clone {marketplace.remote_url}: {e}")

        # Update marketplace local_path to the cloned location
        marketplace.local_path = clone_path

        return self._scan_for_skills(clone_path, marketplace)

    def _scan_for_skills(
        self, directory: Path, marketplace: Marketplace
    ) -> list[MarketplaceSkill]:
        """Scan a directory for skills (directories containing SKILL.md).

        Args:
            directory: The directory to scan.
            marketplace: The marketplace being scanned (for source attribution).

        Returns:
            List of MarketplaceSkill objects.
        """
        skills: list[MarketplaceSkill] = []

        # Recursively find all SKILL.md files
        for skill_md in directory.rglob("SKILL.md"):
            skill_dir = skill_md.parent

            try:
                metadata = self._parse_skill_metadata(skill_md)
                skill_name = metadata.get("name", skill_dir.name)
                description = metadata.get("description", "")
                version = metadata.get("version")
                if version is not None:
                    version = str(version)

                # Build source reference
                relative_path = skill_dir.relative_to(directory)
                if marketplace.source_type == MarketplaceSource.LOCAL:
                    source = f"local:{marketplace.name}/{relative_path}"
                else:
                    source = f"github:{marketplace.name}/{relative_path}"

                skill = MarketplaceSkill(
                    name=skill_name,
                    description=description,
                    source=source,
                    version=version,
                )
                skills.append(skill)

                logger.debug(f"Found skill: {skill_name} at {skill_dir}")

            except Exception as e:
                logger.warning(f"Failed to parse skill at {skill_dir}: {e}")
                continue

        logger.info(f"Found {len(skills)} skill(s) in {directory}")
        return skills

    def _parse_skill_metadata(self, skill_md_path: Path) -> dict:
        """Parse YAML frontmatter from a SKILL.md file.

        Only extracts frontmatter metadata, not the full skill content.

        Args:
            skill_md_path: Path to the SKILL.md file.

        Returns:
            Dictionary of metadata from frontmatter, or empty dict if none.
        """
        content = skill_md_path.read_text(encoding="utf-8")

        # Check for frontmatter
        if not content.startswith("---"):
            return {}

        # Find closing delimiter
        rest = content[3:].lstrip("\n")
        end_pos = rest.find("\n---")

        if end_pos == -1:
            return {}

        frontmatter = rest[:end_pos].strip()

        try:
            return yaml.safe_load(frontmatter) or {}
        except yaml.YAMLError:
            return {}

    def download_skill(
        self,
        marketplace: Marketplace,
        skill: MarketplaceSkill,
        destination: Path,
    ) -> Path:
        """Download a skill to a destination directory.

        For local marketplaces, copies the skill directory.
        For remote marketplaces, copies from the cached clone.

        Args:
            marketplace: The marketplace containing the skill.
            skill: The skill to download.
            destination: Directory to copy the skill to.

        Returns:
            Path to the downloaded skill directory.

        Raises:
            FetchError: If the skill cannot be found or copied.
        """
        if marketplace.local_path is None:
            # Need to clone first
            self.fetch_metadata(marketplace)

        if marketplace.local_path is None:
            raise FetchError(f"Marketplace '{marketplace.name}' has no local path after fetch")

        # Find the skill in the marketplace
        skill_path = self._find_skill_in_marketplace(marketplace, skill)

        if skill_path is None:
            raise FetchError(
                f"Could not find skill '{skill.name}' in marketplace '{marketplace.name}'"
            )

        # Create destination if needed
        destination.mkdir(parents=True, exist_ok=True)

        # Destination skill directory
        dest_skill_dir = destination / skill.name

        # Remove existing if present
        if dest_skill_dir.exists():
            shutil.rmtree(dest_skill_dir)

        # Copy the skill
        shutil.copytree(skill_path, dest_skill_dir)

        logger.info(f"Downloaded skill '{skill.name}' to {dest_skill_dir}")
        return dest_skill_dir

    def _find_skill_in_marketplace(
        self, marketplace: Marketplace, skill: MarketplaceSkill
    ) -> Optional[Path]:
        """Find a skill's directory in a marketplace's local path.

        Args:
            marketplace: The marketplace to search.
            skill: The skill to find.

        Returns:
            Path to the skill directory, or None if not found.
        """
        if marketplace.local_path is None:
            return None

        # Search for the skill by name
        for skill_md in marketplace.local_path.rglob("SKILL.md"):
            skill_dir = skill_md.parent

            # Check if this is the right skill
            metadata = self._parse_skill_metadata(skill_md)
            skill_name = metadata.get("name", skill_dir.name)

            if skill_name == skill.name:
                return skill_dir

        return None

    def clear_cache(self) -> None:
        """Clear all cached repository clones."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            logger.info(f"Cleared cache directory: {self.cache_dir}")
