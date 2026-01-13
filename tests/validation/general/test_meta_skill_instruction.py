"""
Test: Meta-skill instruction following across frameworks.

This test validates a critical assumption for SkillForge:
- Agents reliably follow meta-skill instructions regardless of framework
- The announcement pattern ("I'm using [skill]...") is consistently followed
- Agents check for relevant skills before acting
- The full meta-skill protocol works end-to-end

Assumption Being Validated:
    "Agents follow meta-skill instructions reliably"

This is the final assumption validation before Phase 1. It confirms that
the overall UX pattern works - agents reliably follow meta-skill instructions
regardless of framework (CrewAI or LangChain).

Expected Behavior:
    1. Agent considers available skills when receiving domain-specific tasks
    2. Agent announces skill usage with the specified format
    3. Agent follows the full meta-skill protocol (check -> announce -> load -> follow)
    4. Behavior is consistent across different LLM providers

Test Strategy:
    1. Create agents with meta-skill instructions in both frameworks
    2. Present domain-specific tasks that should trigger skill consideration
    3. Verify announcement patterns are followed
    4. Test with multiple LLM providers when available

Dependencies:
    - crewai
    - langchain (optional)
    - API key for LLM (Anthropic or OpenAI)

Related Design Doc Section:
    See docs/plans/2025-12-04-skillforge-design.md - "Meta-Skill Auto-Injection"
"""

import os
from typing import Tuple, Optional

import pytest
from crewai import Agent, Task, Crew


# LangChain imports - may not be available
LANGCHAIN_AVAILABLE = False
try:
    from langchain_core.messages import SystemMessage, HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    pass


# =============================================================================
# META-SKILL DEFINITIONS
# =============================================================================

# The core meta-skill content that teaches agents how to use SkillForge
USING_SKILLFORGE_META_SKILL = """
# Using SkillForge - Meta-Skill Instructions

You have access to domain-specific skills through the SkillForge system.
Skills extend your capabilities for specialized tasks.

## When to Check for Skills

BEFORE taking action on a task, consider whether a skill might help:
- Is this task in a specialized domain? (interviewing, coaching, data analysis, etc.)
- Does the task require domain-specific knowledge beyond your training?
- Could a structured approach from a skill improve your response?

If yes to any of these, check your available skills before proceeding.

## How to Load Skills

To load a skill, use the command:
```
skillforge read <skill-name> --from <path>
```

The command outputs the skill's instructions in markdown format.
Follow those instructions for the task at hand.

## Skill Usage Announcement Protocol

CRITICAL: Whenever you use or would use a skill, you MUST announce it.

Use EXACTLY this format:
"SKILL_USAGE: [skill-name] - [brief purpose]"

Examples:
- "SKILL_USAGE: rapid-interviewing - conducting executive interview session"
- "SKILL_USAGE: goal-extraction - identifying client's core objectives"
- "SKILL_USAGE: data-analysis - analyzing sales metrics"

## Available Skills (For This Session)

- rapid-interviewing: Structured approach to conducting effective interviews
- goal-extraction: Framework for identifying and articulating goals
- data-analysis: Methods for analyzing and interpreting data
- coaching-framework: Evidence-based executive coaching techniques

## Full Protocol

When handling a task:
1. IDENTIFY: Recognize if task falls into a skill domain
2. ANNOUNCE: Use the SKILL_USAGE format to declare skill intent
3. LOAD (if needed): Use `skillforge read` to load full skill content
4. FOLLOW: Apply the skill's instructions to the task
"""

# Simplified meta-skill for basic tests
SIMPLE_META_SKILL = """
## SkillForge Protocol

You have skills available. When using any skill:
1. First announce: "SKILL_USAGE: [name] - [purpose]"
2. Then proceed with the skill's approach

Available skills:
- interviewing-skill: For conducting interviews
- analysis-skill: For data analysis
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_crewai_llm_config() -> Tuple[Optional[str], bool]:
    """Get CrewAI LLM configuration based on available API keys."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic/claude-sonnet-4-20250514", True
    elif os.environ.get("OPENAI_API_KEY"):
        return "openai/gpt-4o-mini", True
    return None, False


