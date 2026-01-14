"""
End-to-end validation tests for SkillForge skill injection.

These tests validate the complete skill loading pipeline with real LLMs.
They verify that:
1. Skills are correctly injected into agent prompts
2. Agents follow skill instructions
3. Output format compliance is achieved
4. Both progressive and inject modes work correctly

Requirements:
- OPENAI_API_KEY in .env or environment
- crewai and langchain packages installed
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "skills"

# Skip all tests in this module if OPENAI_API_KEY is not set
pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_api_key,
]


def get_openai_api_key() -> str:
    """Get OpenAI API key from environment."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set in environment")
    return key


class MockCrewAIAgent:
    """Mock CrewAI Agent for testing without actual crewai dependency."""

    def __init__(self, *args, role=None, goal=None, backstory=None, **kwargs):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.args = args
        self.kwargs = kwargs


@pytest.fixture
def skill_config_file(tmp_path):
    """Create a temporary .skillforge.yaml config file pointing to test fixtures."""
    config_content = f"""
skill_paths:
  - {FIXTURES_DIR}/*
"""
    config_file = tmp_path / ".skillforge.yaml"
    config_file.write_text(config_content)
    return tmp_path


@pytest.fixture
def mock_crewai(monkeypatch):
    """Mock crewai module for testing."""
    mock_module = MagicMock()
    mock_module.Agent = MockCrewAIAgent

    monkeypatch.setitem(sys.modules, "crewai", mock_module)

    # Clear any cached imports of our adapter
    for mod_name in list(sys.modules.keys()):
        if "skillforge.adapters.crewai" in mod_name or "skillforge.crewai" in mod_name:
            del sys.modules[mod_name]

    return mock_module


# =============================================================================
# CrewAI Tests - Progressive Mode
# =============================================================================


class TestCrewAIProgressiveMode:
    """Test CrewAI adapter in progressive mode with test skills."""

    def test_greeting_skill_injection_progressive(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that greeting skill is injected in progressive mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Customer Service Agent",
            goal="Greet customers warmly",
            backstory="Expert in customer service",
            skills=["example-greeting"],
            skill_mode="progressive",
        )

        # Verify skill is listed
        assert agent.skills == ["example-greeting"]
        assert agent.skill_mode == "progressive"

        # Backstory should contain meta-skill content
        assert "Using SkillForge Skills" in agent.backstory
        assert "example-greeting" in agent.backstory
        assert "skillforge read" in agent.backstory

        # Original backstory should be preserved
        assert "Expert in customer service" in agent.backstory

    def test_summarizer_skill_injection_progressive(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that summarizer skill is injected in progressive mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Research Assistant",
            goal="Summarize research papers",
            backstory="Expert in distilling complex information",
            skills=["example-summarizer"],
            skill_mode="progressive",
        )

        assert agent.skills == ["example-summarizer"]
        assert "example-summarizer" in agent.backstory

    def test_calculator_skill_injection_progressive(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that calculator skill is injected in progressive mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Math Tutor",
            goal="Help students with math problems",
            backstory="Expert mathematics tutor",
            skills=["example-calculator"],
            skill_mode="progressive",
        )

        assert agent.skills == ["example-calculator"]
        assert "example-calculator" in agent.backstory


# =============================================================================
# CrewAI Tests - Inject Mode
# =============================================================================


