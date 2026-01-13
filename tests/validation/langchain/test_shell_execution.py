"""
Test: LangChain agents can execute shell commands via tool.

This test validates a critical assumption for SkillForge:
- LangChain agents must be able to call shell commands at runtime
- This enables the `skillforge read <skill-name>` pattern for progressive skill loading

Assumption Being Validated:
    "Agents can call shell commands via tool"

Expected Behavior:
    1. A LangChain agent with access to a shell tool can execute commands
    2. The command output is captured and returned to the agent
    3. The agent can use this output in its reasoning/response

Test Strategy:
    1. Create a LangChain agent with shell tool access
    2. Give it a task that requires running a simple shell command
    3. Verify the agent executes the command and uses the output

Dependencies:
    - langchain
    - langchain-anthropic or langchain-openai
    - API key for LLM (Anthropic or OpenAI)

Related Design Doc Section:
    See docs/plans/2025-12-04-skillforge-design.md - "LangChain Assumptions"
"""

import tempfile
from pathlib import Path

import pytest

from tests.validation.langchain.conftest import (
    get_langchain_llm,
    shell_command,
    LANGCHAIN_AGENTS_AVAILABLE,
    create_agent_executor,
)


@pytest.mark.validation
@pytest.mark.langchain_assumption
@pytest.mark.requires_api_key
class TestShellExecution:
    """
    Validate that LangChain agents can execute shell commands via tools.

    This is a blocking prerequisite for SkillForge's progressive
    skill loading mechanism in LangChain.
    """

    def test_agent_can_execute_simple_shell_command(self, langchain_llm):
        """
        Test that an agent can execute a simple shell command like 'echo'.

        Expected: Agent runs `echo 'hello world'` and receives "hello world" as output.
        This validates the basic mechanism that SkillForge will use to load skills.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain agents not available")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        system_prompt = (
            "You are a precise command executor. When asked to run a command, "
            "you execute it using the shell_command tool and report the exact output."
        )

        executor = create_agent_executor(
            llm=langchain_llm,
            tools=[shell_command],
            system_prompt=system_prompt
        )

        result = executor.invoke({
            "input": "Run the shell command: echo 'hello world' and tell me exactly what the output was."
        })

        result_str = str(result.get("output", "")).lower()

        # The agent should have executed the command and received "hello world"
        assert "hello" in result_str and "world" in result_str, (
            f"Agent should report 'hello world' in output. Got: {result}"
        )

    def test_agent_receives_shell_output(self, langchain_llm):
        """
        Test that an agent can read file contents via shell and use that output.

        This simulates `skillforge read` which outputs skill content to stdout.
        The agent must receive and act on the command output.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain not installed")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        # Create a temp file with known content
        test_content = "UNIQUE_MARKER_XYZ123: This is test content for validation."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            system_prompt = (
                "You are a file reader. When asked to read a file, "
                "you use the shell_command tool to cat the file and report what you find."
            )

            executor = create_agent_executor(
                llm=langchain_llm,
                tools=[shell_command],
                system_prompt=system_prompt
            )

            result = executor.invoke({
                "input": f"Use the shell_command tool to read the file at '{temp_path}' using 'cat' and tell me what unique marker code you find in the file."
            })

            result_str = str(result.get("output", "")).upper()

            # The agent should have read the file and found the unique marker
            assert "XYZ123" in result_str or "UNIQUE_MARKER" in result_str, (
                f"Agent should find and report the unique marker from the file. Got: {result}"
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_agent_can_handle_command_error(self, langchain_llm):
        """
        Test that an agent gracefully handles command execution errors.

        Expected: Agent receives error message and can report/handle it.
        This is important for robustness when `skillforge read` fails.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain not installed")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        system_prompt = (
            "You are a careful command executor. When commands fail, "
            "you report the error clearly rather than making up results."
        )

        executor = create_agent_executor(
            llm=langchain_llm,
            tools=[shell_command],
            system_prompt=system_prompt
        )

        result = executor.invoke({
            "input": "Run the shell command: cat /nonexistent_file_that_does_not_exist_12345 "
                     "and report what happens. Did the command succeed or fail?"
        })

        result_str = str(result.get("output", "")).lower()

        # The agent should acknowledge that an error occurred
        error_indicators = ["error", "fail", "not found", "no such file", "does not exist"]
        assert any(indicator in result_str for indicator in error_indicators), (
            f"Agent should report that the command failed or produced an error. Got: {result}"
        )

    def test_agent_can_run_multiple_commands(self, langchain_llm):
        """
        Test that an agent can run multiple sequential shell commands.

        This validates that agents can use the shell tool repeatedly,
        which may be needed if loading multiple skills during a session.
        """
        if not LANGCHAIN_AGENTS_AVAILABLE:
            pytest.skip("LangChain not installed")

        if shell_command is None:
            pytest.skip("Shell command tool not available")

        system_prompt = (
            "You are a command executor that can run multiple commands "
            "and report the combined results accurately."
        )

        executor = create_agent_executor(
            llm=langchain_llm,
            tools=[shell_command],
            system_prompt=system_prompt
        )

        result = executor.invoke({
            "input": (
                "Run these two shell commands and report both results:\n"
                "1. echo 'FIRST_OUTPUT_ABC'\n"
                "2. echo 'SECOND_OUTPUT_XYZ'\n"
                "Tell me exactly what each command output."
            )
        })

        result_str = str(result.get("output", "")).upper()

        # The agent should report outputs from both commands
        has_first = "FIRST" in result_str or "ABC" in result_str
        has_second = "SECOND" in result_str or "XYZ" in result_str

        assert has_first and has_second, (
            f"Agent should report outputs from both commands. "
            f"Found first: {has_first}, second: {has_second}. Got: {result}"
        )