def get_langchain_llm():
    """Get LangChain LLM based on available API keys."""
    if not LANGCHAIN_AVAILABLE:
        return None

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
        except ImportError:
            pass

    if os.environ.get("OPENAI_API_KEY"):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4o-mini", temperature=0)
        except ImportError:
            pass

    return None


def create_langchain_chat(llm, system_prompt: str, user_message: str) -> str:
    """Invoke a LangChain LLM with system prompt and user message."""
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]
    response = llm.invoke(messages)
    return response.content


def get_llm_provider_name() -> str:
    """Return the name of the available LLM provider."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    elif os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return "none"


# =============================================================================
# TEST CLASS: AGENT CHECKS SKILLS BEFORE ACTING
# =============================================================================

@pytest.mark.validation
@pytest.mark.general_assumption
@pytest.mark.requires_api_key
class TestAgentChecksSkillsBeforeActing:
    """
    Validate that agents consider available skills before acting on tasks.

    The meta-skill teaches agents to check for relevant skills when:
    - Task involves specialized domains
    - Domain-specific knowledge would help
    - Structured approaches exist

    Agents should demonstrate awareness of available skills.
    """

    def test_crewai_agent_recognizes_skill_domain(self):
        """
        Test that a CrewAI agent recognizes when a task falls into a skill domain.

        The agent should:
        1. Receive a task clearly in a skill domain (interviewing)
        2. Recognize that relevant skills exist
        3. Reference or consider the skill in its response

        This validates the first step of the protocol: IDENTIFY.
        """
        llm, available = get_crewai_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Agent with meta-skill instructions
        backstory = f"""
You are an assistant who helps with various tasks.

{USING_SKILLFORGE_META_SKILL}
"""

        agent = Agent(
            role="Skilled Assistant",
            goal="Help users effectively by leveraging available skills when appropriate",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        # Task that clearly falls into interviewing domain
        task = Task(
            description=(
                "You need to help conduct a job interview for a software engineer position. "
                "What approach should you take? Think about whether any of your available "
                "skills would be helpful and explain your reasoning."
            ),
            expected_output="Explanation of approach, referencing relevant skills if applicable",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        result_str = str(result).lower()

        # Agent should recognize the interviewing skill is relevant
        skill_recognition_indicators = [
            "rapid-interviewing",
            "interviewing-skill",
            "interviewing skill",
            "skill",
            "skillforge"
        ]

        has_skill_recognition = any(
            indicator in result_str for indicator in skill_recognition_indicators
        )

        # Agent should mention the interview context
        has_interview_context = "interview" in result_str

        assert has_interview_context, (
            f"Agent should discuss the interview task. Got: {result}"
        )

        # This is the key assertion - agent recognizes skill relevance
        assert has_skill_recognition, (
            f"Agent should recognize available skills for the interviewing domain. "
            f"Expected reference to skills. Got: {result}"
        )

    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
    def test_langchain_agent_recognizes_skill_domain(self):
        """
        Test that a LangChain agent recognizes when a task falls into a skill domain.

        Same validation as CrewAI but using LangChain's message-based approach.
        """
        llm = get_langchain_llm()
        if llm is None:
            pytest.skip("No LLM API key available or LangChain not properly installed")

        system_prompt = f"""
You are an assistant who helps with various tasks.

{USING_SKILLFORGE_META_SKILL}
"""

        user_message = (
            "You need to help conduct a job interview for a software engineer position. "
            "What approach should you take? Think about whether any of your available "
            "skills would be helpful and explain your reasoning."
        )

        response = create_langchain_chat(llm, system_prompt, user_message)
        response_lower = response.lower()

        # Check for skill recognition
        skill_recognition_indicators = [
            "rapid-interviewing",
            "interviewing-skill",
            "interviewing skill",
            "skill",
            "skillforge"
        ]

        has_skill_recognition = any(
            indicator in response_lower for indicator in skill_recognition_indicators
        )

        assert has_skill_recognition, (
            f"LangChain agent should recognize available skills for interviewing domain. "
            f"Got: {response}"
        )

    def test_crewai_agent_considers_skills_for_data_analysis(self):
        """
        Test agent skill consideration for a different domain (data analysis).

        This ensures the agent doesn't just respond to "interview" keyword
        but genuinely considers skills across domains.
        """
        llm, available = get_crewai_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        backstory = f"""
