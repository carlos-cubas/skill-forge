"""
Customer Support Agent - LangChain Demo with SkillForge Skills

This module demonstrates a single conversational customer support agent using
SkillForge skills to enhance agent capabilities. It validates:

1. Single-agent architecture (simpler than CrewAI multi-agent pattern)
2. Progressive mode (default): Meta-skill teaches agent to load skills on-demand
3. Inject mode: Full skill content injected into system prompt
4. System prompt composition with skill content
5. Shell tool auto-injection for `skillforge read` command

Validation Checkpoints Supported:
- Checkpoint 4: Agent created (progressive mode)
- Checkpoint 5: System prompt includes meta-skill
- Checkpoint 6: Greeting skill used correctly
- Checkpoint 7: Troubleshooting skill used correctly
- Checkpoint 8: Ticket creation skill used correctly
- Checkpoint 9: Inject mode comparison works

Usage:
    # Import and create agent
    from agent import create_support_agent, create_support_agent_inject_mode

    # Progressive mode (default - meta-skill teaches on-demand loading)
    agent = create_support_agent()

    # Inject mode (full skill content in system prompt)
    agent = create_support_agent_inject_mode()

    # Direct testing
    python agent.py
"""

import os
from dataclasses import dataclass, field
from typing import Any, Optional

# Base system prompt for customer support agent
BASE_SYSTEM_PROMPT = """You are a helpful customer support agent for a software company.

Your responsibilities:
- Welcome customers warmly and professionally
- Listen to their issues and concerns
- Diagnose technical problems systematically
- Create support tickets when issues need escalation
- Search the knowledge base for solutions

Always maintain a friendly, patient, and solution-oriented demeanor.
"""

# Skills available for the customer support agent
CUSTOMER_SUPPORT_SKILLS = [
    "greeting",
    "troubleshooting",
    "ticket-creation",
    "knowledge-search",
]


@dataclass
class CustomerSupportAgent:
    """Wrapper for a LangChain agent with SkillForge skill support.

    This class provides a convenient wrapper that exposes the system prompt
    and other metadata for validation and testing purposes. It uses SkillForge's
    internal functions to compose the system prompt with skills.

    Attributes:
        system_prompt: The composed system prompt including skill content.
        skills: List of skill names used by this agent.
        skill_mode: The skill injection mode ("progressive" or "inject").
        tools: List of tools available to the agent.
        llm: The underlying LLM instance.
        _inner_agent: The underlying LangChain agent (if created).
    """

    system_prompt: str
    skills: list[str]
    skill_mode: str
    tools: list[Any] = field(default_factory=list)
    llm: Any = None
    _inner_agent: Any = None

    def invoke(self, input_dict: dict[str, Any]) -> dict[str, Any]:
        """Invoke the agent with the given input.

        Args:
            input_dict: Input dictionary for the agent.

        Returns:
            Agent response dictionary.
        """
        if self._inner_agent is not None:
            return self._inner_agent.invoke(input_dict)
        # Mock response for testing
        return {"messages": [("assistant", "Mock response from CustomerSupportAgent")]}


def _build_system_prompt(
    base_prompt: str,
    skills: list[str],
    skill_mode: str,
) -> str:
    """Build the enhanced system prompt with skill content.

    This function uses SkillForge's internal functions to compose the system
    prompt with skill content, making it independent of how LangChain agents
    expose their prompts.

    Args:
        base_prompt: The base system prompt.
        skills: List of skill names to include.
        skill_mode: The skill injection mode ("progressive" or "inject").

    Returns:
        The composed system prompt with skill content.
    """
    from skillforge.core.config import load_config
    from skillforge.core.loader import SkillLoader
    from skillforge.core.meta_skill import render_meta_skill

    if not skills:
        return base_prompt

    # Load skill objects
    config = load_config()
    loader = SkillLoader(skill_paths=config.skill_paths)
    skill_objects = [loader.get(name) for name in skills]

    if skill_mode == "inject":
        # Full skill content injection
        parts = [base_prompt] if base_prompt else []
        parts.append("\n## Available Skills\n")
        for skill in skill_objects:
            parts.append(f"\n### {skill.name}\n\n{skill.instructions}\n")
        return "".join(parts)
    else:
        # Progressive mode: meta-skill with skill list
        meta_skill_content = render_meta_skill(skill_objects)
        if base_prompt:
            return f"{base_prompt}\n\n{meta_skill_content}"
        return meta_skill_content


