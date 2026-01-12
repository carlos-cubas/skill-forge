"""
Test: CrewAI agents can execute Bash commands during task execution.

This test validates a critical assumption for SkillForge:
- CrewAI agents must be able to call shell/bash commands at runtime
- This enables the `skillforge read <skill-name>` pattern for progressive skill loading

Assumption Being Validated:
    "Agents can call Bash commands during execution"

Expected Behavior:
    1. A CrewAI agent with access to a shell/bash tool can execute commands
    2. The command output is captured and returned to the agent
    3. The agent can use this output in its reasoning/response

Test Strategy:
    1. Create a CrewAI agent with shell tool access
    2. Give it a task that requires running a simple bash command
    3. Verify the agent executes the command and uses the output

Dependencies:
    - crewai
    - crewai-tools (for shell tool)
    - API key for LLM (Anthropic or OpenAI)

Related Design Doc Section:
    See docs/plans/2025-12-04-skillforge-design.md - "Meta-Skill Auto-Injection"
"""

import tempfile
from pathlib import Path

import pytest
from crewai import Agent, Task, Crew

from tests.validation.crewai.conftest import get_llm_config, bash_command


@pytest.mark.validation
@pytest.mark.crewai_assumption
@pytest.mark.requires_api_key
class TestBashExecution:
    """
    Validate that CrewAI agents can execute Bash commands.

    This is a blocking prerequisite for SkillForge's progressive
    skill loading mechanism.
    """

    def test_agent_can_execute_simple_bash_command(self):
        """
        Test that an agent can execute a simple bash command like 'echo'.

        Expected: Agent runs `echo 'hello world'` and receives "hello world" as output.
        This validates the basic mechanism that SkillForge will use to load skills.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        agent = Agent(
            role="Command Executor",
            goal="Execute bash commands precisely as instructed and report their exact output",
            backstory="You are a precise command executor. When asked to run a command, "
                      "you execute it using the bash_command tool and report the exact output.",
            tools=[bash_command],
            llm=llm,
            verbose=False
        )

        task = Task(
            description="Run the bash command: echo 'hello world' and tell me exactly what the output was.",
            expected_output="The exact output from the echo command",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).lower()

        # The agent should have executed the command and received "hello world"
        assert "hello" in result_str and "world" in result_str, (
            f"Agent should report 'hello world' in output. Got: {result}"
        )

    def test_agent_receives_bash_output(self):
        """
        Test that an agent can read file contents via bash and use that output.

        This simulates `skillforge read` which outputs skill content to stdout.
        The agent must receive and act on the command output.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Create a temp file with known content
        test_content = "UNIQUE_MARKER_XYZ123: This is test content for validation."
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            agent = Agent(
                role="File Reader",
                goal="Read files using bash commands and report their contents accurately",
                backstory="You are a file reader. When asked to read a file, "
                          "you use the bash_command tool to cat the file and report what you find.",
                tools=[bash_command],
                llm=llm,
                verbose=False
            )

            task = Task(
                description=f"Use the bash_command tool to read the file at '{temp_path}' using 'cat' and tell me what unique marker code you find in the file.",
                expected_output="The unique marker code found in the file",
                agent=agent
            )

            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            )

            result = crew.kickoff()
            result_str = str(result).upper()

            # The agent should have read the file and found the unique marker
            assert "XYZ123" in result_str or "UNIQUE_MARKER" in result_str, (
                f"Agent should find and report the unique marker from the file. Got: {result}"
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_agent_can_handle_command_error(self):
        """
        Test that an agent gracefully handles command execution errors.

        Expected: Agent receives error message and can report/handle it.
        This is important for robustness when `skillforge read` fails.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        agent = Agent(
            role="Error Handler",
            goal="Execute commands and accurately report their outcomes including errors",
            backstory="You are a careful command executor. When commands fail, "
                      "you report the error clearly rather than making up results.",
            tools=[bash_command],
            llm=llm,
            verbose=False
        )

        task = Task(
            description="Run the bash command: cat /nonexistent_file_that_does_not_exist_12345 "
                        "and report what happens. Did the command succeed or fail?",
            expected_output="A report on whether the command succeeded or failed, including any error message",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).lower()

        # The agent should acknowledge that an error occurred
        error_indicators = ["error", "fail", "not found", "no such file", "does not exist"]
        assert any(indicator in result_str for indicator in error_indicators), (
            f"Agent should report that the command failed or produced an error. Got: {result}"
        )

    def test_agent_can_run_multiple_commands(self):
        """
        Test that an agent can run multiple sequential bash commands.

        This validates that agents can use the bash tool repeatedly,
        which may be needed if loading multiple skills during a session.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        agent = Agent(
            role="Multi-Command Executor",
            goal="Execute multiple bash commands and combine their outputs",
            backstory="You are a command executor that can run multiple commands "
                      "and report the combined results accurately.",
            tools=[bash_command],
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "Run these two bash commands and report both results:\n"
                "1. echo 'FIRST_OUTPUT_ABC'\n"
                "2. echo 'SECOND_OUTPUT_XYZ'\n"
                "Tell me exactly what each command output."
            ),
            expected_output="The output from both commands clearly reported",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).upper()

        # The agent should report outputs from both commands
        has_first = "FIRST" in result_str or "ABC" in result_str
        has_second = "SECOND" in result_str or "XYZ" in result_str

        assert has_first and has_second, (
            f"Agent should report outputs from both commands. "
            f"Found first: {has_first}, second: {has_second}. Got: {result}"
        )