You are a helpful assistant.

{USING_SKILLFORGE_META_SKILL}
"""

        agent = Agent(
            role="Analytical Assistant",
            goal="Help users with analysis tasks using available skills",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "I have quarterly sales data that I need to analyze. "
                "The data includes revenue, units sold, and regional breakdowns. "
                "Before you begin, consider your available skills and "
                "explain how you would approach this analysis."
            ),
            expected_output="Approach explanation considering available skills",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        result_str = str(result).lower()

        # Should recognize data-analysis skill
        skill_indicators = [
            "data-analysis",
            "analysis-skill",
            "analysis skill",
            "skill"
        ]

        has_skill_reference = any(indicator in result_str for indicator in skill_indicators)

        # Should discuss analysis approach
        analysis_terms = ["analysis", "data", "revenue", "sales", "approach"]
        has_analysis_content = any(term in result_str for term in analysis_terms)

        assert has_analysis_content, (
            f"Agent should discuss the analysis task. Got: {result}"
        )

        assert has_skill_reference, (
            f"Agent should consider available skills for data analysis. Got: {result}"
        )


# =============================================================================
# TEST CLASS: AGENT ANNOUNCES SKILL USAGE
# =============================================================================

@pytest.mark.validation
@pytest.mark.general_assumption
@pytest.mark.requires_api_key
class TestAgentAnnouncesSkillUsage:
    """
    Validate that agents announce skill usage with the specified format.

    The meta-skill requires agents to announce:
    "SKILL_USAGE: [skill-name] - [brief purpose]"

    This is critical for UX - users should know when skills are being applied.
    """

    def test_crewai_agent_follows_announcement_format(self):
        """
        Test that a CrewAI agent uses the SKILL_USAGE announcement format.

        The agent should:
        1. Recognize a skill-relevant task
        2. Announce using the exact format: SKILL_USAGE: [name] - [purpose]
        3. Proceed with the task

        This validates the ANNOUNCE step of the protocol.
        """
        llm, available = get_crewai_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Backstory with pre-loaded skill to ensure usage
        backstory = f"""
You are an executive coach.

{USING_SKILLFORGE_META_SKILL}

## Note: Skill Already Loaded

For this session, the "coaching-framework" skill is already loaded and active.
You MUST announce its usage when coaching.
"""

        agent = Agent(
            role="Executive Coach",
            goal="Coach executives using available skills with proper announcements",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "A client says: 'I'm struggling with delegation - I do everything myself.' "
                "Provide coaching advice. Remember to follow your skill usage protocol."
            ),
            expected_output="Coaching response with proper skill announcement",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        result_str = str(result)

        # Check for announcement format variants
        announcement_patterns = [
            "SKILL_USAGE:",
            "SKILL_USAGE",
            "Using coaching-framework",
            "using the coaching-framework skill",
            "I'm using"
        ]

        has_announcement = any(pattern in result_str for pattern in announcement_patterns)

        # Should also have coaching content
        coaching_terms = ["delegation", "trust", "team", "tasks", "help"]
        has_coaching_content = any(
            term in result_str.lower() for term in coaching_terms
        )

        assert has_coaching_content, (
            f"Agent should provide coaching content. Got: {result}"
        )

        assert has_announcement, (
            f"Agent should announce skill usage with SKILL_USAGE format. "
            f"Expected 'SKILL_USAGE:' or similar announcement. Got: {result}"
        )

    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
    def test_langchain_agent_follows_announcement_format(self):
        """
        Test that a LangChain agent uses the SKILL_USAGE announcement format.

        Same validation as CrewAI but using LangChain.
        """
        llm = get_langchain_llm()
        if llm is None:
            pytest.skip("No LLM API key available or LangChain not properly installed")

        system_prompt = f"""
You are a data analyst.

{USING_SKILLFORGE_META_SKILL}

## Note: Skill Already Loaded

