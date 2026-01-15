"""
Unit tests for ElevenLabs meta-skill rendering functions.

Tests the rendering of the using-skillforge-elevenlabs meta-skill with
dynamically populated available skills lists and RAG query instructions.
"""

from pathlib import Path

import pytest

from skillforge.core.skill import Skill
from skillforge.adapters.elevenlabs.meta_skill import (
    render_elevenlabs_meta_skill,
    format_skills_for_rag,
    get_elevenlabs_meta_skill_content,
    META_SKILL_PATH,
    AVAILABLE_SKILLS_PLACEHOLDER,
)


class TestMetaSkillExists:
    """Tests for ElevenLabs meta-skill file existence."""

    def test_meta_skill_exists(self):
        """Test that the ElevenLabs meta-skill SKILL.md file exists."""
        assert META_SKILL_PATH.exists(), (
            f"ElevenLabs meta-skill file not found at {META_SKILL_PATH}"
        )

    def test_meta_skill_file_is_readable(self):
        """Test that the ElevenLabs meta-skill file can be read."""
        content = META_SKILL_PATH.read_text(encoding="utf-8")
        assert len(content) > 0, "ElevenLabs meta-skill file is empty"


class TestMetaSkillHasTemplateVariable:
    """Tests for template variable presence."""

    def test_meta_skill_has_template_variable(self):
        """Test that the ElevenLabs meta-skill contains the {available_skills} placeholder."""
        content = META_SKILL_PATH.read_text(encoding="utf-8")
        assert AVAILABLE_SKILLS_PLACEHOLDER in content, (
            f"ElevenLabs meta-skill missing {AVAILABLE_SKILLS_PLACEHOLDER} placeholder"
        )

    def test_meta_skill_has_single_template_variable(self):
        """Test that the ElevenLabs meta-skill contains exactly one placeholder."""
        content = META_SKILL_PATH.read_text(encoding="utf-8")
        count = content.count(AVAILABLE_SKILLS_PLACEHOLDER)
        assert count == 1, (
            f"Expected 1 occurrence of {AVAILABLE_SKILLS_PLACEHOLDER}, found {count}"
        )


class TestMetaSkillContent:
    """Tests for ElevenLabs meta-skill content structure."""

    def test_meta_skill_teaches_rag_loading(self):
        """Test that meta-skill teaches RAG-based skill loading, not CLI."""
        content = get_elevenlabs_meta_skill_content()

        # Should teach RAG/Knowledge Base approach
        assert "knowledge base" in content.lower(), (
            "ElevenLabs meta-skill should mention knowledge base"
        )
        assert "SKILL:" in content, (
            "ElevenLabs meta-skill should include SKILL: query pattern"
        )

        # Should NOT mention CLI commands
        assert "skillforge read" not in content, (
            "ElevenLabs meta-skill should not mention CLI commands"
        )
        assert "bash" not in content.lower(), (
            "ElevenLabs meta-skill should not mention bash"
        )

    def test_meta_skill_has_frontmatter(self):
        """Test that ElevenLabs meta-skill content includes frontmatter."""
        content = get_elevenlabs_meta_skill_content()

        # Should start with frontmatter delimiter
        assert content.startswith("---")

        # Should contain key frontmatter fields
        assert "name: using-skillforge-elevenlabs" in content
        assert "description:" in content

    def test_meta_skill_has_key_sections(self):
        """Test that ElevenLabs meta-skill has required sections."""
        content = get_elevenlabs_meta_skill_content()

        assert "# Using Skills" in content
        assert "## Before Acting on Complex Situations" in content
        assert "## Important Guidelines" in content
        assert "## Available Skills" in content


class TestFormatSkillsForRag:
    """Tests for format_skills_for_rag function."""

    def test_format_skills_includes_query_instruction(self):
        """Test that formatted skills include RAG query instructions."""
        skill = Skill(
            name="rapid-interviewing",
            description="Conduct rapid discovery interviews",
            instructions="# Rapid Interviewing\n\nInstructions here.",
            path=Path("./skills/rapid-interviewing"),
        )
        result = format_skills_for_rag([skill])

        # Should include the skill name and description
        assert "rapid-interviewing" in result
        assert "Conduct rapid discovery interviews" in result

        # Should include RAG query instruction
        assert 'Query: "SKILL: rapid-interviewing"' in result

    def test_format_skills_empty_list(self):
        """Test formatting an empty skills list."""
        result = format_skills_for_rag([])
        assert result == "(No skills available)"

    def test_format_skills_multiple(self):
        """Test formatting multiple skills."""
        skills = [
            Skill(
                name="rapid-interviewing",
                description="Conduct rapid discovery interviews",
                instructions="",
                path=Path("./skills/rapid-interviewing"),
            ),
            Skill(
                name="goal-extraction",
                description="Extract goals from conversations",
                instructions="",
                path=Path("./skills/goal-extraction"),
            ),
        ]
        result = format_skills_for_rag(skills)

        # Check all skills are present with query instructions
        assert "rapid-interviewing" in result
        assert 'Query: "SKILL: rapid-interviewing"' in result
        assert "goal-extraction" in result
        assert 'Query: "SKILL: goal-extraction"' in result

        # Check format (each skill on its own line)
        lines = result.strip().split("\n")
        assert len(lines) == 2

        # Each line should start with markdown list format
        for line in lines:
            assert line.startswith("- **")

    def test_format_skills_without_description(self):
        """Test formatting a skill with no description."""
        skill = Skill(
            name="no-description-skill",
            description="",
            instructions="",
            path=Path("./skills/no-description"),
        )
        result = format_skills_for_rag([skill])

        assert "no-description-skill" in result
        assert "(no description)" in result
        assert 'Query: "SKILL: no-description-skill"' in result


