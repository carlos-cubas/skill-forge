"""
Unit tests for the CrewAI adapter.

These tests verify the SkillForge CrewAI adapter correctly:
- Provides drop-in replacement for crewai.Agent
- Injects meta-skill into backstory (progressive mode)
- Injects full skill content (inject mode)
- Preserves original backstory
- Handles missing skills appropriately
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "skills"


class MockCrewAIAgent:
    """Mock CrewAI Agent for testing without crewai dependency."""

    def __init__(self, *args, role=None, goal=None, backstory=None, **kwargs):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.args = args
        self.kwargs = kwargs


@pytest.fixture
def mock_crewai(monkeypatch):
    """Mock crewai module for testing."""
    # Create mock crewai module
    mock_module = MagicMock()
    mock_module.Agent = MockCrewAIAgent

    # Insert mock into sys.modules before importing adapter
    monkeypatch.setitem(sys.modules, "crewai", mock_module)

    # Clear any cached imports of our adapter
    for mod_name in list(sys.modules.keys()):
        if "skillforge.adapters.crewai" in mod_name or "skillforge.crewai" in mod_name:
            del sys.modules[mod_name]

    return mock_module


@pytest.fixture
def skill_config_file(tmp_path):
    """Create a temporary .skillforge.yaml config file."""
    config_content = f"""