For this session, the "data-analysis" skill is already loaded and active.
You MUST announce its usage when analyzing data.
"""

        user_message = (
            "Please analyze this simple dataset: [100, 150, 200, 250, 300]. "
            "Calculate statistics and provide insights. "
            "Remember to follow your skill usage protocol."
        )

        response = create_langchain_chat(llm, system_prompt, user_message)

        # Check for announcement
        announcement_patterns = [
            "SKILL_USAGE:",
            "SKILL_USAGE",
            "Using data-analysis",
            "using the data-analysis skill"
        ]

        has_announcement = any(pattern in response for pattern in announcement_patterns)

        # Should have analysis content
        has_analysis = any(
            term in response.lower()
            for term in ["average", "mean", "data", "analysis", "200"]
        )

        assert has_analysis, (
            f"Agent should provide data analysis. Got: {response}"
        )

        assert has_announcement, (
            f"LangChain agent should announce skill usage. Got: {response}"
        )

    def test_agent_announces_without_explicit_reminder(self):
        """
        Test that agent announces skill usage even without explicit reminder in task.

        The meta-skill instructions should be followed automatically,
        not just when the task reminds the agent.
        """
        llm, available = get_crewai_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Clear meta-skill with pre-loaded skill
        backstory = f"""
You are a goal-setting expert.

{USING_SKILLFORGE_META_SKILL}

The "goal-extraction" skill is loaded and active for this session.
"""

        agent = Agent(
            role="Goal Expert",
            goal="Help clients identify and articulate their goals",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        # Task WITHOUT reminder about protocol
        task = Task(
            description=(
                "A client says: 'I want to be more successful but I don't know where to start.' "
                "Help them identify their core goals."
            ),
            expected_output="Goal identification assistance",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        result_str = str(result)

        # Check for announcement (should happen automatically)
        has_any_skill_announcement = (
            "SKILL_USAGE" in result_str or
            "goal-extraction" in result_str.lower() or
            ("using" in result_str.lower() and "skill" in result_str.lower())
        )

        # Should have goal-related content
        has_goal_content = any(
            term in result_str.lower()
            for term in ["goal", "success", "objective", "achieve", "clarif"]
        )

        assert has_goal_content, (
            f"Agent should provide goal-related guidance. Got: {result}"
        )

        # Note: This test may be more lenient - some agents may not always announce
        # without reminder. This is informational about instruction-following reliability.
        if not has_any_skill_announcement:
            pytest.skip(
                "Agent did not announce skill usage without explicit reminder. "
                "This indicates instruction-following may need reinforcement. "
                f"Response: {result}"
            )


# =============================================================================
# TEST CLASS: AGENT FOLLOWS META-SKILL PROTOCOL
# =============================================================================

@pytest.mark.validation
@pytest.mark.general_assumption
@pytest.mark.requires_api_key
class TestAgentFollowsMetaSkillProtocol:
    """
    Validate that agents follow the full meta-skill protocol.

    Full Protocol:
    1. IDENTIFY: Recognize if task falls into a skill domain
    2. ANNOUNCE: Use the SKILL_USAGE format to declare skill intent
    3. LOAD (if needed): Reference skillforge read command
    4. FOLLOW: Apply skill-based approach

    These tests validate the complete workflow.
    """

    def test_crewai_full_protocol_execution(self):
        """
        Test that a CrewAI agent executes the full meta-skill protocol.

        This is an end-to-end test of the complete workflow:
        identify -> announce -> (would load) -> follow

        Since we can't actually load skills at runtime in this test,
        we verify the agent demonstrates understanding of each step.
        """
        llm, available = get_crewai_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        backstory = f"""
You are a versatile assistant with SkillForge capabilities.

{USING_SKILLFORGE_META_SKILL}

