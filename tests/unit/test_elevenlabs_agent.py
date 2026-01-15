"""
Unit tests for ElevenLabs agent creation and configuration.

Tests cover:
- Agent creation with skills
- Agent configuration for existing agents
- Prompt building (core + meta-skill + skill directory)
- KB reference generation
- Error handling for unsynced skills
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skillforge.adapters.elevenlabs.agent import (
    AgentError,
    SkillNotSyncedError,
    build_prompt,
    configure_agent,
    create_agent,
    get_kb_references,
)
from skillforge.adapters.elevenlabs.manifest import ElevenLabsManifest
from skillforge.core.skill import Skill


class TestBuildPrompt:
    """Tests for build_prompt function."""

    def test_build_prompt_combines_correctly(self, tmp_path: Path) -> None:
        """Test that build_prompt combines core + meta-skill + skill directory."""
        # Set up manifest with synced skills
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("socratic-questioning", "doc_123")
        manifest.set_document_id("adaptive-scaffolding", "doc_456")
        manifest.save()

        # Create test skills directory
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()

        # Create skill directories with SKILL.md
        skill1_dir = skills_dir / "socratic-questioning"
        skill1_dir.mkdir()
        (skill1_dir / "SKILL.md").write_text("""---
name: socratic-questioning
description: Guide discovery through questioning
---

# Socratic Questioning
Ask probing questions.
""")

        skill2_dir = skills_dir / "adaptive-scaffolding"
        skill2_dir.mkdir()
        (skill2_dir / "SKILL.md").write_text("""---
name: adaptive-scaffolding
description: Adapt teaching to student level
---

# Adaptive Scaffolding
Adjust complexity.
""")

        # Create .skillforge.yaml
        config_file = tmp_path / ".skillforge.yaml"
        config_file.write_text(f"""
