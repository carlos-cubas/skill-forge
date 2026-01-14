"""
Marketplace data classes for skill marketplace management.

This module provides the core data structures for representing marketplaces
and their skills:
- MarketplaceSource: Enum for different marketplace source types
- MarketplaceSkill: Metadata for a skill in a marketplace
- Marketplace: A configured skill marketplace

Marketplaces can be:
- GitHub repos (shorthand: owner/repo or full URL)
- Git URLs (any git-compatible URL)
- Local directories (for development/testing)
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class MarketplaceSource(Enum):
    """Types of marketplace sources.

    Attributes:
        GITHUB: GitHub repository (e.g., "owner/repo" or "github:owner/repo")
        GIT_URL: Git URL (e.g., "https://github.com/org/repo.git")
        LOCAL: Local directory path (e.g., "./local-marketplace" or "/abs/path")
    """

    GITHUB = "github"
    GIT_URL = "git"
    LOCAL = "local"


@dataclass
class MarketplaceSkill:
    """Skill metadata from a marketplace.

    Represents a skill's metadata as advertised by a marketplace,
    before the skill is installed locally.

    Attributes:
        name: Unique skill identifier (e.g., "rapid-interviewing")
        description: Human-readable description of the skill
        source: Full source reference (e.g., "github:owner/repo/skill-name")
        version: Semantic version string if available (e.g., "1.0.0")

    Example:
        >>> skill = MarketplaceSkill(
        ...     name="rapid-interviewing",
        ...     description="Conduct rapid discovery interviews",
        ...     source="github:dearmarkus/event-skills/rapid-interviewing",
        ...     version="1.0.0"
        ... )
    """

    name: str
    description: str
    source: str
    version: Optional[str] = None

    def __repr__(self) -> str:
        """Return a concise string representation."""
        return (
            f"MarketplaceSkill(name={self.name!r}, "
            f"description={self.description!r}, source={self.source!r})"
        )


@dataclass
class Marketplace:
    """A configured skill marketplace.

    Represents a source of skills that can be browsed and installed.
    Marketplaces are identified by a name (derived from source) and track
    available skills after fetching metadata.

    Attributes:
        name: Unique marketplace identifier (e.g., "dearmarkus/event-skills")
        source: Original source string used to add the marketplace
        source_type: Type of source (GITHUB, GIT_URL, or LOCAL)
        skills: List of available skills (populated after fetch)
        local_path: Local cache path for cloned repos (optional)
        remote_url: Resolved remote URL for git-based sources (optional)

    Example:
        >>> marketplace = Marketplace(
        ...     name="dearmarkus/event-skills",
        ...     source="dearmarkus/event-skills",
        ...     source_type=MarketplaceSource.GITHUB,
        ...     remote_url="https://github.com/dearmarkus/event-skills.git"
        ... )
    """

    name: str
    source: str
    source_type: MarketplaceSource
    skills: list[MarketplaceSkill] = field(default_factory=list)
    local_path: Optional[Path] = None
    remote_url: Optional[str] = None

    def __repr__(self) -> str:
        """Return a concise string representation."""
        return (
            f"Marketplace(name={self.name!r}, "
            f"source_type={self.source_type.value!r}, "
            f"skills_count={len(self.skills)})"
        )

    def to_dict(self) -> dict:
        """Serialize marketplace to a dictionary for JSON storage.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return {
            "name": self.name,
            "source": self.source,
            "source_type": self.source_type.value,
            "skills": [
                {
                    "name": skill.name,
                    "description": skill.description,
                    "source": skill.source,
                    "version": skill.version,
                }
                for skill in self.skills
            ],
            "local_path": str(self.local_path) if self.local_path else None,
            "remote_url": self.remote_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Marketplace":
        """Deserialize marketplace from a dictionary.

        Args:
            data: Dictionary representation (from JSON storage).

        Returns:
            Marketplace instance.
        """
        skills = [
            MarketplaceSkill(
                name=s["name"],
                description=s["description"],
                source=s["source"],
                version=s.get("version"),
            )
            for s in data.get("skills", [])
        ]

        local_path = None
        if data.get("local_path"):
            local_path = Path(data["local_path"])

        return cls(
            name=data["name"],
            source=data["source"],
            source_type=MarketplaceSource(data["source_type"]),
            skills=skills,
            local_path=local_path,
            remote_url=data.get("remote_url"),
        )


def parse_marketplace_source(source: str) -> tuple[MarketplaceSource, str, str]:
    """Parse a marketplace source string into its components.

    Handles multiple formats:
    - "owner/repo" -> GitHub shorthand
    - "github:owner/repo" -> Explicit GitHub
    - "https://github.com/owner/repo.git" -> Git URL
    - "./local/path" or "/absolute/path" -> Local directory

    Args:
        source: The source string to parse.

    Returns:
        Tuple of (source_type, name, resolved_url_or_path).

    Raises:
        ValueError: If the source format is not recognized.

    Example:
        >>> source_type, name, url = parse_marketplace_source("dearmarkus/skills")
        >>> source_type
        <MarketplaceSource.GITHUB: 'github'>
        >>> name
        'dearmarkus/skills'
        >>> url
        'https://github.com/dearmarkus/skills.git'
    """
    source = source.strip()

    # Check for explicit prefixes
    if source.startswith("github:"):
        # Explicit GitHub format: github:owner/repo
        repo_path = source[7:]  # Remove "github:" prefix
        if "/" not in repo_path:
            raise ValueError(
                f"Invalid GitHub source '{source}'. Expected format: github:owner/repo"
            )
        return (
            MarketplaceSource.GITHUB,
            repo_path,
            f"https://github.com/{repo_path}.git",
        )

    if source.startswith("git:") or source.startswith("git@"):
        # Git URL format
        url = source[4:] if source.startswith("git:") else source
        # Extract name from git URL
        name = _extract_name_from_git_url(url)
        return MarketplaceSource.GIT_URL, name, url

    if source.startswith("https://") or source.startswith("http://"):
        # HTTP(S) Git URL
        name = _extract_name_from_git_url(source)
        return MarketplaceSource.GIT_URL, name, source

    if source.startswith("./") or source.startswith("/") or source.startswith("~"):
        # Local path
        path = Path(source).expanduser().resolve()
        name = path.name
        return MarketplaceSource.LOCAL, name, str(path)

    # Default: treat as GitHub shorthand (owner/repo)
    if "/" in source and not source.startswith("."):
        return (
            MarketplaceSource.GITHUB,
            source,
            f"https://github.com/{source}.git",
        )

    raise ValueError(
        f"Unrecognized marketplace source format: '{source}'. "
        f"Expected: 'owner/repo', 'github:owner/repo', 'https://...', or './local/path'"
    )


def _extract_name_from_git_url(url: str) -> str:
    """Extract a marketplace name from a git URL.

    Args:
        url: Git URL (HTTPS or SSH format).

    Returns:
        Extracted name in 'owner/repo' format or just repo name.

    Example:
        >>> _extract_name_from_git_url("https://github.com/owner/repo.git")
        'owner/repo'
        >>> _extract_name_from_git_url("git@github.com:owner/repo.git")
        'owner/repo'
    """
    # Remove trailing .git
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    # Handle SSH format (git@github.com:owner/repo)
    if "@" in url and ":" in url:
        # git@github.com:owner/repo
        parts = url.split(":")
        if len(parts) == 2:
            return parts[1]

    # Handle HTTPS format (https://github.com/owner/repo)
    # Extract last two path components as owner/repo
    parts = url.rstrip("/").split("/")
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"

    # Fallback: just use the last path component
    return parts[-1] if parts else url
