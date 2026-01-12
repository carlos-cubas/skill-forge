"""
Test: CrewAI agents can read and act on Bash command output.

This test validates a critical assumption for SkillForge:
- When an agent executes a bash command, it receives the output
- The agent can parse, understand, and act on that output
- This enables dynamic skill loading via `skillforge read`

Assumption Being Validated:
    "Agent can read Bash output and act on it"

Expected Behavior:
    1. Agent executes bash command and receives stdout
    2. Agent can parse structured output (like skill markdown)
    3. Agent incorporates the loaded content into its behavior
    4. Agent can chain multiple command executions

Test Strategy:
    1. Create agent with shell tool access
    2. Have agent read file content via bash
    3. Verify agent can use that content in its response
    4. Test with actual skill-formatted content

Dependencies:
    - crewai
    - crewai-tools
    - API key for LLM (Anthropic or OpenAI)

Related Design Doc Section:
    See docs/plans/2025-12-04-skillforge-design.md - "Progressive Loading"
"""

import pytest


@pytest.mark.validation
@pytest.mark.crewai_assumption
@pytest.mark.requires_api_key
class TestBashOutputUsage:
    """
    Validate that CrewAI agents can use bash command output.

    SkillForge relies on agents reading `skillforge read` output
    and incorporating skill instructions mid-task.
    """

    def test_agent_uses_simple_output(self):
        """
        Test that agent can use simple command output in its reasoning.

        Run a command, verify agent references the output.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create temp file with content "The answer is 42"
        # 2. Create agent with shell tool
        # 3. Task: "Read the file at <path> and tell me what the answer is"
        # 4. Verify response includes "42"
        pytest.skip("Implementation pending - Phase 0.2")

    def test_agent_parses_markdown_output(self, test_skill_path):
        """
        Test that agent can parse markdown-formatted output.

        Skills are markdown files, agent must handle this format.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with shell tool
        # 2. Task: "Read the skill file at <test_skill_path> and tell me its name"
        # 3. Verify response includes "test-skill"
        pytest.skip("Implementation pending - Phase 0.2")

    def test_agent_follows_loaded_instructions(self, temp_skill_file):
        """
        Test that agent follows instructions loaded via bash.

        This is the core SkillForge use case.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with shell tool
        # 2. Task: "Read the skill at <temp_skill_file>, then follow its instructions"
        # 3. Verify agent response matches skill instructions
        pytest.skip("Implementation pending - Phase 0.2")

    def test_agent_handles_large_output(self):
        """
        Test that agent can handle large command output.

        Skills can be substantial, verify large outputs work.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create temp file with large content (e.g., 5000+ chars)
        # 2. Create agent with shell tool
        # 3. Task: "Read the file and summarize it"
        # 4. Verify agent received and processed the content
        pytest.skip("Implementation pending - Phase 0.2")

    def test_agent_chains_commands(self):
        """
        Test that agent can execute multiple commands in sequence.

        May need to load multiple skills or combine operations.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create two temp files with different content
        # 2. Create agent with shell tool
        # 3. Task: "Read both files and combine their information"
        # 4. Verify agent used content from both files
        pytest.skip("Implementation pending - Phase 0.2")

    def test_output_available_in_subsequent_reasoning(self):
        """
        Test that command output persists in agent's context.

        After reading a skill, agent should remember it for the task.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with shell tool
        # 2. Multi-step task: Read skill, then answer questions about it
        # 3. Verify agent retains information from the skill
        pytest.skip("Implementation pending - Phase 0.2")