def _ensure_shell_tool(tools: list[Any]) -> list[Any]:
    """Ensure a shell tool is available in the tools list.

    Args:
        tools: List of LangChain tools.

    Returns:
        Tools list with shell tool added if not present.
    """
    shell_tool_names = {"shell", "bash", "subprocess", "terminal", "shell_command"}

    has_shell = any(
        getattr(t, "name", "").lower() in shell_tool_names for t in tools
    )

    if not has_shell:
        try:
            from langchain_community.tools import ShellTool
            tools = list(tools) + [ShellTool()]
        except ImportError:
            # ShellTool not available - log warning in main
            pass

    return tools


def get_llm(model: str = "gpt-4o-mini", mock: bool = False) -> Any:
    """Get a LangChain LLM instance.

    Args:
        model: The OpenAI model name to use.
        mock: If True, return a mock LLM for testing.

    Returns:
        A LangChain LLM instance (real or mock).

    Raises:
        ValueError: If OPENAI_API_KEY is not set and mock=False.
    """
    if mock:
        from unittest.mock import MagicMock
        llm = MagicMock()
        llm.name = "mock-llm"
        llm.model_name = model
        return llm

    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY environment variable not set. "
            "Set it with: export OPENAI_API_KEY=your-key-here"
        )

    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=model)


def create_support_agent(
    llm: Optional[Any] = None,
    tools: Optional[list[Any]] = None,
    skills: Optional[list[str]] = None,
    system_prompt: str = BASE_SYSTEM_PROMPT,
    mock_llm: bool = False,
) -> CustomerSupportAgent:
    """Create a customer support agent in progressive mode.

    Progressive mode injects the meta-skill into the system prompt, which teaches
    the agent how to discover and load skills on-demand using the
    `skillforge read <skill-name>` command.

    This is the recommended mode for production use as it:
    - Keeps initial context window smaller
    - Allows agent to load only needed skills
    - Demonstrates skill discovery patterns

    Args:
        llm: Optional LangChain LLM instance. If None, creates ChatOpenAI.
        tools: Optional list of LangChain tools. Shell tool is auto-added.
        skills: Optional list of skill names. Defaults to customer support skills.
        system_prompt: Base system prompt. Defaults to customer support prompt.
        mock_llm: If True, use a mock LLM for testing.

    Returns:
        A CustomerSupportAgent wrapper with progressive mode configuration.

    Example:
        >>> agent = create_support_agent()
        >>> # Agent's system prompt includes meta-skill
        >>> "skillforge read" in agent.system_prompt
        True
    """
    if llm is None:
        llm = get_llm(mock=mock_llm)

    if tools is None:
        tools = []

    if skills is None:
        skills = CUSTOMER_SUPPORT_SKILLS

    # Build the composed system prompt using SkillForge internals
    composed_prompt = _build_system_prompt(system_prompt, skills, "progressive")

    # Ensure shell tool is available for skillforge read command
    tools_with_shell = _ensure_shell_tool(tools)

    # Try to create actual LangChain agent if possible
    inner_agent = None
    if not mock_llm:
        try:
            from skillforge.langchain import create_agent
            inner_agent = create_agent(
                llm=llm,
                tools=tools,
                system_prompt=system_prompt,
                skills=skills,
                skill_mode="progressive",
            )
        except ImportError:
            pass  # LangChain adapter not available

    return CustomerSupportAgent(
        system_prompt=composed_prompt,
        skills=skills,
        skill_mode="progressive",
        tools=tools_with_shell,
        llm=llm,
        _inner_agent=inner_agent,
    )


