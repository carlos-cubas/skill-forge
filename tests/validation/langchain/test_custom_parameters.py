"""
Test: LangChain agent custom parameters work as expected.

This test validates assumptions about LangChain agent configuration:
- Custom parameters can be passed to agent constructors
- Agent configuration affects behavior appropriately
- SkillForge can inject custom parameters for skill support

Assumption Being Validated:
    "Custom agent parameters work for skill injection"

Expected Behavior:
    1. LangChain agents accept custom configuration parameters
    2. Configuration changes (temperature, model, etc.) affect behavior
    3. Custom tools can be added at agent creation time
    4. Agent callbacks and hooks work for monitoring skill usage

Test Strategy:
    1. Create agents with various custom configurations
    2. Verify configuration affects agent behavior
    3. Test adding custom tools (like skillforge read)
    4. Validate callback mechanisms for monitoring

Dependencies:
    - langchain
    - langchain-anthropic or langchain-openai
    - API key for LLM (Anthropic or OpenAI)

Related Design Doc Section:
    See docs/plans/2025-12-04-skillforge-design.md - "Framework Adapters"
"""

import pytest


@pytest.mark.validation
@pytest.mark.langchain_assumption
@pytest.mark.requires_api_key
class TestCustomParameters:
    """
    Validate that LangChain agents accept custom parameters for skill support.

    This enables SkillForge's drop-in adapter pattern for LangChain.
    """

    @pytest.mark.skip(reason="Implementation pending - Phase 0.2")
    def test_agent_accepts_custom_tools(self, langchain_llm):
        """
        Test that custom tools can be added to a LangChain agent.

        Expected: Agent with custom shell tool can use it when prompted.
        This is essential for the skillforge read command pattern.
        """
        pass

    @pytest.mark.skip(reason="Implementation pending - Phase 0.2")
    def test_agent_with_custom_system_message(self, langchain_llm):
        """
        Test that agents accept custom system messages.

        Expected: Agent behavior is influenced by custom system message
        content, enabling skill content injection.
        """
        pass

    @pytest.mark.skip(reason="Implementation pending - Phase 0.2")
    def test_agent_creation_with_kwargs(self, langchain_llm):
        """
        Test that agents accept arbitrary kwargs for extension.

        Expected: SkillForge can pass skills=[] parameter that doesn't
        break agent creation (even if ignored initially).
        """
        pass

    @pytest.mark.skip(reason="Implementation pending - Phase 0.2")
    def test_agent_callback_for_tool_usage(self, langchain_llm):
        """
        Test that callbacks can monitor agent tool usage.

        Expected: Callback is triggered when agent uses tools,
        enabling SkillForge to track skill loading.
        """
        pass
