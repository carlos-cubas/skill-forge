"""
Unit tests for ElevenLabs sync functionality.

Tests cover:
- Credential storage and retrieval
- ElevenLabs manifest tracking
- Skill formatting for RAG
- Sync operations (mocked API)
- CLI commands
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from skillforge.adapters.elevenlabs.credentials import (
    CREDENTIALS_DIR,
    CREDENTIALS_FILE,
    CredentialsError,
    CredentialsNotFoundError,
    InvalidCredentialsError,
    delete_credentials,
    load_credentials,
    save_credentials,
    verify_credentials,
)
from skillforge.adapters.elevenlabs.manifest import ElevenLabsManifest
from skillforge.adapters.elevenlabs.sync import (
    SyncError,
    compute_content_hash,
    format_skill_for_rag,
    sync_skill_to_kb,
    sync_skills_to_kb,
)
from skillforge.core.skill import Skill


class TestCredentials:
    """Tests for credential management."""

    def test_save_credentials(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that credentials are saved securely."""
        creds_file = tmp_path / "elevenlabs.json"
        monkeypatch.setattr(
            "skillforge.adapters.elevenlabs.credentials.CREDENTIALS_FILE", creds_file
        )
        monkeypatch.setattr(
            "skillforge.adapters.elevenlabs.credentials.CREDENTIALS_DIR", tmp_path
        )

        save_credentials("test-api-key-12345")

        assert creds_file.exists()
        with open(creds_file) as f:
            data = json.load(f)
        assert data["api_key"] == "test-api-key-12345"

        # Check file permissions (0o600)
        import stat
        mode = creds_file.stat().st_mode & 0o777
        assert mode == 0o600

    def test_save_credentials_empty_key_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that empty API key raises ValueError."""
        monkeypatch.setattr(
            "skillforge.adapters.elevenlabs.credentials.CREDENTIALS_DIR", tmp_path
        )

        with pytest.raises(ValueError, match="cannot be empty"):
            save_credentials("")

        with pytest.raises(ValueError, match="cannot be empty"):
            save_credentials("   ")

    def test_load_credentials(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading stored credentials."""
        creds_file = tmp_path / "elevenlabs.json"
        creds_file.write_text(json.dumps({"api_key": "loaded-api-key"}))
        monkeypatch.setattr(
            "skillforge.adapters.elevenlabs.credentials.CREDENTIALS_FILE", creds_file
        )

        api_key = load_credentials()

        assert api_key == "loaded-api-key"

    def test_load_credentials_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that missing credentials raise CredentialsNotFoundError."""
        creds_file = tmp_path / "elevenlabs.json"
        monkeypatch.setattr(
            "skillforge.adapters.elevenlabs.credentials.CREDENTIALS_FILE", creds_file
        )

        with pytest.raises(CredentialsNotFoundError, match="not found"):
            load_credentials()

    def test_load_credentials_corrupt_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that corrupt credentials file raises CredentialsError."""
        creds_file = tmp_path / "elevenlabs.json"
        creds_file.write_text("not valid json {{{")
        monkeypatch.setattr(
            "skillforge.adapters.elevenlabs.credentials.CREDENTIALS_FILE", creds_file
        )

        with pytest.raises(CredentialsError, match="Corrupt credentials"):
            load_credentials()

    def test_delete_credentials(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test deleting stored credentials."""
        creds_file = tmp_path / "elevenlabs.json"
        creds_file.write_text(json.dumps({"api_key": "to-delete"}))
        monkeypatch.setattr(
            "skillforge.adapters.elevenlabs.credentials.CREDENTIALS_FILE", creds_file
        )

        result = delete_credentials()

        assert result is True
        assert not creds_file.exists()

    def test_delete_credentials_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test deleting non-existent credentials returns False."""
        creds_file = tmp_path / "elevenlabs.json"
        monkeypatch.setattr(
            "skillforge.adapters.elevenlabs.credentials.CREDENTIALS_FILE", creds_file
        )

        result = delete_credentials()

        assert result is False

    def test_verify_credentials_valid(self) -> None:
        """Test verifying valid credentials."""
        import sys
        mock_elevenlabs_module = MagicMock()
        mock_client = MagicMock()
        mock_elevenlabs_module.ElevenLabs.return_value = mock_client

        with patch.dict(sys.modules, {"elevenlabs": mock_elevenlabs_module}):
            # Need to reimport to pick up mock
            from skillforge.adapters.elevenlabs.credentials import verify_credentials as verify_creds
            result = verify_creds("valid-api-key")

            assert result is True
            mock_elevenlabs_module.ElevenLabs.assert_called_once_with(api_key="valid-api-key")
            mock_client.conversational_ai.knowledge_base.documents.get_all.assert_called_once()

    def test_verify_credentials_invalid(self) -> None:
        """Test verifying invalid credentials raises error."""
        import sys
        mock_elevenlabs_module = MagicMock()
        mock_client = MagicMock()
        mock_client.conversational_ai.knowledge_base.documents.get_all.side_effect = (
            Exception("401 Unauthorized")
        )
        mock_elevenlabs_module.ElevenLabs.return_value = mock_client

        with patch.dict(sys.modules, {"elevenlabs": mock_elevenlabs_module}):
            from skillforge.adapters.elevenlabs.credentials import verify_credentials as verify_creds
            with pytest.raises(InvalidCredentialsError, match="Invalid API key"):
                verify_creds("invalid-api-key")


class TestElevenLabsManifest:
    """Tests for ElevenLabsManifest."""

    def test_manifest_init(self, tmp_path: Path) -> None:
        """Test manifest initialization."""
        manifest = ElevenLabsManifest(project_root=tmp_path)

        assert manifest.project_root == tmp_path
        assert manifest.manifest_dir == tmp_path / ".skillforge"
        assert manifest.manifest_file == tmp_path / ".skillforge" / "elevenlabs_manifest.json"

    def test_set_and_get_document_id(self, tmp_path: Path) -> None:
        """Test setting and getting document IDs."""
        manifest = ElevenLabsManifest(project_root=tmp_path)

        manifest.set_document_id("test-skill", "doc_abc123", "hash123")
        manifest.save()

        doc_id = manifest.get_document_id("test-skill")

        assert doc_id == "doc_abc123"

    def test_get_document_id_not_found(self, tmp_path: Path) -> None:
        """Test getting document ID for non-synced skill returns None."""
        manifest = ElevenLabsManifest(project_root=tmp_path)

        doc_id = manifest.get_document_id("nonexistent")

        assert doc_id is None

    def test_remove_document(self, tmp_path: Path) -> None:
        """Test removing a document entry."""
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("test-skill", "doc_abc123")
        manifest.save()

        removed_id = manifest.remove_document("test-skill")
        manifest.save()

        assert removed_id == "doc_abc123"
        assert manifest.get_document_id("test-skill") is None

    def test_list_synced_skills(self, tmp_path: Path) -> None:
        """Test listing synced skills."""
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("skill-b", "doc_b")
        manifest.set_document_id("skill-a", "doc_a")
        manifest.save()

        synced = manifest.list_synced_skills()

        assert synced == ["skill-a", "skill-b"]  # Sorted

    def test_has_skill(self, tmp_path: Path) -> None:
        """Test checking if skill is synced."""
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("synced-skill", "doc_123")

        assert manifest.has_skill("synced-skill") is True
        assert manifest.has_skill("not-synced") is False

    def test_get_sync_info(self, tmp_path: Path) -> None:
        """Test getting full sync info."""
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("test-skill", "doc_abc", "content_hash_123")
        manifest.save()

        info = manifest.get_sync_info("test-skill")

        assert info is not None
        assert info["document_id"] == "doc_abc"
        assert info["content_hash"] == "content_hash_123"
        assert "synced_at" in info

    def test_persistence(self, tmp_path: Path) -> None:
        """Test that manifest changes persist to disk."""
        manifest1 = ElevenLabsManifest(project_root=tmp_path)
        manifest1.set_document_id("test-skill", "doc_xyz")
        manifest1.save()

        # Load fresh instance
        manifest2 = ElevenLabsManifest(project_root=tmp_path)

        assert manifest2.get_document_id("test-skill") == "doc_xyz"

    def test_clear(self, tmp_path: Path) -> None:
        """Test clearing all document entries."""
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("skill-1", "doc_1")
        manifest.set_document_id("skill-2", "doc_2")
        manifest.save()

        manifest.clear()

        assert manifest.list_synced_skills() == []


class TestFormatSkillForRag:
    """Tests for skill formatting."""

    def test_format_skill_for_rag(self) -> None:
        """Test formatting skill with SKILL header."""
        skill = Skill(
            name="rapid-interviewing",
            description="Conduct rapid discovery interviews",
            instructions="## When to Use\n- When you need to understand users",
            path=Path("./skills/rapid-interviewing"),
        )

        content = format_skill_for_rag(skill)

        assert content.startswith("# SKILL: rapid-interviewing")
        assert "> Conduct rapid discovery interviews" in content
        assert "## When to Use" in content
        assert "When you need to understand users" in content

    def test_format_skill_without_description(self) -> None:
        """Test formatting skill without description."""
        skill = Skill(
            name="minimal-skill",
            description="",
            instructions="Just instructions",
            path=Path("./skills/minimal-skill"),
        )

        content = format_skill_for_rag(skill)

        assert content.startswith("# SKILL: minimal-skill")
        assert "Just instructions" in content
        # No description line
        assert ">" not in content or "> " not in content.split("\n")[1]


class TestComputeContentHash:
    """Tests for content hashing."""

    def test_compute_content_hash(self) -> None:
        """Test that hash is computed correctly."""
        content = "Some skill content"

        hash1 = compute_content_hash(content)
        hash2 = compute_content_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated to 16 chars

    def test_compute_content_hash_different_content(self) -> None:
        """Test that different content produces different hash."""
        hash1 = compute_content_hash("Content A")
        hash2 = compute_content_hash("Content B")

        assert hash1 != hash2


class TestSyncSkillToKb:
    """Tests for sync operations (mocked API)."""

    @patch("skillforge.adapters.elevenlabs.sync.get_client")
    def test_sync_skill_creates_document(
        self, mock_get_client: MagicMock, tmp_path: Path
    ) -> None:
        """Test that syncing a new skill creates a document."""
        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "new_doc_123"
        mock_client.conversational_ai.knowledge_base.documents.create_from_text.return_value = (
            mock_doc
        )
        mock_get_client.return_value = mock_client

        skill = Skill(
            name="test-skill",
            description="Test description",
            instructions="Test instructions",
            path=tmp_path / "test-skill",
        )
        manifest = ElevenLabsManifest(project_root=tmp_path)

        doc_id, was_updated = sync_skill_to_kb(skill, manifest)

        assert doc_id == "new_doc_123"
        assert was_updated is True
        mock_client.conversational_ai.knowledge_base.documents.create_from_text.assert_called_once()

    @patch("skillforge.adapters.elevenlabs.sync.get_client")
    def test_sync_skill_skips_unchanged(
        self, mock_get_client: MagicMock, tmp_path: Path
    ) -> None:
        """Test that unchanged skills are skipped."""
        skill = Skill(
            name="test-skill",
            description="Test description",
            instructions="Test instructions",
            path=tmp_path / "test-skill",
        )

        # Pre-populate manifest with matching hash
        from skillforge.adapters.elevenlabs.sync import format_skill_for_rag, compute_content_hash
        content = format_skill_for_rag(skill)
        content_hash = compute_content_hash(content)

        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("test-skill", "existing_doc_123", content_hash)
        manifest.save()

        doc_id, was_updated = sync_skill_to_kb(skill, manifest)

        assert doc_id == "existing_doc_123"
        assert was_updated is False
        mock_get_client.assert_not_called()  # No API call needed

    @patch("skillforge.adapters.elevenlabs.sync.get_client")
    def test_sync_skill_updates_existing(
        self, mock_get_client: MagicMock, tmp_path: Path
    ) -> None:
        """Test that existing documents are replaced on content change."""
        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "updated_doc_456"
        mock_client.conversational_ai.knowledge_base.documents.create_from_text.return_value = (
            mock_doc
        )
        mock_get_client.return_value = mock_client

        skill = Skill(
            name="test-skill",
            description="Updated description",
            instructions="Updated instructions",
            path=tmp_path / "test-skill",
        )

        # Pre-populate manifest with old document
        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("test-skill", "old_doc_123", "old_hash")
        manifest.save()

        doc_id, was_updated = sync_skill_to_kb(skill, manifest)

        assert doc_id == "updated_doc_456"
        assert was_updated is True
        # Should delete old document first
        mock_client.conversational_ai.knowledge_base.documents.delete.assert_called_once_with(
            "old_doc_123"
        )

    @patch("skillforge.adapters.elevenlabs.sync.get_client")
    def test_sync_skill_force_resync(
        self, mock_get_client: MagicMock, tmp_path: Path
    ) -> None:
        """Test that force flag re-syncs unchanged skills."""
        mock_client = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = "forced_doc_789"
        mock_client.conversational_ai.knowledge_base.documents.create_from_text.return_value = (
            mock_doc
        )
        mock_get_client.return_value = mock_client

        skill = Skill(
            name="test-skill",
            description="Test description",
            instructions="Test instructions",
            path=tmp_path / "test-skill",
        )

        # Pre-populate manifest with matching hash
        from skillforge.adapters.elevenlabs.sync import format_skill_for_rag, compute_content_hash
        content = format_skill_for_rag(skill)
        content_hash = compute_content_hash(content)

        manifest = ElevenLabsManifest(project_root=tmp_path)
        manifest.set_document_id("test-skill", "existing_doc", content_hash)
        manifest.save()

        doc_id, was_updated = sync_skill_to_kb(skill, manifest, force=True)

        assert doc_id == "forced_doc_789"
        assert was_updated is True


class TestSyncSkillsToKb:
    """Tests for bulk sync operations."""

    @patch("skillforge.adapters.elevenlabs.sync.sync_skill_to_kb")
    def test_sync_all_skills(
        self, mock_sync_skill: MagicMock, tmp_path: Path
    ) -> None:
        """Test syncing multiple skills."""
        mock_sync_skill.side_effect = [
            ("doc_1", True),
            ("doc_2", True),
        ]

        skills = {
            "skill-1": Skill(
                name="skill-1",
                description="Skill 1",
                instructions="Instructions 1",
                path=tmp_path / "skill-1",
            ),
            "skill-2": Skill(
                name="skill-2",
                description="Skill 2",
                instructions="Instructions 2",
                path=tmp_path / "skill-2",
            ),
        }

        result = sync_skills_to_kb(skills, ElevenLabsManifest(project_root=tmp_path))

        assert result == {"skill-1": "doc_1", "skill-2": "doc_2"}
        assert mock_sync_skill.call_count == 2

    @patch("skillforge.adapters.elevenlabs.sync.sync_skill_to_kb")
    def test_sync_specific_skills(
        self, mock_sync_skill: MagicMock, tmp_path: Path
    ) -> None:
        """Test syncing specific skills."""
        mock_sync_skill.return_value = ("doc_single", True)

        skills = {
            "target-skill": Skill(
                name="target-skill",
                description="Target",
                instructions="Instructions",
                path=tmp_path / "target-skill",
            ),
        }

        result = sync_skills_to_kb(skills)

        assert "target-skill" in result
        assert result["target-skill"] == "doc_single"

    @patch("skillforge.adapters.elevenlabs.sync.sync_skill_to_kb")
    def test_sync_handles_errors(
        self, mock_sync_skill: MagicMock, tmp_path: Path
    ) -> None:
        """Test that sync errors are collected and raised."""
        mock_sync_skill.side_effect = [
            ("doc_1", True),
            SyncError("Failed to sync skill-2"),
        ]

        skills = {
            "skill-1": Skill(
                name="skill-1",
                description="Skill 1",
                instructions="Instructions 1",
                path=tmp_path / "skill-1",
            ),
            "skill-2": Skill(
                name="skill-2",
                description="Skill 2",
                instructions="Instructions 2",
                path=tmp_path / "skill-2",
            ),
        }

        with pytest.raises(SyncError, match="1 error"):
            sync_skills_to_kb(skills, ElevenLabsManifest(project_root=tmp_path))


class TestElevenLabsCLI:
    """Tests for CLI commands."""

    def test_connect_command_exists(self) -> None:
        """Test that connect command is defined."""
        from skillforge.cli.elevenlabs import connect
        assert callable(connect)

    def test_sync_command_exists(self) -> None:
        """Test that sync command is defined."""
        from skillforge.cli.elevenlabs import sync
        assert callable(sync)

    def test_status_command_exists(self) -> None:
        """Test that status command is defined."""
        from skillforge.cli.elevenlabs import status
        assert callable(status)

    def test_disconnect_command_exists(self) -> None:
        """Test that disconnect command is defined."""
        from skillforge.cli.elevenlabs import disconnect
        assert callable(disconnect)

    def test_cli_app_has_commands(self) -> None:
        """Test that CLI app has registered commands."""
        from skillforge.cli.elevenlabs import app

        # Check that the app has commands registered
        # Commands: connect, disconnect, sync, status, create, configure, cleanup
        assert len(app.registered_commands) == 7


class TestCLIMainIntegration:
    """Tests for CLI integration in main.py."""

    def test_elevenlabs_subcommand_registered(self) -> None:
        """Test that elevenlabs is registered as a subcommand."""
        from skillforge.cli.main import app

        # Check registered typers
        registered_groups = [group.name for group in app.registered_groups]
        assert "elevenlabs" in registered_groups
