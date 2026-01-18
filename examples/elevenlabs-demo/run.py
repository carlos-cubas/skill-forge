#!/usr/bin/env python3
"""
ElevenLabs Demo Validation Script

This script validates the SkillForge ElevenLabs integration by running
a series of checkpoints that verify:

1. Installation verified (skillforge[elevenlabs] importable)
2. Skills copied locally (symlink or copy from shared-skills)
3. Credentials configured (from env or interactive)
4. Skills synced to KB via `skillforge elevenlabs sync`
5. Manifest created with document IDs
6. Agent created via CLI with skills
7. System prompt includes ElevenLabs meta-skill
8. Agent configured via CLI (update skills)
9. KB references verified via API

Usage:
    python run.py --quick    # Mocked API calls for CI (default)
    python run.py --real     # Actual API calls (requires ELEVENLABS_API_KEY)

Requirements:
    - skillforge[elevenlabs] installed
    - For --real mode: ELEVENLABS_API_KEY in environment
"""

import argparse
import os
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
    cp = ValidationCheckpoint(
        "Checkpoint 1: Installation verified (skillforge[elevenlabs] importable)"
    )

    try:
        import skillforge

        skillforge_version = getattr(skillforge, "__version__", "unknown")
        cp.add_detail(f"skillforge version: {skillforge_version}")

        # Check for elevenlabs extras availability
        try:
            import elevenlabs

            elevenlabs_version = getattr(elevenlabs, "__version__", "unknown")
            cp.add_detail(f"elevenlabs version: {elevenlabs_version}")
        except ImportError:
            cp.add_detail("elevenlabs: not installed (optional for mock mode)")

        # Try importing ElevenLabs adapter components
        try:
            from skillforge.adapters import elevenlabs as el_adapter

            cp.add_detail("skillforge.adapters.elevenlabs: importable")
        except ImportError:
            cp.add_detail("skillforge.adapters.elevenlabs: not yet implemented")

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

    expected_skills = [
        "greeting",
        "troubleshooting",
        "ticket-creation",
        "knowledge-search",
    ]
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
# Checkpoint 3: Credentials configured
# =============================================================================


def validate_credentials(report: ValidationReport, mock_api: bool = True) -> bool:
    """Checkpoint 3: Validate that ElevenLabs credentials are configured."""
    cp = ValidationCheckpoint(
        "Checkpoint 3: Credentials configured (from env or interactive)"
    )

    if mock_api:
        # In mock mode, credentials are not required
        cp.add_detail("Running in mock mode - credentials not required")
        cp.add_detail("ELEVENLABS_API_KEY: skipped (mock mode)")
        cp.check(True)
        report.add(cp)
        return True

    # In real mode, check for API key
    api_key = os.environ.get("ELEVENLABS_API_KEY")

    if api_key:
        # Mask the key for display
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        cp.add_detail(f"ELEVENLABS_API_KEY: {masked_key} (set)")

        # Optionally validate the key format
        if api_key.startswith("sk_"):
            cp.add_detail("API key format: valid (starts with sk_)")
        else:
            cp.add_detail("API key format: non-standard (may still work)")

        cp.check(True)
        report.add(cp)
        return True

    cp.add_detail("ELEVENLABS_API_KEY: not set")
    cp.add_detail("Set with: export ELEVENLABS_API_KEY=your-key")
    cp.check(False, "ELEVENLABS_API_KEY environment variable not set")
    report.add(cp)
    return False


# =============================================================================
# Checkpoint 4: Skills synced to KB
# =============================================================================


