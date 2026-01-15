"""
Test: ElevenLabs End-to-End Validation (Issue #25 - Phase 2.8)

This test validates the complete ElevenLabs adapter with generic test skills.
Confirms the full flow: sync skills -> create agent -> agent uses skills via RAG.

Test Fixtures Used:
    - example-greeting: Simple greeting skill
    - example-summarizer: Text summarization skill
    - example-calculator: Math calculation skill

Environment Requirements:
    - ELEVENLABS_API_KEY must be set (via .env or environment)

Validation Checklist:
    - Sync Validation: Skills appear in ElevenLabs KB, manifest file created
    - Agent Configuration: Agent created with KB access, system prompt includes meta-skill
    - Skill Usage: Test greeting, summarizer, and calculator skills via RAG retrieval
"""

import os
import pytest
import time
from pathlib import Path
from dotenv import load_dotenv
from unittest.mock import patch

# Load environment variables from .env
load_dotenv()

# Test fixture skills directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "skills"
TEST_SKILLS = ["example-greeting", "example-summarizer", "example-calculator"]


def has_api_key():
    """Check if ElevenLabs API key is available."""
    return bool(os.getenv("ELEVENLABS_API_KEY"))


def get_test_config():
    """Return a test configuration that points to fixture skills."""
    return {
        "skill_paths": [str(FIXTURES_DIR / "*")],
        "skill_mode": "progressive",
    }


@pytest.fixture
def elevenlabs_manifest():
    """Create and cleanup an ElevenLabs manifest for testing."""
    from skillforge.adapters.elevenlabs import ElevenLabsManifest

    # Use a test-specific manifest location
    test_root = Path(__file__).parent
    manifest = ElevenLabsManifest(project_root=test_root)

    yield manifest

    # Cleanup: Remove all synced documents
    for skill_name in manifest.list_synced_skills():
        try:
            doc_id = manifest.get_document_id(skill_name)
            if doc_id:
                client = get_elevenlabs_client()
                if client:
                    client.conversational_ai.knowledge_base.documents.delete(doc_id)
        except Exception as e:
            print(f"Warning: Could not cleanup document for {skill_name}: {e}")

    # Clear the manifest
    manifest.clear()


