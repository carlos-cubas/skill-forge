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
from crewai import Agent, Task, Crew

from tests.validation.crewai.conftest import get_llm_config


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

# More detailed meta-skill with specific announcement patterns
DETAILED_META_SKILL = """
# Using SkillForge

You have access to skills that extend your capabilities.

## When to Use Skills

Check for relevant skills when:
- A task mentions a domain-specific need (e.g., interviewing, coaching, data analysis)
- You need specialized knowledge beyond your general training
- The user explicitly asks about available capabilities

## How to Load Skills

1. Run: `skillforge read <skill-name>` to load a skill's instructions
2. The command outputs the skill's markdown content
3. Follow the loaded skill's instructions for the task

## Announcement Protocol

CRITICAL: When using ANY skill, you MUST announce it with EXACTLY this format:
"SKILL_ANNOUNCEMENT: Using [skill-name] for [brief purpose]"

Example: "SKILL_ANNOUNCEMENT: Using rapid-interviewing for executive coaching session"

## Available Skills (Example)

- rapid-interviewing: For conducting structured interviews
- goal-extraction: For identifying and articulating goals
- data-analysis: For analyzing structured data
"""

# Role-specific backstory to combine with meta-skill
EXECUTIVE_COACH_BACKSTORY = """
You are an experienced executive coach with 15 years of experience.
Your specialty is helping leaders identify blind spots and set actionable goals.
You approach every interaction with empathy and directness.
Your signature technique is the "3 Whys" method: asking why three times to get to root causes.
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

    def test_meta_skill_injection_doesnt_break_agent(self):
        """
        Test that an agent still performs its role after meta-skill injection.

        The meta-skill should enhance, not replace or break, agent behavior.
        This is the most basic validation - the agent must still work.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Combine role backstory with meta-skill instructions
        combined_backstory = f"""
{EXECUTIVE_COACH_BACKSTORY}

---

{TEST_META_SKILL}
"""

        agent = Agent(
            role="Executive Coach",
            goal="Help leaders identify goals and create action plans",
            backstory=combined_backstory,
            llm=llm,
            verbose=False
        )

        # Simple task that tests basic agent functionality
        task = Task(
            description=(
                "A client says: 'I want to improve my team's productivity.' "
                "Ask ONE clarifying question to understand their situation better."
            ),
            expected_output="A single clarifying question about the client's situation",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).lower()

        # Verify agent produced a reasonable coaching response
        # Should contain a question (has "?" or question-like words)
        has_question = (
            "?" in result_str or
            "what" in result_str or
            "how" in result_str or
            "why" in result_str or
            "tell me" in result_str
        )

        assert has_question, (
            f"Agent should ask a clarifying question (meta-skill didn't break it). Got: {result}"
        )

        # Should be about the topic at hand (team, productivity, or related)
        relevant_terms = ["team", "product", "improve", "goal", "specific", "challenge"]
        has_relevant_content = any(term in result_str for term in relevant_terms)

        assert has_relevant_content, (
            f"Agent should produce relevant coaching content despite meta-skill injection. Got: {result}"
        )

    def test_agent_follows_skill_usage_announcement_pattern(self):
        """
        Test that agent follows the "announce skill usage" instruction.

        Meta-skill tells agents to announce: "SKILL_ANNOUNCEMENT: Using [skill] for [purpose]"
        This validates agents can follow meta-skill behavioral patterns.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Include a test skill that's already "loaded" in the backstory
        backstory_with_skill = f"""
{DETAILED_META_SKILL}

---

## Currently Loaded Skill: data-analysis