class TestCrewAIInjectMode:
    """Test CrewAI adapter in inject mode with test skills."""

    def test_greeting_skill_injection_inject(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that greeting skill content is fully injected."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Customer Service Agent",
            goal="Greet customers warmly",
            backstory="Expert in customer service",
            skills=["example-greeting"],
            skill_mode="inject",
        )

        assert agent.skill_mode == "inject"

        # Backstory should contain full skill content
        assert "## Available Skills" in agent.backstory
        assert "### example-greeting" in agent.backstory
        assert "Greeting Skill" in agent.backstory
        assert "When to Use" in agent.backstory
        assert "Output Format" in agent.backstory

        # Should contain specific instructions
        assert "Acknowledge the user warmly" in agent.backstory
        assert "Greeting: [warm greeting]" in agent.backstory

    def test_summarizer_skill_injection_inject(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that summarizer skill content is fully injected."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Research Assistant",
            goal="Summarize research papers",
            backstory="Expert summarizer",
            skills=["example-summarizer"],
            skill_mode="inject",
        )

        # Should contain summarizer skill instructions
        assert "Summarizer Skill" in agent.backstory
        assert "Extract 3-5 key points" in agent.backstory
        assert "Format as bullet points" in agent.backstory
        assert "Summary of [topic]" in agent.backstory

    def test_calculator_skill_injection_inject(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that calculator skill content is fully injected."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Math Tutor",
            goal="Help students with math problems",
            backstory="Expert tutor",
            skills=["example-calculator"],
            skill_mode="inject",
        )

        # Should contain calculator skill instructions
        assert "Calculator Skill" in agent.backstory
        assert "State the problem" in agent.backstory
        assert "Show each step of the calculation" in agent.backstory
        assert "Step 1: [first operation]" in agent.backstory


# =============================================================================
# Multiple Skills Tests
# =============================================================================


class TestMultipleSkillsSelection:
    """Test agents with multiple skills assigned."""

    def test_multiple_skills_progressive(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test agent with multiple skills in progressive mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Teaching Assistant",
            goal="Help students learn",
            backstory="Expert educator",
            skills=["example-greeting", "example-calculator", "example-summarizer"],
            skill_mode="progressive",
        )

        assert len(agent.skills) == 3
        assert "example-greeting" in agent.backstory
        assert "example-calculator" in agent.backstory
        assert "example-summarizer" in agent.backstory

    def test_multiple_skills_inject(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test agent with multiple skills in inject mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Teaching Assistant",
            goal="Help students learn",
            backstory="Expert educator",
            skills=["example-greeting", "example-calculator"],
            skill_mode="inject",
        )

        # Both skills should have full content injected
        assert "### example-greeting" in agent.backstory
        assert "### example-calculator" in agent.backstory
        assert "Greeting Skill" in agent.backstory
        assert "Calculator Skill" in agent.backstory


# =============================================================================
# LangChain Tests - System Prompt Building
# =============================================================================


