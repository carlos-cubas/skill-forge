"""
Unit tests for Skill data class, SKILL.md parser, and SkillLoader.
"""

import tempfile
from pathlib import Path

import pytest

from skillforge.core.skill import Skill
from skillforge.core.loader import SkillLoader, SkillNotFoundError
from skillforge.utils.markdown import (
    parse_skill_md,
    _split_frontmatter,
    SkillParseError,
)


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "skills"


class TestSkillDataClass:
    """Tests for the Skill dataclass."""

    def test_skill_creation_with_required_fields(self):
        """Test creating a Skill with only required fields."""
        skill = Skill(
            name="test-skill",
            description="A test skill",
            instructions="# Test\n\nInstructions here.",
            path=Path("/tmp/test-skill"),
        )

        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert skill.instructions == "# Test\n\nInstructions here."
        assert skill.path == Path("/tmp/test-skill")
        assert skill.allowed_tools == []
        assert skill.version is None
        assert skill.author is None

    def test_skill_creation_with_all_fields(self):
        """Test creating a Skill with all fields."""
        skill = Skill(
            name="complete-skill",
            description="A complete skill with all fields",
            instructions="# Complete\n\nAll fields set.",
            path=Path("/tmp/complete-skill"),
            allowed_tools=["Bash", "Read"],
            version="1.0.0",
            author="Test Author",
        )

        assert skill.name == "complete-skill"
        assert skill.description == "A complete skill with all fields"
        assert skill.allowed_tools == ["Bash", "Read"]
        assert skill.version == "1.0.0"
        assert skill.author == "Test Author"

    def test_has_tools_property_without_tools(self):
        """Test has_tools returns False when no tools.py exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill = Skill(
                name="no-tools",
                description="No tools",
                instructions="",
                path=Path(tmpdir),
            )
            assert skill.has_tools is False

    def test_has_tools_property_with_tools(self):
        """Test has_tools returns True when tools.py exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_path = Path(tmpdir) / "tools.py"
            tools_path.write_text("# tools")

            skill = Skill(
                name="with-tools",
                description="Has tools",
                instructions="",
                path=Path(tmpdir),
            )
            assert skill.has_tools is True

    def test_tools_module_path_property_without_tools(self):
        """Test tools_module_path returns None when no tools.py exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill = Skill(
                name="no-tools",
                description="No tools",
                instructions="",
                path=Path(tmpdir),
            )
            assert skill.tools_module_path is None

    def test_tools_module_path_property_with_tools(self):
        """Test tools_module_path returns path when tools.py exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_path = Path(tmpdir) / "tools.py"
            tools_path.write_text("# tools")

            skill = Skill(
                name="with-tools",
                description="Has tools",
                instructions="",
                path=Path(tmpdir),
            )
            assert skill.tools_module_path == tools_path

    def test_skill_repr(self):
        """Test Skill string representation."""
        skill = Skill(
            name="test-skill",
            description="A test skill",
            instructions="# Test",
            path=Path("/tmp/test-skill"),
        )
        repr_str = repr(skill)
        assert "test-skill" in repr_str
        assert "A test skill" in repr_str


class TestSplitFrontmatter:
    """Tests for the _split_frontmatter function."""

    def test_content_with_frontmatter(self):
        """Test splitting content with valid frontmatter."""
        content = """---
name: test
description: A test
---

# Body Content

Some text here.
"""
        frontmatter, body = _split_frontmatter(content)

        assert frontmatter == "name: test\ndescription: A test"
        assert body.startswith("# Body Content")
        assert "Some text here." in body

    def test_content_without_frontmatter(self):
        """Test content without frontmatter."""
        content = """# No Frontmatter

Just body content.
"""
        frontmatter, body = _split_frontmatter(content)

        assert frontmatter is None
        assert body == content

    def test_content_with_only_opening_delimiter(self):
        """Test content with only opening --- but no closing."""
        content = """---
name: test
# This looks like frontmatter but isn't closed
"""
        frontmatter, body = _split_frontmatter(content)

        # Should treat as no frontmatter
        assert frontmatter is None
        assert body == content

    def test_empty_frontmatter(self):
        """Test empty frontmatter section."""
        content = "---\n---\n\n# Body\n"
        frontmatter, body = _split_frontmatter(content)

        # Empty frontmatter returns empty string
        assert frontmatter == ""
        assert body.strip() == "# Body"

    def test_frontmatter_with_complex_yaml(self):
        """Test frontmatter with lists and nested values."""
        content = """---
name: complex
allowed-tools:
  - Bash
  - Read
  - Write
---

# Complex skill
"""
        frontmatter, body = _split_frontmatter(content)

        assert "name: complex" in frontmatter
        assert "allowed-tools:" in frontmatter
        assert "- Bash" in frontmatter


