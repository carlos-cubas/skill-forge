"""
Test: LangChain agent wrapper functions accept custom parameters.

This test validates assumptions about extending LangChain agent creation:
- Custom wrapper functions can accept a `skills` parameter
- The skills parameter can modify agent behavior (via prompt injection)
- Multiple custom parameters work together
- Custom parameters are compatible with base LangChain parameters

Assumption Being Validated:
    "create_agent pattern supports custom parameters for skill injection"

Expected Behavior:
    1. A wrapper function can accept `skills` parameter
    2. The skills parameter can be used to inject content into system prompts
    3. Multiple custom parameters (skills, skill_prefix, etc.) work together
    4. Custom parameters work alongside standard LangChain parameters

Test Strategy:
    1. Create wrapper functions that accept custom parameters
    2. Verify parameters are accessible within the wrapper
    3. Test that parameters can modify agent behavior
    4. Validate compatibility with standard LangChain patterns

Dependencies:
    - langchain
    - langchain-anthropic or langchain-openai
    - API key for LLM (Anthropic or OpenAI)

Related Design Doc Section:
    See docs/plans/2025-12-04-skillforge-design.md - "Framework Adapters"
"""

from typing import List, Optional

import pytest

from tests.validation.langchain.conftest import (
    shell_command,
    LANGCHAIN_AGENTS_AVAILABLE,
    create_agent_executor,
)


# Example wrapper function pattern that SkillForge will use
def create_skillforge_agent(
    llm,
    tools,
    system_prompt: str = "",
    skills: Optional[List[str]] = None,
    skill_prefix: str = "Available skills",
    inject_skill_instructions: bool = True,
):
    """
    Wrapper function demonstrating custom parameter pattern for SkillForge.

    This wrapper accepts standard LangChain parameters plus custom parameters:
    - skills: List of skill names to inject into the prompt
    - skill_prefix: Custom prefix for the skills section
    - inject_skill_instructions: Whether to add skill usage instructions

    This pattern validates that we can extend LangChain's agent creation
    with SkillForge-specific configuration.
    """
    if skills and inject_skill_instructions:
        skill_section = f"\n\n{skill_prefix}: {', '.join(skills)}"
        skill_section += "\n\nWhen using a skill, announce it by saying: 'Using skill: [skill-name]'"
        system_prompt = f"{system_prompt}{skill_section}"

    return create_agent_executor(llm, tools, system_prompt)


