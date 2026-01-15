"""
SkillForge ElevenLabs Python API.

This module provides a high-level Pythonic interface for integrating
SkillForge skills with ElevenLabs conversational AI agents.

Usage:
    >>> from skillforge.elevenlabs import Agent, sync_skills
    >>>
    >>> # First, sync skills to ElevenLabs Knowledge Base
    >>> doc_ids = sync_skills()
    >>> print(f"Synced skills: {list(doc_ids.keys())}")
    >>>
    >>> # Create a new agent with skills
    >>> agent = Agent.create(
    ...     name="Math Tutor",
    ...     system_prompt="You are a dedicated math tutor who loves helping students.",
    ...     skills=["socratic-questioning", "adaptive-scaffolding"],
    ...     first_message="Hi! What math topic shall we explore today?"
    ... )
    >>> print(f"Created agent: {agent.agent_id}")
    >>>
    >>> # Or configure an existing agent
    >>> agent = Agent(agent_id="abc123")
    >>> agent.configure(skills=["socratic-questioning"])

The module wraps the lower-level adapter functions from
skillforge.adapters.elevenlabs, providing a cleaner class-based API.
"""

from skillforge.elevenlabs.agent import Agent, AgentError, SkillNotSyncedError
from skillforge.elevenlabs.sync import sync_skills, SyncError

__all__ = [
    # Agent class and operations
    "Agent",
    "AgentError",
    "SkillNotSyncedError",
    # Sync operations
    "sync_skills",
    "SyncError",
]
