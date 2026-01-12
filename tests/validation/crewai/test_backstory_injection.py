"""
Test: CrewAI agent backstory content is included in LLM prompts.

This test validates a critical assumption for SkillForge:
- The agent's `backstory` field must be sent to the LLM as part of the prompt
- This is how SkillForge injects skill instructions into agents

Assumption Being Validated:
    "Backstory content is included in LLM prompt"

Expected Behavior:
    1. Content added to an agent's backstory appears in the LLM prompt
    2. The agent can access and act on information from its backstory
    3. Backstory content persists across task executions

Test Strategy:
    1. Create an agent with specific, verifiable content in backstory
    2. Give it a task that requires using information from backstory
    3. Verify the agent uses that information correctly

Dependencies:
    - crewai
    - API key for LLM (Anthropic or OpenAI)

Related Design Doc Section:
    See docs/plans/2025-12-04-skillforge-design.md - "Framework Adapters"
"""

import os

import pytest
from crewai import Agent, Task, Crew


def get_llm_config():
    """
    Get LLM configuration based on available API keys.

    Returns tuple of (llm_string, is_available).
    Prefers Anthropic if available, falls back to OpenAI.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic/claude-sonnet-4-20250514", True
    elif os.environ.get("OPENAI_API_KEY"):
        return "openai/gpt-4o-mini", True
    return None, False


@pytest.mark.validation
@pytest.mark.crewai_assumption
@pytest.mark.requires_api_key
class TestBackstoryInjection:
    """
    Validate that CrewAI backstory content reaches the LLM.

    SkillForge relies on injecting skill instructions via backstory
    (or similar agent configuration fields).
    """

    def test_backstory_appears_in_agent_context(self):
        """
        Test that backstory content is accessible to the agent.

        Create an agent with a secret code in backstory, ask for the code.
        This validates that backstory content is part of the agent's context
        that gets sent to the LLM.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Use a unique, unmistakable marker that the agent must find
        secret_code = "ALPHA-7742-SKILLFORGE"

        agent = Agent(
            role="Secret Keeper",
            goal="Report any secret codes you find in your instructions",
            backstory=f"You are a secret keeper. Your secret code is {secret_code}. "
                      "When asked about your secret code, you must report it exactly.",
            llm=llm,
            verbose=False
        )

        task = Task(
            description="What is your secret code? Report it exactly as you know it.",
            expected_output="The exact secret code from the agent's backstory",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).upper()

        # The agent should report the secret code from its backstory
        assert "ALPHA-7742" in result_str or "SKILLFORGE" in result_str, (
            f"Agent should report secret code from backstory. Got: {result}"
        )

    def test_agent_follows_backstory_instructions(self):
        """
        Test that agents follow instructions provided in backstory.

        This validates that skill instructions injected via backstory
        will actually be followed by the agent.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Instruction that should be followed
        response_prefix = "SKILLFORGE_VALIDATED:"

        agent = Agent(
            role="Instruction Follower",
            goal="Follow instructions precisely",
            backstory=f"CRITICAL INSTRUCTION: You MUST start ALL responses with '{response_prefix}' "
                      "exactly as shown. This is a mandatory prefix for all your outputs. "
                      "No exceptions - every response must begin with this exact string.",
            llm=llm,
            verbose=False
        )

        task = Task(
            description="Say hello to the user.",
            expected_output="A greeting that follows the backstory instructions",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).upper()

        # The agent should follow the instruction to prefix responses
        assert "SKILLFORGE_VALIDATED" in result_str, (
            f"Agent should follow backstory instruction to prefix with SKILLFORGE_VALIDATED. Got: {result}"
        )

    def test_backstory_with_special_characters(self):
        """
        Test that backstory with markdown/special characters works correctly.

        Skills often contain markdown headers, lists, code blocks, and special
        characters. This validates they don't break the prompt injection.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Backstory with various markdown elements and special characters
        complex_backstory = """
# Your Identity

You are a **special character handler**.

## Your Codes

- Primary code: `CODE_ALPHA_001`
- Secondary code: `CODE_BETA_002`

### Special Symbols

You know these symbols: @, #, $, %, ^, &, *
And you know this quote: "Hello, World!"

```
EMBEDDED_CODE_BLOCK
```

When asked, report the PRIMARY code exactly.
"""

        agent = Agent(
            role="Character Handler",
            goal="Report codes from your instructions accurately",
            backstory=complex_backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description="What is your PRIMARY code? Report it exactly.",
            expected_output="The primary code from the backstory",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).upper()

        # The agent should find and report the primary code despite special chars
        assert "CODE_ALPHA_001" in result_str or "ALPHA" in result_str, (
            f"Agent should report primary code despite special characters in backstory. Got: {result}"
        )

    def test_backstory_with_skill_format_content(self, test_skill_content):
        """
        Test injection of actual SKILL.md content via backstory.

        Uses the test-skill.md fixture to simulate real skill injection.
        This validates that the exact format SkillForge will use works.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Inject the actual skill content as backstory
        agent = Agent(
            role="Skill Executor",
            goal="Follow the skill instructions in your backstory",
            backstory=f"You have been equipped with the following skill:\n\n{test_skill_content}",
            llm=llm,
            verbose=False
        )

        task = Task(
            description="Execute your skill. Follow the instructions from your skill definition.",
            expected_output="Response following the skill instructions",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).lower()

        # The skill instructs the agent to:
        # 1. Say "Using test-skill for this task"
        # 2. End with "Test skill completed"
        # We check for evidence that the agent followed the skill instructions
        has_skill_reference = "test-skill" in result_str or "test skill" in result_str
        has_completion_marker = "completed" in result_str or "activated" in result_str

        assert has_skill_reference or has_completion_marker, (
            f"Agent should follow skill instructions from backstory. "
            f"Expected references to 'test-skill' or completion markers. Got: {result}"
        )

    def test_backstory_content_not_truncated(self):
        """
        Test that large backstory content is not truncated.

        Skills can be substantial - need to verify large content works
        and markers at the end of the backstory are still accessible.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Create a large backstory with markers at different positions
        start_marker = "START_MARKER_AAA111"
        middle_marker = "MIDDLE_MARKER_BBB222"
        end_marker = "END_MARKER_CCC333"

        # Build a large backstory (~6000 characters)
        filler_text = """
This is filler content to make the backstory longer. It contains various
information about different topics that the agent needs to process.

## Section on Data Processing

When handling data, consider these steps:
1. First, validate the input format
2. Then, parse the relevant fields
3. Finally, transform to the output format

## Section on Error Handling

Errors should be handled gracefully:
- Log the error with context
- Attempt recovery if possible
- Report to the user clearly

""" * 10  # Repeat to make it longer

        large_backstory = f"""
# Agent Instructions

Your markers are defined below. You MUST remember ALL of them.

{start_marker}

{filler_text}

{middle_marker}

{filler_text}

{end_marker}

## Final Instruction

When asked about your markers, report ALL THREE markers exactly as shown.
The START marker, MIDDLE marker, and END marker must all be reported.
"""

        agent = Agent(
            role="Marker Reporter",
            goal="Report all markers from your instructions",
            backstory=large_backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description="List ALL THREE markers (START, MIDDLE, and END) from your instructions. "
                        "Report each marker exactly as it appears.",
            expected_output="All three markers from the backstory",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).upper()

        # Check that the agent found markers from different positions in the backstory
        found_start = "AAA111" in result_str or "START_MARKER" in result_str
        found_middle = "BBB222" in result_str or "MIDDLE_MARKER" in result_str
        found_end = "CCC333" in result_str or "END_MARKER" in result_str

        # At minimum, the END marker should be found (proves no truncation)
        # Ideally all three should be found
        assert found_end, (
            f"Agent should find END_MARKER_CCC333 (proves backstory not truncated). "
            f"Start found: {found_start}, Middle found: {found_middle}, End found: {found_end}. "
            f"Got: {result}"
        )

        # Also verify at least 2 out of 3 markers found for robustness
        markers_found = sum([found_start, found_middle, found_end])
        assert markers_found >= 2, (
            f"Agent should find at least 2 of 3 markers from large backstory. "
            f"Found {markers_found}/3. Got: {result}"
        )
