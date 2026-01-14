"""
Shared fixtures for LangChain validation tests.

These fixtures provide common setup for testing LangChain assumptions
that are critical to SkillForge's design.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Generator, Tuple, Optional

import pytest

# LangChain imports - these may not be installed in all environments
try:
    from langchain_core.tools import tool as langchain_tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    langchain_tool = None

# LangChain agent imports - may not be available in all LangChain versions
LANGCHAIN_AGENTS_AVAILABLE = False
create_agent = None
if LANGCHAIN_AVAILABLE:
    try:
        from langchain.agents import create_agent
        LANGCHAIN_AGENTS_AVAILABLE = True
    except ImportError:
        pass


# Path to the shared fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def get_llm_config() -> Tuple[Optional[str], bool]:
    """
    Get LLM configuration based on available API keys.

    Returns tuple of (llm_provider, is_available).
    Prefers Anthropic if available, falls back to OpenAI.

    For LangChain, this returns the provider name to be used
    with the appropriate LangChain model class.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", True
    elif os.environ.get("OPENAI_API_KEY"):
        return "openai", True
    return None, False


def get_langchain_llm():
    """
    Create a LangChain LLM instance based on available API keys.

    Returns:
        A LangChain LLM instance (ChatAnthropic or ChatOpenAI) or None if no API key available.
    """
    provider, available = get_llm_config()
    if not available:
        return None

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
        except ImportError:
            pass

    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model="gpt-4o-mini", temperature=0)
        except ImportError:
            pass

    return None


# Shell tool for LangChain agents - shared across validation tests
if LANGCHAIN_AVAILABLE and langchain_tool is not None:
    @langchain_tool
    def shell_command(command: str) -> str:
        """
        Execute a shell command and return its output.

        Args:
            command: The shell command to execute.

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
else:
    shell_command = None


class AgentWrapper:
    """
    Wrapper that provides a compatible interface for LangChain 1.2.x agents.

    This wrapper allows tests to use the same invocation pattern as the old API:
    - executor.invoke({"input": "..."}) returns {"output": "..."}

    The new LangChain 1.2.x API uses:
    - agent.invoke({"messages": [("user", "...")]}) returns response with messages
    """

    def __init__(self, agent):
        self._agent = agent

    def invoke(self, input_dict):
        """
        Invoke the agent with the old-style input format.

        Args:
            input_dict: Dict with "input" key containing the user message

        Returns:
            Dict with "output" key containing the agent's final response
        """
        user_input = input_dict.get("input", "")
        result = self._agent.invoke({"messages": [("user", user_input)]})

        # Extract the final response from the new API format
        # The result contains a "messages" list; we want the last AI message content
        if hasattr(result, "get"):
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                # Handle both message objects and tuples
                if hasattr(last_message, "content"):
                    return {"output": last_message.content}
                elif isinstance(last_message, tuple) and len(last_message) >= 2:
                    return {"output": last_message[1]}
            # Fallback: try to get output directly
            if "output" in result:
                return {"output": result["output"]}
        # If result is a string or has content attribute
        if hasattr(result, "content"):
            return {"output": result.content}
        return {"output": str(result)}


def create_agent_executor(llm, tools, system_prompt: str):
    """
    Create a LangChain agent with the given LLM and tools.

    This is a shared helper for LangChain validation tests.
    Updated for LangChain 1.2.x API.

    Args:
        llm: The LangChain LLM instance
        tools: List of tools the agent can use
        system_prompt: The system prompt describing the agent's role

    Returns:
        AgentWrapper instance ready to invoke with {"input": "..."} format

    Note:
        This function requires LANGCHAIN_AGENTS_AVAILABLE to be True.
        Callers should check this before calling.
    """
    if not LANGCHAIN_AGENTS_AVAILABLE:
        raise RuntimeError(
            "LangChain agents not available. "
            "Check LANGCHAIN_AGENTS_AVAILABLE before calling create_agent_executor."
        )

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )
    return AgentWrapper(agent)


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
def test_skill_content(test_skill_path) -> str:
    """
    Returns the content of the test-skill.md fixture file.

    Useful for tests that need to inject skill content directly
    into agent prompts or system messages.
    """
    return test_skill_path.read_text()


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

This is a test skill for validating LangChain integration.

## Instructions

When activated, always respond with: "Test skill activated successfully."

## Behavior

1. When you receive a task, first announce: "Using test-skill for this task."
2. Execute the task according to your role
3. End your response with: "Test skill completed."
"""


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


@pytest.fixture
def langchain_llm():
    """
    Provides a LangChain LLM instance for tests.

    Skips the test if no API key is available.
    """
    llm = get_langchain_llm()
    if llm is None:
        pytest.skip("No LLM API key available or LangChain not installed")
    return llm