class TestRenderElevenlabsMetaSkill:
    """Tests for render_elevenlabs_meta_skill function."""

    def test_render_meta_skill_replaces_variable(self):
        """Test that render_elevenlabs_meta_skill replaces the placeholder."""
        skills = [
            Skill(
                name="test-skill",
                description="A test skill",
                instructions="",
                path=Path("./skills/test-skill"),
            ),
        ]
        result = render_elevenlabs_meta_skill(skills)

        # Placeholder should be replaced
        assert AVAILABLE_SKILLS_PLACEHOLDER not in result

        # Skill should be present with query instruction
        assert "test-skill" in result
        assert "A test skill" in result
        assert 'Query: "SKILL: test-skill"' in result

    def test_render_with_empty_skills(self):
        """Test rendering ElevenLabs meta-skill with no available skills."""
        result = render_elevenlabs_meta_skill([])

        # Placeholder should be replaced
        assert AVAILABLE_SKILLS_PLACEHOLDER not in result

        # Should show no skills message
        assert "(No skills available)" in result

    def test_render_preserves_structure(self):
        """Test that rendering preserves the overall document structure."""
        skills = [
            Skill(
                name="example-skill",
                description="An example",
                instructions="",
                path=Path("./skills/example"),
            ),
        ]
        result = render_elevenlabs_meta_skill(skills)

        # Should preserve all sections
        assert "# Using Skills" in result
        assert "## Before Acting on Complex Situations" in result
        assert "## Important Guidelines" in result
        assert "## Available Skills" in result

        # Should preserve frontmatter
        assert result.startswith("---")

    def test_render_with_multiple_skills(self):
        """Test rendering ElevenLabs meta-skill with multiple skills."""
        skills = [
            Skill(name="skill-a", description="First skill", instructions="", path=Path("./a")),
            Skill(name="skill-b", description="Second skill", instructions="", path=Path("./b")),
        ]
        result = render_elevenlabs_meta_skill(skills)

        assert "skill-a" in result
        assert "skill-b" in result
        assert "First skill" in result
        assert "Second skill" in result
        assert 'Query: "SKILL: skill-a"' in result
        assert 'Query: "SKILL: skill-b"' in result


class TestElevenlabsMetaSkillIntegration:
    """Integration tests for ElevenLabs meta-skill rendering."""

    def test_full_rendering_workflow(self):
        """Test the complete ElevenLabs meta-skill rendering workflow."""
        # 1. Get raw template
        template = get_elevenlabs_meta_skill_content()
        assert AVAILABLE_SKILLS_PLACEHOLDER in template

        # 2. Create skills list
        skills = [
            Skill(
                name="rapid-interviewing",
                description="Conduct rapid discovery interviews",
                instructions="# Rapid Interviewing...",
                path=Path("./agents/coach/skills/rapid-interviewing"),
                allowed_tools=["Bash", "Read"],
                version="1.0.0",
            ),
            Skill(
                name="goal-extraction",
                description="Extract goals from conversations",
                instructions="# Goal Extraction...",
                path=Path("./agents/coach/skills/goal-extraction"),
            ),
        ]

        # 3. Format skills list with RAG instructions
        skills_list = format_skills_for_rag(skills)
        assert "rapid-interviewing" in skills_list
        assert "goal-extraction" in skills_list
        assert 'Query: "SKILL: rapid-interviewing"' in skills_list
        assert 'Query: "SKILL: goal-extraction"' in skills_list

        # 4. Render complete meta-skill
        rendered = render_elevenlabs_meta_skill(skills)
        assert AVAILABLE_SKILLS_PLACEHOLDER not in rendered
        assert "rapid-interviewing" in rendered
        assert "goal-extraction" in rendered
        assert 'Query: "SKILL: rapid-interviewing"' in rendered

        # 5. Verify it's suitable for ElevenLabs Knowledge Base
        # (should use RAG approach, not CLI)
        assert "knowledge base" in rendered.lower()
        assert "skillforge read" not in rendered
