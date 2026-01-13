"""
Test: LangChain tool output is returned to agent context.

This test validates a critical assumption for SkillForge:
- Tool outputs (including shell command results) are returned to the agent
- The agent can use tool outputs in its reasoning and responses
- Tool outputs can contain skill content that influences subsequent behavior

Assumption Being Validated:
    "Tool output is returned to agent context"

Expected Behavior:
    1. When a LangChain agent calls a tool, the output is captured
    2. The agent receives and can read the tool output
    3. The agent's subsequent behavior is influenced by tool output
    4. Large tool outputs (like skill files) are properly handled

Test Strategy:
    1. Create agents with tools that return specific outputs
    2. Verify agents can reference and use the tool outputs
    3. Test that tool outputs influence agent decision-making
    4. Validate handling of multi-line/structured tool outputs

IMPORTANT: These tests validate that output is USED, not just that
commands run. The distinction is critical - test_shell_execution.py
validates commands execute; these tests validate output informs behavior.

Dependencies:
    - langchain
    - langchain-anthropic or langchain-openai
    - API key for LLM (Anthropic or OpenAI)

Related Design Doc Section:
    See docs/plans/2025-12-04-skillforge-design.md - "Progressive Loading"
"""

import tempfile
from pathlib import Path

import pytest

from tests.validation.langchain.conftest import get_langchain_llm, shell_command, LANGCHAIN_AVAILABLE

# LangChain agent imports - may not be available in all LangChain versions
LANGCHAIN_AGENTS_AVAILABLE = False
if LANGCHAIN_AVAILABLE:
    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain.agents import create_tool_calling_agent, AgentExecutor
        LANGCHAIN_AGENTS_AVAILABLE = True
    except ImportError:
        pass


def create_agent_executor(llm, tools, system_prompt: str):
    """
    Create a LangChain agent executor with the given LLM and tools.

    Args:
        llm: The LangChain LLM instance
        tools: List of tools the agent can use
        system_prompt: The system prompt describing the agent's role

    Returns:
        AgentExecutor instance ready to invoke
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)


@pytest.mark.validation
@pytest.mark.langchain_assumption
@pytest.mark.requires_api_key
class TestToolOutputUsage:
    """
    Validate that LangChain agents receive and use tool outputs.

    This is critical for the `skillforge read` pattern where
    skill content is loaded via tool execution.

    IMPORTANT: These tests validate that output is USED, not just that
    commands run. The distinction is critical - test_shell_execution.py
    validates commands execute; these tests validate output informs behavior.
    """

    def test_agent_uses_tool_output_in_response(self, langchain_llm):
        """
        Test that an agent incorporates tool output into its response.

        This is the most basic validation: agent executes command, receives
        output, and incorporates that output into its response.

        Difference from test_shell_execution: We verify the agent TRANSFORMS
        the output (extracts meaning), not just echoes it back.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        # Create temp file with structured data the agent must interpret
        test_content = """SECRET_CODE: BRAVO-9921-ECHO
STATUS: operational
PRIORITY: critical"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            system_prompt = (
                "You are a data analyst who reads files and extracts specific information. "
                "You never just echo file content - you extract and report specific values."
            )

            executor = create_agent_executor(
                llm=langchain_llm,
                tools=[shell_command],
                system_prompt=system_prompt
            )

            # Ask for interpretation, not just reading
            result = executor.invoke({
                "input": (
                    f"Read the file at '{temp_path}' using the shell_command tool (use cat). "
                    f"Then answer: What is the secret code? What is the priority level? "
                    f"Respond with just the extracted values."
                )
            })

            result_str = str(result.get("output", "")).upper()

            # Verify agent extracted and reported the specific values
            has_code = "BRAVO-9921-ECHO" in result_str or ("BRAVO" in result_str and "9921" in result_str)
            has_priority = "CRITICAL" in result_str

            assert has_code, (
                f"Agent should extract and report the secret code (BRAVO-9921-ECHO). Got: {result}"
            )
            assert has_priority, (
                f"Agent should extract and report the priority (critical). Got: {result}"
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_agent_can_summarize_file_content(self, langchain_llm, test_skill_path):
        """
        Test that agent can summarize file content read via shell.

        This validates the agent doesn't just echo content but can
        produce a meaningful summary - critical for SkillForge where
        agents need to understand skill instructions.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        system_prompt = (
            "You are a skilled summarizer who reads documents and extracts "
            "key points. You never just repeat content verbatim - you "
            "synthesize and summarize."
        )

        executor = create_agent_executor(
            llm=langchain_llm,
            tools=[shell_command],
            system_prompt=system_prompt
        )

        result = executor.invoke({
            "input": (
                f"Read the skill file at '{test_skill_path}' using shell_command (use cat). "
                f"Then provide a brief summary answering: "
                f"1. What is the skill name? "
                f"2. What should you say when the skill is activated? "
                f"3. How should you end your response when using this skill?"
            )
        })

        result_str = str(result.get("output", "")).lower()

        # Verify agent extracted key information from the skill file
        assert "test-skill" in result_str or "test skill" in result_str, (
            f"Agent should identify the skill name as 'test-skill'. Got: {result}"
        )
        # The skill says to respond with "Test skill activated successfully"
        assert "activated" in result_str or "success" in result_str, (
            f"Agent should mention the activation phrase. Got: {result}"
        )
        # The skill says to end with "Test skill completed"
        assert "completed" in result_str or "complete" in result_str, (
            f"Agent should mention the completion phrase. Got: {result}"
        )

    def test_agent_uses_output_for_decision_making(self, langchain_llm):
        """
        Test that agent can use tool output to make decisions.

        This validates agents can read conditional information and
        act accordingly - essential for skill-based behavior.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        # Create a config file that dictates behavior
        config_content = """MODE: VERBOSE
