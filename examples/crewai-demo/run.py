#!/usr/bin/env python3
"""
CrewAI Demo Validation Script

This script validates the SkillForge CrewAI integration by running
a series of checkpoints that verify:

1. Installation and imports
2. Marketplace CLI operations
3. Skill loading and injection
4. Crew creation and agent configuration
5. Skill mode behavior (progressive vs inject)
6. Tool bundling (ticket-creation, knowledge-search)

Usage:
    python run.py --quick    # Mocked LLM calls for CI
    python run.py --real     # Actual API calls (requires OPENAI_API_KEY)

Requirements:
    - skillforge[crewai] installed
    - For --real mode: OPENAI_API_KEY in environment
"""

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch


@dataclass
class ValidationCheckpoint:
    """A single validation checkpoint with pass/fail tracking."""

    name: str
    passed: bool = False
    error: Optional[str] = None
    details: list[str] = field(default_factory=list)

    def check(self, condition: bool, error_msg: str = "") -> bool:
        """Check a condition and record the result.

        Args:
            condition: Boolean condition to check.
            error_msg: Error message if condition fails.

        Returns:
            The condition value.
        """
        self.passed = condition
        if not condition:
            self.error = error_msg
        self._print_status()
        return self.passed

    def add_detail(self, detail: str) -> None:
        """Add a detail line to the checkpoint."""
        self.details.append(detail)

    def _print_status(self) -> None:
        """Print the checkpoint status."""
        status = "[PASS]" if self.passed else "[FAIL]"
        print(f"{status} {self.name}")
        if self.error:
            print(f"       Error: {self.error}")
        for detail in self.details:
            print(f"       {detail}")


@dataclass
class ValidationReport:
    """Aggregated validation report."""

    checkpoints: list[ValidationCheckpoint] = field(default_factory=list)

    def add(self, checkpoint: ValidationCheckpoint) -> None:
        """Add a checkpoint to the report."""
        self.checkpoints.append(checkpoint)

    def summary(self) -> tuple[int, int]:
        """Return (passed_count, total_count)."""
        passed = sum(1 for cp in self.checkpoints if cp.passed)
        return passed, len(self.checkpoints)

    def print_summary(self) -> None:
        """Print the validation summary."""
        passed, total = self.summary()
        print("\n" + "=" * 60)
        print(f"VALIDATION SUMMARY: {passed}/{total} checkpoints passed")
        print("=" * 60)

        if passed == total:
            print("\nAll validations passed!")
        else:
            print("\nFailed checkpoints:")
            for cp in self.checkpoints:
                if not cp.passed:
                    print(f"  - {cp.name}: {cp.error}")

    def exit_code(self) -> int:
        """Return appropriate exit code."""
        passed, total = self.summary()
        return 0 if passed == total else 1


def change_to_script_directory() -> Path:
    """Change to the script's directory and return it."""
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)
    return script_dir


def validate_installation(report: ValidationReport) -> bool:
    """Validate that required packages are installed."""
    cp = ValidationCheckpoint("Installation: skillforge[crewai] importable")

    try:
        import crewai
        from skillforge.crewai import Agent

        cp.add_detail(f"crewai version: {crewai.__version__ if hasattr(crewai, '__version__') else 'unknown'}")
        cp.check(True)
        report.add(cp)
        return True
    except ImportError as e:
        cp.check(False, f"Import failed: {e}")
        report.add(cp)
        return False