def create_support_agent_inject_mode(
    llm: Optional[Any] = None,
    tools: Optional[list[Any]] = None,
    skills: Optional[list[str]] = None,
    system_prompt: str = BASE_SYSTEM_PROMPT,
    mock_llm: bool = False,
) -> CustomerSupportAgent:
    """Create a customer support agent in inject mode.

    Inject mode injects the full content of all skills directly into the
    system prompt. This means:
    - Larger initial context window usage
    - All skill instructions immediately available
    - No need for agent to run `skillforge read` commands

    Use inject mode when:
    - Context window is not a concern
    - You want all skills available immediately
    - Agent execution environment cannot run shell commands

    Args:
        llm: Optional LangChain LLM instance. If None, creates ChatOpenAI.
        tools: Optional list of LangChain tools.
        skills: Optional list of skill names. Defaults to customer support skills.
        system_prompt: Base system prompt. Defaults to customer support prompt.
        mock_llm: If True, use a mock LLM for testing.

    Returns:
        A CustomerSupportAgent wrapper with inject mode configuration.

    Example:
        >>> agent = create_support_agent_inject_mode()
        >>> # Agent's system prompt includes full skill content
        >>> "## Available Skills" in agent.system_prompt
        True
    """
    if llm is None:
        llm = get_llm(mock=mock_llm)

    if tools is None:
        tools = []

    if skills is None:
        skills = CUSTOMER_SUPPORT_SKILLS

    # Build the composed system prompt using SkillForge internals
    composed_prompt = _build_system_prompt(system_prompt, skills, "inject")

    # Ensure shell tool is available (even in inject mode, for consistency)
    tools_with_shell = _ensure_shell_tool(tools)

    # Try to create actual LangChain agent if possible
    inner_agent = None
    if not mock_llm:
        try:
            from skillforge.langchain import create_agent
            inner_agent = create_agent(
                llm=llm,
                tools=tools,
                system_prompt=system_prompt,
                skills=skills,
                skill_mode="inject",
            )
        except ImportError:
            pass  # LangChain adapter not available

    return CustomerSupportAgent(
        system_prompt=composed_prompt,
        skills=skills,
        skill_mode="inject",
        tools=tools_with_shell,
        llm=llm,
        _inner_agent=inner_agent,
    )


# --- Helper functions for validation ---


def get_agent_system_prompt(agent: CustomerSupportAgent) -> str:
    """Extract the system prompt from a CustomerSupportAgent.

    This helper function retrieves the system prompt from an agent,
    which is useful for validation and testing.

    Args:
        agent: A CustomerSupportAgent instance.

    Returns:
        The agent's system prompt string.
    """
    return agent.system_prompt


def verify_meta_skill_present(agent: CustomerSupportAgent) -> bool:
    """Verify that the meta-skill content is in the agent's system prompt.

    The meta-skill teaches agents how to use SkillForge and includes:
    - "Using SkillForge Skills" header
    - "skillforge read" command instructions
    - Available skills list

    Args:
        agent: A CustomerSupportAgent instance.

    Returns:
        True if meta-skill content is present, False otherwise.
    """
    system_prompt = agent.system_prompt
    return all([
        "Using SkillForge Skills" in system_prompt,
        "skillforge read" in system_prompt,
    ])


def verify_skill_in_prompt(agent: CustomerSupportAgent, skill_name: str) -> bool:
    """Verify that a skill is referenced in the agent's system prompt.

    For progressive mode, checks if skill appears in available skills list.
    For inject mode, checks if full skill content is present.

    Args:
        agent: A CustomerSupportAgent instance.
        skill_name: The name of the skill to verify.

    Returns:
        True if skill is present in system prompt, False otherwise.
    """
    return skill_name in agent.system_prompt


def verify_inject_mode(agent: CustomerSupportAgent) -> bool:
    """Verify that agent is in inject mode (full skill content present).

    Inject mode includes the "## Available Skills" section header
    followed by full skill content for each skill.

    Args:
        agent: A CustomerSupportAgent instance.

    Returns:
        True if agent appears to be in inject mode, False otherwise.
    """
    return "## Available Skills" in agent.system_prompt


def verify_progressive_mode(agent: CustomerSupportAgent) -> bool:
    """Verify that agent is in progressive mode (meta-skill only).

    Progressive mode includes the meta-skill header and skill list as
    markdown bullets (- **skill-name**:), NOT the full skill content
    with ### headers for each skill.

    Args:
        agent: A CustomerSupportAgent instance.

    Returns:
        True if agent appears to be in progressive mode, False otherwise.
    """
    has_meta_skill = "Using SkillForge Skills" in agent.system_prompt
    # In inject mode, skills are added with ### headers (e.g., "### greeting")
    # In progressive mode, skills are listed as bullets (e.g., "- **greeting**:")
    has_inject_skill_headers = "### greeting" in agent.system_prompt
    return has_meta_skill and not has_inject_skill_headers