def get_elevenlabs_client():
    """Get configured ElevenLabs client."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return None

    from elevenlabs import ElevenLabs
    return ElevenLabs(api_key=api_key)


@pytest.mark.integration
@pytest.mark.elevenlabs
@pytest.mark.skipif(not has_api_key(), reason="ELEVENLABS_API_KEY not set")
class TestElevenLabsSyncValidation:
    """
    Validate skill sync to ElevenLabs Knowledge Base.

    Tests:
    - Skills are discovered from fixture directory
    - Skills are uploaded to ElevenLabs KB
    - Manifest file is created with document IDs
    - Content hash is stored for change detection
    """

    def test_sync_discovers_skills(self):
        """
        Test that sync_skills discovers test fixture skills.

        Expected: All 3 test skills are discovered from fixtures directory.
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader

        # Load skills from fixtures
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        skills = loader.discover()

        # Verify test skills are found
        found_skills = set(skills.keys())
        expected_skills = set(TEST_SKILLS)

        assert expected_skills.issubset(found_skills), (
            f"Missing skills: {expected_skills - found_skills}. "
            f"Found: {found_skills}"
        )

        print(f"\nDiscovered {len(skills)} skills from fixtures:")
        for name, skill in skills.items():
            print(f"  - {name}: {skill.description}")

    def test_sync_skills_to_kb(self, elevenlabs_manifest):
        """
        Test that skills are synced to ElevenLabs Knowledge Base.

        Expected:
        - All test skills are uploaded to KB
        - Document IDs are returned
        - Manifest is updated with document IDs and hashes
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import sync_skills_to_kb

        # Load skills from fixtures
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        all_skills = loader.discover()

        # Filter to just test skills
        skills_to_sync = {name: all_skills[name] for name in TEST_SKILLS if name in all_skills}

        # Sync to KB
        doc_ids = sync_skills_to_kb(skills_to_sync, elevenlabs_manifest, force=True)

        # Verify all skills were synced
        assert len(doc_ids) == len(TEST_SKILLS), (
            f"Expected {len(TEST_SKILLS)} skills synced, got {len(doc_ids)}"
        )

        # Verify manifest was updated
        for skill_name in TEST_SKILLS:
            assert elevenlabs_manifest.has_skill(skill_name), (
                f"Skill {skill_name} not in manifest after sync"
            )
            doc_id = elevenlabs_manifest.get_document_id(skill_name)
            assert doc_id is not None, f"No document ID for {skill_name}"
            assert elevenlabs_manifest.get_content_hash(skill_name) is not None, (
                f"No content hash for {skill_name}"
            )

        print(f"\nSynced {len(doc_ids)} skills to ElevenLabs KB:")
        for name, doc_id in doc_ids.items():
            print(f"  - {name}: {doc_id}")

    def test_sync_idempotent(self, elevenlabs_manifest):
        """
        Test that re-syncing unchanged skills skips upload.

        Expected:
        - First sync uploads all skills
        - Second sync skips unchanged skills (no force flag)
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import sync_skill_to_kb

        # Load a single test skill
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        all_skills = loader.discover()

        skill_name = "example-greeting"
        skill = all_skills[skill_name]

        # First sync - should upload
        doc_id1, was_updated1 = sync_skill_to_kb(skill, elevenlabs_manifest, force=False)
        assert was_updated1 is True, "First sync should upload"
        print(f"\nFirst sync: uploaded {skill_name} -> {doc_id1}")

        # Second sync - should skip (content unchanged)
        doc_id2, was_updated2 = sync_skill_to_kb(skill, elevenlabs_manifest, force=False)
        assert was_updated2 is False, "Second sync should skip unchanged content"
        assert doc_id1 == doc_id2, "Document ID should remain the same"
        print(f"Second sync: skipped (unchanged)")

        # Force sync - should re-upload
        doc_id3, was_updated3 = sync_skill_to_kb(skill, elevenlabs_manifest, force=True)
        assert was_updated3 is True, "Force sync should upload"
        print(f"Force sync: re-uploaded {skill_name} -> {doc_id3}")