The data-analysis skill is now active. It provides methods for analyzing numerical data.
When you analyze any data, you MUST announce using this skill per the protocol above.
"""

        agent = Agent(
            role="Data Analyst",
            goal="Analyze data and provide insights, always announcing when using skills",
            backstory=backstory_with_skill,
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "Analyze this simple dataset: [10, 20, 30, 40, 50]. "
                "Calculate the average and provide your analysis. "
                "Remember to follow your announcement protocol when using skills."
            ),
            expected_output="Data analysis with proper skill announcement",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result)

        # Check for announcement pattern
        has_announcement = (
            "SKILL_ANNOUNCEMENT" in result_str or
            "Using data-analysis" in result_str or
            "using the data-analysis skill" in result_str.lower() or
            ("I'm using" in result_str and "skill" in result_str.lower())
        )

        # Also verify the agent actually did the analysis (average is 30)
        has_analysis = "30" in result_str or "average" in result_str.lower()

        assert has_analysis, (
            f"Agent should perform the data analysis (average=30). Got: {result}"
        )

        assert has_announcement, (
            f"Agent should announce skill usage per meta-skill instructions. "
            f"Expected 'SKILL_ANNOUNCEMENT' or 'Using data-analysis'. Got: {result}"
        )

    def test_agent_understands_when_to_load_skills(self):
        """
        Test that agent knows when skills are relevant based on meta-skill guidance.

        The meta-skill explains when to check for skills. Agent should recognize
        domain-specific needs and reference skill loading appropriately.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Meta-skill with clear guidance on when to use skills
        backstory = f"""
You are a helpful assistant.

{DETAILED_META_SKILL}

NOTE: For this session, you do NOT have bash access to actually load skills.
Instead, when you would load a skill, describe what skill you would load and why.
"""

        agent = Agent(
            role="Adaptive Assistant",
            goal="Help users and recognize when specialized skills would be useful",
            backstory=backstory,
            llm=llm,
            verbose=False
        )

        # Task that clearly falls into a skill domain
        task = Task(
            description=(
                "A user asks: 'I need to conduct an executive interview tomorrow. "
                "What approach should I take?' "
                "Based on your skill instructions, explain what skill you would use "
                "and why it's appropriate for this task."
            ),
            expected_output="Explanation of which skill would be useful and why",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).lower()

        # Agent should recognize this calls for the interviewing skill
        recognizes_skill_need = (
            "rapid-interviewing" in result_str or
            ("interview" in result_str and "skill" in result_str) or
            "skillforge" in result_str or
            ("load" in result_str and "skill" in result_str)
        )

        assert recognizes_skill_need, (
            f"Agent should recognize the interviewing task needs a skill. "
            f"Expected mention of 'rapid-interviewing' skill or skill loading. Got: {result}"
        )

    def test_complex_instructions_dont_cause_confusion(self):
        """
        Test that multiple instructions work together without conflict.

        Agent has: role instructions + meta-skill instructions + task instructions.
        All should coexist without the agent getting confused or contradicting itself.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Complex backstory with multiple instruction sets
        complex_backstory = f"""
# Your Identity

You are a Senior Technical Consultant specializing in software architecture.

## Your Core Principles

1. Always explain technical concepts clearly
2. Provide concrete examples when possible
3. Acknowledge uncertainty rather than guessing
4. End every response with "CONSULTANT_SIGNATURE_ABC123"

---

{TEST_META_SKILL}

---

## Additional Guidelines

