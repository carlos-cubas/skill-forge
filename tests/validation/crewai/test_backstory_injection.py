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

import pytest


@pytest.mark.validation
@pytest.mark.crewai_assumption
@pytest.mark.requires_api_key
class TestBackstoryInjection:
    """
    Validate that CrewAI backstory content reaches the LLM.

    SkillForge relies on injecting skill instructions via backstory
    (or similar agent configuration fields).
    """

    def test_backstory_basic_injection(self):
        """
        Test that basic backstory content is accessible to the agent.

        Create an agent with a secret code in backstory, ask for the code.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with backstory containing: "Your secret code is ALPHA-7742"
        # 2. Create task: "What is your secret code?"
        # 3. Execute crew
        # 4. Verify response contains "ALPHA-7742"
        pytest.skip("Implementation pending - Phase 0.2")

    def test_backstory_instruction_following(self):
        """
        Test that agents follow instructions provided in backstory.

        This validates that skill instructions in backstory will be followed.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with backstory: "Always start responses with 'VALIDATION:'"
        # 2. Create task: "Say hello"
        # 3. Execute crew
        # 4. Verify response starts with "VALIDATION:"
        pytest.skip("Implementation pending - Phase 0.2")

    def test_backstory_with_skill_content(self, test_skill_content):
        """
        Test injection of actual skill content via backstory.

        Uses the test-skill.md fixture to simulate real skill injection.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with backstory containing test_skill_content
        # 2. Create task: "Execute your skill instructions"
        # 3. Execute crew
        # 4. Verify response contains expected skill outputs
        pytest.skip("Implementation pending - Phase 0.2")

    def test_backstory_multiline_content(self):
        """
        Test that multiline/formatted backstory content works correctly.

        Skills often have headers, lists, code blocks, etc.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with complex multiline backstory (headers, lists, etc.)
        # 2. Create task that requires understanding the structure
        # 3. Execute crew
        # 4. Verify agent correctly interprets the formatted content
        pytest.skip("Implementation pending - Phase 0.2")

    def test_backstory_length_limits(self):
        """
        Test behavior with large backstory content.

        Skills can be substantial - need to verify large content works.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with very long backstory (e.g., 5000+ characters)
        # 2. Include specific markers at different positions
        # 3. Create task: "Find all the markers in your backstory"
        # 4. Verify all markers are found (content not truncated)
        pytest.skip("Implementation pending - Phase 0.2")
