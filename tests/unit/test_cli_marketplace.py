"""
Unit tests for the 'skillforge marketplace' CLI commands.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from skillforge.cli.main import app
from skillforge.core.marketplace import MarketplaceSkill, Marketplace, MarketplaceSource
from skillforge.core.marketplace_registry import (
    MarketplaceRegistry,
    MarketplaceNotFoundError,
    MarketplaceExistsError,
)


runner = CliRunner()

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "skills"


class TestMarketplaceAdd:
    """Tests for 'skillforge marketplace add' command."""

    def test_marketplace_add_github(self) -> None:
        """Test adding a GitHub marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                result = runner.invoke(
                    app, ["marketplace", "add", "dearmarkus/event-skills"]
                )

                assert result.exit_code == 0
                assert "Added marketplace:" in result.stdout
                assert "dearmarkus/event-skills" in result.stdout
                assert "Type: github" in result.stdout

    def test_marketplace_add_local(self) -> None:
        """Test adding a local marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a local skills directory
            skills_dir = Path(tmpdir) / "local-skills"
            skills_dir.mkdir()

            config_dir = Path(tmpdir) / "config"
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                config_dir,
            ):
                result = runner.invoke(
                    app, ["marketplace", "add", str(skills_dir)]
                )

                assert result.exit_code == 0
                assert "Added marketplace:" in result.stdout
                assert "local-skills" in result.stdout
                assert "Type: local" in result.stdout

    def test_marketplace_add_explicit_github(self) -> None:
        """Test adding a marketplace with explicit github: prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                result = runner.invoke(
                    app, ["marketplace", "add", "github:owner/repo"]
                )

                assert result.exit_code == 0
                assert "Added marketplace:" in result.stdout
                assert "owner/repo" in result.stdout
                assert "Type: github" in result.stdout

    def test_marketplace_add_git_url(self) -> None:
        """Test adding a marketplace with a Git URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                result = runner.invoke(
                    app,
                    ["marketplace", "add", "https://github.com/owner/repo.git"],
                )

                assert result.exit_code == 0
                assert "Added marketplace:" in result.stdout
                assert "owner/repo" in result.stdout
                assert "Type: git" in result.stdout

    def test_marketplace_add_duplicate_fails(self) -> None:
        """Test that adding a duplicate marketplace fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                # First add
                runner.invoke(app, ["marketplace", "add", "owner/repo"])

                # Second add should fail
                result = runner.invoke(app, ["marketplace", "add", "owner/repo"])

                assert result.exit_code == 1
                assert "Error" in result.stdout
                assert "already exists" in result.stdout

    def test_marketplace_add_invalid_source(self) -> None:
        """Test that adding an invalid source fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                result = runner.invoke(
                    app, ["marketplace", "add", "invalid-source"]
                )

                assert result.exit_code == 1
                assert "Error" in result.stdout
                assert "Unrecognized marketplace source" in result.stdout

    def test_marketplace_add_help(self) -> None:
        """Test that help is displayed correctly."""
        result = runner.invoke(app, ["marketplace", "add", "--help"])

        assert result.exit_code == 0
        assert "SOURCE" in result.stdout
        assert "owner/repo" in result.stdout


class TestMarketplaceList:
    """Tests for 'skillforge marketplace list' command."""

    def test_marketplace_list_empty(self) -> None:
        """Test listing when no marketplaces are configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                result = runner.invoke(app, ["marketplace", "list"])

                assert result.exit_code == 0
                assert "No marketplaces configured" in result.stdout
                assert "skillforge marketplace add" in result.stdout

    def test_marketplace_list_with_data(self) -> None:
        """Test listing configured marketplaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                # Add some marketplaces
                runner.invoke(app, ["marketplace", "add", "owner1/repo1"])
                runner.invoke(app, ["marketplace", "add", "owner2/repo2"])

                result = runner.invoke(app, ["marketplace", "list"])

                assert result.exit_code == 0
                assert "owner1/repo1" in result.stdout
                assert "owner2/repo2" in result.stdout
                assert "github" in result.stdout

    def test_marketplace_list_shows_table(self) -> None:
        """Test that list displays in table format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                runner.invoke(app, ["marketplace", "add", "owner/repo"])

                result = runner.invoke(app, ["marketplace", "list"])

                assert result.exit_code == 0
                assert "Configured Marketplaces" in result.stdout
                assert "Name" in result.stdout
                assert "Type" in result.stdout
                assert "Skills" in result.stdout

    def test_marketplace_list_help(self) -> None:
        """Test that help is displayed correctly."""
        result = runner.invoke(app, ["marketplace", "list", "--help"])

        assert result.exit_code == 0
        assert "List configured marketplaces" in result.stdout


