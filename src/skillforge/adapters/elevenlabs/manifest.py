"""
ElevenLabs manifest for tracking skills synced to Knowledge Base.

This module provides the ElevenLabsManifest class that tracks which skills
have been synced to ElevenLabs Knowledge Base, their document IDs, and
sync timestamps.

The manifest is stored in .skillforge/elevenlabs_manifest.json
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ElevenLabsManifest:
    """Manages ElevenLabs sync manifest (.skillforge/elevenlabs_manifest.json).

    The manifest tracks which skills have been synced to ElevenLabs Knowledge Base,
    storing document IDs and timestamps to enable updates and re-syncs.

    Attributes:
        project_root: Root directory of the project.
        manifest_dir: Directory containing the manifest (.skillforge/).
        manifest_file: Path to the elevenlabs_manifest.json file.

    Example:
        >>> manifest = ElevenLabsManifest()
        >>> manifest.set_document_id("rapid-interviewing", "doc_abc123")
        >>> doc_id = manifest.get_document_id("rapid-interviewing")
        >>> print(doc_id)
        'doc_abc123'
    """

    MANIFEST_DIRNAME = ".skillforge"
    MANIFEST_FILENAME = "elevenlabs_manifest.json"

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """Initialize the ElevenLabsManifest manager.

        Args:
            project_root: Root directory of the project.
                         Defaults to current working directory.
        """
        self.project_root = project_root or Path.cwd()
        self.manifest_dir = self.project_root / self.MANIFEST_DIRNAME
        self.manifest_file = self.manifest_dir / self.MANIFEST_FILENAME
        self._documents: dict[str, dict] = {}
        self._load()

    def _ensure_manifest_dir(self) -> None:
        """Ensure the manifest directory exists."""
        self.manifest_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> None:
        """Load the manifest from disk."""
        if not self.manifest_file.exists():
            logger.debug(f"No ElevenLabs manifest found at {self.manifest_file}")
            return

        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._documents = data.get("documents", {})
            logger.debug(
                f"Loaded ElevenLabs manifest with {len(self._documents)} document(s)"
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse ElevenLabs manifest file: {e}")
        except Exception as e:
            logger.warning(f"Failed to load ElevenLabs manifest: {e}")

    def save(self) -> None:
        """Save the manifest to disk."""
        self._ensure_manifest_dir()

        data = {
            "version": "1.0",
            "documents": self._documents,
        }

        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved ElevenLabs manifest with {len(self._documents)} document(s)")

    def get_document_id(self, skill_name: str) -> Optional[str]:
        """Get the ElevenLabs document ID for a skill.

        Args:
            skill_name: Name of the skill.

        Returns:
            The document ID if the skill has been synced, None otherwise.

        Example:
            >>> manifest.get_document_id("rapid-interviewing")
            'doc_abc123'
        """
        entry = self._documents.get(skill_name)
        if entry:
            return entry.get("document_id")
        return None

    def set_document_id(
        self,
        skill_name: str,
        doc_id: str,
        content_hash: Optional[str] = None,
    ) -> None:
        """Set the ElevenLabs document ID for a skill.

        Args:
            skill_name: Name of the skill.
            doc_id: The ElevenLabs document ID.
            content_hash: Optional hash of skill content for change detection.

        Example:
            >>> manifest.set_document_id("rapid-interviewing", "doc_abc123")
            >>> manifest.save()
        """
        self._documents[skill_name] = {
            "document_id": doc_id,
            "synced_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "content_hash": content_hash,
        }
        logger.debug(f"Set document ID for skill '{skill_name}': {doc_id}")

    def remove_document(self, skill_name: str) -> Optional[str]:
        """Remove a skill's document entry from the manifest.

        Args:
            skill_name: Name of the skill to remove.

        Returns:
            The document ID that was removed, or None if not found.

        Example:
            >>> manifest.remove_document("rapid-interviewing")
            'doc_abc123'
        """
        entry = self._documents.pop(skill_name, None)
        if entry:
            logger.debug(f"Removed document entry for skill '{skill_name}'")
            return entry.get("document_id")
        return None

    def get_sync_info(self, skill_name: str) -> Optional[dict]:
        """Get full sync information for a skill.

        Args:
            skill_name: Name of the skill.

        Returns:
            Dictionary with document_id, synced_at, and content_hash,
            or None if not synced.

        Example:
            >>> info = manifest.get_sync_info("rapid-interviewing")
            >>> print(info["synced_at"])
            '2025-01-14T10:30:00Z'
        """
        return self._documents.get(skill_name, {}).copy() or None

    def list_synced_skills(self) -> list[str]:
        """List all skills that have been synced.

        Returns:
            Sorted list of synced skill names.

        Example:
            >>> manifest.list_synced_skills()
            ['goal-extraction', 'rapid-interviewing']
        """
        return sorted(self._documents.keys())

    def has_skill(self, skill_name: str) -> bool:
        """Check if a skill has been synced.

        Args:
            skill_name: Name of the skill.

        Returns:
            True if the skill has been synced, False otherwise.
        """
        return skill_name in self._documents

    def get_content_hash(self, skill_name: str) -> Optional[str]:
        """Get the content hash for a synced skill.

        Args:
            skill_name: Name of the skill.

        Returns:
            The content hash if available, None otherwise.
        """
        entry = self._documents.get(skill_name)
        if entry:
            return entry.get("content_hash")
        return None

    def clear(self) -> None:
        """Clear all document entries (useful for testing)."""
        self._documents.clear()
        self.save()
        logger.info("Cleared all documents from ElevenLabs manifest")
