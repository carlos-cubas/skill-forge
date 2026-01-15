"""
Unit tests for the ElevenLabs Python API.

Tests cover:
- Agent.create() creates new agent with skills
- Agent(agent_id).configure() updates existing agent
- sync_skills() uploads skills to KB
- API mirrors CLI functionality
- Clear error messages for unsynced skills
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skillforge.elevenlabs import Agent, sync_skills, AgentError, SkillNotSyncedError, SyncError
from skillforge.adapters.elevenlabs.manifest import ElevenLabsManifest
from skillforge.core.skill import Skill


class TestAgentCreate:
    """Tests for Agent.create() class method."""

    @patch("skillforge.elevenlabs.agent._create_agent")
    def test_agent_create(self, mock_create_agent: MagicMock) -> None:
        """Test that Agent.create() creates a new agent with skills."""
        mock_create_agent.return_value = "agent_new123"

        agent = Agent.create(
            name="Test Agent",
            system_prompt="You are a helpful assistant.",
            skills=["skill-a", "skill-b"],
            first_message="Hello there!",
        )

        assert agent.agent_id == "agent_new123"
        assert agent.name == "Test Agent"
        assert agent.skills == ["skill-a", "skill-b"]

        # Verify the underlying function was called correctly
        mock_create_agent.assert_called_once_with(
            name="Test Agent",
            core_prompt="You are a helpful assistant.",
            first_message="Hello there!",
            skills=["skill-a", "skill-b"],
            voice_id=None,
            language="en",
            llm="gpt-4o-mini",
        )

    @patch("skillforge.elevenlabs.agent._create_agent")
    def test_agent_create_all_options(self, mock_create_agent: MagicMock) -> None:
        """Test Agent.create() with all options specified."""
        mock_create_agent.return_value = "agent_full789"

        agent = Agent.create(
            name="Full Options Agent",
            system_prompt="You are an expert math tutor.",
            skills=["socratic-questioning"],
            first_message="Welcome to math tutoring!",
            voice_id="voice_abc",
            language="es",
            llm="gpt-4o",
        )

        assert agent.agent_id == "agent_full789"
        assert agent.name == "Full Options Agent"
        assert agent.skills == ["socratic-questioning"]

        mock_create_agent.assert_called_once_with(
            name="Full Options Agent",
            core_prompt="You are an expert math tutor.",
            first_message="Welcome to math tutoring!",
            skills=["socratic-questioning"],
            voice_id="voice_abc",
            language="es",
            llm="gpt-4o",
        )

    @patch("skillforge.elevenlabs.agent._create_agent")
    def test_agent_create_without_sync_raises(self, mock_create_agent: MagicMock) -> None:
        """Test that Agent.create() raises SkillNotSyncedError for unsynced skills."""
        mock_create_agent.side_effect = SkillNotSyncedError(
            "Skills not synced to ElevenLabs KB: unsynced-skill"
        )

        with pytest.raises(SkillNotSyncedError) as exc_info:
            Agent.create(
                name="Test Agent",
                system_prompt="Test prompt",
                skills=["unsynced-skill"],
            )

        assert "unsynced-skill" in str(exc_info.value)

    @patch("skillforge.elevenlabs.agent._create_agent")
    def test_agent_create_error(self, mock_create_agent: MagicMock) -> None:
        """Test that Agent.create() propagates AgentError."""
        mock_create_agent.side_effect = AgentError("Failed to create agent")

        with pytest.raises(AgentError) as exc_info:
            Agent.create(
                name="Test Agent",
                system_prompt="Test prompt",
                skills=["some-skill"],
            )

        assert "Failed to create agent" in str(exc_info.value)


class TestAgentConfigure:
    """Tests for Agent.configure() method."""

    @patch("skillforge.elevenlabs.agent._configure_agent")
    def test_agent_configure(self, mock_configure_agent: MagicMock) -> None:
        """Test that Agent.configure() updates existing agent with skills."""
        agent = Agent(agent_id="agent_existing")

        agent.configure(skills=["new-skill-a", "new-skill-b"])

        mock_configure_agent.assert_called_once_with(
            agent_id="agent_existing",
            skills=["new-skill-a", "new-skill-b"],
            core_prompt=None,
            preserve_prompt=True,
        )

        # Check local state updated
        assert agent.skills == ["new-skill-a", "new-skill-b"]

    @patch("skillforge.elevenlabs.agent._configure_agent")
    def test_agent_configure_with_new_prompt(self, mock_configure_agent: MagicMock) -> None:
        """Test Agent.configure() with new system prompt."""
        agent = Agent(agent_id="agent_existing")

        agent.configure(
            skills=["skill-x"],
            system_prompt="New system prompt content.",
        )

        mock_configure_agent.assert_called_once_with(
            agent_id="agent_existing",
            skills=["skill-x"],
            core_prompt="New system prompt content.",
            preserve_prompt=False,
        )

    @patch("skillforge.elevenlabs.agent._configure_agent")
    def test_agent_configure_unsynced_skill_raises(self, mock_configure_agent: MagicMock) -> None:
        """Test that configure() raises SkillNotSyncedError for unsynced skills."""
        mock_configure_agent.side_effect = SkillNotSyncedError(
            "Skills not synced to ElevenLabs KB: missing-skill"
        )

        agent = Agent(agent_id="agent_123")

        with pytest.raises(SkillNotSyncedError) as exc_info:
            agent.configure(skills=["missing-skill"])

        assert "missing-skill" in str(exc_info.value)


class TestAgentGetDetails:
    """Tests for Agent.get_details() method."""

    @patch("skillforge.elevenlabs.agent.get_client")
    def test_agent_get_details(self, mock_get_client: MagicMock) -> None:
        """Test that get_details() retrieves agent information."""
        mock_client = MagicMock()
        mock_agent_data = MagicMock()
        mock_agent_data.name = "Retrieved Agent"
        mock_agent_data.conversation_config.agent.first_message = "Hello!"
        mock_agent_data.conversation_config.agent.language = "en"
        mock_agent_data.conversation_config.agent.prompt.prompt = "You are helpful."
        mock_agent_data.conversation_config.agent.prompt.llm = "gpt-4o-mini"
        mock_client.conversational_ai.agents.get.return_value = mock_agent_data
        mock_get_client.return_value = mock_client

        agent = Agent(agent_id="agent_details123")
        details = agent.get_details()

        assert details["agent_id"] == "agent_details123"
        assert details["name"] == "Retrieved Agent"
        assert "conversation_config" in details
        assert details["conversation_config"]["agent"]["first_message"] == "Hello!"
        assert details["conversation_config"]["agent"]["language"] == "en"

        # Check that local name was updated
        assert agent.name == "Retrieved Agent"

    @patch("skillforge.elevenlabs.agent.get_client")
    def test_agent_get_details_error(self, mock_get_client: MagicMock) -> None:
        """Test that get_details() raises AgentError on failure."""
        mock_client = MagicMock()
        mock_client.conversational_ai.agents.get.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        agent = Agent(agent_id="agent_error")

        with pytest.raises(AgentError) as exc_info:
            agent.get_details()

        assert "Failed to get agent details" in str(exc_info.value)


class TestSyncSkillsAll:
    """Tests for sync_skills() function - syncing all skills."""

    @patch("skillforge.elevenlabs.sync._sync_skills_to_kb")
    @patch("skillforge.elevenlabs.sync.ElevenLabsManifest")
    @patch("skillforge.elevenlabs.sync.SkillLoader")
    @patch("skillforge.elevenlabs.sync.load_config")
    def test_sync_skills_all(
        self,
        mock_load_config: MagicMock,
        mock_skill_loader: MagicMock,
        mock_manifest: MagicMock,
        mock_sync_to_kb: MagicMock,
    ) -> None:
        """Test syncing all discovered skills."""
        # Setup mocks
        mock_load_config.return_value = MagicMock(skill_paths=["./skills/*"])

        mock_skills = {
            "skill-1": MagicMock(spec=Skill),
            "skill-2": MagicMock(spec=Skill),
        }
        mock_loader_instance = MagicMock()
        mock_loader_instance.discover.return_value = mock_skills
        mock_skill_loader.return_value = mock_loader_instance

        mock_manifest_instance = MagicMock()
        mock_manifest.return_value = mock_manifest_instance

        mock_sync_to_kb.return_value = {
            "skill-1": "doc_1",
            "skill-2": "doc_2",
        }

        # Execute
        result = sync_skills()

        # Verify
        assert result == {"skill-1": "doc_1", "skill-2": "doc_2"}
        mock_sync_to_kb.assert_called_once_with(
            skills=mock_skills,
            manifest=mock_manifest_instance,
            force=False,
        )


class TestSyncSkillsSpecific:
    """Tests for sync_skills() function - syncing specific skills."""

    @patch("skillforge.elevenlabs.sync._sync_skills_to_kb")
    @patch("skillforge.elevenlabs.sync.ElevenLabsManifest")
    @patch("skillforge.elevenlabs.sync.SkillLoader")
    @patch("skillforge.elevenlabs.sync.load_config")
    def test_sync_skills_specific(
        self,
        mock_load_config: MagicMock,
        mock_skill_loader: MagicMock,
        mock_manifest: MagicMock,
        mock_sync_to_kb: MagicMock,
    ) -> None:
        """Test syncing specific skills by name."""
        # Setup mocks
        mock_load_config.return_value = MagicMock(skill_paths=["./skills/*"])

        mock_skill_1 = MagicMock(spec=Skill)
        mock_skill_2 = MagicMock(spec=Skill)
        mock_skill_3 = MagicMock(spec=Skill)
        mock_skills = {
            "skill-1": mock_skill_1,
            "skill-2": mock_skill_2,
            "skill-3": mock_skill_3,
        }
        mock_loader_instance = MagicMock()
        mock_loader_instance.discover.return_value = mock_skills
        mock_skill_loader.return_value = mock_loader_instance

        mock_manifest_instance = MagicMock()
        mock_manifest.return_value = mock_manifest_instance

        mock_sync_to_kb.return_value = {
            "skill-1": "doc_1",
        }

        # Execute - only sync skill-1
        result = sync_skills(skill_names=["skill-1"])

        # Verify only requested skill was synced
        assert result == {"skill-1": "doc_1"}
        mock_sync_to_kb.assert_called_once()

        call_args = mock_sync_to_kb.call_args
        synced_skills = call_args[1]["skills"]
        assert list(synced_skills.keys()) == ["skill-1"]

    @patch("skillforge.elevenlabs.sync.SkillLoader")
    @patch("skillforge.elevenlabs.sync.load_config")
    def test_sync_skills_missing_skill_raises(
        self,
        mock_load_config: MagicMock,
        mock_skill_loader: MagicMock,
    ) -> None:
        """Test that sync_skills() raises ValueError for missing skills."""
        mock_load_config.return_value = MagicMock(skill_paths=["./skills/*"])

        mock_skills = {"existing-skill": MagicMock(spec=Skill)}
        mock_loader_instance = MagicMock()
        mock_loader_instance.discover.return_value = mock_skills
        mock_skill_loader.return_value = mock_loader_instance

        with pytest.raises(ValueError) as exc_info:
            sync_skills(skill_names=["nonexistent-skill"])

        assert "Skills not found: nonexistent-skill" in str(exc_info.value)

    @patch("skillforge.elevenlabs.sync.SkillLoader")
    @patch("skillforge.elevenlabs.sync.load_config")
    def test_sync_skills_no_skills_found_raises(
        self,
        mock_load_config: MagicMock,
        mock_skill_loader: MagicMock,
    ) -> None:
        """Test that sync_skills() raises ValueError when no skills found."""
        mock_load_config.return_value = MagicMock(skill_paths=["./skills/*"])

        mock_loader_instance = MagicMock()
        mock_loader_instance.discover.return_value = {}  # No skills
        mock_skill_loader.return_value = mock_loader_instance

        with pytest.raises(ValueError) as exc_info:
            sync_skills()

        assert "No skills found" in str(exc_info.value)


class TestSyncSkillsForce:
    """Tests for sync_skills() with force flag."""

    @patch("skillforge.elevenlabs.sync._sync_skills_to_kb")
    @patch("skillforge.elevenlabs.sync.ElevenLabsManifest")
    @patch("skillforge.elevenlabs.sync.SkillLoader")
    @patch("skillforge.elevenlabs.sync.load_config")
    def test_sync_skills_force(
        self,
        mock_load_config: MagicMock,
        mock_skill_loader: MagicMock,
        mock_manifest: MagicMock,
        mock_sync_to_kb: MagicMock,
    ) -> None:
        """Test force re-sync of skills."""
        mock_load_config.return_value = MagicMock(skill_paths=["./skills/*"])

        mock_skills = {"skill-1": MagicMock(spec=Skill)}
        mock_loader_instance = MagicMock()
        mock_loader_instance.discover.return_value = mock_skills
        mock_skill_loader.return_value = mock_loader_instance

        mock_manifest_instance = MagicMock()
        mock_manifest.return_value = mock_manifest_instance

        mock_sync_to_kb.return_value = {"skill-1": "doc_new"}

        result = sync_skills(force=True)

        assert result == {"skill-1": "doc_new"}
        mock_sync_to_kb.assert_called_once_with(
            skills=mock_skills,
            manifest=mock_manifest_instance,
            force=True,
        )


class TestModuleImports:
    """Tests for module imports and exports."""

    def test_agent_import(self) -> None:
        """Test that Agent can be imported from skillforge.elevenlabs."""
        from skillforge.elevenlabs import Agent
        assert Agent is not None

    def test_sync_skills_import(self) -> None:
        """Test that sync_skills can be imported from skillforge.elevenlabs."""
        from skillforge.elevenlabs import sync_skills
        assert sync_skills is not None

    def test_exceptions_import(self) -> None:
        """Test that exceptions can be imported."""
        from skillforge.elevenlabs import AgentError, SkillNotSyncedError, SyncError
        assert AgentError is not None
        assert SkillNotSyncedError is not None
        assert SyncError is not None

    def test_all_exports(self) -> None:
        """Test that __all__ contains expected exports."""
        from skillforge import elevenlabs
        expected = ["Agent", "AgentError", "SkillNotSyncedError", "sync_skills", "SyncError"]
        for name in expected:
            assert name in elevenlabs.__all__


class TestAgentDataclass:
    """Tests for Agent dataclass functionality."""

    def test_agent_init_minimal(self) -> None:
        """Test Agent initialization with just agent_id."""
        agent = Agent(agent_id="test123")

        assert agent.agent_id == "test123"
        assert agent.name is None
        assert agent.skills == []

    def test_agent_init_full(self) -> None:
        """Test Agent initialization with all fields."""
        agent = Agent(
            agent_id="test456",
            name="Test Agent",
            skills=["skill-a", "skill-b"],
        )

        assert agent.agent_id == "test456"
        assert agent.name == "Test Agent"
        assert agent.skills == ["skill-a", "skill-b"]

    def test_agent_skills_is_list(self) -> None:
        """Test that skills default to empty list, not shared mutable."""
        agent1 = Agent(agent_id="a1")
        agent2 = Agent(agent_id="a2")

        agent1.skills.append("skill-x")

        assert agent1.skills == ["skill-x"]
        assert agent2.skills == []  # Should not be affected
