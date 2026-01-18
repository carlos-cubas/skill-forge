"""
Unit tests for example skills in examples/shared-skills/.

Tests verify that all example skills:
1. Load successfully via SkillLoader
2. Have correct frontmatter (name, description, allowed-tools)
3. Have correct has_tools property based on presence of tools.py
4. Tool functions work correctly (for skills with tools)
"""

import importlib.util
from pathlib import Path

import pytest

from skillforge.core.loader import SkillLoader
from skillforge.utils.markdown import parse_skill_md


def load_function_from_tools_file(tools_path: Path, function_name: str):
    """
    Load a function from a tools.py file without polluting sys.modules.

    This avoids module caching issues when multiple skills have tools.py files.
    """
    spec = importlib.util.spec_from_file_location(
        f"tools_{tools_path.parent.name}",  # Unique module name per skill
        tools_path,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, function_name)


# Path to example skills
EXAMPLES_DIR = (Path(__file__).parent.parent.parent / "examples" / "shared-skills").resolve()


class TestExampleSkillsDiscovery:
    """Tests for discovering example skills via SkillLoader."""

    @pytest.fixture
    def loader(self):
        """Create a SkillLoader configured for example skills."""
        return SkillLoader(
            [str(EXAMPLES_DIR / "*")],
            base_path=EXAMPLES_DIR.parent,
        )

    def test_all_example_skills_discoverable(self, loader):
        """Test that all 4 example skills are discoverable."""
        skills = loader.discover()

        expected_skills = {"greeting", "troubleshooting", "ticket-creation", "knowledge-search"}
        discovered_names = set(skills.keys())

        assert expected_skills == discovered_names, (
            f"Expected skills {expected_skills}, got {discovered_names}"
        )

    def test_can_get_each_skill_by_name(self, loader):
        """Test that each example skill can be retrieved by name."""
        skill_names = ["greeting", "troubleshooting", "ticket-creation", "knowledge-search"]

        for name in skill_names:
            skill = loader.get(name)
            assert skill is not None
            assert skill.name == name


class TestGreetingSkill:
    """Tests for the greeting skill (no tools)."""

    @pytest.fixture(scope="class")
    def skill(self):
        """Load the greeting skill."""
        return parse_skill_md(EXAMPLES_DIR / "greeting")

    def test_frontmatter_name(self, skill):
        """Test greeting skill has correct name."""
        assert skill.name == "greeting"

    def test_frontmatter_description(self, skill):
        """Test greeting skill has correct description."""
        assert skill.description == "Welcome users warmly and set a helpful tone"

    def test_frontmatter_allowed_tools(self, skill):
        """Test greeting skill has empty allowed-tools."""
        assert skill.allowed_tools == []

    def test_has_tools_false(self, skill):
        """Test greeting skill has no tools.py."""
        assert skill.has_tools is False

    def test_tools_module_path_none(self, skill):
        """Test greeting skill tools_module_path is None."""
        assert skill.tools_module_path is None

    def test_instructions_contain_expected_content(self, skill):
        """Test greeting skill instructions contain expected content."""
        assert "# Customer Greeting Skill" in skill.instructions
        assert "When to Use" in skill.instructions
        assert "Output Format" in skill.instructions


class TestTroubleshootingSkill:
    """Tests for the troubleshooting skill (no tools)."""

    @pytest.fixture(scope="class")
    def skill(self):
        """Load the troubleshooting skill."""
        return parse_skill_md(EXAMPLES_DIR / "troubleshooting")

    def test_frontmatter_name(self, skill):
        """Test troubleshooting skill has correct name."""
        assert skill.name == "troubleshooting"

    def test_frontmatter_description(self, skill):
        """Test troubleshooting skill has correct description."""
        assert skill.description == "Step-by-step diagnosis framework for common support issues"

    def test_frontmatter_allowed_tools(self, skill):
        """Test troubleshooting skill has empty allowed-tools."""
        assert skill.allowed_tools == []

    def test_has_tools_false(self, skill):
        """Test troubleshooting skill has no tools.py."""
        assert skill.has_tools is False

    def test_instructions_contain_expected_content(self, skill):
        """Test troubleshooting skill instructions contain expected content."""
        assert "# Troubleshooting Skill" in skill.instructions
        assert "Email Sync Issues" in skill.instructions
        assert "Password Reset Problems" in skill.instructions
        assert "Login/Access Issues" in skill.instructions

    def test_tools_module_path_none(self, skill):
        """Test troubleshooting skill tools_module_path is None."""
        assert skill.tools_module_path is None