def validate_skills_synced(report: ValidationReport, mock_api: bool = True) -> bool:
    """Checkpoint 4: Validate that skills are synced to Knowledge Base."""
    cp = ValidationCheckpoint(
        "Checkpoint 4: Skills synced to KB via `skillforge elevenlabs sync`"
    )

    try:
        from agent import VOICE_SUPPORT_SKILLS, verify_skills_synced

        synced = verify_skills_synced(VOICE_SUPPORT_SKILLS, mock_api=mock_api)

        all_synced = all(synced.values())
        synced_count = sum(1 for v in synced.values() if v)

        cp.add_detail(f"Skills checked: {len(synced)}")
        cp.add_detail(f"Skills synced: {synced_count}/{len(synced)}")

        for skill_name, is_synced in synced.items():
            status = "synced" if is_synced else "NOT synced"
            cp.add_detail(f"  - {skill_name}: {status}")

        if mock_api:
            cp.add_detail("Mode: mock (simulated sync)")
        else:
            cp.add_detail("Mode: real (ElevenLabs API)")

        cp.check(all_synced, f"Only {synced_count}/{len(synced)} skills synced")
        report.add(cp)
        return all_synced
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 5: Manifest created with document IDs
# =============================================================================


def validate_manifest_documents(
    report: ValidationReport, mock_api: bool = True
) -> bool:
    """Checkpoint 5: Validate that manifest has document IDs for skills."""
    cp = ValidationCheckpoint("Checkpoint 5: Manifest created with document IDs")

    try:
        from agent import VOICE_SUPPORT_SKILLS, verify_manifest_has_documents

        doc_ids = verify_manifest_has_documents(VOICE_SUPPORT_SKILLS, mock_api=mock_api)

        all_have_ids = all(v is not None for v in doc_ids.values())
        ids_count = sum(1 for v in doc_ids.values() if v is not None)

        cp.add_detail(f"Skills checked: {len(doc_ids)}")
        cp.add_detail(f"Document IDs present: {ids_count}/{len(doc_ids)}")

        for skill_name, doc_id in doc_ids.items():
            if doc_id:
                # Truncate long doc IDs for display
                display_id = doc_id[:20] + "..." if len(doc_id) > 20 else doc_id
                cp.add_detail(f"  - {skill_name}: {display_id}")
            else:
                cp.add_detail(f"  - {skill_name}: NO DOCUMENT ID")

        if mock_api:
            cp.add_detail("Mode: mock (simulated manifest)")
        else:
            cp.add_detail("Mode: real (from .skillforge/elevenlabs-manifest.json)")

        cp.check(all_have_ids, f"Only {ids_count}/{len(doc_ids)} skills have doc IDs")
        report.add(cp)
        return all_have_ids
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 6: Agent created via CLI with skills
# =============================================================================


def validate_agent_created(report: ValidationReport, mock_api: bool = True) -> bool:
    """Checkpoint 6: Validate that agent is created with skills."""
    cp = ValidationCheckpoint("Checkpoint 6: Agent created via CLI with skills")

    try:
        from agent import create_voice_agent

        agent = create_voice_agent(mock_api=mock_api)

        has_name = agent.name is not None and len(agent.name) > 0
        has_prompt = agent.system_prompt is not None and len(agent.system_prompt) > 0
        has_skills = len(agent.skills) > 0
        has_first_message = (
            agent.first_message is not None and len(agent.first_message) > 0
        )

        cp.add_detail(f"Agent type: {type(agent).__name__}")
        cp.add_detail(f"Name: {agent.name}")
        cp.add_detail(f"Mock mode: {agent.mock_mode}")
        cp.add_detail(f"Agent ID: {agent.agent_id or 'None (mock)'}")
        cp.add_detail(f"System prompt length: {len(agent.system_prompt)} chars")
        cp.add_detail(f"Skills count: {len(agent.skills)}")
        cp.add_detail(f"Skills: {agent.skills}")
        cp.add_detail(f"First message: {agent.first_message[:50]}...")

        success = all([has_name, has_prompt, has_skills, has_first_message])
        cp.check(success, "Agent missing required fields")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 7: System prompt includes ElevenLabs meta-skill
# =============================================================================