def validate_marketplace_add(report: ValidationReport) -> bool:
    """Validate marketplace add CLI command."""
    cp = ValidationCheckpoint("Marketplace CLI: add ./shared-skills")

    try:
        # First remove if exists (to make test idempotent)
        subprocess.run(
            ["skillforge", "marketplace", "remove", "shared-skills", "-f"],
            capture_output=True,
            text=True,
        )

        # Resolve the absolute path to shared-skills
        shared_skills_path = (Path(__file__).parent / ".." / "shared-skills").resolve()

        # Add the marketplace using absolute path (starts with /)
        result = subprocess.run(
            ["skillforge", "marketplace", "add", str(shared_skills_path)],
            capture_output=True,
            text=True,
        )

        success = result.returncode == 0
        if success:
            cp.add_detail("Marketplace added successfully")
            if "Added marketplace:" in result.stdout:
                cp.add_detail("Output confirmed: 'Added marketplace:'")
        else:
            cp.add_detail(f"stdout: {result.stdout[:200]}")
            cp.add_detail(f"stderr: {result.stderr[:200]}")

        cp.check(success, f"Exit code: {result.returncode}")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def validate_marketplace_install(report: ValidationReport) -> bool:
    """Validate marketplace install CLI command."""
    cp = ValidationCheckpoint("Marketplace CLI: install greeting@shared-skills")

    install_dir = Path(__file__).parent / "installed-skills"

    try:
        # Clean up any previous installation
        if install_dir.exists():
            import shutil
            shutil.rmtree(install_dir)

        # Install the skill from marketplace (use --force to handle stale manifest entries)
        result = subprocess.run(
            ["skillforge", "install", "greeting@shared-skills", "--to", str(install_dir), "--force"],
            capture_output=True,
            text=True,
        )

        success = result.returncode == 0
        skill_installed = (install_dir / "greeting" / "SKILL.md").exists()

        if success and skill_installed:
            cp.add_detail("Skill installed successfully")
            cp.add_detail(f"Installed to: {install_dir / 'greeting'}")
        else:
            cp.add_detail(f"returncode: {result.returncode}")
            cp.add_detail(f"stdout: {result.stdout[:200]}")
            cp.add_detail(f"stderr: {result.stderr[:200]}")
            cp.add_detail(f"SKILL.md exists: {skill_installed}")

        overall_success = success and skill_installed
        cp.check(overall_success, f"Install failed or SKILL.md not found")
        report.add(cp)
        return overall_success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False
    finally:
        # Clean up installed skill directory
        if install_dir.exists():
            import shutil
            shutil.rmtree(install_dir)