class TestLangChainSystemPromptBuilding:
    """Test LangChain adapter system prompt building with test skills."""

    def test_greeting_skill_progressive_prompt(
        self, skill_config_file, monkeypatch
    ):
        """Test that greeting skill is added to system prompt in progressive mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import _build_system_prompt
        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skill = loader.get("example-greeting")

        prompt = _build_system_prompt(
            "You are a helpful assistant.",
            [skill],
            "progressive"
        )

        assert "You are a helpful assistant." in prompt
        assert "Using SkillForge Skills" in prompt
        assert "example-greeting" in prompt

    def test_greeting_skill_inject_prompt(
        self, skill_config_file, monkeypatch
    ):
        """Test that greeting skill is fully added to system prompt in inject mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import _build_system_prompt
        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skill = loader.get("example-greeting")

        prompt = _build_system_prompt(
            "You are a helpful assistant.",
            [skill],
            "inject"
        )

        assert "You are a helpful assistant." in prompt
        assert "## Available Skills" in prompt
        assert "### example-greeting" in prompt
        assert "Greeting Skill" in prompt
        assert "Acknowledge the user warmly" in prompt

    def test_multiple_skills_inject_prompt(
        self, skill_config_file, monkeypatch
    ):
        """Test multiple skills in inject mode system prompt."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import _build_system_prompt
        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skills = [
            loader.get("example-greeting"),
            loader.get("example-summarizer"),
        ]

        prompt = _build_system_prompt(
            "You are a helpful assistant.",
            skills,
            "inject"
        )

        assert "### example-greeting" in prompt
        assert "### example-summarizer" in prompt
        assert "Greeting Skill" in prompt
        assert "Summarizer Skill" in prompt


# =============================================================================
# Output Format Compliance Tests
# =============================================================================


class TestOutputFormatCompliance:
    """Test that skill output format instructions are properly included."""

    def test_greeting_format_included_inject(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that greeting output format is included in inject mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Assistant",
            goal="Greet users",
            backstory="",
            skills=["example-greeting"],
            skill_mode="inject",
        )

        # Should include output format instructions
        assert "Output Format" in agent.backstory
        assert "Greeting: [warm greeting]" in agent.backstory
        assert "Introduction: [one sentence about your role]" in agent.backstory
        assert "Offer: [ask how to help]" in agent.backstory

    def test_summarizer_format_included_inject(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that summarizer output format is included in inject mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Assistant",
            goal="Summarize text",
            backstory="",
            skills=["example-summarizer"],
            skill_mode="inject",
        )

        # Should include output format instructions
        assert "Output Format" in agent.backstory
        assert "Summary of [topic]" in agent.backstory
        assert "[key point 1]" in agent.backstory

    def test_calculator_format_included_inject(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that calculator output format is included in inject mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Assistant",
            goal="Calculate",
            backstory="",
            skills=["example-calculator"],
            skill_mode="inject",
        )

        # Should include output format instructions
        assert "Output Format" in agent.backstory
        assert "Problem: [restate the question]" in agent.backstory
        assert "Step 1: [first operation]" in agent.backstory
        assert "Answer: [final result]" in agent.backstory


# =============================================================================
# Real LLM Integration Tests (requires OPENAI_API_KEY)
# =============================================================================


class TestRealLLMIntegration:
    """Integration tests using real LLM calls with OpenAI."""

    @pytest.mark.slow
    def test_langchain_openai_greeting_skill(
        self, skill_config_file, monkeypatch
    ):
        """Test LangChain with OpenAI and greeting skill (inject mode)."""
        get_openai_api_key()
        monkeypatch.chdir(skill_config_file)

        from langchain_openai import ChatOpenAI
        from skillforge.adapters.langchain import _build_system_prompt
        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skill = loader.get("example-greeting")

        system_prompt = _build_system_prompt(
            "You are a friendly customer service agent.",
            [skill],
            "inject"
        )

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Hello!"},
        ]

        response = llm.invoke(messages)

        # Verify the response follows the skill format
        response_text = response.content.lower()

        # The model should follow the greeting skill format
        # Check for structure elements (case-insensitive)
        has_greeting_structure = any([
            "greeting:" in response_text,
            "introduction:" in response_text,
            "offer:" in response_text,
            "hello" in response_text and "help" in response_text,
        ])

        assert has_greeting_structure, (
            f"Expected greeting skill format in response. Got: {response.content}"
        )

    @pytest.mark.slow
    def test_langchain_openai_summarizer_skill(
        self, skill_config_file, monkeypatch
    ):
        """Test LangChain with OpenAI and summarizer skill (inject mode)."""
        get_openai_api_key()
        monkeypatch.chdir(skill_config_file)

        from langchain_openai import ChatOpenAI
        from skillforge.adapters.langchain import _build_system_prompt
        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skill = loader.get("example-summarizer")

        system_prompt = _build_system_prompt(
            "You are a research assistant.",
            [skill],
            "inject"
        )

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
        )

        text_to_summarize = """
        Artificial intelligence has transformed many industries. In healthcare,
        AI helps diagnose diseases earlier and more accurately. In finance,
        AI algorithms detect fraud and optimize trading strategies. Transportation
        is being revolutionized by autonomous vehicles. Manufacturing uses AI
        for quality control and predictive maintenance. The impact continues to grow.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please summarize this: {text_to_summarize}"},
        ]

        response = llm.invoke(messages)

        # Verify the response follows the skill format
        response_text = response.content

        # The model should use bullet points as specified
        has_bullet_points = any([
            "*" in response_text,  # Markdown bullets
            "-" in response_text,  # Dash bullets
            "1." in response_text,  # Numbered list
        ])

        # Should mention the summary topic
        is_summary = any([
            "summary" in response_text.lower(),
            "ai" in response_text.lower(),
            "artificial intelligence" in response_text.lower(),
        ])

        assert has_bullet_points and is_summary, (
            f"Expected summarizer skill format in response. Got: {response.content}"
        )

    @pytest.mark.slow
    def test_langchain_openai_calculator_skill(
        self, skill_config_file, monkeypatch
    ):
        """Test LangChain with OpenAI and calculator skill (inject mode)."""
        get_openai_api_key()
        monkeypatch.chdir(skill_config_file)

        from langchain_openai import ChatOpenAI
        from skillforge.adapters.langchain import _build_system_prompt
        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skill = loader.get("example-calculator")

        system_prompt = _build_system_prompt(
            "You are a math tutor.",
            [skill],
            "inject"
        )

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "What is 15 + 27?"},
        ]

        response = llm.invoke(messages)

        # Verify the response follows the skill format
        response_text = response.content.lower()

        # Should show step-by-step work
        has_step_format = any([
            "step" in response_text,
            "problem:" in response_text,
            "answer:" in response_text,
        ])

        # Should have correct answer
        has_correct_answer = "42" in response_text

        assert has_step_format and has_correct_answer, (
            f"Expected calculator skill format with correct answer. Got: {response.content}"
        )

    @pytest.mark.slow
    def test_langchain_openai_multiple_skills(
        self, skill_config_file, monkeypatch
    ):
        """Test LangChain with OpenAI and multiple skills (inject mode)."""
        get_openai_api_key()
        monkeypatch.chdir(skill_config_file)

        from langchain_openai import ChatOpenAI
        from skillforge.adapters.langchain import _build_system_prompt
        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skills = [
            loader.get("example-greeting"),
            loader.get("example-calculator"),
        ]

        system_prompt = _build_system_prompt(
            "You are a helpful teaching assistant.",
            skills,
            "inject"
        )

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
        )

        # First interaction - greeting
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Hi! Can you help me with math?"},
        ]

        response = llm.invoke(messages)
        response_text = response.content.lower()

        # Should include some form of greeting and offer to help
        is_helpful_response = any([
            "help" in response_text,
            "happy to" in response_text,
            "glad" in response_text,
            "assist" in response_text,
        ])

        assert is_helpful_response, (
            f"Expected helpful response with greeting. Got: {response.content}"
        )