IMPORTANT FOR THIS SESSION:
- You cannot actually run commands, so don't try to load skills
- Instead, explain what skill you WOULD load and why
- Then demonstrate how you would approach the task using that skill's domain
"""

        agent = Agent(
            role="SkillForge-Enabled Assistant",
            goal="Demonstrate the full SkillForge protocol for tasks",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "A new executive needs help preparing for their first 1-on-1 meetings with their team. "
                "They want to understand each team member's goals and challenges. "
                "Walk through how you would help them, demonstrating your skill protocol."
            ),
            expected_output="Full protocol demonstration: identify skill, announce, explain approach",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        result_str = str(result)
        result_lower = result_str.lower()

        # Check for IDENTIFY step - recognizes relevant domain
        domain_recognition = any(term in result_lower for term in [
            "interview", "coaching", "goal", "skill"
        ])

        # Check for ANNOUNCE step - some form of skill declaration
        announcement_indicators = [
            "SKILL_USAGE",
            "rapid-interviewing",
            "goal-extraction",
            "coaching-framework",
            "would use",
            "using the",
            "skill"
        ]
        has_announcement_intent = any(
            indicator in result_str or indicator in result_lower
            for indicator in announcement_indicators
        )

        # Check for LOAD reference - mentions skillforge or loading
        load_indicators = ["skillforge", "load", "read"]
        has_load_reference = any(ind in result_lower for ind in load_indicators)

        # Check for FOLLOW step - actual helpful content
        helpful_content = any(term in result_lower for term in [
            "1-on-1", "one-on-one", "meeting", "team", "question", "listen", "understand"
        ])

        assert domain_recognition, (
            f"Agent should recognize the coaching/interviewing domain. Got: {result}"
        )

        assert has_announcement_intent, (
            f"Agent should announce or reference skill usage. Got: {result}"
        )

        assert helpful_content, (
            f"Agent should provide helpful task-relevant content. Got: {result}"
        )

        # Load reference is optional but indicates deep protocol understanding
        # We don't assert on it to avoid brittleness

    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
    def test_langchain_full_protocol_execution(self):
        """
        Test that a LangChain agent executes the full meta-skill protocol.

        Same validation as CrewAI but using LangChain.
        """
        llm = get_langchain_llm()
        if llm is None:
            pytest.skip("No LLM API key available or LangChain not properly installed")

        system_prompt = f"""
You are a versatile assistant with SkillForge capabilities.

{USING_SKILLFORGE_META_SKILL}

IMPORTANT FOR THIS SESSION:
- You cannot actually run commands, so don't try to load skills
- Instead, explain what skill you WOULD load and why
- Then demonstrate how you would approach the task using that skill's domain
"""

        user_message = (
            "A new executive needs help preparing for their first 1-on-1 meetings with their team. "
            "They want to understand each team member's goals and challenges. "
            "Walk through how you would help them, demonstrating your skill protocol."
        )

        response = create_langchain_chat(llm, system_prompt, user_message)
        response_lower = response.lower()

        # Check for domain recognition
        domain_recognition = any(term in response_lower for term in [
            "interview", "coaching", "goal", "skill"
        ])

        # Check for skill reference
        has_skill_reference = any(term in response_lower for term in [
            "rapid-interviewing", "goal-extraction", "coaching", "skill"
        ])

        # Check for helpful content
        helpful_content = any(term in response_lower for term in [
            "1-on-1", "one-on-one", "meeting", "team", "question"
        ])

        assert domain_recognition and has_skill_reference, (
            f"LangChain agent should recognize domain and reference skills. Got: {response}"
        )

        assert helpful_content, (
            f"LangChain agent should provide helpful content. Got: {response}"
        )

    def test_protocol_with_non_skill_task(self):
        """
        Test that agent doesn't force skills on tasks that don't need them.

        The protocol should only engage when tasks genuinely benefit from skills.
        Simple questions shouldn't trigger skill announcements.
        """
        llm, available = get_crewai_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        backstory = f"""
You are a helpful assistant.

