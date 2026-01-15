"""
High-level Agent class for ElevenLabs integration.

This module provides a Pythonic interface for creating and configuring
ElevenLabs agents with SkillForge skills.

Example:
    >>> from skillforge.elevenlabs import Agent, sync_skills
    >>>
    >>> # Sync skills to KB first
    >>> sync_skills()
    >>>
    >>> # Create new agent
    >>> agent = Agent.create(
    ...     name="Math Tutor",
    ...     system_prompt="You are a math tutor.",
    ...     skills=["socratic-questioning", "adaptive-scaffolding"]
    ... )
    >>>
    >>> # Configure existing agent
    >>> agent = Agent(agent_id="abc123")
    >>> agent.configure(skills=["socratic-questioning"])
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from skillforge.adapters.elevenlabs import (
    AgentError,
    SkillNotSyncedError,
    create_agent as _create_agent,
    configure_agent as _configure_agent,
    get_client,
)


@dataclass
class Agent:
    """ElevenLabs agent with SkillForge skill support.

    This class provides a high-level interface for working with ElevenLabs
    agents equipped with SkillForge skills.

    Attributes:
        agent_id: The ElevenLabs agent ID.
        name: The agent name (populated after create or get_details).
        skills: List of skill names equipped on this agent.

    Example:
        >>> # Wrap an existing agent
        >>> agent = Agent(agent_id="abc123")
        >>> agent.configure(skills=["rapid-interviewing"])
        >>>
        >>> # Create a new agent
        >>> agent = Agent.create(
        ...     name="Coach",
        ...     system_prompt="You are an executive coach.",
        ...     skills=["goal-extraction"]
        ... )
    """

    agent_id: str
    name: Optional[str] = None
    skills: list[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        name: str,
        system_prompt: str,
        skills: list[str],
        first_message: str = "Hello! How can I help you today?",
        voice_id: Optional[str] = None,
        language: str = "en",
        llm: str = "gpt-4o-mini",
    ) -> "Agent":
        """Create a new ElevenLabs agent with skills.

        Creates a new agent in ElevenLabs with the specified configuration,
        including the system prompt and skills. Skills must be synced to
        the ElevenLabs Knowledge Base before creating the agent.

        Args:
            name: Name for the new agent.
            system_prompt: The core system prompt (agent identity/personality).
            skills: List of skill names to equip the agent with.
            first_message: Initial greeting message. Default: "Hello! How can I help you today?"
            voice_id: Optional ElevenLabs voice ID.
            language: Agent language code. Default: "en".
            llm: LLM model to use. Default: "gpt-4o-mini".

        Returns:
            Agent instance wrapping the created agent.

        Raises:
            SkillNotSyncedError: If any skill is not synced to KB.
            AgentError: If agent creation fails.

        Example:
            >>> agent = Agent.create(
            ...     name="Math Tutor",
            ...     system_prompt="You are a dedicated math tutor who loves helping students.",
            ...     skills=["socratic-questioning", "adaptive-scaffolding"],
            ...     first_message="Hi! What math topic shall we explore today?"
            ... )
            >>> print(f"Created agent: {agent.agent_id}")
        """
        agent_id = _create_agent(
            name=name,
            core_prompt=system_prompt,
            first_message=first_message,
            skills=skills,
            voice_id=voice_id,
            language=language,
            llm=llm,
        )

        return cls(
            agent_id=agent_id,
            name=name,
            skills=list(skills),
        )

    def configure(
        self,
        skills: list[str],
        system_prompt: Optional[str] = None,
    ) -> None:
        """Configure this agent with skills.

        Updates the agent's configuration to include the specified skills.
        Skills must be synced to the ElevenLabs Knowledge Base first.

        If system_prompt is not provided, the existing prompt is preserved
        (the core part before any SkillForge metadata).

        Args:
            skills: List of skill names to equip the agent with.
            system_prompt: Optional new system prompt. If None, preserves existing.

        Raises:
            SkillNotSyncedError: If any skill is not synced to KB.
            AgentError: If agent configuration fails.

        Example:
            >>> agent = Agent(agent_id="abc123")
            >>> agent.configure(skills=["socratic-questioning", "adaptive-scaffolding"])
        """
        _configure_agent(
            agent_id=self.agent_id,
            skills=skills,
            core_prompt=system_prompt,
            preserve_prompt=system_prompt is None,
        )

        # Update local state
        self.skills = list(skills)

    def get_details(self) -> dict:
        """Get agent details from ElevenLabs.

        Fetches the current agent configuration from ElevenLabs API.

        Returns:
            Dictionary with agent details including:
            - agent_id: The agent ID
            - name: The agent name
            - conversation_config: Full conversation configuration

        Raises:
            AgentError: If fetching details fails.

        Example:
            >>> agent = Agent(agent_id="abc123")
            >>> details = agent.get_details()
            >>> print(f"Agent name: {details['name']}")
        """
        try:
            client = get_client()
            agent_data = client.conversational_ai.agents.get(self.agent_id)

            # Extract details into a dict
            details = {
                "agent_id": self.agent_id,
                "name": getattr(agent_data, "name", None),
            }

            # Add conversation config if available
            if hasattr(agent_data, "conversation_config"):
                conv_config = agent_data.conversation_config
                details["conversation_config"] = {}

                if hasattr(conv_config, "agent"):
                    agent_conf = conv_config.agent
                    details["conversation_config"]["agent"] = {
                        "first_message": getattr(agent_conf, "first_message", None),
                        "language": getattr(agent_conf, "language", None),
                    }

                    if hasattr(agent_conf, "prompt"):
                        prompt_conf = agent_conf.prompt
                        details["conversation_config"]["agent"]["prompt"] = {
                            "prompt": getattr(prompt_conf, "prompt", None),
                            "llm": getattr(prompt_conf, "llm", None),
                        }

            # Update local name if retrieved
            if details.get("name"):
                self.name = details["name"]

            return details

        except Exception as e:
            raise AgentError(f"Failed to get agent details for {self.agent_id}: {e}") from e


# Re-export exceptions for convenience
__all__ = ["Agent", "AgentError", "SkillNotSyncedError"]
