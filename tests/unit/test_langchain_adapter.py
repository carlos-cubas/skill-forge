"""
Unit tests for the LangChain adapter.

These tests verify the SkillForge LangChain adapter correctly:
- Provides create_agent function with skill support
- Injects meta-skill into system prompt (progressive mode)
- Injects full skill content (inject mode)
- Preserves original system prompt
- Auto-adds shell tool when needed
- Handles missing skills appropriately
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "skills"


class MockLangChainAgent:
    """Mock LangChain agent for testing without LangChain dependency."""

    def __init__(self, model, tools, system_prompt, **kwargs):
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt
        self.kwargs = kwargs

    def invoke(self, input_dict):
        """Mock invoke method."""
        return {"messages": [("assistant", "Mock response")]}


class MockShellTool:
    """Mock shell tool for testing."""

    name = "shell"

    def __init__(self):
        pass


@pytest.fixture
def mock_langchain(monkeypatch):
    """Mock langchain module for testing."""
    # Create mock langchain.agents module
    mock_agents = MagicMock()
    mock_agents.create_agent = MockLangChainAgent

    # Create mock langchain module
    mock_langchain_module = MagicMock()
    mock_langchain_module.agents = mock_agents
    mock_langchain_module.agents.create_agent = MockLangChainAgent

    # Create mock langchain_community module
    mock_community = MagicMock()
    mock_community.tools = MagicMock()
    mock_community.tools.ShellTool = MockShellTool

    # Insert mocks into sys.modules
    monkeypatch.setitem(sys.modules, "langchain", mock_langchain_module)
    monkeypatch.setitem(sys.modules, "langchain.agents", mock_agents)
    monkeypatch.setitem(sys.modules, "langchain_community", mock_community)
    monkeypatch.setitem(sys.modules, "langchain_community.tools", mock_community.tools)

    # Clear any cached imports of our adapter
    for mod_name in list(sys.modules.keys()):
        if "skillforge.adapters.langchain" in mod_name or "skillforge.langchain" in mod_name:
            del sys.modules[mod_name]

    return mock_langchain_module


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


@pytest.fixture
def mock_llm():
    """Create a mock LLM instance."""
    llm = MagicMock()
    llm.name = "mock-llm"
    return llm


class TestCreateAgentWithoutSkills:
    """Tests for create_agent without skills."""

    def test_create_agent_without_skills(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test creating an agent without any skills."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="You are a helpful assistant.",
        )

        assert isinstance(agent, MockLangChainAgent)
        assert agent.model == mock_llm
        assert agent.system_prompt == "You are a helpful assistant."

    def test_create_agent_without_skills_empty_prompt(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test creating an agent without skills and empty system prompt."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
        )

        assert agent.system_prompt == ""


class TestCreateAgentWithSkillsProgressive:
    """Tests for create_agent with skills in progressive mode."""

    def test_create_agent_with_skills_progressive(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test creating agent with skills in progressive (default) mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="You are an executive coach.",
            skills=["rapid-interviewing"],
        )

        # System prompt should contain meta-skill content
        assert "Using SkillForge Skills" in agent.system_prompt
        assert "rapid-interviewing" in agent.system_prompt
        assert "skillforge read" in agent.system_prompt

        # Original system prompt should be preserved
        assert "You are an executive coach." in agent.system_prompt

    def test_create_agent_with_multiple_skills_progressive(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test creating agent with multiple skills in progressive mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="You are a data analyst.",
            skills=["rapid-interviewing", "data-analysis"],
        )

        assert "rapid-interviewing" in agent.system_prompt
        assert "data-analysis" in agent.system_prompt


class TestCreateAgentWithSkillsInjectMode:
    """Tests for create_agent with skills in inject mode."""

    def test_create_agent_with_skills_inject_mode(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test creating agent with skills in inject mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="You are an executive coach.",
            skills=["rapid-interviewing"],
            skill_mode="inject",
        )

        # System prompt should contain full skill content
        assert "## Available Skills" in agent.system_prompt
        assert "### rapid-interviewing" in agent.system_prompt
        # Should contain skill instructions
        assert "Rapid Interviewing Skill" in agent.system_prompt

        # Original system prompt should be preserved
        assert "You are an executive coach." in agent.system_prompt

    def test_inject_mode_includes_full_instructions(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that inject mode includes full skill instructions."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="",
            skills=["rapid-interviewing"],
            skill_mode="inject",
        )

        # Should include instructions from SKILL.md
        assert "When to Use" in agent.system_prompt
        assert "How to Use" in agent.system_prompt
        assert "Example Questions" in agent.system_prompt


class TestSystemPromptPreserved:
    """Tests for system prompt preservation."""

    def test_system_prompt_preserved_progressive(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that original system prompt is preserved in progressive mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        original_prompt = "I am an expert with 20 years of experience in executive coaching."

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt=original_prompt,
            skills=["rapid-interviewing"],
            skill_mode="progressive",
        )

        # Original prompt should appear first
        assert agent.system_prompt.startswith(original_prompt)

    def test_system_prompt_preserved_inject(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that original system prompt is preserved in inject mode."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        original_prompt = "I am an expert with 20 years of experience."

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt=original_prompt,
            skills=["rapid-interviewing"],
            skill_mode="inject",
        )

        # Original prompt should appear first
        assert agent.system_prompt.startswith(original_prompt)

    def test_empty_system_prompt_with_skills(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test skills work when system prompt is empty."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="",
            skills=["rapid-interviewing"],
            skill_mode="progressive",
        )

        # Should still have meta-skill content
        assert "Using SkillForge Skills" in agent.system_prompt


class TestShellToolAutoAdded:
    """Tests for automatic shell tool addition."""

    def test_shell_tool_auto_added(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that shell tool is automatically added if missing."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="You are a helpful assistant.",
        )

        # Should have shell tool added
        tool_names = [getattr(t, "name", "") for t in agent.tools]
        assert "shell" in tool_names

    def test_shell_tool_not_duplicated(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that shell tool is not added if already present."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        existing_shell = MagicMock()
        existing_shell.name = "bash"

        agent = create_agent(
            llm=mock_llm,
            tools=[existing_shell],
            system_prompt="You are a helpful assistant.",
        )

        # Should only have the original tool (no shell added)
        assert len(agent.tools) == 1
        assert agent.tools[0] == existing_shell

    def test_various_shell_tool_names_recognized(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that various shell tool name variants are recognized."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        for tool_name in ["shell", "bash", "subprocess", "terminal", "Shell_Command"]:
            existing_tool = MagicMock()
            existing_tool.name = tool_name

            agent = create_agent(
                llm=mock_llm,
                tools=[existing_tool],
                system_prompt="Test",
            )

            # Should not add another shell tool
            assert len(agent.tools) == 1


class TestMissingSkillError:
    """Tests for handling missing skills."""

    def test_missing_skill_raises_error(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that requesting a non-existent skill raises an error."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent
        from skillforge.core.loader import SkillNotFoundError

        with pytest.raises(SkillNotFoundError, match="nonexistent-skill"):
            create_agent(
                llm=mock_llm,
                tools=[],
                system_prompt="Test",
                skills=["nonexistent-skill"],
            )


class TestInvalidSkillMode:
    """Tests for invalid skill mode handling."""

    def test_invalid_skill_mode_raises_error(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that invalid skill_mode raises ValueError."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        with pytest.raises(ValueError, match="Invalid skill_mode"):
            create_agent(
                llm=mock_llm,
                tools=[],
                skill_mode="invalid",
            )


class TestConvenienceImport:
    """Tests for the convenience import module."""

    def test_convenience_import_create_agent(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test importing create_agent from skillforge.langchain."""
        monkeypatch.chdir(skill_config_file)

        # Clear cached imports
        for mod_name in list(sys.modules.keys()):
            if "skillforge.langchain" in mod_name:
                del sys.modules[mod_name]

        from skillforge.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="Test",
        )

        assert isinstance(agent, MockLangChainAgent)


class TestKwargsPassThrough:
    """Tests for kwargs pass-through to LangChain's create_agent."""

    def test_kwargs_passed_to_langchain(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that additional kwargs are passed to LangChain's create_agent."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="Test",
            verbose=True,  # Custom kwarg
            custom_param="value",  # Custom kwarg
        )

        # These should be passed to the underlying create_agent
        assert agent.kwargs.get("verbose") is True
        assert agent.kwargs.get("custom_param") == "value"


class TestConfigurationLoading:
    """Tests for configuration loading behavior."""

    def test_loads_config_from_skillforge_yaml(
        self, mock_langchain, skill_config_file, mock_llm, monkeypatch
    ):
        """Test that configuration is loaded from .skillforge.yaml."""
        monkeypatch.chdir(skill_config_file)

        from skillforge.adapters.langchain import create_agent

        # This should work because the config file points to fixtures
        agent = create_agent(
            llm=mock_llm,
            tools=[],
            system_prompt="Test",
            skills=["rapid-interviewing"],
        )

        # Should have loaded the skill from fixtures
        assert "rapid-interviewing" in agent.system_prompt
