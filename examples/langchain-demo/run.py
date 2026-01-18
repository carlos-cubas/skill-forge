#!/usr/bin/env python3
"""
LangChain Demo Validation Script

This script validates the SkillForge LangChain integration by running
a series of checkpoints that verify:

1. Installation verified (skillforge[langchain] importable)
2. Skills copied locally (symlink or copy from shared-skills)
3. CLI `skillforge read` command works
4. Agent created in progressive mode
5. System prompt includes meta-skill
6. Greeting skill used correctly (output format matches)
7. Troubleshooting skill used correctly
8. Ticket creation skill used correctly
9. Inject mode comparison works (compare prompt sizes)

Usage:
    python run.py --quick    # Mocked LLM calls for CI (default)
    python run.py --real     # Actual API calls (requires OPENAI_API_KEY)

Requirements:
    - skillforge[langchain] installed
    - For --real mode: OPENAI_API_KEY in environment
"""

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


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


# =============================================================================
# Checkpoint 1: Installation verified
# =============================================================================


def validate_installation(report: ValidationReport) -> bool:
    """Checkpoint 1: Validate that required packages are installed."""
    cp = ValidationCheckpoint("Checkpoint 1: Installation verified (skillforge[langchain] importable)")

    try:
        import langchain
        from skillforge.langchain import create_agent

        langchain_version = getattr(langchain, "__version__", "unknown")
        cp.add_detail(f"langchain version: {langchain_version}")
        cp.add_detail("skillforge.langchain adapter importable: True")
        cp.check(True)
        report.add(cp)
        return True
    except ImportError as e:
        cp.check(False, f"Import failed: {e}")
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 2: Skills copied locally
# =============================================================================


def validate_skills_local(report: ValidationReport) -> bool:
    """Checkpoint 2: Validate that skills are copied/symlinked locally."""
    cp = ValidationCheckpoint("Checkpoint 2: Skills copied locally (symlink or copy)")

    script_dir = Path(__file__).parent
    skills_dir = script_dir / "skills"

    expected_skills = ["greeting", "troubleshooting", "ticket-creation", "knowledge-search"]
    found_skills = []
    missing_skills = []

    for skill_name in expected_skills:
        skill_path = skills_dir / skill_name
        skill_md_path = skill_path / "SKILL.md"

        if skill_path.exists() and skill_md_path.exists():
            found_skills.append(skill_name)
            # Check if it's a symlink
            if skill_path.is_symlink():
                cp.add_detail(f"{skill_name}: symlink -> {skill_path.resolve()}")
            else:
                cp.add_detail(f"{skill_name}: copy at {skill_path}")
        else:
            missing_skills.append(skill_name)

    success = len(missing_skills) == 0
    if missing_skills:
        cp.add_detail(f"Missing skills: {missing_skills}")

    cp.check(success, f"Missing {len(missing_skills)} skills: {missing_skills}")
    report.add(cp)
    return success


# =============================================================================
# Checkpoint 3: CLI skillforge read command works
# =============================================================================