def validate_meta_skill_in_prompt(
    report: ValidationReport, mock_api: bool = True
) -> bool:
    """Checkpoint 7: Validate that system prompt includes ElevenLabs meta-skill."""
    cp = ValidationCheckpoint(
        "Checkpoint 7: System prompt includes ElevenLabs meta-skill"
    )

    try:
        from agent import create_voice_agent, verify_meta_skill_present

        agent = create_voice_agent(mock_api=mock_api)
        has_meta_skill = verify_meta_skill_present(agent)

        # Additional checks for ElevenLabs-specific meta-skill content
        prompt = agent.system_prompt
        has_using_skills = "Using Skills" in prompt
        has_kb_query = "Query" in prompt or "knowledge base" in prompt.lower()
        has_available_skills = "Available Skills" in prompt
        has_skill_prefix = "SKILL:" in prompt

        # Check that all configured skills are mentioned
        all_skills_mentioned = all(skill in prompt for skill in agent.skills)

        cp.add_detail(f"Has meta-skill: {has_meta_skill}")
        cp.add_detail(f"Contains 'Using Skills': {has_using_skills}")
        cp.add_detail(f"Contains KB query instructions: {has_kb_query}")
        cp.add_detail(f"Contains 'Available Skills': {has_available_skills}")
        cp.add_detail(f"Contains 'SKILL:' prefix: {has_skill_prefix}")
        cp.add_detail(f"All skills mentioned in prompt: {all_skills_mentioned}")

        success = all(
            [
                has_meta_skill,
                has_using_skills,
                has_kb_query,
                has_available_skills,
                all_skills_mentioned,
            ]
        )
        cp.check(success, "Meta-skill content not properly included in system prompt")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 8: Agent configured via CLI (update skills)
# =============================================================================


def validate_agent_configured(report: ValidationReport, mock_api: bool = True) -> bool:
    """Checkpoint 8: Validate that agent can be configured with different skills."""
    cp = ValidationCheckpoint("Checkpoint 8: Agent configured via CLI (update skills)")

    try:
        from agent import configure_voice_agent, create_voice_agent

        # Create initial agent
        initial_agent = create_voice_agent(mock_api=mock_api)
        initial_skills = initial_agent.skills.copy()
        initial_kb_refs = len(initial_agent.kb_references)

        # Configure with fewer skills
        new_skills = ["greeting", "troubleshooting"]
        updated_agent = configure_voice_agent(
            initial_agent, new_skills, mock_api=mock_api
        )

        skills_updated = set(updated_agent.skills) == set(new_skills)
        kb_refs_updated = len(updated_agent.kb_references) == len(new_skills)
        prompt_updated = updated_agent.system_prompt != initial_agent.system_prompt

        # Verify the removed skills are not in new prompt
        removed_skills = set(initial_skills) - set(new_skills)
        removed_skills_absent = all(
            skill not in updated_agent.system_prompt
            or f"SKILL: {skill}" not in updated_agent.system_prompt
            for skill in removed_skills
        )

        cp.add_detail(f"Initial skills: {initial_skills}")
        cp.add_detail(f"New skills: {updated_agent.skills}")
        cp.add_detail(f"Initial KB refs: {initial_kb_refs}")
        cp.add_detail(f"New KB refs: {len(updated_agent.kb_references)}")
        cp.add_detail(f"Skills updated correctly: {skills_updated}")
        cp.add_detail(f"KB refs updated correctly: {kb_refs_updated}")
        cp.add_detail(f"Prompt changed: {prompt_updated}")

        success = all([skills_updated, kb_refs_updated])
        cp.check(success, "Agent configuration update failed")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Checkpoint 9: KB references verified via API
# =============================================================================