def verify_shell_tool_present(agent: CustomerSupportAgent) -> bool:
    """Verify that a shell tool is present in the agent's tools.

    The shell tool is required for agents to execute `skillforge read`
    commands at runtime in progressive mode.

    Args:
        agent: A CustomerSupportAgent instance.

    Returns:
        True if a shell tool is present, False otherwise.
    """
    shell_tool_names = {"shell", "bash", "subprocess", "terminal", "shell_command"}

    for tool in agent.tools:
        tool_name = getattr(tool, "name", "").lower()
        if tool_name in shell_tool_names:
            return True

    return False


def get_skill_content_from_prompt(agent: CustomerSupportAgent, skill_name: str) -> Optional[str]:
    """Extract a skill's content section from the agent's system prompt.

    Only works in inject mode where full skill content is present.

    Args:
        agent: A CustomerSupportAgent instance.
        skill_name: The name of the skill to extract.

    Returns:
        The skill's content section if found, None otherwise.
    """
    system_prompt = agent.system_prompt

    # Look for skill section header
    skill_header = f"### {skill_name}"
    if skill_header not in system_prompt:
        return None

    # Extract section (rough extraction - until next ### or end)
    start_idx = system_prompt.index(skill_header)
    rest = system_prompt[start_idx + len(skill_header):]

    # Find end of section (next ### or end)
    next_header = rest.find("\n###")
    if next_header == -1:
        return rest.strip()
    return rest[:next_header].strip()


def compare_modes() -> dict[str, Any]:
    """Compare progressive and inject modes for demonstration.

    Creates agents in both modes and returns comparison metrics.
    Useful for validation checkpoint 9.

    Returns:
        Dict with comparison data including prompt lengths and mode markers.
    """
    # Create agents in both modes using mock LLM
    progressive_agent = create_support_agent(mock_llm=True)
    inject_agent = create_support_agent_inject_mode(mock_llm=True)

    return {
        "progressive": {
            "prompt_length": len(progressive_agent.system_prompt),
            "has_meta_skill": verify_meta_skill_present(progressive_agent),
            "has_shell_tool": verify_shell_tool_present(progressive_agent),
            "is_progressive_mode": verify_progressive_mode(progressive_agent),
            "skills_referenced": [
                s for s in CUSTOMER_SUPPORT_SKILLS
                if verify_skill_in_prompt(progressive_agent, s)
            ],
        },
        "inject": {
            "prompt_length": len(inject_agent.system_prompt),
            "has_full_skills": verify_inject_mode(inject_agent),
            "has_shell_tool": verify_shell_tool_present(inject_agent),
            "is_inject_mode": verify_inject_mode(inject_agent),
            "skills_referenced": [
                s for s in CUSTOMER_SUPPORT_SKILLS
                if verify_skill_in_prompt(inject_agent, s)
            ],
        },
        "comparison": {
            "inject_larger_by": len(inject_agent.system_prompt) - len(progressive_agent.system_prompt),
            "progressive_saves_tokens": len(inject_agent.system_prompt) > len(progressive_agent.system_prompt),
        },
    }


# --- Main section for direct testing ---


