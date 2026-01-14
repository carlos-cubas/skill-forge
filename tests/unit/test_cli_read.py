"""
Unit tests for the 'skillforge read' CLI command.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from skillforge.cli.main import app


runner = CliRunner()

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "skills"


class TestReadCommand:
    """Tests for the 'skillforge read' command."""

    def test_read_existing_skill(self):
        """Test reading an existing skill successfully."""
        result = runner.invoke(
            app, ["read", "rapid-interviewing", "--from", str(FIXTURES_DIR)]
        )

        assert result.exit_code == 0
        assert "# Rapid Interviewing Skill" in result.stdout
        assert "When to Use" in result.stdout
        assert "How to Use" in result.stdout

    def test_read_nonexistent_skill(self):
        """Test reading a nonexistent skill returns exit code 1."""
        result = runner.invoke(
            app, ["read", "nonexistent-skill", "--from", str(FIXTURES_DIR)]
        )

        assert result.exit_code == 1
        assert "Error" in result.stdout
        assert "nonexistent-skill" in result.stdout
        assert "not found" in result.stdout

    def test_read_outputs_instructions_only(self):
        """Test that output contains instructions without frontmatter."""
        result = runner.invoke(
            app, ["read", "rapid-interviewing", "--from", str(FIXTURES_DIR)]
        )

        assert result.exit_code == 0
        # Should NOT contain frontmatter markers or metadata
        assert "---" not in result.stdout
        assert "name:" not in result.stdout
        assert "description:" not in result.stdout
        assert "allowed-tools:" not in result.stdout
        assert "version:" not in result.stdout
        # Should contain actual instructions
        assert "# Rapid Interviewing Skill" in result.stdout

    def test_read_from_short_option(self):
        """Test that -f alias works for --from option."""
        result = runner.invoke(
            app, ["read", "rapid-interviewing", "-f", str(FIXTURES_DIR)]
        )

        assert result.exit_code == 0
        assert "# Rapid Interviewing Skill" in result.stdout

    def test_read_help(self):
        """Test that help text is displayed correctly."""
        result = runner.invoke(app, ["read", "--help"])

        assert result.exit_code == 0
        assert "SKILL_NAME" in result.stdout
        assert "--from" in result.stdout
        assert "-f" in result.stdout
        assert "Path to search for skill" in result.stdout
        assert "Name of the skill to read" in result.stdout

    def test_read_minimal_skill(self):
        """Test reading a minimal skill (no frontmatter)."""
        result = runner.invoke(
            app, ["read", "minimal-skill", "--from", str(FIXTURES_DIR)]
        )

        assert result.exit_code == 0
        assert "# Minimal Skill" in result.stdout

    def test_read_skill_with_tools(self):
        """Test reading a skill that has tools.py."""
        result = runner.invoke(
            app, ["read", "data-analysis", "--from", str(FIXTURES_DIR)]
        )

        assert result.exit_code == 0
        # Verify instructions are returned (content depends on fixture)
        assert result.stdout.strip() != ""

    def test_read_from_nonexistent_path(self):
        """Test reading from a path that doesn't exist."""
        result = runner.invoke(
            app, ["read", "any-skill", "--from", "/nonexistent/path"]
        )

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_read_missing_required_argument(self):
        """Test that missing skill_name argument causes error."""
        result = runner.invoke(app, ["read", "--from", str(FIXTURES_DIR)])

        assert result.exit_code != 0

    def test_read_missing_from_option(self):
        """Test that missing --from option causes error."""
        result = runner.invoke(app, ["read", "rapid-interviewing"])

        assert result.exit_code != 0
