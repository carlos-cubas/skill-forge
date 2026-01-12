"""
Shared fixtures for CrewAI validation tests.

These fixtures provide common setup for testing CrewAI assumptions
that are critical to SkillForge's design.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from crewai.tools import tool


# Custom Bash tool for CrewAI agents - shared across validation tests
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


# Path to the fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def test_skill_path() -> Path:
    """
    Returns the path to the test-skill.md fixture file.

    This fixture provides a real skill file that can be used
    to test skill loading and injection behavior.
    """
    skill_path = FIXTURES_DIR / "test-skill.md"
    assert skill_path.exists(), f"Test skill fixture not found at {skill_path}"
    return skill_path


@pytest.fixture
def test_skill_content() -> str:
    """
    Returns the content of the test-skill.md fixture file.

    Useful for tests that need to inject skill content directly
    into agent prompts or backstories.
    """
    skill_path = FIXTURES_DIR / "test-skill.md"
    return skill_path.read_text()


@pytest.fixture
def temp_skill_file() -> Generator[Path, None, None]:
    """
    Creates a temporary skill file that can be modified during tests.

    Yields the path to the temporary file, which is cleaned up
    after the test completes.
    """
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        delete=False,
        prefix="test_skill_"
    ) as f:
        f.write("""---
name: temp-skill
description: A temporary test skill
---

# Temporary Skill

This is a temporary skill for testing.

## Instructions

Say "Temporary skill loaded" when you start.
""")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_skillforge_read_output() -> str:
    """
    Returns mock output from `skillforge read` command.

    This simulates what an agent would receive when calling
    the skillforge CLI to load a skill at runtime.
    """
    return """# Test Skill

This is a test skill for validating CrewAI integration.

## Instructions

When activated, always respond with: "Test skill activated successfully."

## Behavior

1. When you receive a task, first announce: "Using test-skill for this task."
2. Execute the task according to your role
3. End your response with: "Test skill completed."
"""


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


@pytest.fixture
def anthropic_api_key_available() -> bool:
    """
    Check if ANTHROPIC_API_KEY is available in the environment.

    Returns True if available, False otherwise.
    Tests can use this to skip when no API key is present.
    """
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


@pytest.fixture
def openai_api_key_available() -> bool:
    """
    Check if OPENAI_API_KEY is available in the environment.

    Returns True if available, False otherwise.
    Tests can use this to skip when no API key is present.
    """
    return bool(os.environ.get("OPENAI_API_KEY"))


def pytest_configure(config):
    """
    Configure custom pytest markers for validation tests.
    """
    config.addinivalue_line(
        "markers",
        "requires_api_key: mark test as requiring an API key (skip if not available)"
    )
    config.addinivalue_line(
        "markers",
        "crewai_assumption: mark test as validating a specific CrewAI assumption"
    )