class TestMarketplaceUpdate:
    """Tests for 'skillforge marketplace update' command."""

    def test_marketplace_update_specific(self) -> None:
        """Test updating a specific marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"

            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                config_dir,
            ):
                # Add a marketplace
                runner.invoke(app, ["marketplace", "add", "owner/repo"])

                # Mock the fetcher to return some skills
                mock_fetcher = MagicMock()
                mock_fetcher.fetch_metadata.return_value = [
                    MarketplaceSkill(
                        name="test-skill",
                        description="A test skill",
                        source="github:owner/repo/test-skill",
                    )
                ]

                with patch(
                    "skillforge.core.fetcher.MarketplaceFetcher",
                    return_value=mock_fetcher,
                ):
                    result = runner.invoke(
                        app, ["marketplace", "update", "owner/repo"]
                    )

                    assert result.exit_code == 0
                    assert "Updating marketplace" in result.stdout
                    assert "owner/repo" in result.stdout
                    assert "Updated!" in result.stdout
                    assert "1 skill" in result.stdout

    def test_marketplace_update_all(self) -> None:
        """Test updating all marketplaces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"

            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                config_dir,
            ):
                # Add multiple marketplaces
                runner.invoke(app, ["marketplace", "add", "owner1/repo1"])
                runner.invoke(app, ["marketplace", "add", "owner2/repo2"])

                # Mock the fetcher
                mock_fetcher = MagicMock()
                mock_fetcher.fetch_metadata.return_value = []

                with patch(
                    "skillforge.core.fetcher.MarketplaceFetcher",
                    return_value=mock_fetcher,
                ):
                    result = runner.invoke(app, ["marketplace", "update"])

                    assert result.exit_code == 0
                    assert "Updating 2 marketplace(s)" in result.stdout
                    assert "owner1/repo1" in result.stdout
                    assert "owner2/repo2" in result.stdout
                    assert "All marketplaces updated" in result.stdout

    def test_marketplace_update_nonexistent(self) -> None:
        """Test updating a nonexistent marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"

            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                config_dir,
            ):
                # Add a marketplace first so we have something configured
                runner.invoke(app, ["marketplace", "add", "owner/repo"])

                result = runner.invoke(
                    app, ["marketplace", "update", "nonexistent"]
                )

                assert result.exit_code == 1
                assert "Error" in result.stdout
                assert "not found" in result.stdout

    def test_marketplace_update_empty_registry(self) -> None:
        """Test updating when no marketplaces are configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                result = runner.invoke(app, ["marketplace", "update"])

                assert result.exit_code == 0
                assert "No marketplaces configured" in result.stdout

    def test_marketplace_update_help(self) -> None:
        """Test that help is displayed correctly."""
        result = runner.invoke(app, ["marketplace", "update", "--help"])

        assert result.exit_code == 0
        assert "Update marketplace metadata" in result.stdout
        assert "NAME" in result.stdout


class TestMarketplaceRemove:
    """Tests for 'skillforge marketplace remove' command."""

    def test_marketplace_remove(self) -> None:
        """Test removing a marketplace with force flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                # Add and remove
                runner.invoke(app, ["marketplace", "add", "owner/repo"])
                result = runner.invoke(
                    app, ["marketplace", "remove", "owner/repo", "--force"]
                )

                assert result.exit_code == 0
                assert "Removed marketplace:" in result.stdout
                assert "owner/repo" in result.stdout

                # Verify it's gone
                list_result = runner.invoke(app, ["marketplace", "list"])
                assert "No marketplaces configured" in list_result.stdout

    def test_marketplace_remove_with_confirmation(self) -> None:
        """Test removing a marketplace with confirmation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                # Add marketplace
                runner.invoke(app, ["marketplace", "add", "owner/repo"])

                # Remove with confirmation (answer yes)
                result = runner.invoke(
                    app,
                    ["marketplace", "remove", "owner/repo"],
                    input="y\n",
                )

                assert result.exit_code == 0
                assert "Removed marketplace:" in result.stdout

    def test_marketplace_remove_cancelled(self) -> None:
        """Test cancelling marketplace removal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                # Add marketplace
                runner.invoke(app, ["marketplace", "add", "owner/repo"])

                # Remove with confirmation (answer no) - typer.confirm returns False
                # Use typer's expected "N" input for declining
                result = runner.invoke(
                    app,
                    ["marketplace", "remove", "owner/repo"],
                    input="N\n",
                )

                # When confirmation is declined, typer.Exit(0) is raised
                assert result.exit_code == 0
                assert "Cancelled" in result.stdout

                # Verify it's still there
                list_result = runner.invoke(app, ["marketplace", "list"])
                assert "owner/repo" in list_result.stdout

    def test_marketplace_remove_nonexistent(self) -> None:
        """Test removing a nonexistent marketplace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                result = runner.invoke(
                    app, ["marketplace", "remove", "nonexistent", "--force"]
                )

                assert result.exit_code == 1
                assert "Error" in result.stdout
                assert "not found" in result.stdout

    def test_marketplace_remove_help(self) -> None:
        """Test that help is displayed correctly."""
        result = runner.invoke(app, ["marketplace", "remove", "--help"])

        assert result.exit_code == 0
        assert "Remove a marketplace" in result.stdout
        assert "NAME" in result.stdout
        assert "--force" in result.stdout