class TestTicketCreationSkill:
    """Tests for the ticket-creation skill (with tools)."""

    @pytest.fixture(scope="class")
    def skill(self):
        """Load the ticket-creation skill."""
        return parse_skill_md(EXAMPLES_DIR / "ticket-creation")

    def test_frontmatter_name(self, skill):
        """Test ticket-creation skill has correct name."""
        assert skill.name == "ticket-creation"

    def test_frontmatter_description(self, skill):
        """Test ticket-creation skill has correct description."""
        assert skill.description == "Create support tickets with proper categorization and priority"

    def test_frontmatter_allowed_tools(self, skill):
        """Test ticket-creation skill has create_ticket in allowed-tools."""
        assert skill.allowed_tools == ["create_ticket"]

    def test_has_tools_true(self, skill):
        """Test ticket-creation skill has tools.py."""
        assert skill.has_tools is True

    def test_tools_module_path_exists(self, skill):
        """Test ticket-creation skill tools_module_path points to tools.py."""
        assert skill.tools_module_path is not None
        assert skill.tools_module_path.name == "tools.py"
        assert skill.tools_module_path.exists()

    def test_instructions_contain_expected_content(self, skill):
        """Test ticket-creation skill instructions contain expected content."""
        assert "# Ticket Creation Skill" in skill.instructions
        assert "create_ticket" in skill.instructions
        assert "Priority Guidelines" in skill.instructions


class TestKnowledgeSearchSkill:
    """Tests for the knowledge-search skill (with tools)."""

    @pytest.fixture(scope="class")
    def skill(self):
        """Load the knowledge-search skill."""
        return parse_skill_md(EXAMPLES_DIR / "knowledge-search")

    def test_frontmatter_name(self, skill):
        """Test knowledge-search skill has correct name."""
        assert skill.name == "knowledge-search"

    def test_frontmatter_description(self, skill):
        """Test knowledge-search skill has correct description."""
        assert skill.description == "Search knowledge base for relevant articles and documentation"

    def test_frontmatter_allowed_tools(self, skill):
        """Test knowledge-search skill has search_kb in allowed-tools."""
        assert skill.allowed_tools == ["search_kb"]

    def test_has_tools_true(self, skill):
        """Test knowledge-search skill has tools.py."""
        assert skill.has_tools is True

    def test_tools_module_path_exists(self, skill):
        """Test knowledge-search skill tools_module_path points to tools.py."""
        assert skill.tools_module_path is not None
        assert skill.tools_module_path.name == "tools.py"
        assert skill.tools_module_path.exists()

    def test_instructions_contain_expected_content(self, skill):
        """Test knowledge-search skill instructions contain expected content."""
        assert "# Knowledge Search Skill" in skill.instructions
        assert "search_kb" in skill.instructions
        assert "Search Strategy" in skill.instructions


class TestCreateTicketTool:
    """Tests for the create_ticket tool function."""

    @pytest.fixture
    def create_ticket(self):
        """Import and return the create_ticket function."""
        tools_path = EXAMPLES_DIR / "ticket-creation" / "tools.py"
        return load_function_from_tools_file(tools_path, "create_ticket")

    def test_create_ticket_returns_dict(self, create_ticket):
        """Test create_ticket returns a dictionary."""
        result = create_ticket(
            title="Test ticket",
            description="Test description",
            priority="medium",
        )
        assert isinstance(result, dict)

    def test_create_ticket_has_required_keys(self, create_ticket):
        """Test create_ticket returns all required keys."""
        result = create_ticket(
            title="Test ticket",
            description="Test description",
            priority="high",
        )

        required_keys = {"ticket_id", "status", "priority", "title", "message"}
        assert required_keys.issubset(result.keys())

    def test_create_ticket_id_format(self, create_ticket):
        """Test create_ticket generates TICK-XXXX format ID."""
        result = create_ticket(
            title="Test ticket",
            description="Test description",
        )

        ticket_id = result["ticket_id"]
        assert ticket_id.startswith("TICK-")
        # Verify numeric portion
        numeric_part = ticket_id.split("-")[1]
        assert numeric_part.isdigit()
        assert 1000 <= int(numeric_part) <= 9999

    def test_create_ticket_status_is_created(self, create_ticket):
        """Test create_ticket returns status='created'."""
        result = create_ticket(
            title="Test ticket",
            description="Test description",
        )
        assert result["status"] == "created"

    def test_create_ticket_priority_levels(self, create_ticket):
        """Test create_ticket accepts all valid priority levels."""
        priorities = ["critical", "high", "medium", "low"]

        for priority in priorities:
            result = create_ticket(
                title=f"Test {priority}",
                description="Test description",
                priority=priority,
            )
            assert result["priority"] == priority

    def test_create_ticket_default_priority(self, create_ticket):
        """Test create_ticket defaults to medium priority."""
        result = create_ticket(
            title="Test ticket",
            description="Test description",
        )
        assert result["priority"] == "medium"

    def test_create_ticket_truncates_long_title(self, create_ticket):
        """Test create_ticket truncates title longer than 100 chars."""
        long_title = "A" * 150
        result = create_ticket(
            title=long_title,
            description="Test description",
        )
        assert len(result["title"]) == 100

    def test_create_ticket_message_contains_id_and_priority(self, create_ticket):
        """Test create_ticket message includes ticket ID and priority."""
        result = create_ticket(
            title="Test ticket",
            description="Test description",
            priority="high",
        )

        assert result["ticket_id"] in result["message"]
        assert "high" in result["message"]

    def test_create_ticket_with_empty_title(self, create_ticket):
        """Test create_ticket handles empty title."""
        result = create_ticket(title="", description="Test", priority="low")
        assert result["title"] == ""


