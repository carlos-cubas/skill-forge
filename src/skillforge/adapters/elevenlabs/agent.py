"""
ElevenLabs agent creation and configuration with skills.

This module provides functions to create and configure ElevenLabs agents
with SkillForge skills via Knowledge Base integration.

The combined agent prompt follows this structure:
1. Core identity prompt (user-provided)
2. Meta-skill instructions (how to use skills)
3. Skill directory (available skills with KB query instructions)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from skillforge.adapters.elevenlabs.credentials import get_client
from skillforge.adapters.elevenlabs.manifest import ElevenLabsManifest
from skillforge.adapters.elevenlabs.meta_skill import (
    format_skills_for_rag,
    get_elevenlabs_meta_skill_content,
)
from skillforge.core.config import load_config
from skillforge.core.loader import SkillLoader
from skillforge.core.skill import Skill

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Raised when agent creation or configuration fails."""

    pass


class SkillNotSyncedError(AgentError):
    """Raised when a skill has not been synced to ElevenLabs KB."""

    pass


def build_prompt(
    core_prompt: str,
    skill_names: list[str],
    manifest: Optional[ElevenLabsManifest] = None,
) -> str:
    """Build combined prompt: core identity + meta-skill + skill directory.

    The combined prompt teaches the agent how to use SkillForge skills
    and provides a directory of available skills with RAG query instructions.

    Args:
        core_prompt: The core identity/system prompt for the agent.
        skill_names: List of skill names to include in the directory.
        manifest: Optional ElevenLabsManifest. If None, creates a new one.

    Returns:
        Combined prompt string ready for agent configuration.

    Raises:
        SkillNotSyncedError: If any skill in skill_names is not synced to KB.

    Example:
        >>> prompt = build_prompt(
        ...     core_prompt="You are a math tutor.",
        ...     skill_names=["socratic-questioning", "adaptive-scaffolding"]
        ... )
        >>> "You are a math tutor" in prompt
        True
        >>> "SKILL: socratic-questioning" in prompt
        True
    """
    if manifest is None:
        manifest = ElevenLabsManifest()

    # Validate all skills are synced
    unsynced = []
    for name in skill_names:
        if not manifest.has_skill(name):
            unsynced.append(name)

    if unsynced:
        raise SkillNotSyncedError(
            f"Skills not synced to ElevenLabs KB: {', '.join(unsynced)}. "
            f"Run 'skillforge elevenlabs sync --skills {','.join(unsynced)}' first."
        )

    # Load skills to get their metadata
    config = load_config()
    loader = SkillLoader(config.skill_paths)
    skills = loader.discover()

    # Build skill objects for formatting
    skill_objects: list[Skill] = []
    for name in skill_names:
        if name in skills:
            skill_objects.append(skills[name])
        else:
            # Skill synced but not found locally - create minimal object
            skill_objects.append(
                Skill(
                    name=name,
                    description="(synced to ElevenLabs KB)",
                    instructions="",
                    path=Path("."),
                )
            )

    # Get meta-skill template and format with skills
    meta_skill_template = get_elevenlabs_meta_skill_content()
    skills_list = format_skills_for_rag(skill_objects)
    meta_skill_content = meta_skill_template.replace("{available_skills}", skills_list)

    # Remove frontmatter from meta-skill (starts with --- and ends with ---)
    if meta_skill_content.startswith("---"):
        # Find the second ---
        end_idx = meta_skill_content.find("---", 3)
        if end_idx != -1:
            meta_skill_content = meta_skill_content[end_idx + 3:].strip()

    # Combine: core prompt + separator + meta-skill
    combined = f"""{core_prompt.strip()}

---

{meta_skill_content}"""

    return combined


def get_kb_references(
    skill_names: list[str],
    manifest: Optional[ElevenLabsManifest] = None,
) -> list[dict]:
    """Get Knowledge Base document references for skills.

    Returns a list of KB reference dicts suitable for the ElevenLabs SDK
    conversation_config.agent.prompt.knowledge_base field.

    Args:
        skill_names: List of skill names to get references for.
        manifest: Optional ElevenLabsManifest. If None, creates a new one.

    Returns:
        List of KB reference dictionaries with type, name, id, and usage_mode.

    Raises:
        SkillNotSyncedError: If any skill in skill_names is not synced to KB.

    Example:
        >>> refs = get_kb_references(["socratic-questioning"])
        >>> refs[0]["type"]
        'text'
        >>> refs[0]["usage_mode"]
        'auto'
    """
    if manifest is None:
        manifest = ElevenLabsManifest()

    references = []
    unsynced = []

    for name in skill_names:
        doc_id = manifest.get_document_id(name)
        if not doc_id:
            unsynced.append(name)
            continue

        references.append({
            "type": "text",
            "name": f"SKILL: {name}",
            "id": doc_id,
            "usage_mode": "auto",
        })

    if unsynced:
        raise SkillNotSyncedError(
            f"Skills not synced to ElevenLabs KB: {', '.join(unsynced)}. "
            f"Run 'skillforge elevenlabs sync --skills {','.join(unsynced)}' first."
        )

    return references