def validate_marketplace_list(report: ValidationReport) -> bool:
    """Validate marketplace list CLI command shows skills."""
    cp = ValidationCheckpoint("Marketplace CLI: list shows shared-skills")

    try:
        result = subprocess.run(
            ["skillforge", "marketplace", "list"],
            capture_output=True,
            text=True,
        )

        success = result.returncode == 0 and "shared-skills" in result.stdout
        if success:
            cp.add_detail("shared-skills marketplace found in list")
        else:
            cp.add_detail(f"stdout: {result.stdout[:200]}")

        cp.check(success, "shared-skills not in marketplace list")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def validate_skill_list(report: ValidationReport) -> bool:
    """Validate that skills are discoverable via config."""
    cp = ValidationCheckpoint("Skill Discovery: shared skills found via config")

    try:
        from skillforge.core.config import load_config
        from skillforge.core.loader import SkillLoader

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skills = loader.discover()

        expected_skills = ["greeting", "troubleshooting", "knowledge-search", "ticket-creation"]
        found_skills = list(skills.keys())

        all_found = all(s in found_skills for s in expected_skills)

        cp.add_detail(f"Found skills: {found_skills}")
        cp.add_detail(f"Expected: {expected_skills}")

        cp.check(all_found, f"Missing skills: {set(expected_skills) - set(found_skills)}")
        report.add(cp)
        return all_found
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def validate_crew_creation(report: ValidationReport) -> bool:
    """Validate crew creation with 3 agents."""
    cp = ValidationCheckpoint("Crew Creation: 3 agents created")

    try:
        from crew import CustomerSupportCrew

        support_crew = CustomerSupportCrew()
        crew = support_crew.crew()

        agent_count = len(crew.agents)
        task_count = len(crew.tasks)

        cp.add_detail(f"Agents created: {agent_count}")
        cp.add_detail(f"Tasks created: {task_count}")

        success = agent_count == 3 and task_count == 3
        cp.check(success, f"Expected 3 agents and 3 tasks, got {agent_count} agents and {task_count} tasks")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def validate_router_progressive_mode(report: ValidationReport) -> bool:
    """Validate router agent uses progressive mode with greeting skill."""
    cp = ValidationCheckpoint("Router Agent: progressive mode with greeting skill")

    try:
        from crew import CustomerSupportCrew

        support_crew = CustomerSupportCrew()
        router = support_crew.router_agent()

        has_greeting_skill = "greeting" in router.skills
        is_progressive = router.skill_mode == "progressive"
        has_meta_skill = "Using SkillForge Skills" in router.backstory
        has_skill_list = "greeting" in router.backstory

        cp.add_detail(f"Skills: {router.skills}")
        cp.add_detail(f"Mode: {router.skill_mode}")
        cp.add_detail(f"Has meta-skill in backstory: {has_meta_skill}")
        cp.add_detail(f"Has skill list in backstory: {has_skill_list}")

        success = all([has_greeting_skill, is_progressive, has_meta_skill, has_skill_list])
        cp.check(success, "Progressive mode not configured correctly")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def validate_specialist_inject_mode(report: ValidationReport) -> bool:
    """Validate specialist agent uses inject mode with troubleshooting skills."""
    cp = ValidationCheckpoint("Specialist Agent: inject mode with troubleshooting + knowledge-search")

    try:
        from crew import CustomerSupportCrew

        support_crew = CustomerSupportCrew()
        specialist = support_crew.specialist_agent()

        has_troubleshooting = "troubleshooting" in specialist.skills
        has_knowledge = "knowledge-search" in specialist.skills
        is_inject = specialist.skill_mode == "inject"
        has_full_content = "## Available Skills" in specialist.backstory
        has_troubleshooting_content = "Troubleshooting Skill" in specialist.backstory
        has_knowledge_content = "Knowledge Search Skill" in specialist.backstory

        cp.add_detail(f"Skills: {specialist.skills}")
        cp.add_detail(f"Mode: {specialist.skill_mode}")
        cp.add_detail(f"Has full skills section: {has_full_content}")
        cp.add_detail(f"Has troubleshooting content: {has_troubleshooting_content}")
        cp.add_detail(f"Has knowledge-search content: {has_knowledge_content}")

        success = all([
            has_troubleshooting,
            has_knowledge,
            is_inject,
            has_full_content,
            has_troubleshooting_content,
            has_knowledge_content,
        ])
        cp.check(success, "Inject mode not configured correctly")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def validate_escalation_inject_mode(report: ValidationReport) -> bool:
    """Validate escalation agent uses inject mode with ticket-creation skill."""
    cp = ValidationCheckpoint("Escalation Agent: inject mode with ticket-creation")

    try:
        from crew import CustomerSupportCrew

        support_crew = CustomerSupportCrew()
        escalation = support_crew.escalation_agent()

        has_ticket_skill = "ticket-creation" in escalation.skills
        is_inject = escalation.skill_mode == "inject"
        has_full_content = "## Available Skills" in escalation.backstory
        has_ticket_content = "Ticket Creation Skill" in escalation.backstory
        has_tool_reference = "create_ticket" in escalation.backstory

        cp.add_detail(f"Skills: {escalation.skills}")
        cp.add_detail(f"Mode: {escalation.skill_mode}")
        cp.add_detail(f"Has full skills section: {has_full_content}")
        cp.add_detail(f"Has ticket-creation content: {has_ticket_content}")
        cp.add_detail(f"Has create_ticket tool reference: {has_tool_reference}")

        success = all([
            has_ticket_skill,
            is_inject,
            has_full_content,
            has_ticket_content,
            has_tool_reference,
        ])
        cp.check(success, "Inject mode with tool not configured correctly")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def validate_greeting_output_format(report: ValidationReport) -> bool:
    """Validate greeting skill output format is in backstory."""
    cp = ValidationCheckpoint("Greeting Skill: output format available")

    try:
        from skillforge.core.config import load_config
        from skillforge.core.loader import SkillLoader

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        greeting = loader.get("greeting")

        has_output_format = "Output Format" in greeting.instructions
        has_greeting_template = "Greeting:" in greeting.instructions
        has_introduction_template = "Introduction:" in greeting.instructions
        has_offer_template = "Offer:" in greeting.instructions

        cp.add_detail(f"Has Output Format section: {has_output_format}")
        cp.add_detail(f"Has Greeting template: {has_greeting_template}")
        cp.add_detail(f"Has Introduction template: {has_introduction_template}")
        cp.add_detail(f"Has Offer template: {has_offer_template}")

        success = all([
            has_output_format,
            has_greeting_template,
            has_introduction_template,
            has_offer_template,
        ])
        cp.check(success, "Greeting skill output format incomplete")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def validate_troubleshooting_output_format(report: ValidationReport) -> bool:
    """Validate troubleshooting skill output format is in backstory."""
    cp = ValidationCheckpoint("Troubleshooting Skill: output format available")

    try:
        from skillforge.core.config import load_config
        from skillforge.core.loader import SkillLoader

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skill = loader.get("troubleshooting")

        has_output_format = "Output Format" in skill.instructions
        has_problem_template = "Problem:" in skill.instructions
        has_diagnosis_template = "Diagnosis Steps:" in skill.instructions
        has_resolution_template = "Resolution:" in skill.instructions

        cp.add_detail(f"Has Output Format section: {has_output_format}")
        cp.add_detail(f"Has Problem template: {has_problem_template}")
        cp.add_detail(f"Has Diagnosis Steps template: {has_diagnosis_template}")
        cp.add_detail(f"Has Resolution template: {has_resolution_template}")

        success = all([
            has_output_format,
            has_problem_template,
            has_diagnosis_template,
            has_resolution_template,
        ])
        cp.check(success, "Troubleshooting skill output format incomplete")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def validate_ticket_creation_tool(report: ValidationReport) -> bool:
    """Validate ticket-creation skill has bundled tool."""
    cp = ValidationCheckpoint("Ticket Creation: bundled create_ticket tool")

    ticket_path = str((Path(__file__).parent / ".." / "shared-skills" / "ticket-creation").resolve())

    try:
        # Clean up any previous tools import
        if "tools" in sys.modules:
            del sys.modules["tools"]

        # Import the tool directly from the shared-skills
        sys.path.insert(0, ticket_path)
        from tools import create_ticket

        # Test the tool
        result = create_ticket(
            title="Test ticket",
            description="Test description",
            priority="medium",
        )

        has_ticket_id = "ticket_id" in result
        has_status = result.get("status") == "created"
        has_priority = result.get("priority") == "medium"

        cp.add_detail(f"Tool result: {result}")
        cp.add_detail(f"Has ticket_id: {has_ticket_id}")
        cp.add_detail(f"Has correct status: {has_status}")
        cp.add_detail(f"Has correct priority: {has_priority}")

        success = all([has_ticket_id, has_status, has_priority])
        cp.check(success, "create_ticket tool not working correctly")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False
    finally:
        # Clean up sys.path and sys.modules
        if ticket_path in sys.path:
            sys.path.remove(ticket_path)
        if "tools" in sys.modules:
            del sys.modules["tools"]