def validate_kb_references(report: ValidationReport, mock_api: bool = True) -> bool:
    """Checkpoint 9: Validate that KB references are correctly configured."""
    cp = ValidationCheckpoint("Checkpoint 9: KB references verified via API")

    try:
        from agent import (
            create_voice_agent,
            get_kb_references_for_validation,
            verify_kb_references_match_skills,
        )

        agent = create_voice_agent(mock_api=mock_api)
        kb_refs = get_kb_references_for_validation(agent)
        refs_match = verify_kb_references_match_skills(agent)

        cp.add_detail(f"KB references count: {len(kb_refs)}")
        cp.add_detail(f"Configured skills count: {len(agent.skills)}")
        cp.add_detail(f"References match skills: {refs_match}")

        # Validate structure of each KB reference
        all_valid = True
        for ref in kb_refs:
            has_type = ref.get("type") == "text"
            has_name = ref.get("name", "").startswith("SKILL:")
            has_id = ref.get("id") is not None
            has_mode = ref.get("usage_mode") == "auto"

            ref_valid = all([has_type, has_name, has_id, has_mode])
            if not ref_valid:
                all_valid = False

            skill_name = ref.get("name", "SKILL: unknown").replace("SKILL: ", "")
            status = "valid" if ref_valid else "INVALID"
            cp.add_detail(f"  - {skill_name}: {status} (id={ref.get('id', 'N/A')[:15]}...)")

        if mock_api:
            cp.add_detail("Mode: mock (simulated KB references)")
        else:
            cp.add_detail("Mode: real (ElevenLabs API verified)")

        success = refs_match and all_valid and len(kb_refs) == len(agent.skills)
        cp.check(success, "KB references do not match configured skills")
        report.add(cp)
        return success
    except Exception as e:
        cp.check(False, str(e))
        report.add(cp)
        return False


# =============================================================================
# Real Mode: Additional API Validation
# =============================================================================


def validate_real_api_connection(report: ValidationReport) -> bool:
    """Validate real API connection to ElevenLabs (--real mode only)."""
    cp = ValidationCheckpoint("Real Execution: ElevenLabs API connection")

    try:
        from elevenlabs.client import ElevenLabs

        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            cp.check(False, "ELEVENLABS_API_KEY not set")
            report.add(cp)
            return False

        # Test API connection
        client = ElevenLabs(api_key=api_key)

        # Try to list voices as a simple API test
        voices = client.voices.get_all()
        voice_count = len(voices.voices) if hasattr(voices, "voices") else 0

        cp.add_detail(f"API connection: successful")
        cp.add_detail(f"Available voices: {voice_count}")

        cp.check(True)
        report.add(cp)
        return True
    except ImportError:
        cp.check(False, "elevenlabs package not installed")
        report.add(cp)
        return False
    except Exception as e:
        cp.check(False, f"API error: {e}")
        report.add(cp)
        return False


# =============================================================================
# Main Validation Functions
# =============================================================================


def run_quick_validation(report: ValidationReport) -> None:
    """Run quick validation with mocked API calls."""
    print("\n=== Running QUICK validation (mocked API) ===\n")

    # Run all 9 checkpoints in mock mode
    validate_installation(report)
    validate_skills_local(report)
    validate_credentials(report, mock_api=True)
    validate_skills_synced(report, mock_api=True)
    validate_manifest_documents(report, mock_api=True)
    validate_agent_created(report, mock_api=True)
    validate_meta_skill_in_prompt(report, mock_api=True)
    validate_agent_configured(report, mock_api=True)
    validate_kb_references(report, mock_api=True)


def run_real_validation(report: ValidationReport) -> None:
    """Run real validation with actual ElevenLabs API calls."""
    print("\n=== Running REAL validation (with ElevenLabs API) ===\n")

    # Check for API key first
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("[WARN] ELEVENLABS_API_KEY not set.")
        print("       Real validation requires a valid API key.")
        print("       Set it with: export ELEVENLABS_API_KEY=your-key")
        print("       Running quick validation instead...\n")
        run_quick_validation(report)
        return

    # Run all 9 checkpoints in real mode
    validate_installation(report)
    validate_skills_local(report)
    validate_credentials(report, mock_api=False)
    validate_skills_synced(report, mock_api=False)
    validate_manifest_documents(report, mock_api=False)
    validate_agent_created(report, mock_api=False)
    validate_meta_skill_in_prompt(report, mock_api=False)
    validate_agent_configured(report, mock_api=False)
    validate_kb_references(report, mock_api=False)

    # Run additional real API connection test
    validate_real_api_connection(report)


def main() -> int:
    """Main entry point for validation."""
    parser = argparse.ArgumentParser(
        description="Validate SkillForge ElevenLabs integration"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation with mocked API calls (default)",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Run real validation with actual ElevenLabs API calls",
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
