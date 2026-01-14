"""
Unit tests for the Manifest class.
"""

import json
import tempfile
from pathlib import Path

import pytest

from skillforge.core.manifest import (
    Manifest,
    SkillAlreadyInstalledError,
    SkillNotInstalledError,
)


class TestManifestInit:
    """Tests for Manifest initialization."""

    def test_manifest_creates_with_default_root(self) -> None:
        """Test that Manifest initializes with cwd as default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory for this test
            import os
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                manifest = Manifest()
                # Use resolve() to handle macOS /private/var symlink
                assert manifest.project_root.resolve() == Path(tmpdir).resolve()
                assert manifest.manifest_dir.resolve() == (Path(tmpdir) / ".skillforge").resolve()
            finally:
                os.chdir(original_cwd)

    def test_manifest_creates_with_custom_root(self) -> None:
        """Test that Manifest initializes with custom root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = Manifest(project_root=root)

            assert manifest.project_root == root
            assert manifest.manifest_dir == root / ".skillforge"
            assert manifest.manifest_file == root / ".skillforge" / "manifest.json"

    def test_manifest_loads_existing_file(self) -> None:
        """Test that Manifest loads existing manifest.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_dir = root / ".skillforge"
            manifest_dir.mkdir()

            # Create existing manifest
            manifest_data = {
                "version": "1.0",
                "skills": {
                    "test-skill": {
                        "path": "./skills/test-skill",
                        "marketplace": "test/marketplace",
                        "version": "1.0.0",
                    }
                }
            }
            with open(manifest_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)

            # Load manifest
            manifest = Manifest(project_root=root)
            skills = manifest.list()

            assert "test-skill" in skills
            assert skills["test-skill"]["path"] == "./skills/test-skill"
            assert skills["test-skill"]["marketplace"] == "test/marketplace"
            assert skills["test-skill"]["version"] == "1.0.0"

    def test_manifest_handles_missing_file(self) -> None:
        """Test that Manifest handles missing manifest.json gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))
            assert manifest.list() == {}

    def test_manifest_handles_corrupt_file(self) -> None:
        """Test that Manifest handles corrupt manifest.json gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest_dir = root / ".skillforge"
            manifest_dir.mkdir()

            # Create corrupt manifest
            with open(manifest_dir / "manifest.json", "w") as f:
                f.write("not valid json {{{")

            # Should not raise, just log warning
            manifest = Manifest(project_root=root)
            assert manifest.list() == {}


class TestManifestAdd:
    """Tests for Manifest.add()."""

    def test_add_skill(self) -> None:
        """Test adding a skill to the manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
                version="1.0.0",
            )

            skill = manifest.get("test-skill")
            assert skill["path"] == "./skills/test-skill"
            assert skill["marketplace"] == "test/marketplace"
            assert skill["version"] == "1.0.0"

    def test_add_skill_without_version(self) -> None:
        """Test adding a skill without version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
            )

            skill = manifest.get("test-skill")
            assert skill["version"] is None

    def test_add_duplicate_skill_fails(self) -> None:
        """Test that adding a duplicate skill raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
            )

            with pytest.raises(SkillAlreadyInstalledError) as exc_info:
                manifest.add(
                    name="test-skill",
                    path="./other/path",
                    marketplace="other/marketplace",
                )

            assert "already installed" in str(exc_info.value)
            assert "skillforge uninstall" in str(exc_info.value)


class TestManifestRemove:
    """Tests for Manifest.remove()."""

    def test_remove_skill(self) -> None:
        """Test removing a skill from the manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
            )

            removed = manifest.remove("test-skill")

            assert removed["path"] == "./skills/test-skill"
            assert not manifest.has("test-skill")

    def test_remove_nonexistent_skill_fails(self) -> None:
        """Test that removing nonexistent skill raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            with pytest.raises(SkillNotInstalledError) as exc_info:
                manifest.remove("nonexistent")

            assert "not installed" in str(exc_info.value)


class TestManifestGet:
    """Tests for Manifest.get()."""

    def test_get_skill(self) -> None:
        """Test getting a skill from the manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
                version="1.0.0",
            )

            skill = manifest.get("test-skill")

            assert skill["path"] == "./skills/test-skill"
            assert skill["marketplace"] == "test/marketplace"
            assert skill["version"] == "1.0.0"

    def test_get_returns_copy(self) -> None:
        """Test that get returns a copy, not the original."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
            )

            skill = manifest.get("test-skill")
            skill["path"] = "modified"

            # Original should be unchanged
            original = manifest.get("test-skill")
            assert original["path"] == "./skills/test-skill"

    def test_get_nonexistent_skill_fails(self) -> None:
        """Test that getting nonexistent skill raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            with pytest.raises(SkillNotInstalledError) as exc_info:
                manifest.get("nonexistent")

            assert "not installed" in str(exc_info.value)


class TestManifestList:
    """Tests for Manifest.list()."""

    def test_list_empty(self) -> None:
        """Test listing empty manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))
            assert manifest.list() == {}

    def test_list_with_skills(self) -> None:
        """Test listing manifest with skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="skill-1",
                path="./skills/skill-1",
                marketplace="marketplace-1",
            )
            manifest.add(
                name="skill-2",
                path="./skills/skill-2",
                marketplace="marketplace-2",
            )

            skills = manifest.list()

            assert len(skills) == 2
            assert "skill-1" in skills
            assert "skill-2" in skills

    def test_list_returns_copy(self) -> None:
        """Test that list returns a copy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
            )

            skills = manifest.list()
            skills["new-skill"] = {"path": "fake"}

            # Original should be unchanged
            assert "new-skill" not in manifest.list()


class TestManifestHas:
    """Tests for Manifest.has()."""

    def test_has_installed_skill(self) -> None:
        """Test checking for installed skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
            )

            assert manifest.has("test-skill") is True

    def test_has_not_installed_skill(self) -> None:
        """Test checking for non-installed skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            assert manifest.has("nonexistent") is False


class TestManifestPersistence:
    """Tests for manifest persistence."""

    def test_manifest_persistence(self) -> None:
        """Test that manifest changes are persisted to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Add skill
            manifest1 = Manifest(project_root=root)
            manifest1.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
                version="1.0.0",
            )

            # Load fresh instance
            manifest2 = Manifest(project_root=root)
            skill = manifest2.get("test-skill")

            assert skill["path"] == "./skills/test-skill"
            assert skill["marketplace"] == "test/marketplace"
            assert skill["version"] == "1.0.0"

    def test_manifest_persistence_after_remove(self) -> None:
        """Test that removals are persisted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Add and remove skill
            manifest1 = Manifest(project_root=root)
            manifest1.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
            )
            manifest1.remove("test-skill")

            # Load fresh instance
            manifest2 = Manifest(project_root=root)
            assert manifest2.has("test-skill") is False

    def test_manifest_creates_directory(self) -> None:
        """Test that manifest creates .skillforge directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            manifest = Manifest(project_root=root)

            manifest.add(
                name="test-skill",
                path="./skills/test-skill",
                marketplace="test/marketplace",
            )

            assert (root / ".skillforge").is_dir()
            assert (root / ".skillforge" / "manifest.json").is_file()


class TestManifestClear:
    """Tests for Manifest.clear()."""

    def test_clear(self) -> None:
        """Test clearing all skills from manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = Manifest(project_root=Path(tmpdir))

            manifest.add(
                name="skill-1",
                path="./skills/skill-1",
                marketplace="marketplace-1",
            )
            manifest.add(
                name="skill-2",
                path="./skills/skill-2",
                marketplace="marketplace-2",
            )

            manifest.clear()

            assert manifest.list() == {}