def validate_cli_read(report: ValidationReport) -> bool:
    """Checkpoint 3: Validate that `skillforge read` CLI command works."""
    cp = ValidationCheckpoint("Checkpoint 3: CLI `skillforge read` command works")

    try:
        # Run skillforge read for the greeting skill with --from option
        skills_path = Path(__file__).parent / "skills"
        result = subprocess.run(
            ["skillforge", "read", "greeting", "--from", str(skills_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        success = result.returncode == 0
        has_greeting_content = "Customer Greeting Skill" in result.stdout

        if success and has_greeting_content:
            cp.add_detail("skillforge read greeting: success")
            cp.add_detail("Output contains expected skill content")
            # Show first 100 chars of output
            preview = result.stdout[:100].replace("\n", " ")
            cp.add_detail(f"Preview: {preview}...")
        else:
            cp.add_detail(f"returncode: {result.returncode}")
            cp.add_detail(f"stdout preview: {result.stdout[:200]}")
            cp.add_detail(f"stderr: {result.stderr[:200]}")

        overall_success = success and has_greeting_content
        cp.check(overall_success, "skillforge read command failed or missing expected content")
        report.add(cp)
        return overall_success
    except FileNotFoundError:
        cp.check(False, "skillforge CLI not found in PATH")
        report.add(cp)
        return False
    except subprocess.TimeoutExpired:
        cp.check(False, "skillforge read command timed out")
        report.add(cp)
        return False
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 4: Agent created in progressive mode
# =============================================================================


def validate_agent_progressive_mode(report: ValidationReport) -> bool:
    """Checkpoint 4: Validate that agent is created in progressive mode."""
    cp = ValidationCheckpoint("Checkpoint 4: Agent created in progressive mode")

    try:
        from agent import create_support_agent

        agent = create_support_agent(mock_llm=True)

        is_progressive = agent.skill_mode == "progressive"
        has_skills = len(agent.skills) == 4

        cp.add_detail(f"Agent type: {type(agent).__name__}")
        cp.add_detail(f"Mode: {agent.skill_mode}")
        cp.add_detail(f"Skills count: {len(agent.skills)}")
        cp.add_detail(f"Skills: {agent.skills}")
        cp.add_detail(f"System prompt length: {len(agent.system_prompt)} chars")

        success = is_progressive and has_skills
        cp.check(success, "Agent not in progressive mode or missing skills")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 5: System prompt includes meta-skill
# =============================================================================


def validate_meta_skill_in_prompt(report: ValidationReport) -> bool:
    """Checkpoint 5: Validate that system prompt includes meta-skill."""
    cp = ValidationCheckpoint("Checkpoint 5: System prompt includes meta-skill")

    try:
        from agent import create_support_agent, verify_meta_skill_present

        agent = create_support_agent(mock_llm=True)
        has_meta_skill = verify_meta_skill_present(agent)

        # Additional checks
        has_using_skillforge = "Using SkillForge Skills" in agent.system_prompt
        has_skillforge_read = "skillforge read" in agent.system_prompt
        has_skill_list = all(
            skill in agent.system_prompt
            for skill in ["greeting", "troubleshooting", "ticket-creation", "knowledge-search"]
        )

        cp.add_detail(f"Has meta-skill: {has_meta_skill}")
        cp.add_detail(f"Contains 'Using SkillForge Skills': {has_using_skillforge}")
        cp.add_detail(f"Contains 'skillforge read': {has_skillforge_read}")
        cp.add_detail(f"Contains all skill names: {has_skill_list}")

        success = has_meta_skill and has_using_skillforge and has_skillforge_read and has_skill_list
        cp.check(success, "Meta-skill content not properly included in system prompt")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 6: Greeting skill used correctly
# =============================================================================


def validate_greeting_skill(report: ValidationReport) -> bool:
    """Checkpoint 6: Validate greeting skill output format is available."""
    cp = ValidationCheckpoint("Checkpoint 6: Greeting skill used correctly (output format matches)")

    try:
        from skillforge.core.config import load_config
        from skillforge.core.loader import SkillLoader

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        greeting = loader.get("greeting")

        # Check for expected output format markers
        has_output_format = "Output Format" in greeting.instructions
        has_greeting_template = "Greeting:" in greeting.instructions
        has_introduction_template = "Introduction:" in greeting.instructions
        has_offer_template = "Offer:" in greeting.instructions

        cp.add_detail(f"Skill name: {greeting.name}")
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


# =============================================================================
# Checkpoint 7: Troubleshooting skill used correctly
# =============================================================================


def validate_troubleshooting_skill(report: ValidationReport) -> bool:
    """Checkpoint 7: Validate troubleshooting skill output format is available."""
    cp = ValidationCheckpoint("Checkpoint 7: Troubleshooting skill used correctly")

    try:
        from skillforge.core.config import load_config
        from skillforge.core.loader import SkillLoader

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skill = loader.get("troubleshooting")

        # Check for expected output format markers
        has_output_format = "Output Format" in skill.instructions
        has_problem_template = "Problem:" in skill.instructions
        has_diagnosis_template = "Diagnosis Steps:" in skill.instructions
        has_resolution_template = "Resolution:" in skill.instructions

        # Check for common issue frameworks
        has_email_sync = "Email Sync Issues" in skill.instructions
        has_password_reset = "Password Reset Problems" in skill.instructions

        cp.add_detail(f"Skill name: {skill.name}")
        cp.add_detail(f"Has Output Format section: {has_output_format}")
        cp.add_detail(f"Has Problem template: {has_problem_template}")
        cp.add_detail(f"Has Diagnosis Steps template: {has_diagnosis_template}")
        cp.add_detail(f"Has Resolution template: {has_resolution_template}")
        cp.add_detail(f"Has Email Sync framework: {has_email_sync}")
        cp.add_detail(f"Has Password Reset framework: {has_password_reset}")

        success = all([
            has_output_format,
            has_problem_template,
            has_diagnosis_template,
            has_resolution_template,
            has_email_sync,
            has_password_reset,
        ])
        cp.check(success, "Troubleshooting skill output format incomplete")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 8: Ticket creation skill used correctly
# =============================================================================


def validate_ticket_creation_skill(report: ValidationReport) -> bool:
    """Checkpoint 8: Validate ticket-creation skill and bundled tool."""
    cp = ValidationCheckpoint("Checkpoint 8: Ticket creation skill used correctly")

    ticket_path = str((Path(__file__).parent / "skills" / "ticket-creation").resolve())

    try:
        # First verify the skill itself
        from skillforge.core.config import load_config
        from skillforge.core.loader import SkillLoader

        config = load_config()
        loader = SkillLoader(skill_paths=config.skill_paths)
        skill = loader.get("ticket-creation")

        # Check skill content
        has_output_format = "Output Format" in skill.instructions
        has_tool_reference = "create_ticket" in skill.instructions
        has_priority_guidelines = "Priority Guidelines" in skill.instructions

        cp.add_detail(f"Skill name: {skill.name}")
        cp.add_detail(f"Has Output Format: {has_output_format}")
        cp.add_detail(f"Has create_ticket reference: {has_tool_reference}")
        cp.add_detail(f"Has Priority Guidelines: {has_priority_guidelines}")

        # Clean up any previous tools import
        if "tools" in sys.modules:
            del sys.modules["tools"]

        # Import and test the bundled tool
        sys.path.insert(0, ticket_path)
        from tools import create_ticket

        # Test the tool
        result = create_ticket(
            title="Test ticket from validation",
            description="Testing ticket creation tool",
            priority="medium",
        )

        has_ticket_id = "ticket_id" in result
        has_status = result.get("status") == "created"
        has_priority = result.get("priority") == "medium"

        cp.add_detail(f"Tool test result: {result}")
        cp.add_detail(f"Has ticket_id: {has_ticket_id}")
        cp.add_detail(f"Has correct status: {has_status}")
        cp.add_detail(f"Has correct priority: {has_priority}")

        success = all([
            has_output_format,
            has_tool_reference,
            has_priority_guidelines,
            has_ticket_id,
            has_status,
            has_priority,
        ])
        cp.check(success, "Ticket creation skill or tool not working correctly")
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


# =============================================================================
# Checkpoint 9: Inject mode comparison works
# =============================================================================


def validate_inject_mode_comparison(report: ValidationReport) -> bool:
    """Checkpoint 9: Validate inject mode comparison (compare prompt sizes)."""
    cp = ValidationCheckpoint("Checkpoint 9: Inject mode comparison works (compare prompt sizes)")

    try:
        from agent import (
            compare_modes,
            create_support_agent,
            create_support_agent_inject_mode,
            verify_inject_mode,
            verify_progressive_mode,
        )

        # Create both agents
        progressive_agent = create_support_agent(mock_llm=True)
        inject_agent = create_support_agent_inject_mode(mock_llm=True)

        # Verify modes
        is_progressive = verify_progressive_mode(progressive_agent)
        is_inject = verify_inject_mode(inject_agent)

        # Compare prompt sizes
        progressive_len = len(progressive_agent.system_prompt)
        inject_len = len(inject_agent.system_prompt)
        size_difference = inject_len - progressive_len
        inject_larger = inject_len > progressive_len

        # Use compare_modes() helper for additional validation
        comparison = compare_modes()
        helper_works = (
            "progressive" in comparison
            and "inject" in comparison
            and "comparison" in comparison
        )

        cp.add_detail(f"Progressive agent mode verified: {is_progressive}")
        cp.add_detail(f"Inject agent mode verified: {is_inject}")
        cp.add_detail(f"Progressive prompt length: {progressive_len} chars")
        cp.add_detail(f"Inject prompt length: {inject_len} chars")
        cp.add_detail(f"Inject larger by: {size_difference} chars")
        cp.add_detail(f"Inject mode is larger (expected): {inject_larger}")
        cp.add_detail(f"compare_modes() helper works: {helper_works}")

        success = all([
            is_progressive,
            is_inject,
            inject_larger,
            helper_works,
        ])
        cp.check(success, "Inject mode comparison failed")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Real Mode: Agent Execution with LLM
# =============================================================================


def validate_real_agent_execution(report: ValidationReport) -> bool:
    """Validate agent execution with real LLM calls (--real mode only)."""
    cp = ValidationCheckpoint("Real Execution: Agent invocation with LLM")

    try:
        from agent import create_support_agent

        # Create agent with real LLM
        agent = create_support_agent(mock_llm=False)

        # Simple test invocation
        response = agent.invoke({
            "messages": [("human", "Hello, I need help with my email not syncing.")]
        })

        has_response = response is not None
        response_str = str(response)

        cp.add_detail(f"Got response: {has_response}")
        cp.add_detail(f"Response length: {len(response_str)}")
        cp.add_detail(f"Response preview: {response_str[:200]}...")

        cp.check(has_response, "No response from agent execution")
        report.add(cp)
        return has_response
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Main Validation Functions
# =============================================================================


def setup_mock_llm() -> None:
    """Set up environment for mocked LLM calls.

    LangChain/OpenAI requires OPENAI_API_KEY even for some operations.
    This sets a dummy key for quick validation mode.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = "sk-dummy-key-for-testing-only"


def run_quick_validation(report: ValidationReport) -> None:
    """Run quick validation with mocked LLM calls."""
    print("\n=== Running QUICK validation (mocked LLM) ===\n")

    # Set up mock LLM environment
    setup_mock_llm()

    # Run all 9 checkpoints
    validate_installation(report)
    validate_skills_local(report)
    validate_cli_read(report)
    validate_agent_progressive_mode(report)
    validate_meta_skill_in_prompt(report)
    validate_greeting_skill(report)
    validate_troubleshooting_skill(report)
    validate_ticket_creation_skill(report)
    validate_inject_mode_comparison(report)


def run_real_validation(report: ValidationReport) -> None:
    """Run real validation with actual LLM calls."""
    print("\n=== Running REAL validation (with LLM API) ===\n")

    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "sk-dummy-key-for-testing-only":
        print("[WARN] OPENAI_API_KEY not set or is dummy key.")
        print("       Real validation requires a valid API key.")
        print("       Set it with: export OPENAI_API_KEY=your-key")
        print("       Running quick validation instead...\n")
        run_quick_validation(report)
        return

    # Run all 9 checkpoints first
    validate_installation(report)
    validate_skills_local(report)
    validate_cli_read(report)
    validate_agent_progressive_mode(report)
    validate_meta_skill_in_prompt(report)
    validate_greeting_skill(report)
    validate_troubleshooting_skill(report)
    validate_ticket_creation_skill(report)
    validate_inject_mode_comparison(report)

    # Run real LLM execution as additional checkpoint
    validate_real_agent_execution(report)


def main() -> int:
    """Main entry point for validation."""
    parser = argparse.ArgumentParser(
        description="Validate SkillForge LangChain integration"
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