@pytest.mark.validation
@pytest.mark.langchain_assumption
@pytest.mark.requires_api_key
class TestCustomParameters:
    """
    Validate that LangChain agents accept custom parameters for skill support.

    This enables SkillForge's drop-in adapter pattern for LangChain.
    """

    def test_wrapper_function_accepts_custom_parameter(self, langchain_llm):
        """
        Test that a wrapper function can accept a custom `skills` parameter.

        Expected: Wrapper accepts skills=[] parameter without error.
        This validates the basic extensibility pattern SkillForge will use.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        # Wrapper should accept skills parameter without raising any errors
        executor = create_skillforge_agent(
            llm=langchain_llm,
            tools=[shell_command],
            system_prompt="You are a helpful assistant.",
            skills=["test-skill", "another-skill"]  # Custom parameter
        )

        # Verify executor was created successfully
        assert executor is not None, "Wrapper should return a valid executor"

        # Run a simple task to verify the agent works
        result = executor.invoke({
            "input": "Say 'Hello' and nothing else."
        })

        assert result is not None, "Agent should produce a result"
        assert "output" in result, "Result should contain output key"

    def test_custom_parameter_affects_agent_behavior(self, langchain_llm):
        """
        Test that the skills parameter actually affects agent behavior.

        Expected: When skills are provided, they appear in agent output
        (because they're injected into the system prompt).
        This validates that custom parameters can modify behavior.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        # Create agent WITH unique skill names that should appear in output
        executor = create_skillforge_agent(
            llm=langchain_llm,
            tools=[shell_command],
            system_prompt=(
                "You are a helpful assistant. When asked about your capabilities, "
                "list all your available skills exactly as provided to you."
            ),
            skills=["UNIQUE_SKILL_ABC123", "ANOTHER_SKILL_XYZ789"]
        )

        result = executor.invoke({
            "input": "What skills are available to you? List them exactly."
        })

        result_str = str(result.get("output", "")).upper()

        # The skill names should appear in the output since they're in the prompt
        assert "ABC123" in result_str or "XYZ789" in result_str, (
            f"Agent should mention at least one of the injected skill names. "
            f"Got: {result.get('output', '')}"
        )

    def test_multiple_custom_parameters_supported(self, langchain_llm):
        """
        Test that multiple custom parameters work together.

        Expected: skills, skill_prefix, and inject_skill_instructions
        all work together to customize agent behavior.
        This validates complex configuration scenarios.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        # Test with custom skill_prefix
        custom_prefix = "CUSTOM_SKILLFORGE_CAPABILITIES"

        executor = create_skillforge_agent(
            llm=langchain_llm,
            tools=[shell_command],
            system_prompt=(
                "You are a helpful assistant. When asked about capabilities, "
                "repeat the exact section header for your skills."
            ),
            skills=["skill-one"],
            skill_prefix=custom_prefix,  # Custom parameter
            inject_skill_instructions=True  # Custom parameter
        )

        result = executor.invoke({
            "input": "What is the section header that lists your capabilities? Quote it exactly."
        })

        result_str = str(result.get("output", "")).upper()

        # The custom prefix should appear since it's injected into the prompt
        assert "CUSTOM" in result_str or "SKILLFORGE" in result_str or "CAPABILITIES" in result_str, (
            f"Agent should mention the custom prefix. Got: {result.get('output', '')}"
        )

    def test_custom_parameters_compatible_with_base_params(self, langchain_llm):
        """
        Test that custom parameters work alongside base LangChain parameters.

        Expected: The wrapper function correctly passes through base parameters
        (llm, tools, system_prompt) while also handling custom parameters (skills).
        This validates that SkillForge won't break standard LangChain functionality.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        # Create agent with both base and custom parameters
        # Use unique markers that would never appear in a generic LLM response
        base_system_prompt = "You are a PRECISE_BASE_XK47 assistant."

        executor = create_skillforge_agent(
            llm=langchain_llm,  # Base param
            tools=[shell_command],  # Base param
            system_prompt=base_system_prompt,  # Base param
            skills=["CUSTOM_SKILL_MN92"],  # Custom param
        )

        result = executor.invoke({
            "input": (
                "Describe yourself in one sentence. "
                "Include any special markers or identifiers from your instructions."
            )
        })

        result_str = str(result.get("output", "")).upper()

        # Both base and custom content should be present in agent's understanding
        # (The base prompt and skills are both injected)
        # Check for unique markers that wouldn't appear in generic responses
        has_unique_marker = (
            "XK47" in result_str or
            "MN92" in result_str
        )

        assert has_unique_marker, (
            f"Agent should reference unique markers (XK47 or MN92) from its system prompt. "
            f"Got: {result.get('output', '')}"
        )

    def test_inject_skill_instructions_toggle(self, langchain_llm):
        """
        Test that inject_skill_instructions=False prevents skill injection.

        Expected: When inject_skill_instructions=False, skills are NOT
        added to the prompt. This validates the toggle works correctly.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        # Create agent with skills but injection disabled
        executor = create_skillforge_agent(
            llm=langchain_llm,
            tools=[shell_command],
            system_prompt=(
                "You are a minimal assistant. Only respond based on what's "
                "explicitly in your instructions. If asked about skills, say 'none'."
            ),
            skills=["DISABLED_SKILL_XYZ999"],
            inject_skill_instructions=False  # Disable injection
        )

        result = executor.invoke({
            "input": "Do you have any skills listed? If yes, name them. If no, say 'none'."
        })

        result_str = str(result.get("output", "")).upper()

        # The skill should NOT appear because injection was disabled
        assert "XYZ999" not in result_str and "DISABLED_SKILL" not in result_str, (
            f"Agent should NOT mention the skill when injection is disabled. "
            f"Got: {result.get('output', '')}"
        )