class TestParseSkillMd:
    """Tests for the parse_skill_md function."""

    def test_parse_complete_skill(self):
        """Test parsing a skill with full frontmatter."""
        skill_path = FIXTURES_DIR / "complete-skill"
        skill = parse_skill_md(skill_path)

        assert skill.name == "rapid-interviewing"
        assert "rapid discovery interviews" in skill.description
        assert skill.allowed_tools == ["Bash", "Read", "Write"]
        assert skill.version == "1.0.0"
        assert skill.author == "SkillForge Team"
        assert "# Rapid Interviewing Skill" in skill.instructions
        assert skill.path == skill_path.resolve()

    def test_parse_minimal_skill(self):
        """Test parsing a skill with no frontmatter."""
        skill_path = FIXTURES_DIR / "minimal-skill"
        skill = parse_skill_md(skill_path)

        # Should use directory name as skill name
        assert skill.name == "minimal-skill"
        assert skill.description == ""
        assert skill.allowed_tools == []
        assert skill.version is None
        assert skill.author is None
        assert "# Minimal Skill" in skill.instructions

    def test_parse_skill_with_tools(self):
        """Test parsing a skill that has tools.py."""
        skill_path = FIXTURES_DIR / "skill-with-tools"
        skill = parse_skill_md(skill_path)

        assert skill.name == "data-analysis"
        assert skill.has_tools is True
        assert skill.tools_module_path is not None
        assert skill.tools_module_path.name == "tools.py"

    def test_parse_nonexistent_directory(self):
        """Test parsing a non-existent directory."""
        with pytest.raises(FileNotFoundError):
            parse_skill_md(Path("/nonexistent/path"))

    def test_parse_file_instead_of_directory(self):
        """Test parsing when given a file path instead of directory."""
        with tempfile.NamedTemporaryFile() as tmpfile:
            with pytest.raises(SkillParseError, match="Expected directory"):
                parse_skill_md(Path(tmpfile.name))

    def test_parse_directory_without_skill_md(self):
        """Test parsing a directory without SKILL.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(SkillParseError, match="SKILL.md not found"):
                parse_skill_md(Path(tmpdir))

    def test_parse_skill_with_invalid_yaml(self):
        """Test parsing a skill with invalid YAML frontmatter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = Path(tmpdir) / "SKILL.md"
            skill_md.write_text("""---
name: test
invalid: yaml: syntax:
---

# Body
""")
            with pytest.raises(SkillParseError, match="Invalid YAML"):
                parse_skill_md(Path(tmpdir))

    def test_parse_skill_with_underscore_allowed_tools(self):
        """Test parsing accepts allowed_tools with underscore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = Path(tmpdir) / "SKILL.md"
            skill_md.write_text("""---
name: underscore-test
allowed_tools:
  - Bash
---

# Body
""")
            skill = parse_skill_md(Path(tmpdir))
            assert skill.allowed_tools == ["Bash"]

    def test_parse_skill_with_string_allowed_tools(self):
        """Test parsing handles single tool as string."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_md = Path(tmpdir) / "SKILL.md"
            skill_md.write_text("""---
name: string-tool
allowed-tools: Bash
---

# Body
""")
            skill = parse_skill_md(Path(tmpdir))
            assert skill.allowed_tools == ["Bash"]