def print_separator(title: str) -> None:
    """Print a section separator with title."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


def main() -> None:
    """Run direct tests of the customer support agent."""
    import sys

    print_separator("LangChain Demo - Customer Support Agent")

    # Set up mock environment for testing
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing-only"
        print("Note: Using dummy API key for testing\n")

    all_passed = True

    # Test 1: Create progressive mode agent
    print_separator("Test 1: Progressive Mode Agent")
    try:
        progressive_agent = create_support_agent(mock_llm=True)
        print(f"Agent created: {type(progressive_agent).__name__}")
        print(f"  Mode: {progressive_agent.skill_mode}")
        print(f"  System prompt length: {len(progressive_agent.system_prompt)} chars")
        print(f"  Has meta-skill: {verify_meta_skill_present(progressive_agent)}")
        print(f"  Is progressive mode: {verify_progressive_mode(progressive_agent)}")
        print(f"  Has shell tool: {verify_shell_tool_present(progressive_agent)}")
        print(f"  Skills configured: {progressive_agent.skills}")

        # Verify each skill is referenced
        print("  Skills in prompt:")
        for skill in CUSTOMER_SUPPORT_SKILLS:
            in_prompt = verify_skill_in_prompt(progressive_agent, skill)
            status = "PASS" if in_prompt else "FAIL"
            print(f"    [{status}] {skill}")
            if not in_prompt:
                all_passed = False

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test 2: Create inject mode agent
    print_separator("Test 2: Inject Mode Agent")
    try:
        inject_agent = create_support_agent_inject_mode(mock_llm=True)
        print(f"Agent created: {type(inject_agent).__name__}")
        print(f"  Mode: {inject_agent.skill_mode}")
        print(f"  System prompt length: {len(inject_agent.system_prompt)} chars")
        print(f"  Is inject mode: {verify_inject_mode(inject_agent)}")
        print(f"  Has shell tool: {verify_shell_tool_present(inject_agent)}")
        print(f"  Skills configured: {inject_agent.skills}")

        # Verify each skill content is present
        print("  Skills in prompt:")
        for skill in CUSTOMER_SUPPORT_SKILLS:
            in_prompt = verify_skill_in_prompt(inject_agent, skill)
            status = "PASS" if in_prompt else "FAIL"
            print(f"    [{status}] {skill}")
            if not in_prompt:
                all_passed = False

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test 3: Compare modes
    print_separator("Test 3: Mode Comparison")
    try:
        comparison = compare_modes()

        prog = comparison["progressive"]
        inj = comparison["inject"]
        comp = comparison["comparison"]

        print("Progressive Mode:")
        print(f"  Prompt length: {prog['prompt_length']} chars")
        print(f"  Has meta-skill: {prog['has_meta_skill']}")
        print(f"  Has shell tool: {prog['has_shell_tool']}")
        print(f"  Skills found: {len(prog['skills_referenced'])}/{len(CUSTOMER_SUPPORT_SKILLS)}")

        print("\nInject Mode:")
        print(f"  Prompt length: {inj['prompt_length']} chars")
        print(f"  Has full skills: {inj['has_full_skills']}")
        print(f"  Has shell tool: {inj['has_shell_tool']}")
        print(f"  Skills found: {len(inj['skills_referenced'])}/{len(CUSTOMER_SUPPORT_SKILLS)}")

        print("\nComparison:")
        print(f"  Inject mode larger by: {comp['inject_larger_by']} chars")
        print(f"  Progressive saves tokens: {comp['progressive_saves_tokens']}")

        if not comp['progressive_saves_tokens']:
            print("  [WARN] Progressive mode should be smaller than inject mode")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test 4: Verify system prompt content
    print_separator("Test 4: System Prompt Content Verification")
    try:
        progressive_prompt = progressive_agent.system_prompt
        inject_prompt = inject_agent.system_prompt

        # Progressive mode checks
        print("Progressive Mode Prompt Contains:")
        checks = [
            ("Base system prompt", BASE_SYSTEM_PROMPT.split('\n')[0] in progressive_prompt),
            ("'Using SkillForge Skills'", "Using SkillForge Skills" in progressive_prompt),
            ("'skillforge read'", "skillforge read" in progressive_prompt),
            ("Skill list with 'greeting'", "greeting" in progressive_prompt),
        ]
        for name, passed in checks:
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] {name}")
            if not passed:
                all_passed = False

        # Inject mode checks
        print("\nInject Mode Prompt Contains:")
        checks = [
            ("Base system prompt", BASE_SYSTEM_PROMPT.split('\n')[0] in inject_prompt),
            ("'## Available Skills'", "## Available Skills" in inject_prompt),
            ("'### greeting'", "### greeting" in inject_prompt),
            ("Greeting skill content", "Customer Greeting Skill" in inject_prompt),
            ("'### troubleshooting'", "### troubleshooting" in inject_prompt),
            ("'### ticket-creation'", "### ticket-creation" in inject_prompt),
        ]
        for name, passed in checks:
            status = "PASS" if passed else "FAIL"
            print(f"  [{status}] {name}")
            if not passed:
                all_passed = False

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Final summary
    print_separator("Summary")
    if all_passed:
        print("All tests PASSED!")
        print("The LangChain customer support agent is configured correctly.\n")
    else:
        print("Some tests FAILED.")
        print("Please check the output above for details.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
