"""
LangChain adapter for SkillForge.

This module provides a wrapper function for creating LangChain agents with
skill support. Skills are loaded and injected into the agent's system prompt,
either progressively (meta-skill only) or fully (complete skill content).

The adapter uses LangChain 1.2.x API:
    from langchain.agents import create_agent
    agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)

Example:
    from skillforge.langchain import create_agent

    agent = create_agent(
        llm=model,
        tools=[...],
        system_prompt="You are an executive coach",
        skills=["rapid-interviewing", "goal-extraction"]
    )
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

from skillforge.core.config import load_config
from skillforge.core.loader import SkillLoader
from skillforge.core.meta_skill import render_meta_skill
from skillforge.core.skill import Skill


def create_agent(
    llm: Any,
    tools: list[Any],
    system_prompt: str = "",
    skills: Optional[list[str]] = None,
    skill_mode: str = "progressive",
    **kwargs,
) -> Any:
    """Create a LangChain agent with skill support.

    This function wraps LangChain's create_agent to add SkillForge skill support.
    Skills are injected into the system prompt based on the skill_mode:

    - progressive (default): Injects meta-skill with skill list; agent loads
      skills on-demand via `skillforge read` command
    - inject: Injects full skill content directly into system prompt

    Args:
        llm: The LangChain LLM instance (e.g., ChatAnthropic, ChatOpenAI).
        tools: List of tools the agent can use.
        system_prompt: The base system prompt describing the agent's role.
        skills: List of skill names to load for this agent.
               Skills are looked up via SkillForge configuration.
        skill_mode: How to inject skills into the agent:
                   - "progressive": Inject meta-skill only; agent loads
                     skills on-demand (default)
                   - "inject": Inject full skill content into system prompt
        **kwargs: Additional keyword arguments passed to LangChain's create_agent.

    Returns:
        A LangChain agent instance ready to invoke.

    Raises:
        SkillNotFoundError: If a requested skill is not found.
        ValueError: If skill_mode is not "progressive" or "inject".
        ImportError: If LangChain is not installed or has incompatible version.

    Example:
        >>> from skillforge.langchain import create_agent
        >>> from langchain_anthropic import ChatAnthropic
        >>>
        >>> llm = ChatAnthropic(model="claude-sonnet-4-20250514")
        >>> agent = create_agent(
        ...     llm=llm,
        ...     tools=[],
        ...     system_prompt="You are an executive coach",
        ...     skills=["rapid-interviewing"]
        ... )
    """
    # Validate skill_mode
    valid_modes = {"progressive", "inject"}
    if skill_mode not in valid_modes:
        raise ValueError(
            f"Invalid skill_mode '{skill_mode}'. "
            f"Must be one of: {', '.join(sorted(valid_modes))}"
        )

    # Build system prompt with skills
    enhanced_prompt = system_prompt
    if skills:
        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skill_objects = [loader.get(name) for name in skills]
        enhanced_prompt = _build_system_prompt(
            system_prompt, skill_objects, skill_mode
        )

    # Ensure shell tool is available for skillforge read command
    tools = _ensure_shell_tool(tools)

    # Import and use LangChain 1.2.x API
    try:
        from langchain.agents import create_agent as lc_create_agent
    except ImportError:
        raise ImportError(
            "LangChain is required to use the LangChain adapter. "
            "Install it with: pip install skillforge[langchain]"
        )

    return lc_create_agent(
        model=llm,
        tools=tools,
        system_prompt=enhanced_prompt,
        **kwargs,
    )


def _build_system_prompt(original: str, skills: list[Skill], mode: str) -> str:
    """Build the enhanced system prompt with skill content.

    Args:
        original: The original system prompt string.
        skills: List of Skill objects to include.
        mode: The skill injection mode ("progressive" or "inject").

    Returns:
        The enhanced system prompt with skills injected.
    """
    if mode == "inject":
        return _inject_full_skills(original, skills)
    else:
        # Progressive mode: inject meta-skill with skill list
        meta_skill_content = render_meta_skill(skills)
        if original:
            return f"{original}\n\n{meta_skill_content}"
        return meta_skill_content


def _inject_full_skills(original: str, skills: list[Skill]) -> str:
    """Inject full skill content into system prompt.

    Args:
        original: The original system prompt string.
        skills: List of Skill objects to inject.

    Returns:
        System prompt with full skill instructions appended.
    """
    parts = [original] if original else []
    parts.append("\n## Available Skills\n")
    for skill in skills:
        parts.append(f"\n### {skill.name}\n\n{skill.instructions}\n")
    return "".join(parts)


def _ensure_shell_tool(tools: list[Any]) -> list[Any]:
    """Ensure a shell tool is available in the tools list.

    The shell tool is required for agents to execute `skillforge read`
    commands at runtime to load skills progressively.

    Args:
        tools: List of LangChain tools.

    Returns:
        Original tools list if shell tool exists, otherwise a new list
        with ShellTool appended.
    """
    # Common shell tool names to check for
    shell_tool_names = {"shell", "bash", "subprocess", "terminal", "shell_command"}

    has_shell = any(
        getattr(t, "name", "").lower() in shell_tool_names for t in tools
    )

    if not has_shell:
        try:
            from langchain_community.tools import ShellTool

            tools = list(tools) + [ShellTool()]
        except ImportError:
            logger.warning(
                "langchain-community not installed; ShellTool not added. "
                "In progressive mode, agent may not be able to load skills via 'skillforge read'. "
                "Install with: pip install langchain-community"
            )

    return tools