class TestSkillLoader:
    """Tests for the SkillLoader class."""

    def test_loader_initialization(self):
        """Test SkillLoader initialization."""
        loader = SkillLoader(["./skills/*", "./agents/**/skills/*"])

        assert loader.skill_paths == ["./skills/*", "./agents/**/skills/*"]
        assert loader.skills == {}

    def test_discover_skills(self):
        """Test discovering skills from fixtures directory."""
        loader = SkillLoader(
            [str(FIXTURES_DIR / "*")],
            base_path=FIXTURES_DIR.parent,
        )
        skills = loader.discover()

        assert len(skills) == 3
        assert "rapid-interviewing" in skills
        assert "minimal-skill" in skills
        assert "data-analysis" in skills

    def test_get_skill_by_name(self):
        """Test getting a specific skill by name."""
        loader = SkillLoader(
            [str(FIXTURES_DIR / "*")],
            base_path=FIXTURES_DIR.parent,
        )

        skill = loader.get("rapid-interviewing")

        assert skill.name == "rapid-interviewing"
        assert skill.version == "1.0.0"

    def test_get_nonexistent_skill(self):
        """Test getting a skill that doesn't exist."""
        loader = SkillLoader(
            [str(FIXTURES_DIR / "*")],
            base_path=FIXTURES_DIR.parent,
        )

        with pytest.raises(SkillNotFoundError, match="not found"):
            loader.get("nonexistent-skill")

    def test_get_auto_discovers(self):
        """Test that get() auto-discovers if not already done."""
        loader = SkillLoader(
            [str(FIXTURES_DIR / "*")],
            base_path=FIXTURES_DIR.parent,
        )

        # Don't call discover() explicitly
        skill = loader.get("rapid-interviewing")

        assert skill.name == "rapid-interviewing"

    def test_list_skills(self):
        """Test listing all skill names."""
        loader = SkillLoader(
            [str(FIXTURES_DIR / "*")],
            base_path=FIXTURES_DIR.parent,
        )

        skill_names = loader.list_skills()

        assert len(skill_names) == 3
        assert skill_names == sorted(skill_names)  # Should be sorted
        assert "data-analysis" in skill_names

    def test_reload_skills(self):
        """Test reloading skills clears cache and re-discovers."""
        loader = SkillLoader(
            [str(FIXTURES_DIR / "*")],
            base_path=FIXTURES_DIR.parent,
        )

        # Initial discovery
        skills1 = loader.discover()
        count1 = len(skills1)

        # Reload
        skills2 = loader.reload()
        count2 = len(skills2)

        assert count1 == count2

    def test_discover_with_invalid_pattern(self):
        """Test discover with pattern matching no directories."""
        loader = SkillLoader(
            ["/nonexistent/path/*"],
        )

        skills = loader.discover()

        assert len(skills) == 0

    def test_discover_skips_directories_without_skill_md(self):
        """Test that directories without SKILL.md are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a directory without SKILL.md
            empty_dir = Path(tmpdir) / "empty-skill"
            empty_dir.mkdir()

            # Create a valid skill directory
            valid_dir = Path(tmpdir) / "valid-skill"
            valid_dir.mkdir()
            (valid_dir / "SKILL.md").write_text("# Valid Skill")

            loader = SkillLoader(
                [str(Path(tmpdir) / "*")],
                base_path=Path(tmpdir),
            )
            skills = loader.discover()

            assert len(skills) == 1
            assert "valid-skill" in skills

    def test_discover_handles_duplicate_names(self):
        """Test that duplicate skill names are handled (first encountered wins)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two skills with same name in frontmatter
            dir1 = Path(tmpdir) / "skill1"
            dir1.mkdir()
            (dir1 / "SKILL.md").write_text("""---
name: duplicate-name
description: First occurrence
---

# First
""")

            dir2 = Path(tmpdir) / "skill2"
            dir2.mkdir()
            (dir2 / "SKILL.md").write_text("""---
name: duplicate-name
description: Second occurrence
---

# Second
""")

            loader = SkillLoader(
                [str(Path(tmpdir) / "*")],
                base_path=Path(tmpdir),
            )
            skills = loader.discover()

            # Only one should be loaded (first encountered wins, but glob order is not guaranteed)
            assert len(skills) == 1
            assert "duplicate-name" in skills
            # Verify one of the two descriptions was kept
            assert skills["duplicate-name"].description in [
                "First occurrence",
                "Second occurrence",
            ]


class TestSkillLoaderWithRelativePaths:
    """Tests for SkillLoader with relative path patterns."""

    def test_relative_glob_pattern(self):
        """Test that relative patterns work correctly."""
        # Use the fixtures directory as base
        loader = SkillLoader(
            ["skills/*"],
            base_path=FIXTURES_DIR.parent,
        )

        skills = loader.discover()

        assert len(skills) == 3

    def test_recursive_glob_pattern(self):
        """Test recursive glob patterns with **."""
        # Create a nested structure
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "level1" / "level2" / "my-skill"
            nested_dir.mkdir(parents=True)
            (nested_dir / "SKILL.md").write_text("""---
name: nested-skill
---

# Nested Skill
""")

            loader = SkillLoader(
                ["**/*"],
                base_path=Path(tmpdir),
            )
            skills = loader.discover()

            assert "nested-skill" in skills
