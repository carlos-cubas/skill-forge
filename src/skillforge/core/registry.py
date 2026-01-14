"""
ToolRegistry for managing shared tools and skill-bundled tools.

This module provides the ToolRegistry class that manages:
1. Shared tools - available to all skills that declare them in allowed-tools
2. Skill-bundled tools - tools defined in a skill's tools.py file

Skills can use both shared and bundled tools, giving flexibility in how
tools are distributed and managed.
"""

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from skillforge.core.skill import Skill


class ToolRegistry:
    """Manages both shared tools and skill-bundled tools.

    The registry supports two types of tools:
    1. Shared tools: Registered globally and available to any skill that
       declares them in its `allowed-tools` frontmatter.
    2. Skill-bundled tools: Loaded from a skill's `tools.py` file and
       available only to that specific skill.

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register_shared_tool("Bash", bash_tool)
        >>> registry.register_shared_tool("Read", read_tool)
        >>>
        >>> # Load bundled tools from a skill
        >>> tools = registry.load_skill_tools(Path("./skills/data-analysis"))
        >>> registry.register_skill_tools("data-analysis", tools)
        >>>
        >>> # Get all tools for a skill
        >>> tools = registry.get_tools_for_skill(skill)

    Attributes:
        shared_tools: Dictionary mapping tool names to tool objects.
        skill_tools: Dictionary mapping skill names to lists of bundled tools.
    """

    def __init__(self) -> None:
        """Initialize an empty ToolRegistry."""
        self.shared_tools: dict[str, Any] = {}
        self.skill_tools: dict[str, list[Any]] = {}

    def register_shared_tool(self, name: str, tool: Any) -> None:
        """Register a tool available to all skills.

        Shared tools can be accessed by any skill that declares the tool
        name in its `allowed-tools` frontmatter.

        Args:
            name: The name of the tool (must match what skills use in allowed-tools).
            tool: The tool object (typically a callable or framework-specific tool).
        """
        self.shared_tools[name] = tool

    def register_skill_tools(self, skill_name: str, tools: list[Any]) -> None:
        """Register tools bundled with a specific skill.

        These tools are only available to the named skill, regardless of
        the skill's `allowed-tools` configuration.

        Args:
            skill_name: The name of the skill these tools belong to.
            tools: List of tool objects bundled with the skill.
        """
        self.skill_tools[skill_name] = tools

    def load_skill_tools(self, skill_path: Path) -> list[Any]:
        """Load tools from a skill's tools.py file.

        By convention, a skill's tools.py should export a `TOOLS` list
        containing all tools the skill provides.

        Example tools.py:
            ```python
            def my_tool(arg: str) -> str:
                '''Do something useful.'''
                return result

            TOOLS = [my_tool]
            ```

        Args:
            skill_path: Path to the skill directory.

        Returns:
            List of tools from the skill's tools.py, or empty list if
            no tools.py exists or it doesn't export TOOLS.
        """
        tools_file = skill_path / "tools.py"
        if not tools_file.exists():
            return []

        try:
            # Dynamic import of tools.py
            spec = importlib.util.spec_from_file_location("tools", tools_file)
            if spec is None or spec.loader is None:
                return []

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Convention: tools.py exports TOOLS list
            if hasattr(module, "TOOLS"):
                return module.TOOLS
            return []
        except Exception:
            # If anything goes wrong loading the module, return empty list
            return []

    def get_tools_for_skill(self, skill: "Skill") -> list[Any]:
        """Get all tools a skill can access.

        Returns the combination of:
        1. Shared tools that the skill lists in its `allowed-tools`
        2. Bundled tools registered for this skill

        Unknown tool names in `allowed-tools` are silently ignored.

        Args:
            skill: The Skill object to get tools for.

        Returns:
            List of all tools the skill has access to.
        """
        tools: list[Any] = []

        # Add allowed shared tools
        for tool_name in skill.allowed_tools:
            if tool_name in self.shared_tools:
                tools.append(self.shared_tools[tool_name])

        # Add bundled tools
        if skill.name in self.skill_tools:
            tools.extend(self.skill_tools[skill.name])

        return tools

    def has_tool(self, name: str) -> bool:
        """Check if a shared tool is registered.

        Args:
            name: The tool name to check.

        Returns:
            True if a shared tool with this name is registered.
        """
        return name in self.shared_tools

    def list_shared_tools(self) -> list[str]:
        """List all registered shared tool names.

        Returns:
            List of all shared tool names currently registered.
        """
        return list(self.shared_tools.keys())
