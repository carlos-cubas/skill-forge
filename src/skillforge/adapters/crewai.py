"""
CrewAI adapter for SkillForge.

This module provides a drop-in replacement for crewai.Agent that adds
skill support. Skills are loaded and injected into the agent's backstory,
either progressively (meta-skill only) or fully (complete skill content).
"""

from typing import Optional

try:
    from crewai import Agent as CrewAIAgent
except ImportError:
    raise ImportError(
        "CrewAI is required to use the CrewAI adapter. "
        "Install it with: pip install skillforge[crewai]"
    )

from skillforge.core.config import load_config
from skillforge.core.loader import SkillLoader
from skillforge.core.meta_skill import render_meta_skill
from skillforge.core.skill import Skill


class Agent(CrewAIAgent):
    """Drop-in replacement for crewai.Agent with skill support.

    This class extends CrewAI's Agent to add SkillForge skill support.
    Skills are injected into the agent's backstory based on the skill_mode:

    - progressive (default): Injects meta-skill with skill list; agent loads
      skills on-demand via `skillforge read` command
    - inject: Injects full skill content directly into backstory

    Attributes:
        _skills: List of skill names assigned to this agent
        _skill_mode: How skills are loaded ("progressive" or "inject")

    Example:
        >>> from skillforge.crewai import Agent
        >>>
        >>> agent = Agent(
        ...     role="Executive Coach",
        ...     goal="Conduct effective discovery interviews",
        ...     backstory="Expert executive coach with 20 years experience",
        ...     skills=["rapid-interviewing", "goal-extraction"]
        ... )
    """

    def __init__(
        self,
        *args,
        skills: Optional[list[str]] = None,
        skill_mode: str = "progressive",
        **kwargs,
    ) -> None:
        """Initialize the Agent with skill support.

        Args:
            *args: Positional arguments passed to CrewAI Agent.
            skills: List of skill names to load for this agent.
                   Skills are looked up via SkillForge configuration.
            skill_mode: How to inject skills into the agent:
                       - "progressive": Inject meta-skill only; agent loads
                         skills on-demand (default)
                       - "inject": Inject full skill content into backstory
            **kwargs: Keyword arguments passed to CrewAI Agent.

        Raises:
            SkillNotFoundError: If a requested skill is not found.
            ValueError: If skill_mode is not "progressive" or "inject".
        """
        # Validate skill_mode
        valid_modes = {"progressive", "inject"}
        if skill_mode not in valid_modes:
            raise ValueError(
                f"Invalid skill_mode '{skill_mode}'. "
                f"Must be one of: {', '.join(sorted(valid_modes))}"
            )

        # Load skills if provided
        if skills:
            config = load_config()
            loader = SkillLoader(skill_paths=config.skill_paths)
            skill_objects = [loader.get(name) for name in skills]

            original_backstory = kwargs.get("backstory", "")
            kwargs["backstory"] = self._build_backstory(
                original_backstory, skill_objects, skill_mode
            )

        super().__init__(*args, **kwargs)

        self._skills = skills or []
        self._skill_mode = skill_mode

    def _build_backstory(
        self, original: str, skills: list[Skill], mode: str
    ) -> str:
        """Build the enhanced backstory with skill content.

        Args:
            original: The original backstory string.
            skills: List of Skill objects to include.
            mode: The skill injection mode ("progressive" or "inject").

        Returns:
            The enhanced backstory with skills injected.
        """
        if mode == "inject":
            return self._inject_full_skills(original, skills)
        else:
            # Progressive mode: inject meta-skill with skill list
            meta_skill_content = render_meta_skill(skills)
            if original:
                return f"{original}\n\n{meta_skill_content}"
            return meta_skill_content

    def _inject_full_skills(self, original: str, skills: list[Skill]) -> str:
        """Inject full skill content into backstory.

        Args:
            original: The original backstory string.
            skills: List of Skill objects to inject.

        Returns:
            Backstory with full skill instructions appended.
        """
        parts = [original] if original else []
        parts.append("\n## Available Skills\n")
        for skill in skills:
            parts.append(f"\n### {skill.name}\n\n{skill.instructions}\n")
        return "".join(parts)

    @property
    def skills(self) -> list[str]:
        """Get the list of skill names assigned to this agent."""
        return self._skills

    @property
    def skill_mode(self) -> str:
        """Get the skill injection mode."""
        return self._skill_mode


def agent_from_config(config: dict, **overrides) -> Agent:
    """Create an Agent from a YAML config dictionary.

    This helper function creates a SkillForge Agent from a configuration
    dictionary, typically loaded from a YAML file.

    Args:
        config: Dictionary with agent configuration. Expected keys:
               - role: Agent's role (required)
               - goal: Agent's goal (required)
               - backstory: Agent's backstory (optional)
               - skills: List of skill names (optional)
        **overrides: Additional keyword arguments to override config values.

    Returns:
        A configured Agent instance.

    Example:
        >>> config = {
        ...     "role": "Executive Coach",
        ...     "goal": "Conduct discovery interviews",
        ...     "backstory": "Expert coach",
        ...     "skills": ["rapid-interviewing"]
        ... }
        >>> agent = agent_from_config(config)
    """
    return Agent(
        role=config.get("role"),
        goal=config.get("goal"),
        backstory=config.get("backstory", ""),
        skills=config.get("skills", []),
        **overrides,
    )
