"""
High-level sync function for ElevenLabs integration.

This module provides a simple interface for syncing SkillForge skills
to ElevenLabs Knowledge Base.

Example:
    >>> from skillforge.elevenlabs import sync_skills
    >>>
    >>> # Sync all discovered skills
    >>> doc_ids = sync_skills()
    >>> print(f"Synced skills: {list(doc_ids.keys())}")
    >>>
    >>> # Sync specific skills
    >>> doc_ids = sync_skills(skill_names=["socratic-questioning", "adaptive-scaffolding"])
"""

from __future__ import annotations

from typing import Optional

from skillforge.adapters.elevenlabs import (
    SyncError,
    sync_skills_to_kb as _sync_skills_to_kb,
    ElevenLabsManifest,
)
from skillforge.core.config import load_config
from skillforge.core.loader import SkillLoader


def sync_skills(
    skill_names: Optional[list[str]] = None,
    force: bool = False,
) -> dict[str, str]:
    """Sync skills to ElevenLabs Knowledge Base.

    Uploads SkillForge skills to ElevenLabs KB, enabling RAG-based
    skill retrieval in conversational AI agents.

    If skill_names is not provided, syncs all discovered skills
    from the configured skill paths.

    Args:
        skill_names: Optional list of specific skill names to sync.
                    If None, syncs all discovered skills.
        force: If True, re-sync even if content hasn't changed.

    Returns:
        Dictionary mapping skill names to their KB document IDs.

    Raises:
        SyncError: If sync operation fails.
        ValueError: If specified skills are not found.

    Example:
        >>> # Sync all skills
        >>> doc_ids = sync_skills()
        >>> print(f"Synced: {doc_ids}")
        {'rapid-interviewing': 'doc_abc123', 'goal-extraction': 'doc_def456'}

        >>> # Sync specific skills only
        >>> doc_ids = sync_skills(skill_names=["rapid-interviewing"])
        >>> print(f"Synced: {doc_ids}")
        {'rapid-interviewing': 'doc_abc123'}

        >>> # Force re-sync all skills
        >>> doc_ids = sync_skills(force=True)
    """
    # Load configuration and discover skills
    config = load_config()
    loader = SkillLoader(config.skill_paths)
    all_skills = loader.discover()

    if not all_skills:
        raise ValueError(
            "No skills found. Check your .skillforge.yaml skill_paths configuration."
        )

    # Filter to specific skills if requested
    if skill_names is not None:
        # Validate all requested skills exist
        missing = [name for name in skill_names if name not in all_skills]
        if missing:
            raise ValueError(
                f"Skills not found: {', '.join(missing)}. "
                f"Available skills: {', '.join(all_skills.keys())}"
            )

        # Filter to only requested skills
        skills_to_sync = {name: all_skills[name] for name in skill_names}
    else:
        skills_to_sync = all_skills

    # Create manifest and sync
    manifest = ElevenLabsManifest()

    return _sync_skills_to_kb(
        skills=skills_to_sync,
        manifest=manifest,
        force=force,
    )


# Re-export SyncError for convenience
__all__ = ["sync_skills", "SyncError"]
