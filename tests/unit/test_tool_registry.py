"""
Unit tests for ToolRegistry.

Tests for registering shared tools, loading skill-bundled tools,
and getting tools for skills based on allowed-tools configuration.
"""

import tempfile
from pathlib import Path

import pytest

from skillforge.core.registry import ToolRegistry
from skillforge.core.skill import Skill


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "skills"


class TestRegisterSharedTool:
    """Tests for registering shared tools."""

    def test_register_shared_tool(self):
        """Test registering a shared tool."""
        registry = ToolRegistry()

        def my_tool():
            pass

        registry.register_shared_tool("my_tool", my_tool)

        assert "my_tool" in registry.shared_tools
        assert registry.shared_tools["my_tool"] is my_tool

    def test_register_multiple_shared_tools(self):
        """Test registering multiple shared tools."""
        registry = ToolRegistry()

        def tool_a():
            pass

        def tool_b():
            pass

        registry.register_shared_tool("tool_a", tool_a)
        registry.register_shared_tool("tool_b", tool_b)

        assert len(registry.shared_tools) == 2
        assert "tool_a" in registry.shared_tools
        assert "tool_b" in registry.shared_tools

    def test_register_shared_tool_overwrites(self):
        """Test that registering same name overwrites previous tool."""
        registry = ToolRegistry()

        def tool_v1():
            return 1

        def tool_v2():
            return 2

        registry.register_shared_tool("tool", tool_v1)
        registry.register_shared_tool("tool", tool_v2)

        assert registry.shared_tools["tool"] is tool_v2


class TestRegisterSkillTools:
    """Tests for registering skill-bundled tools."""

    def test_register_skill_tools(self):
        """Test registering skill-bundled tools."""
        registry = ToolRegistry()

        def skill_tool_1():
            pass

        def skill_tool_2():
            pass

        tools = [skill_tool_1, skill_tool_2]
        registry.register_skill_tools("my-skill", tools)

        assert "my-skill" in registry.skill_tools
        assert len(registry.skill_tools["my-skill"]) == 2
        assert skill_tool_1 in registry.skill_tools["my-skill"]
        assert skill_tool_2 in registry.skill_tools["my-skill"]

    def test_register_skill_tools_empty_list(self):
        """Test registering empty tools list for a skill."""
        registry = ToolRegistry()

        registry.register_skill_tools("no-tools-skill", [])

        assert "no-tools-skill" in registry.skill_tools
        assert registry.skill_tools["no-tools-skill"] == []


class TestLoadSkillTools:
    """Tests for loading tools from a skill's tools.py file."""

    def test_load_skill_tools_from_file(self):
        """Test loading tools from tools.py."""
        registry = ToolRegistry()
        skill_path = FIXTURES_DIR / "skill-with-tools"

        tools = registry.load_skill_tools(skill_path)

        assert len(tools) == 2
        # Verify the functions were loaded correctly
        tool_names = [t.__name__ for t in tools]
        assert "analyze_csv" in tool_names
        assert "generate_chart" in tool_names

    def test_load_skill_tools_no_file(self):
        """Test loading when no tools.py exists."""
        registry = ToolRegistry()
        skill_path = FIXTURES_DIR / "minimal-skill"

        tools = registry.load_skill_tools(skill_path)

        assert tools == []

    def test_load_skill_tools_no_tools_export(self):
        """Test loading when tools.py exists but has no TOOLS export."""
        registry = ToolRegistry()

        with tempfile.TemporaryDirectory() as tmpdir:
            tools_path = Path(tmpdir) / "tools.py"
            tools_path.write_text("""
def some_function():
    pass

# No TOOLS export
""")

            tools = registry.load_skill_tools(Path(tmpdir))

            assert tools == []

    def test_load_skill_tools_function_callable(self):
        """Test that loaded tools are callable."""
        registry = ToolRegistry()
        skill_path = FIXTURES_DIR / "skill-with-tools"

        tools = registry.load_skill_tools(skill_path)

        for tool in tools:
            assert callable(tool)

    def test_load_skill_tools_from_nonexistent_path(self):
        """Test loading from non-existent path returns empty list."""
        registry = ToolRegistry()

        tools = registry.load_skill_tools(Path("/nonexistent/path"))

        assert tools == []