- Be concise but thorough
- Reference industry best practices
- Consider scalability in your recommendations
"""

        agent = Agent(
            role="Technical Consultant",
            goal="Provide expert technical guidance while following all instructions",
            backstory=complex_backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "A client asks: 'Should we use microservices or a monolith for our new project?' "
                "Provide a brief recommendation. Remember to follow ALL your instructions."
            ),
            expected_output="Technical recommendation that follows all guidelines including the signature",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result)
        result_lower = result_str.lower()

        # Check agent followed role instructions (technical content)
        has_technical_content = (
            "microservice" in result_lower or
            "monolith" in result_lower or
            "architecture" in result_lower or
            "scalab" in result_lower
        )

        # Check agent followed the signature requirement
        has_signature = "CONSULTANT_SIGNATURE_ABC123" in result_str

        # Check response is coherent (has recommendation language)
        has_recommendation = (
            "recommend" in result_lower or
            "suggest" in result_lower or
            "consider" in result_lower or
            "should" in result_lower
        )

        assert has_technical_content, (
            f"Agent should provide technical content about the architecture question. Got: {result}"
        )

        assert has_recommendation, (
            f"Agent should provide a recommendation. Got: {result}"
        )

        assert has_signature, (
            f"Agent should include CONSULTANT_SIGNATURE_ABC123 as instructed "
            f"(complex instructions didn't cause confusion). Got: {result}"
        )

    def test_meta_skill_content_coexists_with_role_backstory(self):
        """
        Test that meta-skill + role backstory work together properly.

        Real SkillForge usage will always combine:
        - Original agent backstory (defining role, personality, domain)
        - Injected meta-skill (teaching skill usage)

        Both must be accessible and followed.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Rich role backstory with specific personality traits and knowledge
        role_backstory = """
# Dr. Sarah Chen - AI Ethics Consultant

You are Dr. Sarah Chen, a leading AI ethics consultant with a background in philosophy
and computer science. You have three defining characteristics:

1. METHODICAL: You always structure your thinking into clear steps
2. CITATION-MINDED: You reference principles and frameworks by name
3. BALANCED: You present multiple perspectives before giving your view

Your signature phrase that you include in every response: "Ethics is not about finding
the right answer, but asking the right questions."

You have deep knowledge of:
- The EU AI Act
- Asilomar AI Principles
- IEEE Ethically Aligned Design framework
"""

        combined_backstory = f"""
{role_backstory}

---

{TEST_META_SKILL}
"""

        agent = Agent(
            role="AI Ethics Consultant",
            goal="Provide ethical guidance on AI systems while using available skills appropriately",
            backstory=combined_backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "A company asks: 'Is it ethical to use AI for employee monitoring?' "
                "Provide your expert perspective following your usual approach."
            ),
            expected_output="Ethical analysis following the consultant's characteristic approach",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).lower()

        # Check for role backstory elements (personality traits)
        has_structured_approach = (
            "step" in result_str or
            "first" in result_str or
            "1." in result_str or
            "perspective" in result_str
        )

        # Check for domain knowledge from backstory
        has_ethics_content = (
            "ethic" in result_str or
            "privacy" in result_str or
            "consent" in result_str or
            "principle" in result_str
        )

        # Check for signature phrase (tests backstory retention)
        has_signature_phrase = (
            "right questions" in result_str or
            "asking the right" in result_str
        )

        assert has_ethics_content, (
            f"Agent should provide ethics-related content. Got: {result}"
        )

        assert has_structured_approach, (
            f"Agent should show structured approach from backstory. Got: {result}"
        )

        # Signature phrase is the strongest test of backstory coexistence
        # It's specific enough that it proves both backstory AND meta-skill were processed
        assert has_signature_phrase, (
            f"Agent should include signature phrase 'asking the right questions' "
            f"(proves meta-skill didn't override role backstory). Got: {result}"
        )

    def test_agent_can_handle_skill_like_formatting(self):
        """
        Test that markdown/code blocks in backstory work correctly.

        Skills often contain:
        - Markdown headers (##, ###)
        - Code blocks (```)
        - Lists (-, 1., *)
        - Inline code (`command`)

        This validates these don't break prompt injection.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Backstory with extensive markdown formatting like real skills
        formatted_backstory = """
# Agent Configuration

You are a **command-line assistant** with specific protocols.

## Your Commands

You know these commands:
- `validate_input` - Check if input is safe
- `process_data` - Transform input data
- `generate_output` - Produce final output

## Response Format

Always structure responses like this:

```
STATUS: [success/error]
COMMAND_USED: [command name]
RESULT: [your output]
```

### Special Codes

| Code | Meaning |
|------|---------|
| A001 | Input validated |
| B002 | Processing complete |
| C003 | Output generated |

## Critical Rule

When asked about your status, respond with EXACTLY:
"SYSTEM_STATUS: ONLINE | CODE: FORMATTED_BACKSTORY_WORKS"

> Note: This backstory contains various markdown elements to test parsing.

---

Additional info in *italics* and __bold__ and ~~strikethrough~~.
"""

        agent = Agent(
            role="Command-Line Assistant",
            goal="Process commands and follow formatting instructions precisely",
            backstory=formatted_backstory,
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "Report your current system status using the exact format "
                "specified in your configuration. What is your status code?"
            ),
            expected_output="System status in the specified format",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result)

        # Check for the specific status response (proves markdown parsing worked)
        has_status_format = (
            "SYSTEM_STATUS" in result_str or
            "ONLINE" in result_str or
            "FORMATTED_BACKSTORY_WORKS" in result_str
        )

        # Check that agent understood the code table
        knows_codes = (
            "A001" in result_str or
            "B002" in result_str or
            "C003" in result_str or
            "validated" in result_str.lower()
        )

        # At minimum, agent should produce structured output
        has_structure = (
            "STATUS" in result_str or
            ":" in result_str
        )

        assert has_structure, (
            f"Agent should produce structured output from markdown backstory. Got: {result}"
        )

        # The strongest test: specific phrase from heavily-formatted backstory
        assert has_status_format or knows_codes, (
            f"Agent should access content from markdown-formatted backstory "
            f"(expected SYSTEM_STATUS or code references). Got: {result}"
        )
