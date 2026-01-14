"""Unit tests for MarketplaceRegistry and related components."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skillforge.core.marketplace import (
    Marketplace,
    MarketplaceSkill,
    MarketplaceSource,
    parse_marketplace_source,
)
from skillforge.core.marketplace_registry import (
    MarketplaceRegistry,
    MarketplaceNotFoundError,
    MarketplaceExistsError,
    SkillNotInMarketplaceError,
)
from skillforge.core.fetcher import MarketplaceFetcher, FetchError


class TestMarketplaceSource:
    """Tests for MarketplaceSource enum."""

    def test_source_values(self) -> None:
        """Test that source enum has expected values."""
        assert MarketplaceSource.GITHUB.value == "github"
        assert MarketplaceSource.GIT_URL.value == "git"
        assert MarketplaceSource.LOCAL.value == "local"


class TestMarketplaceSkill:
    """Tests for MarketplaceSkill dataclass."""

    def test_create_with_required_fields(self) -> None:
        """Test creating skill with required fields."""
        skill = MarketplaceSkill(
            name="test-skill",
            description="A test skill",
            source="github:owner/repo/test-skill",
        )
        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert skill.source == "github:owner/repo/test-skill"
        assert skill.version is None

    def test_create_with_all_fields(self) -> None:
        """Test creating skill with all fields."""
        skill = MarketplaceSkill(
            name="test-skill",
            description="A test skill",
            source="github:owner/repo/test-skill",
            version="1.0.0",
        )
        assert skill.version == "1.0.0"


class TestMarketplace:
    """Tests for Marketplace dataclass."""

    def test_create_marketplace(self) -> None:
        """Test creating a marketplace."""
        marketplace = Marketplace(
            name="owner/repo",
            source="owner/repo",
            source_type=MarketplaceSource.GITHUB,
        )
        assert marketplace.name == "owner/repo"
        assert marketplace.source == "owner/repo"
        assert marketplace.source_type == MarketplaceSource.GITHUB
        assert marketplace.skills == []
        assert marketplace.local_path is None
        assert marketplace.remote_url is None

    def test_to_dict(self) -> None:
        """Test serializing marketplace to dict."""
        skill = MarketplaceSkill(
            name="skill1",
            description="Skill 1",
            source="github:owner/repo/skill1",
            version="1.0.0",
        )
        marketplace = Marketplace(
            name="owner/repo",
            source="owner/repo",
            source_type=MarketplaceSource.GITHUB,
            skills=[skill],
            remote_url="https://github.com/owner/repo.git",
        )

        data = marketplace.to_dict()

        assert data["name"] == "owner/repo"
        assert data["source"] == "owner/repo"
        assert data["source_type"] == "github"
        assert len(data["skills"]) == 1
        assert data["skills"][0]["name"] == "skill1"
        assert data["remote_url"] == "https://github.com/owner/repo.git"
        assert data["local_path"] is None

    def test_from_dict(self) -> None:
        """Test deserializing marketplace from dict."""
        data = {
            "name": "owner/repo",
            "source": "owner/repo",
            "source_type": "github",
            "skills": [
                {
                    "name": "skill1",
                    "description": "Skill 1",
                    "source": "github:owner/repo/skill1",
                    "version": "1.0.0",
                }
            ],
            "remote_url": "https://github.com/owner/repo.git",
            "local_path": None,
        }

        marketplace = Marketplace.from_dict(data)

        assert marketplace.name == "owner/repo"
        assert marketplace.source_type == MarketplaceSource.GITHUB
        assert len(marketplace.skills) == 1
        assert marketplace.skills[0].name == "skill1"


class TestParseMarketplaceSource:
    """Tests for parse_marketplace_source function."""

    def test_github_shorthand(self) -> None:
        """Test parsing GitHub shorthand (owner/repo)."""
        source_type, name, url = parse_marketplace_source("owner/repo")

        assert source_type == MarketplaceSource.GITHUB
        assert name == "owner/repo"
        assert url == "https://github.com/owner/repo.git"

    def test_explicit_github(self) -> None:
        """Test parsing explicit github: prefix."""
        source_type, name, url = parse_marketplace_source("github:owner/repo")

        assert source_type == MarketplaceSource.GITHUB
        assert name == "owner/repo"
        assert url == "https://github.com/owner/repo.git"

    def test_local_relative_path(self) -> None:
        """Test parsing local relative path."""
        source_type, name, resolved = parse_marketplace_source("./local-skills")

        assert source_type == MarketplaceSource.LOCAL
        assert name == "local-skills"
        assert Path(resolved).is_absolute()

    def test_local_absolute_path(self) -> None:
        """Test parsing local absolute path."""
        source_type, name, resolved = parse_marketplace_source("/tmp/skills")

        assert source_type == MarketplaceSource.LOCAL
        assert name == "skills"
        # On macOS, /tmp resolves to /private/tmp
        assert Path(resolved).resolve() == Path("/tmp/skills").resolve()

    def test_https_git_url(self) -> None:
        """Test parsing HTTPS git URL."""
        source_type, name, url = parse_marketplace_source(
            "https://github.com/owner/repo.git"
        )

        assert source_type == MarketplaceSource.GIT_URL
        assert name == "owner/repo"
        assert url == "https://github.com/owner/repo.git"

    def test_ssh_git_url(self) -> None:
        """Test parsing SSH git URL."""
        source_type, name, url = parse_marketplace_source(
            "git@github.com:owner/repo.git"
        )

        assert source_type == MarketplaceSource.GIT_URL
        assert name == "owner/repo"
        assert url == "git@github.com:owner/repo.git"

    def test_invalid_github_format(self) -> None:
        """Test that invalid github: format raises error."""
        with pytest.raises(ValueError, match="Invalid GitHub source"):
            parse_marketplace_source("github:invalid")

    def test_unrecognized_format(self) -> None:
        """Test that unrecognized format raises error."""
        with pytest.raises(ValueError, match="Unrecognized marketplace source"):
            parse_marketplace_source("invalid-source")


class TestMarketplaceRegistry:
    """Tests for MarketplaceRegistry class."""

    def test_add_github_marketplace(self) -> None:
        """Test adding a GitHub marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))

            marketplace = registry.add("dearmarkus/event-skills")

            assert marketplace.name == "dearmarkus/event-skills"
            assert marketplace.source_type == MarketplaceSource.GITHUB
            assert marketplace.remote_url == "https://github.com/dearmarkus/event-skills.git"

    def test_add_local_marketplace(self) -> None:
        """Test adding a local marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a local skills directory
            skills_dir = Path(tmpdir) / "local-skills"
            skills_dir.mkdir()

            registry = MarketplaceRegistry(config_dir=Path(tmpdir) / "config")

            marketplace = registry.add(str(skills_dir))

            assert marketplace.name == "local-skills"
            assert marketplace.source_type == MarketplaceSource.LOCAL
            # Compare resolved paths to handle macOS symlinks
            assert marketplace.local_path.resolve() == skills_dir.resolve()

    def test_remove_marketplace(self) -> None:
        """Test removing a marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))
            registry.add("owner/repo")

            registry.remove("owner/repo")

            assert len(registry.list()) == 0

    def test_remove_nonexistent_raises_error(self) -> None:
        """Test that removing nonexistent marketplace raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))

            with pytest.raises(MarketplaceNotFoundError, match="not found"):
                registry.remove("nonexistent")

    def test_list_marketplaces(self) -> None:
        """Test listing all marketplaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))
            registry.add("owner1/repo1")
            registry.add("owner2/repo2")

            marketplaces = registry.list()

            assert len(marketplaces) == 2
            names = [m.name for m in marketplaces]
            assert "owner1/repo1" in names
            assert "owner2/repo2" in names

    def test_list_returns_sorted(self) -> None:
        """Test that list returns marketplaces sorted by name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))
            registry.add("zebra/repo")
            registry.add("alpha/repo")
            registry.add("middle/repo")

            marketplaces = registry.list()

            names = [m.name for m in marketplaces]
            assert names == ["alpha/repo", "middle/repo", "zebra/repo"]

    def test_get_marketplace(self) -> None:
        """Test getting a marketplace by name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))
            registry.add("owner/repo")

            marketplace = registry.get("owner/repo")

            assert marketplace.name == "owner/repo"

    def test_get_nonexistent_raises_error(self) -> None:
        """Test that getting nonexistent marketplace raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))

            with pytest.raises(MarketplaceNotFoundError, match="not found"):
                registry.get("nonexistent")

    def test_add_duplicate_raises_error(self) -> None:
        """Test that adding duplicate marketplace raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))
            registry.add("owner/repo")

            with pytest.raises(MarketplaceExistsError, match="already exists"):
                registry.add("owner/repo")

    def test_find_skill(self) -> None:
        """Test finding a skill in a marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))
            marketplace = registry.add("owner/repo")

            # Manually add a skill to the marketplace
            skill = MarketplaceSkill(
                name="test-skill",
                description="Test skill",
                source="github:owner/repo/test-skill",
            )
            marketplace.skills.append(skill)
            registry._save()

            found = registry.find_skill("test-skill", "owner/repo")

            assert found.name == "test-skill"

    def test_find_skill_not_found_raises_error(self) -> None:
        """Test that finding nonexistent skill raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))
            registry.add("owner/repo")

            with pytest.raises(SkillNotInMarketplaceError, match="not found"):
                registry.find_skill("nonexistent", "owner/repo")

    def test_persistence(self) -> None:
        """Test that marketplaces persist across registry instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create first registry and add marketplace
            registry1 = MarketplaceRegistry(config_dir=config_dir)
            registry1.add("owner/repo")

            # Create second registry from same config dir
            registry2 = MarketplaceRegistry(config_dir=config_dir)

            # Should have the marketplace loaded
            marketplace = registry2.get("owner/repo")
            assert marketplace.name == "owner/repo"

    def test_persistence_with_skills(self) -> None:
        """Test that marketplace skills persist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create registry and add marketplace with skill
            registry1 = MarketplaceRegistry(config_dir=config_dir)
            marketplace = registry1.add("owner/repo")
            marketplace.skills.append(
                MarketplaceSkill(
                    name="skill1",
                    description="Skill 1",
                    source="github:owner/repo/skill1",
                    version="1.0.0",
                )
            )
            registry1._save()

            # Load in new registry
            registry2 = MarketplaceRegistry(config_dir=config_dir)
            loaded = registry2.get("owner/repo")

            assert len(loaded.skills) == 1
            assert loaded.skills[0].name == "skill1"
            assert loaded.skills[0].version == "1.0.0"

    def test_update_marketplace(self) -> None:
        """Test updating marketplace metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            registry = MarketplaceRegistry(config_dir=config_dir)
            marketplace = registry.add("owner/repo")

            # Mock fetcher
            mock_fetcher = MagicMock(spec=MarketplaceFetcher)
            mock_fetcher.fetch_metadata.return_value = [
                MarketplaceSkill(
                    name="fetched-skill",
                    description="A fetched skill",
                    source="github:owner/repo/fetched-skill",
                )
            ]

            registry.update("owner/repo", fetcher=mock_fetcher)

            updated = registry.get("owner/repo")
            assert len(updated.skills) == 1
            assert updated.skills[0].name == "fetched-skill"

    def test_clear_removes_all(self) -> None:
        """Test that clear removes all marketplaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))
            registry.add("owner1/repo1")
            registry.add("owner2/repo2")

            registry.clear()

            assert len(registry.list()) == 0

    def test_search_skill_across_marketplaces(self) -> None:
        """Test searching for a skill across all marketplaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MarketplaceRegistry(config_dir=Path(tmpdir))

            # Add two marketplaces with the same skill name
            mp1 = registry.add("owner1/repo1")
            mp1.skills.append(
                MarketplaceSkill(
                    name="common-skill",
                    description="In repo1",
                    source="github:owner1/repo1/common-skill",
                )
            )

            mp2 = registry.add("owner2/repo2")
            mp2.skills.append(
                MarketplaceSkill(
                    name="common-skill",
                    description="In repo2",
                    source="github:owner2/repo2/common-skill",
                )
            )
            registry._save()

            results = registry.search_skill("common-skill")

            assert len(results) == 2
            marketplaces_found = [r[0].name for r in results]
            assert "owner1/repo1" in marketplaces_found
            assert "owner2/repo2" in marketplaces_found


class TestMarketplaceFetcher:
    """Tests for MarketplaceFetcher class."""

    def test_fetch_local_marketplace(self) -> None:
        """Test fetching skills from a local directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a local marketplace with a skill
            mp_dir = Path(tmpdir) / "marketplace"
            skill_dir = mp_dir / "test-skill"
            skill_dir.mkdir(parents=True)

            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                """---
name: test-skill
description: A test skill
version: 1.0.0
---

# Test Skill

Instructions here.
"""
            )

            marketplace = Marketplace(
                name="local-marketplace",
                source=str(mp_dir),
                source_type=MarketplaceSource.LOCAL,
                local_path=mp_dir,
            )

            fetcher = MarketplaceFetcher(cache_dir=Path(tmpdir) / "cache")
            skills = fetcher.fetch_metadata(marketplace)

            assert len(skills) == 1
            assert skills[0].name == "test-skill"
            assert skills[0].description == "A test skill"
            assert skills[0].version == "1.0.0"

    def test_fetch_local_with_nested_skills(self) -> None:
        """Test fetching skills from nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mp_dir = Path(tmpdir) / "marketplace"

            # Create nested skill structure
            (mp_dir / "category1" / "skill-a").mkdir(parents=True)
            (mp_dir / "category1" / "skill-a" / "SKILL.md").write_text(
                "---\nname: skill-a\ndescription: Skill A\n---\n# Skill A"
            )

            (mp_dir / "category2" / "skill-b").mkdir(parents=True)
            (mp_dir / "category2" / "skill-b" / "SKILL.md").write_text(
                "---\nname: skill-b\ndescription: Skill B\n---\n# Skill B"
            )

            marketplace = Marketplace(
                name="local-marketplace",
                source=str(mp_dir),
                source_type=MarketplaceSource.LOCAL,
                local_path=mp_dir,
            )

            fetcher = MarketplaceFetcher(cache_dir=Path(tmpdir) / "cache")
            skills = fetcher.fetch_metadata(marketplace)

            assert len(skills) == 2
            names = [s.name for s in skills]
            assert "skill-a" in names
            assert "skill-b" in names

    def test_fetch_local_missing_path_raises_error(self) -> None:
        """Test that fetching from nonexistent local path raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            marketplace = Marketplace(
                name="local-marketplace",
                source="/nonexistent/path",
                source_type=MarketplaceSource.LOCAL,
                local_path=Path("/nonexistent/path"),
            )

            fetcher = MarketplaceFetcher(cache_dir=Path(tmpdir) / "cache")

            with pytest.raises(FetchError, match="does not exist"):
                fetcher.fetch_metadata(marketplace)

    def test_fetch_skill_without_frontmatter(self) -> None:
        """Test fetching skill that has no frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mp_dir = Path(tmpdir) / "marketplace"
            skill_dir = mp_dir / "minimal-skill"
            skill_dir.mkdir(parents=True)

            # Skill with no frontmatter
            (skill_dir / "SKILL.md").write_text("# Minimal Skill\n\nJust content.")

            marketplace = Marketplace(
                name="local-marketplace",
                source=str(mp_dir),
                source_type=MarketplaceSource.LOCAL,
                local_path=mp_dir,
            )

            fetcher = MarketplaceFetcher(cache_dir=Path(tmpdir) / "cache")
            skills = fetcher.fetch_metadata(marketplace)

            assert len(skills) == 1
            # Name should default to directory name
            assert skills[0].name == "minimal-skill"
            assert skills[0].description == ""

    def test_download_skill_from_local(self) -> None:
        """Test downloading a skill from local marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source marketplace
            mp_dir = Path(tmpdir) / "marketplace"
            skill_dir = mp_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: test-skill\ndescription: Test\n---\n# Test"
            )
            (skill_dir / "tools.py").write_text("# Tools file")

            marketplace = Marketplace(
                name="local-marketplace",
                source=str(mp_dir),
                source_type=MarketplaceSource.LOCAL,
                local_path=mp_dir,
            )

            skill = MarketplaceSkill(
                name="test-skill",
                description="Test",
                source="local:local-marketplace/test-skill",
            )

            dest_dir = Path(tmpdir) / "destination"
            fetcher = MarketplaceFetcher(cache_dir=Path(tmpdir) / "cache")

            result = fetcher.download_skill(marketplace, skill, dest_dir)

            assert result.exists()
            assert (result / "SKILL.md").exists()
            assert (result / "tools.py").exists()

    def test_clear_cache(self) -> None:
        """Test clearing the cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache_dir.mkdir(parents=True)
            (cache_dir / "test_repo").mkdir()
            (cache_dir / "test_repo" / "file.txt").write_text("test")

            fetcher = MarketplaceFetcher(cache_dir=cache_dir)
            fetcher.clear_cache()

            assert not cache_dir.exists()


class TestIntegrationWithFixtures:
    """Integration tests using the test fixtures."""

    @pytest.fixture
    def fixtures_path(self) -> Path:
        """Get path to test fixtures."""
        return Path(__file__).parent.parent / "fixtures" / "skills"

    def test_fetch_from_fixtures_directory(self, fixtures_path: Path) -> None:
        """Test fetching skills from the fixtures directory."""
        if not fixtures_path.exists():
            pytest.skip("Fixtures directory not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            marketplace = Marketplace(
                name="test-fixtures",
                source=str(fixtures_path),
                source_type=MarketplaceSource.LOCAL,
                local_path=fixtures_path,
            )

            fetcher = MarketplaceFetcher(cache_dir=Path(tmpdir) / "cache")
            skills = fetcher.fetch_metadata(marketplace)

            # Should find skills in fixtures
            assert len(skills) > 0

            # Check for known fixture skills
            names = [s.name for s in skills]
            assert "rapid-interviewing" in names  # From complete-skill fixture
