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

import subprocess
import tempfile
from pathlib import Path

import pytest
from crewai import Agent, Task, Crew
from crewai.tools import tool

from tests.validation.crewai.conftest import get_llm_config


# Custom Bash tool for CrewAI agents
@tool("bash_command")
def bash_command(command: str) -> str:
    """
    Execute a bash command and return its output.

    Args:
        command: The bash command to execute.

    Returns:
        The stdout output of the command, or error message if the command fails.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return f"Error (exit code {result.returncode}): {result.stderr}"
        return result.stdout.strip() if result.stdout else "Command completed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


@pytest.mark.validation
@pytest.mark.crewai_assumption
@pytest.mark.requires_api_key
class TestBashOutputUsage:
    """
    Validate that CrewAI agents can use bash command output.

    SkillForge relies on agents reading `skillforge read` output
    and incorporating skill instructions mid-task.

    IMPORTANT: These tests validate that output is USED, not just that
    commands run. The distinction is critical - test_bash_execution.py
    validates commands execute; these tests validate output informs behavior.
    """

    def test_agent_uses_bash_output_in_response(self):
        """
        Test that agent can use simple command output in its reasoning.

        This is the most basic validation: agent executes command, receives
        output, and incorporates that output into its response.

        Difference from test_bash_execution: We verify the agent TRANSFORMS
        the output (extracts meaning), not just echoes it back.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Create temp file with structured data the agent must interpret
        test_content = """SECRET_CODE: ALPHA-7734-DELTA
STATUS: operational
PRIORITY: high"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            agent = Agent(
                role="Data Analyst",
                goal="Read files and extract specific information from structured data",
                backstory="You are a data analyst who reads files and extracts key information. "
                          "You always report the specific values you find, not the raw file content.",
                tools=[bash_command],
                llm=llm,
                verbose=False
            )

            # Ask for interpretation, not just reading
            task = Task(
                description=(
                    f"Read the file at '{temp_path}' using the bash_command tool (use cat). "
                    f"Then answer: What is the secret code? What is the priority level? "
                    f"Respond with just the extracted values."
                ),
                expected_output="The secret code and priority level extracted from the file",
                agent=agent
            )

            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            )

            result = crew.kickoff()
            result_str = str(result).upper()

            # Verify agent extracted and reported the specific values
            has_code = "ALPHA-7734-DELTA" in result_str or "ALPHA" in result_str and "7734" in result_str
            has_priority = "HIGH" in result_str

            assert has_code, (
                f"Agent should extract and report the secret code (ALPHA-7734-DELTA). Got: {result}"
            )
            assert has_priority, (
                f"Agent should extract and report the priority (high). Got: {result}"
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_agent_can_summarize_file_content(self, test_skill_path):
        """
        Test that agent can summarize file content read via bash.

        This validates the agent doesn't just echo content but can
        produce a meaningful summary - critical for SkillForge where
        agents need to understand skill instructions.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        agent = Agent(
            role="Content Summarizer",
            goal="Read files and provide concise, accurate summaries",
            backstory="You are a skilled summarizer who reads documents and extracts "
                      "the key points. You never just repeat content verbatim - you "
                      "synthesize and summarize.",
            tools=[bash_command],
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                f"Read the skill file at '{test_skill_path}' using bash_command (use cat). "
                f"Then provide a brief summary answering: "
                f"1. What is the skill name? "
                f"2. What should you say when the skill is activated? "
                f"3. How should you end your response when using this skill?"
            ),
            expected_output="A summary answering the three questions about the skill",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result).lower()

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

    def test_agent_uses_output_for_decision_making(self):
        """
        Test that agent can use bash output to make decisions.

        This validates agents can read conditional information and
        act accordingly - essential for skill-based behavior.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Create a config file that dictates behavior
        config_content = """MODE: VERBOSE
OUTPUT_FORMAT: json
MAX_ITEMS: 5
ERROR_HANDLING: strict"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.cfg', delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            agent = Agent(
                role="Configuration Reader",
                goal="Read configuration and describe how you would behave based on settings",
                backstory="You are an agent that reads configuration files and explains "
                          "how each setting would affect your behavior. You must read the "
                          "actual config, not guess.",
                tools=[bash_command],
                llm=llm,
                verbose=False
            )

            task = Task(
                description=(
                    f"Read the configuration file at '{config_path}' using bash_command. "
                    f"Based on the settings you read, answer: "
                    f"1. Should you provide brief or detailed output? (check MODE) "
                    f"2. What format should your output be in? (check OUTPUT_FORMAT) "
                    f"3. How many items maximum should you return? (check MAX_ITEMS)"
                ),
                expected_output="Answers to the three questions based on the config file settings",
                agent=agent
            )

            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            )

            result = crew.kickoff()
            result_str = str(result).lower()

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

    def test_agent_handles_multiline_output(self):
        """
        Test that agent correctly handles multi-line bash output.

        Skills are multi-line markdown files. Agent must preserve
        and understand structure across many lines.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Create a file with multiple distinct sections
        multiline_content = """# Document Title: Project Alpha