class TestGetToolsForSkill:
    """Tests for getting all tools a skill can access."""

    def test_get_tools_for_skill_shared_only(self):
        """Test getting tools when skill only uses shared tools."""
        registry = ToolRegistry()

        def bash_tool():
            pass

        def read_tool():
            pass

        registry.register_shared_tool("Bash", bash_tool)
        registry.register_shared_tool("Read", read_tool)

        skill = Skill(
            name="shared-only",
            description="Uses shared tools",
            instructions="# Instructions",
            path=Path("/tmp/shared-only"),
            allowed_tools=["Bash", "Read"],
        )

        tools = registry.get_tools_for_skill(skill)

        assert len(tools) == 2
        assert bash_tool in tools
        assert read_tool in tools

    def test_get_tools_for_skill_bundled_only(self):
        """Test getting tools when skill only has bundled tools."""
        registry = ToolRegistry()

        def bundled_tool():
            pass

        registry.register_skill_tools("bundled-skill", [bundled_tool])

        skill = Skill(
            name="bundled-skill",
            description="Has bundled tools",
            instructions="# Instructions",
            path=Path("/tmp/bundled-skill"),
            allowed_tools=[],  # No shared tools
        )

        tools = registry.get_tools_for_skill(skill)

        assert len(tools) == 1
        assert bundled_tool in tools

    def test_get_tools_for_skill_combined(self):
        """Test getting both shared and bundled tools."""
        registry = ToolRegistry()

        def bash_tool():
            pass

        def bundled_tool():
            pass

        registry.register_shared_tool("Bash", bash_tool)
        registry.register_skill_tools("combined-skill", [bundled_tool])

        skill = Skill(
            name="combined-skill",
            description="Has both types",
            instructions="# Instructions",
            path=Path("/tmp/combined-skill"),
            allowed_tools=["Bash"],
        )

        tools = registry.get_tools_for_skill(skill)

        assert len(tools) == 2
        assert bash_tool in tools
        assert bundled_tool in tools

    def test_tools_respects_allowed_tools(self):
        """Test that only allowed shared tools are returned."""
        registry = ToolRegistry()

        def bash_tool():
            pass

        def read_tool():
            pass

        def write_tool():
            pass

        registry.register_shared_tool("Bash", bash_tool)
        registry.register_shared_tool("Read", read_tool)
        registry.register_shared_tool("Write", write_tool)

        skill = Skill(
            name="limited-skill",
            description="Limited tools",
            instructions="# Instructions",
            path=Path("/tmp/limited-skill"),
            allowed_tools=["Bash"],  # Only Bash allowed
        )

        tools = registry.get_tools_for_skill(skill)

        assert len(tools) == 1
        assert bash_tool in tools
        assert read_tool not in tools
        assert write_tool not in tools

    def test_get_tools_for_skill_ignores_unknown_allowed_tools(self):
        """Test that unknown tool names in allowed-tools are ignored."""
        registry = ToolRegistry()

        def bash_tool():
            pass

        registry.register_shared_tool("Bash", bash_tool)

        skill = Skill(
            name="unknown-tools-skill",
            description="References unknown tools",
            instructions="# Instructions",
            path=Path("/tmp/unknown-tools-skill"),
            allowed_tools=["Bash", "UnknownTool", "AnotherMissing"],
        )

        tools = registry.get_tools_for_skill(skill)

        # Should only return the known tool, silently ignore unknown
        assert len(tools) == 1
        assert bash_tool in tools

    def test_get_tools_for_skill_no_tools(self):
        """Test getting tools when skill has no allowed or bundled tools."""
        registry = ToolRegistry()

        skill = Skill(
            name="no-tools",
            description="No tools at all",
            instructions="# Instructions",
            path=Path("/tmp/no-tools"),
            allowed_tools=[],
        )

        tools = registry.get_tools_for_skill(skill)

        assert tools == []


class TestHasTool:
    """Tests for checking if a shared tool is registered."""

    def test_has_tool_returns_true_when_registered(self):
        """Test has_tool returns True for registered tools."""
        registry = ToolRegistry()

        def my_tool():
            pass

        registry.register_shared_tool("my_tool", my_tool)

        assert registry.has_tool("my_tool") is True

    def test_has_tool_returns_false_when_not_registered(self):
        """Test has_tool returns False for unregistered tools."""
        registry = ToolRegistry()

        assert registry.has_tool("nonexistent") is False


class TestListSharedTools:
    """Tests for listing all registered shared tool names."""

    def test_list_shared_tools_empty(self):
        """Test listing tools when none registered."""
        registry = ToolRegistry()

        assert registry.list_shared_tools() == []

    def test_list_shared_tools_returns_names(self):
        """Test listing returns all tool names."""
        registry = ToolRegistry()

        def tool_a():
            pass

        def tool_b():
            pass

        def tool_c():
            pass

        registry.register_shared_tool("tool_a", tool_a)
        registry.register_shared_tool("tool_b", tool_b)
        registry.register_shared_tool("tool_c", tool_c)

        names = registry.list_shared_tools()

        assert len(names) == 3
        assert "tool_a" in names
        assert "tool_b" in names
        assert "tool_c" in names


class TestToolRegistryIntegration:
    """Integration tests for ToolRegistry with real fixtures."""

    def test_load_and_register_skill_tools_from_fixture(self):
        """Test loading and registering tools from fixture skill."""
        registry = ToolRegistry()
        skill_path = FIXTURES_DIR / "skill-with-tools"

        # Load tools from the skill's tools.py
        tools = registry.load_skill_tools(skill_path)

        # Register them for the skill
        registry.register_skill_tools("data-analysis", tools)

        # Verify tools are registered
        assert "data-analysis" in registry.skill_tools
        assert len(registry.skill_tools["data-analysis"]) == 2

    def test_get_tools_for_fixture_skill(self):
        """Test getting tools for a skill loaded from fixture."""
        from skillforge.utils.markdown import parse_skill_md

        registry = ToolRegistry()

        # Register a shared tool that the skill references
        def bash_tool():
            pass

        def read_tool():
            pass

        registry.register_shared_tool("Bash", bash_tool)
        registry.register_shared_tool("Read", read_tool)

        # Parse the skill from fixture
        skill_path = FIXTURES_DIR / "skill-with-tools"
        skill = parse_skill_md(skill_path)

        # Load and register bundled tools
        bundled_tools = registry.load_skill_tools(skill_path)
        registry.register_skill_tools(skill.name, bundled_tools)

        # Get all tools for the skill
        tools = registry.get_tools_for_skill(skill)

        # Should have 2 shared tools (Bash, Read) + 2 bundled tools
        assert len(tools) == 4