skill_paths:
  - {FIXTURES_DIR}/*
"""
    config_file = tmp_path / ".skillforge.yaml"
    config_file.write_text(config_content)
    return tmp_path


class TestAgentWithoutSkills:
    """Tests for Agent creation without skills."""

    def test_agent_without_skills(self, mock_crewai, skill_config_file, monkeypatch):
        """Test creating an agent without any skills."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Test Role",
            goal="Test Goal",
            backstory="Test backstory",
        )

        assert agent.role == "Test Role"
        assert agent.goal == "Test Goal"
        assert agent.backstory == "Test backstory"
        assert agent.skills == []
        assert agent.skill_mode == "progressive"

    def test_agent_without_skills_empty_backstory(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test creating an agent without skills and no backstory."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Test Role",
            goal="Test Goal",
        )

        assert agent.role == "Test Role"
        assert agent.backstory is None  # CrewAI default


class TestAgentWithSkillsProgressive:
    """Tests for Agent with skills in progressive mode."""

    def test_agent_with_skills_progressive(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test creating agent with skills in progressive (default) mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Executive Coach",
            goal="Conduct discovery interviews",
            backstory="Expert coach",
            skills=["rapid-interviewing"],
        )

        assert agent.skills == ["rapid-interviewing"]
        assert agent.skill_mode == "progressive"

        # Backstory should contain meta-skill content
        assert "Using SkillForge Skills" in agent.backstory
        assert "rapid-interviewing" in agent.backstory
        assert "skillforge read" in agent.backstory

        # Original backstory should be preserved
        assert "Expert coach" in agent.backstory

    def test_agent_with_multiple_skills_progressive(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test creating agent with multiple skills in progressive mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Analyst",
            goal="Analyze data",
            backstory="Data expert",
            skills=["rapid-interviewing", "data-analysis"],
        )

        assert len(agent.skills) == 2
        assert "rapid-interviewing" in agent.backstory
        assert "data-analysis" in agent.backstory


class TestAgentWithSkillsInjectMode:
    """Tests for Agent with skills in inject mode."""

    def test_agent_with_skills_inject_mode(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test creating agent with skills in inject mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Executive Coach",
            goal="Conduct discovery interviews",
            backstory="Expert coach",
            skills=["rapid-interviewing"],
            skill_mode="inject",
        )

        assert agent.skills == ["rapid-interviewing"]
        assert agent.skill_mode == "inject"

        # Backstory should contain full skill content
        assert "## Available Skills" in agent.backstory
        assert "### rapid-interviewing" in agent.backstory
        # Should contain skill instructions
        assert "Rapid Interviewing Skill" in agent.backstory

        # Original backstory should be preserved
        assert "Expert coach" in agent.backstory

    def test_inject_mode_includes_full_instructions(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that inject mode includes full skill instructions."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Coach",
            goal="Interview",
            backstory="",
            skills=["rapid-interviewing"],
            skill_mode="inject",
        )

        # Should include instructions from SKILL.md
        assert "When to Use" in agent.backstory
        assert "How to Use" in agent.backstory
        assert "Example Questions" in agent.backstory


class TestBackstoryPreserved:
    """Tests for backstory preservation."""

    def test_backstory_preserved_progressive(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that original backstory is preserved in progressive mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        original_backstory = "I am an expert with 20 years of experience in executive coaching."

        agent = Agent(
            role="Coach",
            goal="Coach executives",
            backstory=original_backstory,
            skills=["rapid-interviewing"],
            skill_mode="progressive",
        )

        # Original backstory should appear first
        assert agent.backstory.startswith(original_backstory)

    def test_backstory_preserved_inject(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that original backstory is preserved in inject mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        original_backstory = "I am an expert with 20 years of experience."

        agent = Agent(
            role="Coach",
            goal="Coach executives",
            backstory=original_backstory,
            skills=["rapid-interviewing"],
            skill_mode="inject",
        )

        # Original backstory should appear first
        assert agent.backstory.startswith(original_backstory)

    def test_empty_backstory_with_skills(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test skills work when backstory is empty."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        agent = Agent(
            role="Coach",
            goal="Coach executives",
            backstory="",
            skills=["rapid-interviewing"],
            skill_mode="progressive",
        )

        # Should still have meta-skill content
        assert "Using SkillForge Skills" in agent.backstory


class TestAgentFromConfig:
    """Tests for agent_from_config helper function."""

    def test_agent_from_config(self, mock_crewai, skill_config_file, monkeypatch):
        """Test creating agent from config dictionary."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import agent_from_config

        config = {
            "role": "Executive Coach",
            "goal": "Conduct discovery interviews",
            "backstory": "Expert coach with decades of experience",
            "skills": ["rapid-interviewing"],
        }

        agent = agent_from_config(config)

        assert agent.role == "Executive Coach"
        assert agent.goal == "Conduct discovery interviews"
        assert agent.skills == ["rapid-interviewing"]
        assert "rapid-interviewing" in agent.backstory

    def test_agent_from_config_with_overrides(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test agent_from_config with overrides."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import agent_from_config

        config = {
            "role": "Executive Coach",
            "goal": "Conduct discovery interviews",
            "backstory": "Expert coach",
            "skills": ["rapid-interviewing"],
        }

        agent = agent_from_config(config, skill_mode="inject")

        assert agent.skill_mode == "inject"

    def test_agent_from_config_minimal(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test agent_from_config with minimal config."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import agent_from_config

        config = {
            "role": "Coach",
            "goal": "Coach people",
        }

        agent = agent_from_config(config)

        assert agent.role == "Coach"
        assert agent.goal == "Coach people"
        assert agent.skills == []


class TestMissingSkillError:
    """Tests for handling missing skills."""

    def test_missing_skill_raises_error(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that requesting a non-existent skill raises an error."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent
        from skillforge.core.loader import SkillNotFoundError

        with pytest.raises(SkillNotFoundError, match="nonexistent-skill"):
            Agent(
                role="Coach",
                goal="Coach people",
                backstory="Expert",
                skills=["nonexistent-skill"],
            )


class TestInvalidSkillMode:
    """Tests for invalid skill mode handling."""

    def test_invalid_skill_mode_raises_error(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that invalid skill_mode raises ValueError."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        with pytest.raises(ValueError, match="Invalid skill_mode"):
            Agent(
                role="Coach",
                goal="Coach people",
                skill_mode="invalid",
            )


class TestConvenienceImport:
    """Tests for the convenience import module."""

    def test_convenience_import_agent(self, mock_crewai, skill_config_file, monkeypatch):
        """Test importing Agent from skillforge.crewai."""
        monkeypatch.chdir(skill_config_file)

        # Clear cached imports
        for mod_name in list(sys.modules.keys()):
            if "skillforge.crewai" in mod_name:
                del sys.modules[mod_name]

        from skillforge.crewai import Agent

        agent = Agent(
            role="Test",
            goal="Test",
            backstory="Test",
        )

        assert agent.role == "Test"

    def test_convenience_import_agent_from_config(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test importing agent_from_config from skillforge.crewai."""
        monkeypatch.chdir(skill_config_file)

        # Clear cached imports
        for mod_name in list(sys.modules.keys()):
            if "skillforge.crewai" in mod_name:
                del sys.modules[mod_name]

        from skillforge.crewai import agent_from_config

        config = {"role": "Test", "goal": "Test"}
        agent = agent_from_config(config)

        assert agent.role == "Test"


class TestDropInCompatibility:
    """Tests verifying drop-in replacement compatibility."""

    def test_is_subclass_of_crewai_agent(self, mock_crewai, monkeypatch):
        """Test that skillforge Agent is subclass of crewai Agent."""
        from skillforge.adapters.crewai import Agent

        assert issubclass(Agent, MockCrewAIAgent)

    def test_passes_args_to_parent(
        self, mock_crewai, skill_config_file, monkeypatch
    ):
        """Test that all args/kwargs are passed to parent Agent."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.crewai import Agent

        # Any additional kwargs should be passed through
        agent = Agent(
            role="Coach",
            goal="Coach people",
            backstory="Expert",
            verbose=True,  # CrewAI specific kwarg
            allow_delegation=False,  # CrewAI specific kwarg
        )

        # These should be passed to parent
        assert agent.kwargs.get("verbose") is True
        assert agent.kwargs.get("allow_delegation") is False
