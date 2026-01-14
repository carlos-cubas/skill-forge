"""
Unit tests for meta-skill rendering functions.

Tests the rendering of the using-skillforge meta-skill with
dynamically populated available skills lists.
"""

from pathlib import Path

import pytest

from skillforge.core.skill import Skill
from skillforge.core.meta_skill import (
    render_meta_skill,
    format_skills_list,
    get_meta_skill_content,
    META_SKILL_PATH,
    AVAILABLE_SKILLS_PLACEHOLDER,
)


class TestMetaSkillFileExists:
    """Tests for meta-skill file existence."""

    def test_meta_skill_file_exists(self):
        """Test that the meta-skill SKILL.md file exists."""
        assert META_SKILL_PATH.exists(), (
            f"Meta-skill file not found at {META_SKILL_PATH}"
        )

    def test_meta_skill_file_is_readable(self):
        """Test that the meta-skill file can be read."""
        content = META_SKILL_PATH.read_text(encoding="utf-8")
        assert len(content) > 0, "Meta-skill file is empty"


class TestMetaSkillHasTemplateVariable:
    """Tests for template variable presence."""

    def test_meta_skill_has_template_variable(self):
        """Test that the meta-skill contains the {available_skills} placeholder."""
        content = META_SKILL_PATH.read_text(encoding="utf-8")
        assert AVAILABLE_SKILLS_PLACEHOLDER in content, (
            f"Meta-skill missing {AVAILABLE_SKILLS_PLACEHOLDER} placeholder"
        )

    def test_meta_skill_has_single_template_variable(self):
        """Test that the meta-skill contains exactly one placeholder."""
        content = META_SKILL_PATH.read_text(encoding="utf-8")
        count = content.count(AVAILABLE_SKILLS_PLACEHOLDER)
        assert count == 1, (
            f"Expected 1 occurrence of {AVAILABLE_SKILLS_PLACEHOLDER}, found {count}"
        )


class TestFormatSkillsList:
    """Tests for format_skills_list function."""

    def test_format_skills_list_empty(self):
        """Test formatting an empty skills list."""
        result = format_skills_list([])
        assert result == "(No skills available)"

    def test_format_skills_list_single_skill(self):
        """Test formatting a single skill."""
        skill = Skill(
            name="rapid-interviewing",
            description="Conduct rapid discovery interviews",
            instructions="# Rapid Interviewing\n\nInstructions here.",
            path=Path("./skills/rapid-interviewing"),
        )
        result = format_skills_list([skill])

        assert "rapid-interviewing" in result
        assert "Conduct rapid discovery interviews" in result
        assert "skills/rapid-interviewing" in result
        assert result.startswith("- **rapid-interviewing**:")

    def test_format_skills_list_multiple_skills(self):
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
            Skill(
                name="profiling",
                description="Build user profiles",
                instructions="",
                path=Path("./skills/profiling"),
            ),
        ]
        result = format_skills_list(skills)

        # Check all skills are present
        assert "rapid-interviewing" in result
        assert "goal-extraction" in result
        assert "profiling" in result

        # Check format (each skill on its own line)
        lines = result.strip().split("\n")
        assert len(lines) == 3

        # Each line should start with markdown list format
        for line in lines:
            assert line.startswith("- **")

    def test_format_skills_list_skill_without_description(self):
        """Test formatting a skill with no description."""
        skill = Skill(
            name="no-description-skill",
            description="",
            instructions="",
            path=Path("./skills/no-description"),
        )
        result = format_skills_list([skill])

        assert "no-description-skill" in result
        assert "(no description)" in result

    def test_format_skills_list_preserves_order(self):
        """Test that skills are formatted in the order provided."""
        skills = [
            Skill(name="zebra", description="Z skill", instructions="", path=Path("./z")),
            Skill(name="alpha", description="A skill", instructions="", path=Path("./a")),
            Skill(name="middle", description="M skill", instructions="", path=Path("./m")),
        ]
        result = format_skills_list(skills)
        lines = result.strip().split("\n")

        assert "zebra" in lines[0]
        assert "alpha" in lines[1]
        assert "middle" in lines[2]