class TestSearchKbTool:
    """Tests for the search_kb tool function."""

    @pytest.fixture
    def search_kb(self):
        """Import and return the search_kb function."""
        tools_path = EXAMPLES_DIR / "knowledge-search" / "tools.py"
        return load_function_from_tools_file(tools_path, "search_kb")

    def test_search_kb_returns_list(self, search_kb):
        """Test search_kb returns a list."""
        result = search_kb("email")
        assert isinstance(result, list)

    def test_search_kb_results_have_required_keys(self, search_kb):
        """Test search_kb results contain required keys."""
        results = search_kb("email")
        assert len(results) > 0

        required_keys = {"id", "title", "summary", "relevance_score"}
        for result in results:
            assert required_keys.issubset(result.keys())

    def test_search_kb_id_format(self, search_kb):
        """Test search_kb results have KB-XXXX format IDs."""
        results = search_kb("email")

        for result in results:
            assert result["id"].startswith("KB-")

    def test_search_kb_finds_email_articles(self, search_kb):
        """Test search_kb finds email-related articles."""
        results = search_kb("email sync")

        assert len(results) > 0
        # Should find the email sync article
        titles = [r["title"] for r in results]
        assert any("Email" in title for title in titles)

    def test_search_kb_finds_password_articles(self, search_kb):
        """Test search_kb finds password-related articles."""
        results = search_kb("password reset")

        assert len(results) > 0
        titles = [r["title"] for r in results]
        assert any("Password" in title for title in titles)

    def test_search_kb_finds_login_articles(self, search_kb):
        """Test search_kb finds login-related articles."""
        results = search_kb("login trouble")

        assert len(results) > 0
        titles = [r["title"] for r in results]
        assert any("Login" in title for title in titles)

    def test_search_kb_finds_billing_articles(self, search_kb):
        """Test search_kb finds billing-related articles."""
        results = search_kb("billing refund")

        assert len(results) > 0
        titles = [r["title"] for r in results]
        assert any("Billing" in title or "Refund" in title for title in titles)

    def test_search_kb_respects_max_results(self, search_kb):
        """Test search_kb limits results to max_results."""
        # Search with a broad term that should match many articles
        results = search_kb("account", max_results=2)

        assert len(results) <= 2

    def test_search_kb_sorted_by_relevance(self, search_kb):
        """Test search_kb results are sorted by relevance score descending."""
        results = search_kb("email sync")

        if len(results) > 1:
            scores = [r["relevance_score"] for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_search_kb_empty_query_returns_empty(self, search_kb):
        """Test search_kb with no matching terms returns empty list."""
        results = search_kb("xyznonexistentterm123")
        assert results == []

    def test_search_kb_default_max_results(self, search_kb):
        """Test search_kb default max_results is 5."""
        # Use a very broad search that might match many articles
        results = search_kb("account security login password email")
        assert len(results) <= 5

    def test_search_kb_with_zero_max_results(self, search_kb):
        """Test search_kb with max_results=0 returns empty list."""
        results = search_kb("email", max_results=0)
        assert results == []