# =============================================================================
# Skill Discovery Integration Tests
# =============================================================================


class TestSkillDiscoveryIntegration:
    """Test that skills are correctly discovered from fixtures directory."""

    def test_discover_all_example_skills(
        self, skill_config_file, monkeypatch
    ):
        """Test that all example skills are discovered."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skills = loader.discover()

        skill_names = list(skills.keys())

        # Should find our example skills
        assert "example-greeting" in skill_names
        assert "example-summarizer" in skill_names
        assert "example-calculator" in skill_names

    def test_skill_metadata_loaded(
        self, skill_config_file, monkeypatch
    ):
        """Test that skill metadata is correctly loaded."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)

        greeting = loader.get("example-greeting")
        assert greeting.name == "example-greeting"
        assert "greeting users" in greeting.description.lower()

        summarizer = loader.get("example-summarizer")
        assert summarizer.name == "example-summarizer"
        assert "summarizing" in summarizer.description.lower()

        calculator = loader.get("example-calculator")
        assert calculator.name == "example-calculator"
        assert "mathematical" in calculator.description.lower()

    def test_skill_instructions_contain_output_format(
        self, skill_config_file, monkeypatch
    ):
        """Test that skill instructions contain output format."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.core.loader import SkillLoader
        from skillforge.core.config import load_config

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)

        for skill_name in ["example-greeting", "example-summarizer", "example-calculator"]:
            skill = loader.get(skill_name)
            assert "Output Format" in skill.instructions, (
                f"Skill {skill_name} should have Output Format section"
            )