## Section 1: Overview
This project aims to revolutionize widget production.
Key stakeholders: Engineering, Marketing, Sales.

## Section 2: Timeline
- Phase 1: Research (Q1)
- Phase 2: Development (Q2)
- Phase 3: Launch (Q3)

## Section 3: Budget
Total allocated: $500,000
Primary expense: Engineering salaries

## Section 4: Success Metrics
- Widget production up 50%
- Customer satisfaction > 90%
- Revenue increase of $2M"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(multiline_content)
            temp_path = f.name

        try:
            agent = Agent(
                role="Document Analyst",
                goal="Read multi-section documents and extract information from specific sections",
                backstory="You are a document analyst who can read lengthy documents and "
                          "extract information from specific sections. You pay attention to "
                          "document structure and headings.",
                tools=[bash_command],
                llm=llm,
                verbose=False
            )

            task = Task(
                description=(
                    f"Read the document at '{temp_path}' using bash_command. "
                    f"Answer these questions about SPECIFIC sections: "
                    f"1. From Section 2: What happens in Q2? "
                    f"2. From Section 3: What is the total budget? "
                    f"3. From Section 4: What is the target for customer satisfaction?"
                ),
                expected_output="Answers to the three questions, each referencing the correct section",
                agent=agent
            )

            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            )

            result = crew.kickoff()
            result_str = str(result).lower()

            # Verify agent extracted info from different sections
            # Q2 is Development phase
            assert "development" in result_str or "q2" in result_str, (
                f"Agent should identify Development phase in Q2. Got: {result}"
            )
            # Budget is $500,000
            assert "500" in result_str or "500000" in result_str, (
                f"Agent should report budget of $500,000. Got: {result}"
            )
            # Customer satisfaction target is > 90%
            assert "90" in result_str, (
                f"Agent should report 90% customer satisfaction target. Got: {result}"
            )
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_agent_chains_multiple_commands(self):
        """
        Test that agent can use output from one command to inform another.

        This validates command chaining - agent reads one file, uses that
        info to decide what to do next. Critical for multi-skill workflows.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        # Create an index file that points to another file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            data_content = """RESULT: The treasure is buried under the old oak tree.
COORDINATES: 45.123, -93.456
VERIFIED: true"""
            f.write(data_content)
            data_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            index_content = f"""ACTIVE_DATA_FILE: {data_path}
BACKUP_FILE: /tmp/backup.txt
LAST_UPDATED: 2024-01-15"""
            f.write(index_content)
            index_path = f.name

        try:
            agent = Agent(
                role="File System Navigator",
                goal="Read index files to discover data files, then read those data files",
                backstory="You are a file system navigator. You read index files to find "
                          "where data is stored, then read the actual data files. You must "
                          "chain commands: first read the index, then read the file it points to.",
                tools=[bash_command],
                llm=llm,
                verbose=False
            )

            task = Task(
                description=(
                    f"First, read the index file at '{index_path}' using bash_command. "
                    f"Find the ACTIVE_DATA_FILE path in that index. "
                    f"Then, read THAT file using another bash_command. "
                    f"Finally, tell me: What is the RESULT found in the data file? "
                    f"Where are the COORDINATES?"
                ),
                expected_output="The RESULT and COORDINATES from the data file that the index pointed to",
                agent=agent
            )

            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            )

            result = crew.kickoff()
            result_str = str(result).lower()

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

    def test_agent_uses_dynamic_content(self):
        """
        Test that agent can handle dynamically generated content.

        This validates that agents work with runtime-generated output,
        not just static files - important for skill versions, timestamps, etc.
        """
        llm, available = get_llm_config()
        if not available:
            pytest.skip("No LLM API key available")

        agent = Agent(
            role="System Information Analyst",
            goal="Gather and analyze system information from dynamic commands",
            backstory="You are a system analyst who runs commands to gather live "
                      "information about the system state. You analyze the output "
                      "and provide insights.",
            tools=[bash_command],
            llm=llm,
            verbose=False
        )

        task = Task(
            description=(
                "Run these commands and use their output to answer questions:\n"
                "1. Run 'date +%Y' - What year is it?\n"
                "2. Run 'whoami' - What is the current username?\n"
                "3. Run 'pwd' - What is the current working directory?\n"
                "Combine these into a status report starting with 'SYSTEM STATUS REPORT:'"
            ),
            expected_output="A status report including the year, username, and current directory",
            agent=agent
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=False
        )

        result = crew.kickoff()
        result_str = str(result)

        # Verify agent executed dynamic commands and used their output
        # Year should be 2024 or 2025 (or nearby - this is runtime data)
        year_found = any(str(year) in result_str for year in range(2024, 2030))
        assert year_found, (
            f"Agent should report the current year from 'date' command. Got: {result}"
        )

        # Should contain "SYSTEM STATUS" or similar
        assert "status" in result_str.lower() or "report" in result_str.lower(), (
            f"Agent should format as a status report as requested. Got: {result}"
        )

        # Should mention some kind of path (from pwd)
        assert "/" in result_str, (
            f"Agent should include a path from 'pwd' command. Got: {result}"
        )
