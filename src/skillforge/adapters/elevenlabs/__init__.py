"""SkillForge ElevenLabs adapter for conversational AI agents."""

from skillforge.adapters.elevenlabs.meta_skill import (
    render_elevenlabs_meta_skill,
    format_skills_for_rag,
)
from skillforge.adapters.elevenlabs.credentials import (
    get_client,
    save_credentials,
    load_credentials,
    verify_credentials,
    delete_credentials,
    CredentialsError,
    CredentialsNotFoundError,
    InvalidCredentialsError,
)
from skillforge.adapters.elevenlabs.manifest import ElevenLabsManifest
from skillforge.adapters.elevenlabs.sync import (
    format_skill_for_rag as format_skill_for_kb,
    sync_skill_to_kb,
    sync_skills_to_kb,
    delete_skill_from_kb,
    SyncError,
)
from skillforge.adapters.elevenlabs.agent import (
    create_agent,
    configure_agent,
    build_prompt,
    get_kb_references,
    AgentError,
    SkillNotSyncedError,
)

__all__ = [
    # Meta-skill rendering
    "render_elevenlabs_meta_skill",
    "format_skills_for_rag",
    # Credentials management
    "get_client",
    "save_credentials",
    "load_credentials",
    "verify_credentials",
    "delete_credentials",
    "CredentialsError",
    "CredentialsNotFoundError",
    "InvalidCredentialsError",
    # Manifest
    "ElevenLabsManifest",
    # Sync operations
    "format_skill_for_kb",
    "sync_skill_to_kb",
    "sync_skills_to_kb",
    "delete_skill_from_kb",
    "SyncError",
    # Agent operations
    "create_agent",
    "configure_agent",
    "build_prompt",
    "get_kb_references",
    "AgentError",
    "SkillNotSyncedError",
]
