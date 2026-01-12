"""
Test: Meta-skill prompt injection doesn't break CrewAI agent behavior.

This test validates a critical assumption for SkillForge:
- Injecting the "using-skillforge" meta-skill into agent prompts works
- The meta-skill instructions don't conflict with agent role/goal
- Agents can follow meta-skill instructions alongside their primary role

Assumption Being Validated:
    "Prompt injection doesn't break agent behavior"

Expected Behavior:
    1. Agent with injected meta-skill still performs its primary role
    2. Meta-skill instructions are followed when appropriate
    3. No conflicts between role instructions and meta-skill
    4. Agent announces skill usage as instructed by meta-skill

Test Strategy:
    1. Create agent with role + meta-skill content in backstory
    2. Give tasks that test both role and meta-skill behavior
    3. Verify agent handles both correctly

Dependencies:
    - crewai
    - crewai-tools
    - API key for LLM (Anthropic or OpenAI)

Related Design Doc Section:
    See docs/plans/2025-12-04-skillforge-design.md - "Meta-Skill Auto-Injection"
"""

import pytest


# Simplified meta-skill content for testing
# This simulates what SkillForge will inject into agents
TEST_META_SKILL = """
## SkillForge Instructions

You have access to domain-specific skills via the SkillForge system.

### How to Use Skills

1. When you need specialized knowledge, check if a skill is available
2. Load skills using: `skillforge read <skill-name>`
3. When using a skill, announce: "I'm using the [skill-name] skill"

### Available Skills

To see available skills, run: `skillforge list`

### Important

- Only load skills when needed for the task
- Always announce when you're using a skill
- Skills provide instructions, not just information
"""


@pytest.mark.validation
@pytest.mark.crewai_assumption
@pytest.mark.requires_api_key
class TestMetaSkillInjection:
    """
    Validate that meta-skill injection works with CrewAI.

    SkillForge auto-injects a "using-skillforge" meta-skill that teaches
    agents how to discover and use skills at runtime.
    """

    def test_agent_maintains_role_with_meta_skill(self):
        """
        Test that an agent still performs its role after meta-skill injection.

        The meta-skill should enhance, not replace, agent behavior.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with role "Data Analyst" and meta-skill in backstory
        # 2. Task: "Analyze this data: [1, 2, 3, 4, 5]"
        # 3. Verify agent provides analysis (not blocked by meta-skill)
        pytest.skip("Implementation pending - Phase 0.2")

    def test_agent_follows_meta_skill_announcement_rule(self):
        """
        Test that agent follows the "announce skill usage" instruction.

        Meta-skill tells agents to announce: "I'm using the [skill] skill"
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with meta-skill and a test skill loaded
        # 2. Task that triggers skill usage
        # 3. Verify agent includes the announcement phrase
        pytest.skip("Implementation pending - Phase 0.2")

    def test_meta_skill_doesnt_conflict_with_goal(self):
        """
        Test that meta-skill instructions don't override agent goals.

        Agent should prioritize its task while incorporating meta-skill.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with specific goal and meta-skill
        # 2. Task that could be interpreted multiple ways
        # 3. Verify agent follows its goal, not just meta-skill
        pytest.skip("Implementation pending - Phase 0.2")

    def test_multiple_skill_injections(self, test_skill_content):
        """
        Test that agent handles meta-skill + domain skill together.

        Real usage involves meta-skill + one or more domain skills.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with meta-skill + test_skill_content in backstory
        # 2. Task: "Use your skills to complete this task"
        # 3. Verify agent uses both sets of instructions appropriately
        pytest.skip("Implementation pending - Phase 0.2")

    def test_backstory_size_with_full_injection(self):
        """
        Test that full meta-skill + skill content fits in context.

        Verify practical size limits for injected content.
        """
        # TODO: Implement in Phase 0.2
        # 1. Calculate realistic size: meta-skill + 2-3 skills
        # 2. Create agent with full injection
        # 3. Verify agent still functions correctly
        pytest.skip("Implementation pending - Phase 0.2")

    def test_agent_can_load_skill_at_runtime(self):
        """
        Test the full flow: agent uses meta-skill to load a skill.

        This is the complete SkillForge use case.
        """
        # TODO: Implement in Phase 0.2
        # 1. Create agent with meta-skill (but no domain skills)
        # 2. Create test skill file accessible via bash
        # 3. Task: "Load the test-skill and follow its instructions"
        # 4. Verify agent:
        #    - Runs skillforge read (or cat) to load skill
        #    - Announces skill usage
        #    - Follows the skill's instructions
        pytest.skip("Implementation pending - Phase 0.2")
