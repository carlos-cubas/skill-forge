"""
Sync logic for uploading skills to ElevenLabs Knowledge Base.

This module provides functions to sync SkillForge skills to ElevenLabs KB,
enabling RAG-based skill retrieval in conversational AI agents.
"""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, Optional

from skillforge.adapters.elevenlabs.credentials import get_client
from skillforge.adapters.elevenlabs.manifest import ElevenLabsManifest

if TYPE_CHECKING:
    from skillforge.core.skill import Skill

logger = logging.getLogger(__name__)


class SyncError(Exception):
    """Raised when skill sync fails."""

    pass


def format_skill_for_rag(skill: "Skill") -> str:
    """Format skill content with SKILL header for RAG retrieval.

    Adds a `# SKILL: <name>` header to the skill content, which enables
    ElevenLabs agents to query for specific skills by name in the Knowledge Base.

    Args:
        skill: The Skill object to format.

    Returns:
        Formatted skill content with SKILL header.

    Example:
        >>> from skillforge.core.skill import Skill
        >>> from pathlib import Path
        >>> skill = Skill(
        ...     name="rapid-interviewing",
        ...     description="Conduct rapid interviews",
        ...     instructions="## When to Use\\n...",
        ...     path=Path("./skills/rapid-interviewing")
        ... )
        >>> content = format_skill_for_rag(skill)
        >>> content.startswith("# SKILL: rapid-interviewing")
        True
    """
    # Build formatted content with SKILL header
    lines = [f"# SKILL: {skill.name}"]

    # Add description if available
    if skill.description:
        lines.append(f"\n> {skill.description}")

    # Add main instructions content
    lines.append(f"\n{skill.instructions}")

    return "\n".join(lines)


def compute_content_hash(content: str) -> str:
    """Compute a hash of skill content for change detection.

    Args:
        content: The skill content to hash.

    Returns:
        SHA256 hash of the content.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def sync_skill_to_kb(
    skill: "Skill",
    manifest: ElevenLabsManifest,
    force: bool = False,
) -> tuple[str, bool]:
    """Sync a single skill to ElevenLabs Knowledge Base.

    Creates a new document or updates an existing one if the skill
    has already been synced.

    Args:
        skill: The Skill object to sync.
        manifest: ElevenLabsManifest for tracking document IDs.
        force: If True, re-sync even if content hasn't changed.

    Returns:
        Tuple of (document_id, was_updated). was_updated is True if
        a new document was created or existing one was updated.

    Raises:
        SyncError: If sync operation fails.

    Example:
        >>> doc_id, updated = sync_skill_to_kb(skill, manifest)
        >>> print(f"Synced to document: {doc_id}, updated: {updated}")
    """
    # Format skill content for RAG
    content = format_skill_for_rag(skill)
    content_hash = compute_content_hash(content)

    # Check if already synced
    existing_doc_id = manifest.get_document_id(skill.name)
    existing_hash = manifest.get_content_hash(skill.name)

    # Skip if content unchanged (unless force)
    if existing_doc_id and existing_hash == content_hash and not force:
        logger.debug(f"Skill '{skill.name}' unchanged, skipping sync")
        return existing_doc_id, False

    # Only get client when we need to make API calls
    client = get_client()

    try:
        if existing_doc_id:
            # Delete existing document and create new one
            # ElevenLabs API doesn't support in-place updates for text documents
            try:
                client.conversational_ai.knowledge_base.documents.delete(existing_doc_id)
                logger.debug(f"Deleted existing document: {existing_doc_id}")
            except Exception as e:
                logger.warning(f"Could not delete existing document: {e}")

        # Create new document
        doc_name = f"SKILL: {skill.name}"
        doc = client.conversational_ai.knowledge_base.documents.create_from_text(
            text=content,
            name=doc_name,
        )

        # Get document ID
        doc_id = getattr(doc, "id", None) or getattr(doc, "document_id", None)
        if not doc_id:
            raise SyncError(f"Document created but no ID returned for skill '{skill.name}'")

        # Update manifest
        manifest.set_document_id(skill.name, doc_id, content_hash)

        action = "Updated" if existing_doc_id else "Created"
        logger.info(f"{action} document for skill '{skill.name}': {doc_id}")

        return doc_id, True

    except Exception as e:
        raise SyncError(f"Failed to sync skill '{skill.name}': {e}") from e


def sync_skills_to_kb(
    skills: dict[str, "Skill"],
    manifest: Optional[ElevenLabsManifest] = None,
    force: bool = False,
) -> dict[str, str]:
    """Sync multiple skills to ElevenLabs Knowledge Base.

    Creates or updates documents in the Knowledge Base for each skill.

    Args:
        skills: Dictionary mapping skill names to Skill objects.
        manifest: Optional ElevenLabsManifest. If None, creates a new one.
        force: If True, re-sync all skills even if content unchanged.

    Returns:
        Dictionary mapping skill names to their document IDs.

    Raises:
        SyncError: If any sync operation fails (partial results may exist).

    Example:
        >>> from skillforge.core.loader import SkillLoader
        >>> loader = SkillLoader(["./skills/*"])
        >>> skills = loader.discover()
        >>> doc_ids = sync_skills_to_kb(skills)
        >>> print(doc_ids)
        {'rapid-interviewing': 'doc_abc123', 'goal-extraction': 'doc_def456'}
    """
    if manifest is None:
        manifest = ElevenLabsManifest()

    results: dict[str, str] = {}
    errors: list[str] = []

    for skill_name, skill in skills.items():
        try:
            doc_id, _ = sync_skill_to_kb(skill, manifest, force)
            results[skill_name] = doc_id
        except SyncError as e:
            errors.append(str(e))
            logger.error(f"Failed to sync skill '{skill_name}': {e}")

    # Save manifest after all syncs
    manifest.save()

    if errors:
        raise SyncError(
            f"Sync completed with {len(errors)} error(s):\n" + "\n".join(errors)
        )

    return results


def delete_skill_from_kb(
    skill_name: str,
    manifest: Optional[ElevenLabsManifest] = None,
) -> bool:
    """Delete a skill's document from ElevenLabs Knowledge Base.

    Args:
        skill_name: Name of the skill to delete.
        manifest: Optional ElevenLabsManifest. If None, creates a new one.

    Returns:
        True if document was deleted, False if not found in manifest.

    Example:
        >>> delete_skill_from_kb("rapid-interviewing")
        True
    """
    if manifest is None:
        manifest = ElevenLabsManifest()

    doc_id = manifest.get_document_id(skill_name)
    if not doc_id:
        logger.debug(f"Skill '{skill_name}' not found in manifest")
        return False

    try:
        client = get_client()
        client.conversational_ai.knowledge_base.documents.delete(doc_id)
        logger.info(f"Deleted document {doc_id} for skill '{skill_name}'")
    except Exception as e:
        logger.warning(f"Could not delete document from KB: {e}")

    # Remove from manifest regardless of API result
    manifest.remove_document(skill_name)
    manifest.save()

    return True