class TestGetMetaSkillContent:
    """Tests for get_meta_skill_content function."""

    def test_get_meta_skill_content(self):
        """Test getting raw meta-skill content."""
        content = get_meta_skill_content()

        # Should be non-empty
        assert len(content) > 0

        # Should contain expected sections
        assert "# Using SkillForge Skills" in content
        assert "## Available Skills" in content
        assert AVAILABLE_SKILLS_PLACEHOLDER in content

    def test_get_meta_skill_content_has_frontmatter(self):
        """Test that meta-skill content includes frontmatter."""
        content = get_meta_skill_content()

        # Should start with frontmatter delimiter
        assert content.startswith("---")

        # Should contain key frontmatter fields
        assert "name: using-skillforge" in content
        assert "description:" in content

    def test_get_meta_skill_content_has_instructions(self):
        """Test that meta-skill content includes all key instructions."""
        content = get_meta_skill_content()

        # Key sections from the template
        assert "## Before Starting Any Task" in content
        assert "## How to Load a Skill" in content
        assert "## Important Guidelines" in content
        assert "## Common Mistakes to Avoid" in content
        assert "skillforge read" in content


class TestRenderMetaSkill:
    """Tests for render_meta_skill function."""

    def test_render_meta_skill_replaces_variable(self):
        """Test that render_meta_skill replaces the placeholder."""
        skills = [
            Skill(
                name="test-skill",
                description="A test skill",
                instructions="",
                path=Path("./skills/test-skill"),
            ),
        ]
        result = render_meta_skill(skills)

        # Placeholder should be replaced
        assert AVAILABLE_SKILLS_PLACEHOLDER not in result

        # Skill should be present
        assert "test-skill" in result
        assert "A test skill" in result

    def test_render_meta_skill_with_empty_skills(self):
        """Test rendering meta-skill with no available skills."""
        result = render_meta_skill([])

        # Placeholder should be replaced
        assert AVAILABLE_SKILLS_PLACEHOLDER not in result

        # Should show no skills message
        assert "(No skills available)" in result

    def test_render_meta_skill_preserves_structure(self):
        """Test that rendering preserves the overall document structure."""
        skills = [
            Skill(
                name="example-skill",
                description="An example",
                instructions="",
                path=Path("./skills/example"),
            ),
        ]
        result = render_meta_skill(skills)

        # Should preserve all sections
        assert "# Using SkillForge Skills" in result
        assert "## Before Starting Any Task" in result
        assert "## How to Load a Skill" in result
        assert "## Important Guidelines" in result
        assert "## Common Mistakes to Avoid" in result
        assert "## Available Skills" in result

        # Should preserve frontmatter
        assert result.startswith("---")

    def test_render_meta_skill_with_multiple_skills(self):
        """Test rendering meta-skill with multiple skills."""
        skills = [
            Skill(name="skill-a", description="First skill", instructions="", path=Path("./a")),
            Skill(name="skill-b", description="Second skill", instructions="", path=Path("./b")),
        ]
        result = render_meta_skill(skills)

        assert "skill-a" in result
        assert "skill-b" in result
        assert "First skill" in result
        assert "Second skill" in result

    def test_render_meta_skill_with_complex_paths(self):
        """Test rendering handles complex file paths."""
        skill = Skill(
            name="nested-skill",
            description="A deeply nested skill",
            instructions="",
            path=Path("/Users/test/projects/my-app/agents/coach/skills/nested-skill"),
        )
        result = render_meta_skill([skill])

        assert "nested-skill" in result
        assert "agents/coach/skills/nested-skill" in result


class TestMetaSkillIntegration:
    """Integration tests for meta-skill rendering."""

    def test_full_rendering_workflow(self):
        """Test the complete meta-skill rendering workflow."""
        # 1. Get raw template
        template = get_meta_skill_content()
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

        # 3. Format skills list
        skills_list = format_skills_list(skills)
        assert "rapid-interviewing" in skills_list
        assert "goal-extraction" in skills_list

        # 4. Render complete meta-skill
        rendered = render_meta_skill(skills)
        assert AVAILABLE_SKILLS_PLACEHOLDER not in rendered
        assert "rapid-interviewing" in rendered
        assert "goal-extraction" in rendered

        # 5. Verify it's valid for injection into agent prompt
        # (should be readable markdown with clear instructions)
        assert "Before Starting Any Task" in rendered
        assert "skillforge read" in rendered