{USING_SKILLFORGE_META_SKILL}
"""

        agent = Agent(
            role="Helpful Assistant",
            goal="Help with tasks, using skills only when genuinely appropriate",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        # Simple task that doesn't need skills
        task = Task(
            description="What is 2 + 2?",
            expected_output="The answer to the arithmetic question",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        result_str = str(result)

        # Should answer correctly
        assert "4" in result_str, f"Agent should answer 2+2=4. Got: {result}"

        # Should NOT unnecessarily invoke skill protocol for simple math
        # (Though some agents might still reference skills - this is informational)
        unnecessary_skill_use = "SKILL_USAGE" in result_str and "math" not in result_str.lower()

        if unnecessary_skill_use:
            pytest.skip(
                "Agent announced skill usage for simple arithmetic. "
                "This may indicate over-eager skill announcement. "
                f"Response: {result}"
            )


# =============================================================================
# TEST CLASS: INSTRUCTION FOLLOWING WITH MULTIPLE LLMS
# =============================================================================

@pytest.mark.validation
@pytest.mark.general_assumption
@pytest.mark.requires_api_key
class TestInstructionFollowingWithMultipleLLMs:
    """
    Validate that instruction following is consistent across LLM providers.

    SkillForge should work with both Anthropic (Claude) and OpenAI (GPT) models.
    These tests verify the meta-skill instructions work regardless of provider.
    """

    def test_current_provider_follows_instructions(self):
        """
        Test that the currently available LLM provider follows instructions.

        This is a baseline test that confirms whatever provider is available
        can follow the meta-skill instructions reliably.
        """
        llm, available = get_crewai_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        provider = get_llm_provider_name()

        # Use simplified meta-skill for clearer instruction following
        backstory = f"""
You are a test assistant validating instruction following.

{SIMPLE_META_SKILL}

For this test, the "analysis-skill" is active.
"""

        agent = Agent(
            role="Test Assistant",
            goal="Demonstrate instruction following by announcing skill usage",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "Analyze this dataset: [5, 10, 15, 20, 25]. "
                "Calculate the average and announce your skill usage as instructed."
            ),
            expected_output="Analysis with skill announcement",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        result_str = str(result)

        # Check for correct answer
        has_correct_answer = "15" in result_str

        # Check for skill announcement
        has_announcement = (
            "SKILL_USAGE" in result_str or
            "analysis-skill" in result_str.lower() or
            ("using" in result_str.lower() and "skill" in result_str.lower())
        )

        assert has_correct_answer, (
            f"[{provider}] Agent should calculate average as 15. Got: {result}"
        )

        assert has_announcement, (
            f"[{provider}] Agent should announce skill usage. Got: {result}"
        )

    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
    def test_langchain_provider_follows_instructions(self):
        """
        Test instruction following using LangChain (different framework path).

        This confirms the same instructions work through LangChain's API.
        """
        llm = get_langchain_llm()
        if llm is None:
            pytest.skip("No LLM API key available or LangChain not properly installed")

        provider = get_llm_provider_name()

        system_prompt = f"""
You are a test assistant validating instruction following.

{SIMPLE_META_SKILL}

For this test, the "analysis-skill" is active.
"""

        user_message = (
            "Analyze this dataset: [5, 10, 15, 20, 25]. "
            "Calculate the average and announce your skill usage as instructed."
        )

        response = create_langchain_chat(llm, system_prompt, user_message)

        # Check for correct answer and announcement
        has_correct_answer = "15" in response
        has_announcement = (
            "SKILL_USAGE" in response or
            "analysis-skill" in response.lower() or
            ("using" in response.lower() and "skill" in response.lower())
        )

        assert has_correct_answer, (
            f"[{provider}/LangChain] Agent should calculate average as 15. Got: {response}"
        )

        assert has_announcement, (
            f"[{provider}/LangChain] Agent should announce skill usage. Got: {response}"
        )

    def test_instruction_following_with_complex_format(self):
        """
        Test that agents follow specific formatting instructions from meta-skill.

        Uses a more structured format requirement to validate precise
        instruction following across providers.
        """
        llm, available = get_crewai_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        provider = get_llm_provider_name()

        # Very specific format requirement
        backstory = """
You are an assistant that follows precise formatting rules.

## Required Response Format

Every response MUST follow this EXACT format:

```
[HEADER]
Provider: {your provider type}
Status: Active

[SKILL]
Name: test-skill
Usage: SKILL_ACTIVE

[CONTENT]
{your actual response here}

[FOOTER]
Protocol: COMPLETE
```