def validate_knowledge_search_tool(report: ValidationReport) -> bool:
    """Validate knowledge-search skill has bundled tool."""
    cp = ValidationCheckpoint("Knowledge Search: bundled search_kb tool")

    kb_path = str((Path(__file__).parent / ".." / "shared-skills" / "knowledge-search").resolve())

    try:
        # Clean up any previous tools import
        if "tools" in sys.modules:
            del sys.modules["tools"]

        # Import the tool directly from the shared-skills
        sys.path.insert(0, kb_path)
        from tools import search_kb

        # Test the tool
        result = search_kb("email sync")

        is_list = isinstance(result, list)
        has_results = len(result) > 0
        first_has_id = "id" in result[0] if result else False
        first_has_title = "title" in result[0] if result else False

        cp.add_detail(f"Results count: {len(result)}")
        cp.add_detail(f"First result: {result[0] if result else 'N/A'}")
        cp.add_detail(f"Is list: {is_list}")
        cp.add_detail(f"Has results: {has_results}")

        success = all([is_list, has_results, first_has_id, first_has_title])
        cp.check(success, "search_kb tool not working correctly")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False
    finally:
        # Clean up sys.path and sys.modules
        if kb_path in sys.path:
            sys.path.remove(kb_path)
        if "tools" in sys.modules:
            del sys.modules["tools"]