@pytest.mark.integration
@pytest.mark.elevenlabs
@pytest.mark.skipif(not has_api_key(), reason="ELEVENLABS_API_KEY not set")
class TestElevenLabsAgentCreation:
    """
    Validate agent creation with skills.

    Tests:
    - Agent is created with skills specified
    - System prompt includes meta-skill instructions
    - Agent has KB access to skill documents
    """

    def test_build_prompt_includes_skills(self, elevenlabs_manifest):
        """
        Test that build_prompt includes meta-skill and skill directory.

        Expected:
        - Core prompt is preserved
        - Meta-skill instructions are added
        - Skill directory lists all skills with RAG queries
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import sync_skills_to_kb, build_prompt

        # First sync skills to KB
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        all_skills = loader.discover()
        skills_to_sync = {name: all_skills[name] for name in TEST_SKILLS if name in all_skills}
        sync_skills_to_kb(skills_to_sync, elevenlabs_manifest, force=True)

        # Build prompt
        core_prompt = "You are a helpful test assistant."
        prompt = build_prompt(core_prompt, TEST_SKILLS, elevenlabs_manifest)

        # Verify core prompt is preserved
        assert core_prompt in prompt, "Core prompt should be in combined prompt"

        # Verify meta-skill content is included
        assert "Using Skills" in prompt or "Available Skills" in prompt, (
            "Meta-skill content should be included"
        )

        # Verify skill directory includes all test skills
        for skill_name in TEST_SKILLS:
            assert skill_name in prompt, f"Skill {skill_name} should be in directory"
            assert f'SKILL: {skill_name}' in prompt, (
                f"RAG query instruction for {skill_name} should be included"
            )

        print(f"\nGenerated prompt ({len(prompt)} chars):")
        print("-" * 40)
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)

    def test_create_agent_with_skills(self, elevenlabs_manifest):
        """
        Test creating an ElevenLabs agent with skills.

        Expected:
        - Agent is created successfully
        - Agent ID is returned
        - Agent has KB references for skills
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import (
            sync_skills_to_kb,
            create_agent,
        )

        client = get_elevenlabs_client()

        # First sync skills to KB
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        all_skills = loader.discover()
        skills_to_sync = {name: all_skills[name] for name in TEST_SKILLS if name in all_skills}
        sync_skills_to_kb(skills_to_sync, elevenlabs_manifest, force=True)

        # Create agent
        agent_id = None
        try:
            agent_id = create_agent(
                name="SkillForge E2E Test Agent",
                core_prompt="You are a helpful assistant for testing SkillForge integration.",
                first_message="Hi! I'm ready to help. How can I assist you?",
                skills=TEST_SKILLS,
                language="en",
                llm="gpt-4o-mini",
                manifest=elevenlabs_manifest,
            )

            assert agent_id is not None, "Agent creation should return an ID"
            print(f"\nAgent created successfully: {agent_id}")

            # Verify agent exists and has KB references
            agent_data = client.conversational_ai.agents.get(agent_id)
            assert agent_data is not None, "Should be able to retrieve created agent"

            # Check prompt contains skill references
            if hasattr(agent_data, 'conversation_config'):
                conv_config = agent_data.conversation_config
                if hasattr(conv_config, 'agent') and hasattr(conv_config.agent, 'prompt'):
                    prompt_config = conv_config.agent.prompt
                    prompt_text = getattr(prompt_config, 'prompt', '')
                    print(f"Agent prompt length: {len(prompt_text)} chars")

                    # Check KB references
                    kb_refs = getattr(prompt_config, 'knowledge_base', [])
                    print(f"KB references: {len(kb_refs) if kb_refs else 0}")

        finally:
            # Cleanup agent
            if agent_id and client:
                try:
                    client.conversational_ai.agents.delete(agent_id)
                    print(f"Agent {agent_id} cleaned up")
                except Exception as e:
                    print(f"Warning: Could not delete agent: {e}")

    def test_python_api_agent_create(self, elevenlabs_manifest):
        """
        Test the high-level Python API: Agent.create()

        Expected:
        - Agent class can create agent with skills
        - Agent instance is returned with correct attributes
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import sync_skills_to_kb
        from skillforge.elevenlabs import Agent

        client = get_elevenlabs_client()

        # First sync skills to KB
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        all_skills = loader.discover()
        skills_to_sync = {name: all_skills[name] for name in TEST_SKILLS if name in all_skills}
        sync_skills_to_kb(skills_to_sync, elevenlabs_manifest, force=True)

        # Test requires mocking the manifest lookup - patch load_config
        agent = None
        try:
            with patch('skillforge.adapters.elevenlabs.agent.ElevenLabsManifest') as MockManifest:
                MockManifest.return_value = elevenlabs_manifest

                agent = Agent.create(
                    name="SkillForge Python API Test Agent",
                    system_prompt="You are a helpful assistant for testing.",
                    skills=TEST_SKILLS,
                    first_message="Hello! How can I help?",
                )

            assert agent is not None, "Agent.create should return an Agent instance"
            assert agent.agent_id is not None, "Agent should have an ID"
            assert agent.name == "SkillForge Python API Test Agent"
            assert set(agent.skills) == set(TEST_SKILLS)

            print(f"\nAgent.create() successful:")
            print(f"  ID: {agent.agent_id}")
            print(f"  Name: {agent.name}")
            print(f"  Skills: {agent.skills}")

        finally:
            # Cleanup
            if agent and client:
                try:
                    client.conversational_ai.agents.delete(agent.agent_id)
                    print(f"Agent {agent.agent_id} cleaned up")
                except Exception as e:
                    print(f"Warning: Could not delete agent: {e}")


@pytest.mark.integration
@pytest.mark.elevenlabs
@pytest.mark.skipif(not has_api_key(), reason="ELEVENLABS_API_KEY not set")
class TestElevenLabsSkillUsage:
    """
    Validate skill usage via RAG retrieval.

    Note: ElevenLabs conversational AI doesn't expose a simple text-to-text API
    for testing conversations. These tests validate that the KB documents are
    properly formatted and retrievable.

    For full conversation testing, manual testing with ElevenLabs widget is needed.
    """

    def test_skill_document_format(self, elevenlabs_manifest):
        """
        Test that skill documents are formatted correctly for RAG retrieval.

        Expected:
        - Document has SKILL header
        - Document contains skill instructions
        - Document can be retrieved from KB
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import format_skill_for_kb

        # Load a test skill
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        skills = loader.discover()

        skill = skills["example-greeting"]
        formatted = format_skill_for_kb(skill)

        # Verify format
        assert formatted.startswith("# SKILL: example-greeting"), (
            "Document should start with SKILL header"
        )
        assert skill.description in formatted, "Description should be included"
        assert "When to Use" in formatted, "Instructions should be included"

        print(f"\nFormatted skill document:")
        print("-" * 40)
        print(formatted)

    def test_skill_kb_retrieval(self, elevenlabs_manifest):
        """
        Test that synced skills can be listed from KB.

        Expected:
        - Documents are visible in KB listing
        - Document names contain SKILL prefix
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import sync_skills_to_kb

        client = get_elevenlabs_client()

        # Sync skills to KB
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        all_skills = loader.discover()
        skills_to_sync = {name: all_skills[name] for name in TEST_SKILLS if name in all_skills}
        doc_ids = sync_skills_to_kb(skills_to_sync, elevenlabs_manifest, force=True)

        # List all KB documents (use list() on knowledge_base, not documents)
        kb_list = client.conversational_ai.knowledge_base.list()
        doc_names = []

        # The list response may be a paginated response with documents attribute
        docs = getattr(kb_list, 'documents', kb_list) if hasattr(kb_list, 'documents') else kb_list

        if hasattr(docs, '__iter__'):
            for doc in docs:
                doc_id = getattr(doc, 'id', None) or getattr(doc, 'document_id', None)
                doc_name = getattr(doc, 'name', 'unknown')
                if doc_id in doc_ids.values():
                    doc_names.append(doc_name)

        print(f"\nSynced skill documents in KB:")
        for name in doc_names:
            print(f"  - {name}")

        # Verify skill documents are present
        for skill_name in TEST_SKILLS:
            expected_name = f"SKILL: {skill_name}"
            assert expected_name in doc_names, (
                f"Document '{expected_name}' not found in KB"
            )

    def test_greeting_skill_scenario(self, elevenlabs_manifest):
        """
        Test scenario: Greeting skill for user introduction.

        Validates the skill document contains correct guidance for greetings.
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import format_skill_for_kb

        # Load greeting skill
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        skills = loader.discover()

        skill = skills["example-greeting"]
        formatted = format_skill_for_kb(skill)

        # Verify greeting skill content
        assert "When to Use" in formatted
        assert "start of a conversation" in formatted.lower() or "hello" in formatted.lower()
        assert "Output Format" in formatted

        print(f"\nGreeting skill scenario:")
        print(f"  Trigger: User says 'Hello'")
        print(f"  Expected behavior: Agent uses greeting skill")
        print(f"  Skill provides structure for warm greeting")

    def test_summarizer_skill_scenario(self, elevenlabs_manifest):
        """
        Test scenario: Summarizer skill for text summarization.

        Validates the skill document contains correct guidance for summarizing.
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import format_skill_for_kb

        # Load summarizer skill
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        skills = loader.discover()

        skill = skills["example-summarizer"]
        formatted = format_skill_for_kb(skill)

        # Verify summarizer skill content
        assert "When to Use" in formatted
        assert "summarize" in formatted.lower()
        assert "bullet" in formatted.lower() or "key point" in formatted.lower()

        print(f"\nSummarizer skill scenario:")
        print(f"  Trigger: User asks to summarize text")
        print(f"  Expected behavior: Agent uses summarizer skill")
        print(f"  Skill provides 3-5 bullet point format")

    def test_calculator_skill_scenario(self, elevenlabs_manifest):
        """
        Test scenario: Calculator skill for math questions.

        Validates the skill document contains correct guidance for calculations.
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import format_skill_for_kb

        # Load calculator skill
        config = SkillForgeConfig(
            skill_paths=[str(FIXTURES_DIR / "*")],
            skill_mode="progressive"
        )
        loader = SkillLoader(config.skill_paths)
        skills = loader.discover()

        skill = skills["example-calculator"]
        formatted = format_skill_for_kb(skill)

        # Verify calculator skill content
        assert "When to Use" in formatted
        assert "calculation" in formatted.lower() or "mathematical" in formatted.lower()
        assert "step" in formatted.lower()  # Step-by-step format

        print(f"\nCalculator skill scenario:")
        print(f"  Trigger: User asks math question")
        print(f"  Expected behavior: Agent uses calculator skill")
        print(f"  Skill provides step-by-step calculation format")