skill_paths:
  - {skills_dir}/*
""")

        with patch("skillforge.adapters.elevenlabs.agent.load_config") as mock_config:
            mock_config.return_value = MagicMock(skill_paths=[str(skills_dir / "*")])

            with patch("skillforge.adapters.elevenlabs.agent.SkillLoader") as MockLoader:
                # Create mock skills
                mock_skills = {
                    "socratic-questioning": Skill(
                        name="socratic-questioning",
                        description="Guide discovery through questioning",
                        instructions="Ask probing questions.",
                        path=skill1_dir,
                    ),
                    "adaptive-scaffolding": Skill(
                        name="adaptive-scaffolding",
                        description="Adapt teaching to student level",
                        instructions="Adjust complexity.",
                        path=skill2_dir,
                    ),
                }
                mock_loader = MagicMock()
                mock_loader.discover.return_value = mock_skills
                MockLoader.return_value = mock_loader

                core_prompt = "You are a math tutor. Be helpful and patient."

                prompt = build_prompt(
                    core_prompt=core_prompt,
                    skill_names=["socratic-questioning", "adaptive-scaffolding"],
                    manifest=manifest,
                )

        # Verify core prompt is included
        assert "You are a math tutor" in prompt
        assert "Be helpful and patient" in prompt

        # Verify meta-skill content is included (after separator)
        assert "---" in prompt
        assert "Using Skills" in prompt or "Available Skills" in prompt

        # Verify skill directory is included
        assert "socratic-questioning" in prompt
        assert "adaptive-scaffolding" in prompt
        assert 'SKILL: socratic-questioning' in prompt

    def test_build_prompt_with_no_local_skills(self, tmp_path: Path) -> None:
        """Test build_prompt when skills are synced but not found locally."""
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("remote-skill", "doc_789")
        manifest.save()

        with patch("skillforge.adapters.elevenlabs.agent.load_config") as mock_config:
            mock_config.return_value = MagicMock(skill_paths=["./skills/*"])

            with patch("skillforge.adapters.elevenlabs.agent.SkillLoader") as MockLoader:
                mock_loader = MagicMock()
                mock_loader.discover.return_value = {}  # No local skills
                MockLoader.return_value = mock_loader

                prompt = build_prompt(
                    core_prompt="You are an assistant.",
                    skill_names=["remote-skill"],
                    manifest=manifest,
                )

        # Should still include the skill in directory (with placeholder description)
        assert "remote-skill" in prompt
        assert "(synced to ElevenLabs KB)" in prompt


class TestGetKbReferences:
    """Tests for get_kb_references function."""

    def test_get_kb_references_from_manifest(self, tmp_path: Path) -> None:
        """Test that get_kb_references returns correct KB reference dicts."""
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("skill-a", "doc_aaa111")
        manifest.set_document_id("skill-b", "doc_bbb222")
        manifest.save()

        refs = get_kb_references(
            skill_names=["skill-a", "skill-b"],
            manifest=manifest,
        )

        assert len(refs) == 2

        # Check first reference
        ref_a = next(r for r in refs if "skill-a" in r["name"])
        assert ref_a["type"] == "text"
        assert ref_a["name"] == "SKILL: skill-a"
        assert ref_a["id"] == "doc_aaa111"
        assert ref_a["usage_mode"] == "auto"

        # Check second reference
        ref_b = next(r for r in refs if "skill-b" in r["name"])
        assert ref_b["type"] == "text"
        assert ref_b["name"] == "SKILL: skill-b"
        assert ref_b["id"] == "doc_bbb222"
        assert ref_b["usage_mode"] == "auto"

    def test_error_on_unsynced_skill(self, tmp_path: Path) -> None:
        """Test that get_kb_references raises SkillNotSyncedError for unsynced skills."""
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("synced-skill", "doc_123")
        manifest.save()

        with pytest.raises(SkillNotSyncedError) as exc_info:
            get_kb_references(
                skill_names=["synced-skill", "unsynced-skill"],
                manifest=manifest,
            )

        assert "unsynced-skill" in str(exc_info.value)
        assert "not synced" in str(exc_info.value).lower()

    def test_error_on_all_unsynced_skills(self, tmp_path: Path) -> None:
        """Test error when no skills are synced."""
        manifest = ElevenLabsManifest(project_root=tmp_path)

        with pytest.raises(SkillNotSyncedError) as exc_info:
            get_kb_references(
                skill_names=["missing-1", "missing-2"],
                manifest=manifest,
            )

        assert "missing-1" in str(exc_info.value)
        assert "missing-2" in str(exc_info.value)


class TestCreateAgent:
    """Tests for create_agent function."""

    @patch("skillforge.adapters.elevenlabs.agent.get_client")
    @patch("skillforge.adapters.elevenlabs.agent.build_prompt")
    @patch("skillforge.adapters.elevenlabs.agent.get_kb_references")
    def test_create_agent(
        self,
        mock_get_kb_refs: MagicMock,
        mock_build_prompt: MagicMock,
        mock_get_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test basic agent creation."""
        # Set up mocks
        mock_build_prompt.return_value = "Combined prompt content"
        mock_get_kb_refs.return_value = [
            {"type": "text", "name": "SKILL: test-skill", "id": "doc_123", "usage_mode": "auto"}
        ]

        mock_client = MagicMock()
        mock_agent = MagicMock()
        mock_agent.agent_id = "agent_abc123"
        mock_client.conversational_ai.agents.create.return_value = mock_agent
        mock_get_client.return_value = mock_client

        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("test-skill", "doc_123")
        manifest.save()

        # Create agent
        agent_id = create_agent(
            name="Test Agent",
            core_prompt="You are a test agent.",
            first_message="Hello!",
            skills=["test-skill"],
            manifest=manifest,
        )

        assert agent_id == "agent_abc123"
        mock_client.conversational_ai.agents.create.assert_called_once()

        # Verify the call arguments
        call_kwargs = mock_client.conversational_ai.agents.create.call_args[1]
        assert call_kwargs["name"] == "Test Agent"
        assert "conversation_config" in call_kwargs

        conv_config = call_kwargs["conversation_config"]
        assert conv_config["agent"]["first_message"] == "Hello!"
        assert conv_config["agent"]["language"] == "en"
        assert "knowledge_base" in conv_config["agent"]["prompt"]

    @patch("skillforge.adapters.elevenlabs.agent.get_client")
    @patch("skillforge.adapters.elevenlabs.agent.build_prompt")
    @patch("skillforge.adapters.elevenlabs.agent.get_kb_references")
    def test_create_agent_all_options(
        self,
        mock_get_kb_refs: MagicMock,
        mock_build_prompt: MagicMock,
        mock_get_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test agent creation with all options specified."""
        mock_build_prompt.return_value = "Combined prompt"
        mock_get_kb_refs.return_value = [
            {"type": "text", "name": "SKILL: skill-1", "id": "doc_1", "usage_mode": "auto"},
            {"type": "text", "name": "SKILL: skill-2", "id": "doc_2", "usage_mode": "auto"},
        ]

        mock_client = MagicMock()
        mock_agent = MagicMock()
        mock_agent.agent_id = "agent_xyz789"
        mock_client.conversational_ai.agents.create.return_value = mock_agent
        mock_get_client.return_value = mock_client

        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("skill-1", "doc_1")
        manifest.set_document_id("skill-2", "doc_2")
        manifest.save()

        agent_id = create_agent(
            name="Full Options Agent",
            core_prompt="You are an expert tutor.",
            first_message="Welcome! How can I help?",
            skills=["skill-1", "skill-2"],
            voice_id="voice_123abc",
            language="es",
            llm="gpt-4o",
            manifest=manifest,
        )

        assert agent_id == "agent_xyz789"

        call_kwargs = mock_client.conversational_ai.agents.create.call_args[1]
        conv_config = call_kwargs["conversation_config"]

        # Verify all options
        assert conv_config["agent"]["language"] == "es"
        assert conv_config["agent"]["prompt"]["llm"] == "gpt-4o"
        assert conv_config["tts"]["voice_id"] == "voice_123abc"
        assert len(conv_config["agent"]["prompt"]["knowledge_base"]) == 2

    def test_create_agent_unsynced_skill_error(self, tmp_path: Path) -> None:
        """Test that create_agent raises error for unsynced skills."""
        manifest = ElevenLabsManifest(project_root=tmp_path)
        # No skills synced

        with pytest.raises(SkillNotSyncedError) as exc_info:
            create_agent(
                name="Test Agent",
                core_prompt="Test prompt",
                first_message="Hello",
                skills=["unsynced-skill"],
                manifest=manifest,
            )

        assert "unsynced-skill" in str(exc_info.value)


class TestConfigureAgent:
    """Tests for configure_agent function."""

    @patch("skillforge.adapters.elevenlabs.agent.get_client")
    @patch("skillforge.adapters.elevenlabs.agent.build_prompt")
    @patch("skillforge.adapters.elevenlabs.agent.get_kb_references")
    def test_configure_existing_agent(
        self,
        mock_get_kb_refs: MagicMock,
        mock_build_prompt: MagicMock,
        mock_get_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test configuring an existing agent with skills."""
        mock_build_prompt.return_value = "New combined prompt"
        mock_get_kb_refs.return_value = [
            {"type": "text", "name": "SKILL: new-skill", "id": "doc_new", "usage_mode": "auto"}
        ]

        mock_client = MagicMock()
        mock_existing_agent = MagicMock()
        mock_existing_agent.conversation_config.agent.first_message = "Old hello"
        mock_existing_agent.conversation_config.agent.language = "en"
        mock_existing_agent.conversation_config.agent.prompt.prompt = "Old prompt"
        mock_existing_agent.conversation_config.agent.prompt.llm = "gpt-4o-mini"
        mock_client.conversational_ai.agents.get.return_value = mock_existing_agent
        mock_client.conversational_ai.agents.update.return_value = MagicMock()
        mock_get_client.return_value = mock_client

        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("new-skill", "doc_new")
        manifest.save()

        configure_agent(
            agent_id="agent_existing",
            skills=["new-skill"],
            core_prompt="New core prompt",
            manifest=manifest,
        )

        # Verify update was called
        mock_client.conversational_ai.agents.update.assert_called_once()
        call_kwargs = mock_client.conversational_ai.agents.update.call_args[1]
        assert call_kwargs["agent_id"] == "agent_existing"
        assert "conversation_config" in call_kwargs

    @patch("skillforge.adapters.elevenlabs.agent.get_client")
    @patch("skillforge.adapters.elevenlabs.agent.build_prompt")
    @patch("skillforge.adapters.elevenlabs.agent.get_kb_references")
    def test_configure_preserves_existing_prompt(
        self,
        mock_get_kb_refs: MagicMock,
        mock_build_prompt: MagicMock,
        mock_get_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that configure_agent preserves existing core prompt when not specified."""
        mock_get_kb_refs.return_value = [
            {"type": "text", "name": "SKILL: skill", "id": "doc_1", "usage_mode": "auto"}
        ]

        # Set up existing agent with a prompt that has a separator
        existing_prompt = "Original core prompt content.\n\n---\n\nOld meta-skill content"

        mock_client = MagicMock()
        mock_existing_agent = MagicMock()
        mock_existing_agent.conversation_config.agent.first_message = "Hello"
        mock_existing_agent.conversation_config.agent.language = "en"
        mock_existing_agent.conversation_config.agent.prompt.prompt = existing_prompt
        mock_existing_agent.conversation_config.agent.prompt.llm = "gpt-4o-mini"
        mock_client.conversational_ai.agents.get.return_value = mock_existing_agent
        mock_client.conversational_ai.agents.update.return_value = MagicMock()
        mock_get_client.return_value = mock_client

        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("skill", "doc_1")
        manifest.save()

        # Configure without providing new core_prompt
        configure_agent(
            agent_id="agent_preserve",
            skills=["skill"],
            core_prompt=None,  # Should preserve existing
            preserve_prompt=True,
            manifest=manifest,
        )

        # Verify build_prompt was called with the extracted core prompt
        mock_build_prompt.assert_called_once()
        call_args = mock_build_prompt.call_args
        extracted_core = call_args[1]["core_prompt"] if "core_prompt" in call_args[1] else call_args[0][0]
        assert extracted_core == "Original core prompt content."

    @patch("skillforge.adapters.elevenlabs.agent.get_client")
    def test_configure_agent_unsynced_skill_error(
        self,
        mock_get_client: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that configure_agent raises error for unsynced skills."""
        # Set up mock client
        mock_client = MagicMock()
        mock_existing_agent = MagicMock()
        mock_existing_agent.conversation_config.agent.first_message = "Hello"
        mock_existing_agent.conversation_config.agent.language = "en"
        mock_existing_agent.conversation_config.agent.prompt.prompt = "Old prompt"
        mock_existing_agent.conversation_config.agent.prompt.llm = "gpt-4o-mini"
        mock_client.conversational_ai.agents.get.return_value = mock_existing_agent
        mock_get_client.return_value = mock_client

        manifest = ElevenLabsManifest(project_root=tmp_path)

        with pytest.raises(SkillNotSyncedError):
            configure_agent(
                agent_id="agent_123",
                skills=["nonexistent-skill"],
                manifest=manifest,
            )


class TestCLICommands:
    """Tests for CLI command existence and registration."""

    def test_create_command_exists(self) -> None:
        """Test that create command is defined."""
        from skillforge.cli.elevenlabs import create
        assert callable(create)

    def test_configure_command_exists(self) -> None:
        """Test that configure command is defined."""
        from skillforge.cli.elevenlabs import configure
        assert callable(configure)

    def test_cli_app_has_all_commands(self) -> None:
        """Test that CLI app has all expected commands registered."""
        from skillforge.cli.elevenlabs import app

        # Check that the app has commands registered
        # Should now have 6 commands: connect, disconnect, sync, status, create, configure
        assert len(app.registered_commands) == 6

        # Get command names from callback function names
        command_names = [
            cmd.name or cmd.callback.__name__
            for cmd in app.registered_commands
        ]
        assert "create" in command_names
        assert "configure" in command_names
        assert "connect" in command_names
        assert "sync" in command_names
        assert "status" in command_names
        assert "disconnect" in command_names