def create_agent(
    name: str,
    core_prompt: str,
    first_message: str,
    skills: list[str],
    voice_id: Optional[str] = None,
    language: str = "en",
    llm: str = "gpt-4o-mini",
    manifest: Optional[ElevenLabsManifest] = None,
) -> str:
    """Create a new ElevenLabs agent with skills.

    Creates an agent configured with the combined prompt (core + meta-skill
    + skill directory) and KB references for each skill.

    Args:
        name: Name for the new agent.
        core_prompt: The core identity/system prompt for the agent.
        first_message: Initial message the agent sends to users.
        skills: List of skill names to equip the agent with.
        voice_id: Optional ElevenLabs voice ID. Defaults to SDK default.
        language: Agent language code (default: "en").
        llm: LLM model to use (default: "gpt-4o-mini").
        manifest: Optional ElevenLabsManifest. If None, creates a new one.

    Returns:
        The ID of the created agent.

    Raises:
        SkillNotSyncedError: If any skill is not synced to KB.
        AgentError: If agent creation fails.

    Example:
        >>> agent_id = create_agent(
        ...     name="Math Tutor",
        ...     core_prompt="You are an expert math tutor.",
        ...     first_message="Hi! What math topic shall we explore?",
        ...     skills=["socratic-questioning", "adaptive-scaffolding"]
        ... )
        >>> print(f"Created agent: {agent_id}")
    """
    if manifest is None:
        manifest = ElevenLabsManifest()

    # Build combined prompt and get KB references
    combined_prompt = build_prompt(core_prompt, skills, manifest)
    kb_references = get_kb_references(skills, manifest)

    # Build conversation config
    prompt_config: dict = {
        "prompt": combined_prompt,
        "llm": llm,
    }

    if kb_references:
        prompt_config["knowledge_base"] = kb_references

    agent_config: dict = {
        "first_message": first_message,
        "language": language,
        "prompt": prompt_config,
    }

    conversation_config: dict = {
        "agent": agent_config,
    }

    # Add voice if specified
    if voice_id:
        conversation_config["tts"] = {
            "voice_id": voice_id,
        }

    try:
        client = get_client()
        agent = client.conversational_ai.agents.create(
            name=name,
            conversation_config=conversation_config,
        )

        agent_id = getattr(agent, "agent_id", None)
        if not agent_id:
            raise AgentError("Agent created but no ID returned")

        logger.info(f"Created agent '{name}' with ID: {agent_id}")
        return agent_id

    except SkillNotSyncedError:
        raise
    except Exception as e:
        raise AgentError(f"Failed to create agent '{name}': {e}") from e


def configure_agent(
    agent_id: str,
    skills: list[str],
    core_prompt: Optional[str] = None,
    preserve_prompt: bool = True,
    manifest: Optional[ElevenLabsManifest] = None,
) -> None:
    """Configure an existing ElevenLabs agent with skills.

    Updates the agent's prompt to include meta-skill instructions and
    skill directory, and configures KB references for skill retrieval.

    Args:
        agent_id: ID of the agent to configure.
        skills: List of skill names to equip the agent with.
        core_prompt: Optional new core prompt. If None and preserve_prompt=True,
                    extracts core prompt from existing agent.
        preserve_prompt: If True and core_prompt is None, preserves the existing
                        core prompt portion (before any "---" separator).
        manifest: Optional ElevenLabsManifest. If None, creates a new one.

    Raises:
        SkillNotSyncedError: If any skill is not synced to KB.
        AgentError: If agent configuration fails.

    Example:
        >>> configure_agent(
        ...     agent_id="abc123",
        ...     skills=["socratic-questioning", "adaptive-scaffolding"]
        ... )
    """
    if manifest is None:
        manifest = ElevenLabsManifest()

    client = get_client()

    # Get existing agent config if needed
    existing_prompt = None
    existing_first_message = "Hello!"
    existing_language = "en"
    existing_llm = "gpt-4o-mini"

    try:
        existing_agent = client.conversational_ai.agents.get(agent_id)

        # Extract existing configuration
        if hasattr(existing_agent, "conversation_config"):
            conv_config = existing_agent.conversation_config
            if hasattr(conv_config, "agent"):
                agent_conf = conv_config.agent
                if hasattr(agent_conf, "first_message"):
                    existing_first_message = agent_conf.first_message or existing_first_message
                if hasattr(agent_conf, "language"):
                    existing_language = agent_conf.language or existing_language
                if hasattr(agent_conf, "prompt"):
                    prompt_conf = agent_conf.prompt
                    if hasattr(prompt_conf, "prompt"):
                        existing_prompt = prompt_conf.prompt
                    if hasattr(prompt_conf, "llm"):
                        existing_llm = prompt_conf.llm or existing_llm

    except Exception as e:
        logger.warning(f"Could not retrieve existing agent config: {e}")

    # Determine core prompt
    if core_prompt is None:
        if preserve_prompt and existing_prompt:
            # Extract core prompt (everything before first "---" separator)
            if "---" in existing_prompt:
                core_prompt = existing_prompt.split("---")[0].strip()
            else:
                core_prompt = existing_prompt
        else:
            core_prompt = "You are a helpful assistant."

    # Build combined prompt and get KB references
    combined_prompt = build_prompt(core_prompt, skills, manifest)
    kb_references = get_kb_references(skills, manifest)

    # Build conversation config
    prompt_config: dict = {
        "prompt": combined_prompt,
        "llm": existing_llm,
    }

    if kb_references:
        prompt_config["knowledge_base"] = kb_references

    conversation_config: dict = {
        "agent": {
            "first_message": existing_first_message,
            "language": existing_language,
            "prompt": prompt_config,
        }
    }

    try:
        client.conversational_ai.agents.update(
            agent_id=agent_id,
            conversation_config=conversation_config,
        )
        logger.info(f"Configured agent {agent_id} with skills: {', '.join(skills)}")

    except SkillNotSyncedError:
        raise
    except Exception as e:
        raise AgentError(f"Failed to configure agent {agent_id}: {e}") from e