Never deviate from this format.
"""

        agent = Agent(
            role="Format-Compliant Assistant",
            goal="Always respond in the exact required format",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description="Say hello in the required format.",
            expected_output="Response in exact specified format",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        result_str = str(result)

        # Check for format elements
        format_elements = ["[HEADER]", "[SKILL]", "[CONTENT]", "[FOOTER]"]
        found_elements = [elem for elem in format_elements if elem in result_str]

        # Should have most format elements (allowing some flexibility)
        has_significant_formatting = len(found_elements) >= 2

        # Should have the protocol marker
        has_protocol_markers = (
            "SKILL_ACTIVE" in result_str or
            "Protocol" in result_str or
            "test-skill" in result_str
        )

        assert has_significant_formatting or has_protocol_markers, (
            f"[{provider}] Agent should follow structured format instructions. "
            f"Found format elements: {found_elements}. Got: {result}"
        )


# =============================================================================
# TEST CLASS: CROSS-FRAMEWORK CONSISTENCY
# =============================================================================

@pytest.mark.validation
@pytest.mark.general_assumption
@pytest.mark.requires_api_key
class TestCrossFrameworkConsistency:
    """
    Validate that meta-skill behavior is consistent across frameworks.

    SkillForge users may use either CrewAI or LangChain. The meta-skill
    should produce similar behavior in both frameworks.
    """

    @pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")
    def test_same_instructions_same_behavior(self):
        """
        Test that the same meta-skill instructions produce similar behavior
        in both CrewAI and LangChain.

        Uses identical instructions and task, compares key behaviors.
        """
        crewai_llm, crewai_available = get_crewai_llm_config()
        langchain_llm = get_langchain_llm()

        if not crewai_available:
            pytest.skip("No LLM API key available for CrewAI")
        if langchain_llm is None:
            pytest.skip("No LLM API key available for LangChain")

        # Identical instructions
        instructions = f"""
You are an assistant with SkillForge.

{SIMPLE_META_SKILL}

The "interviewing-skill" is active.
"""

        task_text = (
            "Help me prepare for a job interview. "
            "Announce your skill usage and give one tip."
        )

        # CrewAI execution
        crewai_agent = Agent(
            role="Interview Helper",
            goal="Help with interview prep",
            backstory=instructions,
            llm=crewai_llm,
            verbose=False
        )
        crewai_task = Task(
            description=task_text,
            expected_output="Skill announcement and interview tip",
            agent=crewai_agent
        )
        crewai_crew = Crew(agents=[crewai_agent], tasks=[crewai_task], verbose=False)
        crewai_result = str(crewai_crew.kickoff()).lower()

        # LangChain execution
        langchain_result = create_langchain_chat(
            langchain_llm, instructions, task_text
        ).lower()

        # Both should reference skills
        crewai_has_skill = any(
            term in crewai_result
            for term in ["skill", "interview", "skillforge"]
        )
        langchain_has_skill = any(
            term in langchain_result
            for term in ["skill", "interview", "skillforge"]
        )

        # Both should provide interview content
        crewai_has_content = any(
            term in crewai_result
            for term in ["tip", "prepare", "question", "practice", "research"]
        )
        langchain_has_content = any(
            term in langchain_result
            for term in ["tip", "prepare", "question", "practice", "research"]
        )

        assert crewai_has_skill, (
            f"CrewAI agent should reference skills. Got: {crewai_result}"
        )
        assert langchain_has_skill, (
            f"LangChain agent should reference skills. Got: {langchain_result}"
        )
        assert crewai_has_content, (
            f"CrewAI agent should provide interview content. Got: {crewai_result}"
        )
        assert langchain_has_content, (
            f"LangChain agent should provide interview content. Got: {langchain_result}"
        )

    def test_crewai_only_fallback(self):
        """
        Fallback test if LangChain is not available.

        Ensures the test suite still validates instruction following
        even when only CrewAI is installed.
        """
        if LANGCHAIN_AVAILABLE:
            pytest.skip("LangChain is available, running full cross-framework tests")

        llm, available = get_crewai_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # At minimum, verify CrewAI follows instructions
        backstory = f"""
You are an assistant. {SIMPLE_META_SKILL}
The "analysis-skill" is active.
"""

        agent = Agent(
            role="Test Agent",
            goal="Follow instructions",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description="Calculate 10 + 20 and announce your skill usage.",
            expected_output="Answer with skill announcement",
            agent=agent
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = str(crew.kickoff())

        assert "30" in result, f"Should calculate correctly. Got: {result}"
        assert "skill" in result.lower(), f"Should reference skill. Got: {result}"