@pytest.mark.integration
@pytest.mark.elevenlabs
@pytest.mark.skipif(not has_api_key(), reason="ELEVENLABS_API_KEY not set")
class TestElevenLabsFullE2E:
    """
    Full end-to-end validation: sync -> create agent -> verify configuration.

    This test class performs the complete workflow as a single test.
    """

    def test_complete_e2e_flow(self, elevenlabs_manifest):
        """
        Complete E2E test: sync skills, create agent, verify configuration.

        This is the main validation test for Issue #25 Phase 2.8.
        """
        from skillforge.core.config import SkillForgeConfig
        from skillforge.core.loader import SkillLoader
        from skillforge.adapters.elevenlabs import (
            sync_skills_to_kb,
            create_agent,
            get_kb_references,
        )

        client = get_elevenlabs_client()
        results = {
            "sync_validation": False,
            "agent_creation": False,
            "prompt_validation": False,
            "kb_validation": False,
        }

        agent_id = None

        try:
            # === Step 1: Sync Skills ===
            print("\n" + "=" * 60)
            print("Step 1: Sync Skills to ElevenLabs KB")
            print("=" * 60)

            config = SkillForgeConfig(
                skill_paths=[str(FIXTURES_DIR / "*")],
                skill_mode="progressive"
            )
            loader = SkillLoader(config.skill_paths)
            all_skills = loader.discover()
            skills_to_sync = {name: all_skills[name] for name in TEST_SKILLS if name in all_skills}

            doc_ids = sync_skills_to_kb(skills_to_sync, elevenlabs_manifest, force=True)

            assert len(doc_ids) == len(TEST_SKILLS), "All skills should be synced"
            for skill_name in TEST_SKILLS:
                assert elevenlabs_manifest.has_skill(skill_name), f"{skill_name} should be in manifest"

            results["sync_validation"] = True
            print(f"  Synced {len(doc_ids)} skills:")
            for name, doc_id in doc_ids.items():
                print(f"    - {name}: {doc_id}")

            # === Step 2: Create Agent ===
            print("\n" + "=" * 60)
            print("Step 2: Create Agent with Skills")
            print("=" * 60)

            agent_id = create_agent(
                name="SkillForge Complete E2E Test Agent",
                core_prompt="""You are a helpful assistant with specialized skills.

When users interact with you:
1. For greetings: Use a warm, structured greeting
2. For summarization requests: Provide bullet-point summaries
3. For math questions: Show step-by-step calculations

Always announce when you're using a skill.""",
                first_message="Hi there! I'm equipped with greeting, summarization, and calculation skills. How can I help you today?",
                skills=TEST_SKILLS,
                language="en",
                llm="gpt-4o-mini",
                manifest=elevenlabs_manifest,
            )

            assert agent_id is not None, "Agent should be created"
            results["agent_creation"] = True
            print(f"  Agent created: {agent_id}")

            # === Step 3: Verify Agent Configuration ===
            print("\n" + "=" * 60)
            print("Step 3: Verify Agent Configuration")
            print("=" * 60)

            agent_data = client.conversational_ai.agents.get(agent_id)

            # Check prompt
            if hasattr(agent_data, 'conversation_config'):
                conv_config = agent_data.conversation_config
                if hasattr(conv_config, 'agent') and hasattr(conv_config.agent, 'prompt'):
                    prompt_config = conv_config.agent.prompt
                    prompt_text = getattr(prompt_config, 'prompt', '')

                    # Verify prompt contains skill references
                    has_skills_section = any(
                        marker in prompt_text
                        for marker in ["Available Skills", "Using Skills", "SKILL:"]
                    )

                    if has_skills_section:
                        results["prompt_validation"] = True
                        print(f"  Prompt length: {len(prompt_text)} chars")
                        print(f"  Contains skill instructions: Yes")
                    else:
                        print(f"  Warning: Prompt may be missing skill instructions")
                        print(f"  Prompt preview: {prompt_text[:200]}...")

            # Check KB references
            kb_refs = get_kb_references(TEST_SKILLS, elevenlabs_manifest)
            if len(kb_refs) == len(TEST_SKILLS):
                results["kb_validation"] = True
                print(f"  KB references: {len(kb_refs)}")
                for ref in kb_refs:
                    print(f"    - {ref['name']}: {ref['id'][:20]}...")

            # === Summary ===
            print("\n" + "=" * 60)
            print("E2E Validation Results")
            print("=" * 60)

            all_passed = all(results.values())
            for check, passed in results.items():
                status = "PASS" if passed else "FAIL"
                print(f"  {check}: {status}")

            print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")

            assert all_passed, f"E2E validation failed: {results}"

        finally:
            # Cleanup
            if agent_id and client:
                try:
                    client.conversational_ai.agents.delete(agent_id)
                    print(f"\nCleanup: Agent {agent_id} deleted")
                except Exception as e:
                    print(f"Warning: Could not delete agent: {e}")


