"""
MarketplaceRegistry for managing configured skill marketplaces.

This module provides the MarketplaceRegistry class that handles:
- Adding and removing marketplaces
- Persisting marketplace configuration to disk
- Finding skills across marketplaces
- Updating marketplace metadata

Configuration is stored in ~/.skillforge/marketplaces.json by default.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from skillforge.core.marketplace import (
    Marketplace,
    MarketplaceSkill,
    MarketplaceSource,
    parse_marketplace_source,
)


logger = logging.getLogger(__name__)


class MarketplaceNotFoundError(Exception):
    """Raised when a requested marketplace is not found."""

    pass


class MarketplaceExistsError(Exception):
    """Raised when trying to add a marketplace that already exists."""

    pass


class SkillNotInMarketplaceError(Exception):
    """Raised when a skill is not found in a marketplace."""

    pass


class MarketplaceRegistry:
    """Manages configured skill marketplaces.

    The registry provides CRUD operations for marketplaces and persists
    the configuration to a JSON file. It supports multiple marketplace
    source types (GitHub, Git URLs, local directories).

    Attributes:
        config_dir: Directory where marketplace configuration is stored.
        config_file: Path to the marketplaces.json file.
        marketplaces: Dictionary mapping marketplace names to Marketplace objects.

    Example:
        >>> registry = MarketplaceRegistry()
        >>> marketplace = registry.add("dearmarkus/event-skills")
        >>> print(marketplace.name)
        'dearmarkus/event-skills'

        >>> registry.list()
        [Marketplace(name='dearmarkus/event-skills', ...)]

        >>> skill = registry.find_skill("rapid-interviewing", "dearmarkus/event-skills")
    """

    DEFAULT_CONFIG_DIR = Path.home() / ".skillforge"
    CONFIG_FILENAME = "marketplaces.json"

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        """Initialize the MarketplaceRegistry.

        Args:
            config_dir: Directory for storing marketplace configuration.
                       Defaults to ~/.skillforge/
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_file = self.config_dir / self.CONFIG_FILENAME
        self._marketplaces: dict[str, Marketplace] = {}
        self._load()

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load marketplaces from the configuration file."""
        if not self.config_file.exists():
            logger.debug(f"No marketplace config found at {self.config_file}")
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for mp_data in data.get("marketplaces", []):
                marketplace = Marketplace.from_dict(mp_data)
                self._marketplaces[marketplace.name] = marketplace

            logger.debug(f"Loaded {len(self._marketplaces)} marketplace(s)")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse marketplace config: {e}")
        except Exception as e:
            logger.warning(f"Failed to load marketplace config: {e}")

    def _save(self) -> None:
        """Save marketplaces to the configuration file."""
        self._ensure_config_dir()

        data = {
            "version": "1.0",
            "marketplaces": [mp.to_dict() for mp in self._marketplaces.values()],
        }

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved {len(self._marketplaces)} marketplace(s) to {self.config_file}")

    def add(self, source: str) -> Marketplace:
        """Add a new marketplace.

        Parses the source string to determine the marketplace type and
        creates a new Marketplace entry. Does not fetch skills yet -
        call update() to fetch skill metadata.

        Supported formats:
        - "owner/repo" - GitHub shorthand
        - "github:owner/repo" - Explicit GitHub
        - "https://github.com/org/repo.git" - Git URL
        - "./local-path" - Local directory

        Args:
            source: The marketplace source string.

        Returns:
            The newly created Marketplace object.

        Raises:
            MarketplaceExistsError: If a marketplace with this name already exists.
            ValueError: If the source format is not recognized.

        Example:
            >>> registry = MarketplaceRegistry()
            >>> mp = registry.add("dearmarkus/event-skills")
            >>> mp.source_type
            <MarketplaceSource.GITHUB: 'github'>
        """
        source_type, name, resolved = parse_marketplace_source(source)

        if name in self._marketplaces:
            raise MarketplaceExistsError(
                f"Marketplace '{name}' already exists. "
                f"Remove it first with remove('{name}') to re-add."
            )

        marketplace = Marketplace(
            name=name,
            source=source,
            source_type=source_type,
        )

        # Set resolved path or URL based on source type
        if source_type == MarketplaceSource.LOCAL:
            marketplace.local_path = Path(resolved)
        else:
            marketplace.remote_url = resolved

        self._marketplaces[name] = marketplace
        self._save()

        logger.info(f"Added marketplace: {name} ({source_type.value})")
        return marketplace

    def remove(self, name: str) -> None:
        """Remove a marketplace by name.

        Args:
            name: The name of the marketplace to remove.

        Raises:
            MarketplaceNotFoundError: If no marketplace with this name exists.
        """
        if name not in self._marketplaces:
            raise MarketplaceNotFoundError(
                f"Marketplace '{name}' not found. "
                f"Available marketplaces: {', '.join(self._marketplaces.keys()) or '(none)'}"
            )

        del self._marketplaces[name]
        self._save()

        logger.info(f"Removed marketplace: {name}")

    def list(self) -> list[Marketplace]:
        """List all configured marketplaces.

        Returns:
            List of all Marketplace objects, sorted by name.
        """
        return sorted(self._marketplaces.values(), key=lambda m: m.name)

    def get(self, name: str) -> Marketplace:
        """Get a marketplace by name.

        Args:
            name: The name of the marketplace to retrieve.

        Returns:
            The Marketplace object.

        Raises:
            MarketplaceNotFoundError: If no marketplace with this name exists.
        """
        if name not in self._marketplaces:
            raise MarketplaceNotFoundError(
                f"Marketplace '{name}' not found. "
                f"Available marketplaces: {', '.join(self._marketplaces.keys()) or '(none)'}"
            )

        return self._marketplaces[name]

    def update(self, name: Optional[str] = None, fetcher: Optional["MarketplaceFetcher"] = None) -> None:
        """Update marketplace metadata by fetching from source.

        If name is provided, only that marketplace is updated.
        Otherwise, all marketplaces are updated.

        Args:
            name: Optional marketplace name to update. If None, updates all.
            fetcher: Optional MarketplaceFetcher instance. If None, creates one.

        Raises:
            MarketplaceNotFoundError: If the specified marketplace doesn't exist.
        """
        # Import here to avoid circular dependency
        from skillforge.core.fetcher import MarketplaceFetcher

        if fetcher is None:
            fetcher = MarketplaceFetcher()

        if name is not None:
            marketplace = self.get(name)
            marketplaces_to_update = [marketplace]
        else:
            marketplaces_to_update = list(self._marketplaces.values())

        for marketplace in marketplaces_to_update:
            try:
                skills = fetcher.fetch_metadata(marketplace)
                marketplace.skills = skills
                logger.info(
                    f"Updated marketplace '{marketplace.name}': "
                    f"found {len(skills)} skill(s)"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to update marketplace '{marketplace.name}': {e}"
                )

        self._save()

    def find_skill(self, skill_name: str, marketplace_name: str) -> MarketplaceSkill:
        """Find a skill in a specific marketplace.

        Args:
            skill_name: The name of the skill to find.
            marketplace_name: The name of the marketplace to search in.

        Returns:
            The MarketplaceSkill object.

        Raises:
            MarketplaceNotFoundError: If the marketplace doesn't exist.
            SkillNotInMarketplaceError: If the skill is not in the marketplace.
        """
        marketplace = self.get(marketplace_name)

        for skill in marketplace.skills:
            if skill.name == skill_name:
                return skill

        available = ", ".join(s.name for s in marketplace.skills) or "(none - run update first)"
        raise SkillNotInMarketplaceError(
            f"Skill '{skill_name}' not found in marketplace '{marketplace_name}'. "
            f"Available skills: {available}"
        )

    def search_skill(self, skill_name: str) -> list[tuple[Marketplace, MarketplaceSkill]]:
        """Search for a skill across all marketplaces.

        Args:
            skill_name: The name of the skill to search for.

        Returns:
            List of (Marketplace, MarketplaceSkill) tuples for all matches.
        """
        results: list[tuple[Marketplace, MarketplaceSkill]] = []

        for marketplace in self._marketplaces.values():
            for skill in marketplace.skills:
                if skill.name == skill_name:
                    results.append((marketplace, skill))

        return results

    def clear(self) -> None:
        """Remove all marketplaces (useful for testing)."""
        self._marketplaces.clear()
        self._save()
        logger.info("Cleared all marketplaces")