OUTPUT_FORMAT: json
MAX_ITEMS: 5
ERROR_HANDLING: strict"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            system_prompt = (
                "You are an agent that reads configuration files and explains "
                "how each setting would affect your behavior. You must read the "
                "actual config, not guess."
            )

            executor = create_agent_executor(
                llm=langchain_llm,
                tools=[shell_command],
                system_prompt=system_prompt
            )

            result = executor.invoke({
                "input": (
                    f"Read the configuration file at '{config_path}' using shell_command. "
                    f"Based on the settings you read, answer: "
                    f"1. Should you provide brief or detailed output? (check MODE) "
                    f"2. What format should your output be in? (check OUTPUT_FORMAT) "
                    f"3. How many items maximum should you return? (check MAX_ITEMS)"
                )
            })

            result_str = str(result.get("output", "")).lower()

            # Verify agent read config and made correct decisions
            # MODE: VERBOSE means detailed output
            assert "verbose" in result_str or "detailed" in result_str, (
                f"Agent should recognize VERBOSE mode means detailed output. Got: {result}"
            )
            # OUTPUT_FORMAT: json
            assert "json" in result_str, (
                f"Agent should report JSON output format. Got: {result}"
            )
            # MAX_ITEMS: 5
            assert "5" in result_str or "five" in result_str, (
                f"Agent should report max items as 5. Got: {result}"
            )
        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_agent_chains_tool_calls(self, langchain_llm):
        """
        Test that agent can use output from one command to inform another.

        This validates command chaining - agent reads one file, uses that
        info to decide what to do next. Critical for multi-skill workflows.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        # Create a data file with the target information
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            data_content = """RESULT: The treasure is buried under the old oak tree.
COORDINATES: 45.123, -93.456
VERIFIED: true"""
            f.write(data_content)
            data_path = f.name

        # Create an index file that points to the data file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            index_content = f"""ACTIVE_DATA_FILE: {data_path}
BACKUP_FILE: /tmp/backup.txt
LAST_UPDATED: 2024-01-15"""
            f.write(index_content)
            index_path = f.name

        try:
            system_prompt = (
                "You are a file system navigator. You read index files to find "
                "where data is stored, then read the actual data files. You must "
                "chain commands: first read the index, then read the file it points to."
            )

            executor = create_agent_executor(
                llm=langchain_llm,
                tools=[shell_command],
                system_prompt=system_prompt
            )

            result = executor.invoke({
                "input": (
                    f"First, read the index file at '{index_path}' using shell_command. "
                    f"Find the ACTIVE_DATA_FILE path in that index. "
                    f"Then, read THAT file using another shell_command. "
                    f"Finally, tell me: What is the RESULT found in the data file? "
                    f"Where are the COORDINATES?"
                )
            })

            result_str = str(result.get("output", "")).lower()

            # Verify agent followed the chain and got data from the second file
            assert "treasure" in result_str or "oak" in result_str, (
                f"Agent should find the treasure result from chained file read. Got: {result}"
            )
            assert "45" in result_str or "93" in result_str or "coordinate" in result_str, (
                f"Agent should report coordinates from the data file. Got: {result}"
            )
        finally:
            Path(index_path).unlink(missing_ok=True)
            Path(data_path).unlink(missing_ok=True)