# Manual validation helper functions
def run_manual_validation():
    """
    Run manual E2E validation for interactive testing.

    Usage:
        python -c "from tests.integration.test_elevenlabs_e2e import run_manual_validation; run_manual_validation()"
    """
    load_dotenv()

    if not has_api_key():
        print("ERROR: ELEVENLABS_API_KEY not set")
        return

    from skillforge.adapters.elevenlabs import ElevenLabsManifest

    print("=" * 60)
    print("ElevenLabs E2E Manual Validation")
    print("=" * 60)

    # Create temporary manifest
    manifest = ElevenLabsManifest()

    # Run full E2E test
    test = TestElevenLabsFullE2E()

    class FakeManifest:
        """Fixture substitute for manual testing."""
        def __enter__(self):
            return manifest
        def __exit__(self, *args):
            # Cleanup
            client = get_elevenlabs_client()
            for skill_name in manifest.list_synced_skills():
                try:
                    doc_id = manifest.get_document_id(skill_name)
                    if doc_id and client:
                        client.conversational_ai.knowledge_base.documents.delete(doc_id)
                except Exception as e:
                    print(f"Cleanup warning: {e}")
            manifest.clear()

    with FakeManifest() as m:
        try:
            test.test_complete_e2e_flow(m)
        except Exception as e:
            print(f"\nE2E Validation FAILED: {e}")
            raise


if __name__ == "__main__":
    # Run manual validation when executed directly
    run_manual_validation()