def setup_mock_llm() -> None:
    """Set up environment for mocked LLM calls.

    CrewAI requires OPENAI_API_KEY even for agent creation.
    This sets a dummy key for quick validation mode.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing-only"


def run_quick_validation(report: ValidationReport) -> None:
    """Run quick validation with mocked LLM calls."""
    print("\n=== Running QUICK validation (mocked LLM) ===\n")

    # Set up mock LLM environment
    setup_mock_llm()

    # Run all validations
    validate_installation(report)
    validate_marketplace_add(report)
    validate_marketplace_install(report)
    validate_marketplace_list(report)
    validate_skill_list(report)
    validate_crew_creation(report)
    validate_router_progressive_mode(report)
    validate_specialist_inject_mode(report)
    validate_escalation_inject_mode(report)
    validate_greeting_output_format(report)
    validate_troubleshooting_output_format(report)
    validate_ticket_creation_tool(report)
    validate_knowledge_search_tool(report)


def validate_real_crew_execution(report: ValidationReport) -> bool:
    """Validate crew execution with real LLM calls."""
    cp = ValidationCheckpoint("Real Execution: crew kickoff with LLM")

    try:
        from crew import CustomerSupportCrew

        support_crew = CustomerSupportCrew()
        crew = support_crew.crew(
            customer_message="Hi, I can't log into my email account",
            issue_description="Email login failing with incorrect password error",
            issue_summary="Email login issue requires password reset assistance",
        )

        # Execute the crew
        result = crew.kickoff()

        # Check if we got a result
        has_result = result is not None
        result_str = str(result)

        cp.add_detail(f"Got result: {has_result}")
        cp.add_detail(f"Result length: {len(result_str)}")
        cp.add_detail(f"Result preview: {result_str[:200]}...")

        cp.check(has_result, "No result from crew execution")
        report.add(cp)
        return has_result
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


def run_real_validation(report: ValidationReport) -> None:
    """Run real validation with actual LLM calls."""
    print("\n=== Running REAL validation (with LLM API) ===\n")

    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("[WARN] OPENAI_API_KEY not set. Real validation requires an API key.")
        print("       Set it with: export OPENAI_API_KEY=your-key")
        print("       Running quick validation instead...\n")
        run_quick_validation(report)
        return

    # Run quick validations first
    validate_installation(report)
    validate_marketplace_add(report)
    validate_marketplace_install(report)
    validate_marketplace_list(report)
    validate_skill_list(report)
    validate_crew_creation(report)
    validate_router_progressive_mode(report)
    validate_specialist_inject_mode(report)
    validate_escalation_inject_mode(report)
    validate_greeting_output_format(report)
    validate_troubleshooting_output_format(report)
    validate_ticket_creation_tool(report)
    validate_knowledge_search_tool(report)

    # Run real LLM execution
    validate_real_crew_execution(report)


def main() -> int:
    """Main entry point for validation."""
    parser = argparse.ArgumentParser(
        description="Validate SkillForge CrewAI integration"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation with mocked LLM calls (default)",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Run real validation with actual LLM API calls",
    )
    args = parser.parse_args()

    # Default to quick mode
    if not args.quick and not args.real:
        args.quick = True

    # Change to script directory
    script_dir = change_to_script_directory()
    print(f"Working directory: {script_dir}")

    # Create report
    report = ValidationReport()

    # Run validation
    if args.real:
        run_real_validation(report)
    else:
        run_quick_validation(report)

    # Print summary
    report.print_summary()

    return report.exit_code()


if __name__ == "__main__":
    sys.exit(main())