class TestMarketplaceHelp:
    """Tests for marketplace help output."""

    def test_marketplace_help(self) -> None:
        """Test that main marketplace help displays correctly."""
        result = runner.invoke(app, ["marketplace", "--help"])

        assert result.exit_code == 0
        assert "Manage skill marketplaces" in result.stdout
        assert "add" in result.stdout
        assert "list" in result.stdout
        assert "update" in result.stdout
        assert "remove" in result.stdout

    def test_marketplace_no_args_shows_help(self) -> None:
        """Test that running marketplace with no args shows usage info."""
        result = runner.invoke(app, ["marketplace"])

        # Typer shows usage/help when no command is given (in output or stderr)
        # Check either stdout or output (which includes both)
        output = result.output if hasattr(result, "output") else result.stdout
        # Depending on typer version, it may show usage or error
        assert "marketplace" in output.lower() or result.exit_code == 0


class TestMarketplaceIntegration:
    """Integration tests using test fixtures."""

    def test_add_local_fixtures_directory(self) -> None:
        """Test adding the fixtures directory as a local marketplace."""
        if not FIXTURES_DIR.exists():
            pytest.skip("Fixtures directory not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                Path(tmpdir),
            ):
                result = runner.invoke(
                    app, ["marketplace", "add", str(FIXTURES_DIR)]
                )

                assert result.exit_code == 0
                assert "Added marketplace:" in result.stdout
                assert "skills" in result.stdout
                assert "Type: local" in result.stdout

    def test_full_workflow(self) -> None:
        """Test complete add -> list -> update -> remove workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "config"

            with patch.object(
                MarketplaceRegistry,
                "DEFAULT_CONFIG_DIR",
                config_dir,
            ):
                # 1. List (empty)
                result = runner.invoke(app, ["marketplace", "list"])
                assert "No marketplaces configured" in result.stdout

                # 2. Add
                result = runner.invoke(
                    app, ["marketplace", "add", "test/marketplace"]
                )
                assert result.exit_code == 0
                assert "Added marketplace:" in result.stdout

                # 3. List (with data)
                result = runner.invoke(app, ["marketplace", "list"])
                assert "test/marketplace" in result.stdout

                # 4. Update (mock fetcher)
                mock_fetcher = MagicMock()
                mock_fetcher.fetch_metadata.return_value = [
                    MarketplaceSkill(
                        name="skill-1",
                        description="First skill",
                        source="github:test/marketplace/skill-1",
                    ),
                    MarketplaceSkill(
                        name="skill-2",
                        description="Second skill",
                        source="github:test/marketplace/skill-2",
                    ),
                ]

                with patch(
                    "skillforge.core.fetcher.MarketplaceFetcher",
                    return_value=mock_fetcher,
                ):
                    result = runner.invoke(
                        app, ["marketplace", "update", "test/marketplace"]
                    )
                    assert "2 skill" in result.stdout
                    assert "skill-1" in result.stdout
                    assert "skill-2" in result.stdout

                # 5. Remove
                result = runner.invoke(
                    app,
                    ["marketplace", "remove", "test/marketplace", "--force"],
                )
                assert "Removed marketplace:" in result.stdout

                # 6. List (empty again)
                result = runner.invoke(app, ["marketplace", "list"])
                assert "No marketplaces configured" in result.stdout
