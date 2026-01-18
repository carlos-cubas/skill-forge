"""
Customer Support Voice Agent - ElevenLabs Demo with SkillForge Skills

This module demonstrates a voice customer support agent using SkillForge's
ElevenLabs adapter. It validates:

1. Knowledge Base-backed skills (RAG-based skill retrieval)
2. Full ElevenLabs workflow (sync -> create -> configure)
3. ElevenLabs-specific meta-skill injection
4. Manifest tracking with document IDs

Validation Checkpoints Supported:
- Checkpoint 4: Skills synced to KB via `skillforge elevenlabs sync`
- Checkpoint 5: Manifest created with document IDs
- Checkpoint 6: Agent created via CLI with skills
- Checkpoint 7: System prompt includes ElevenLabs meta-skill
- Checkpoint 8: Agent configured via CLI (update skills)
- Checkpoint 9: KB references verified via API

Usage:
    # Import and create agent
    from agent import CustomerSupportVoiceAgent, create_voice_agent

    # Mock mode (default - no API calls)
    agent = create_voice_agent(mock_api=True)

    # Real mode (requires ElevenLabs credentials)
    agent = create_voice_agent(mock_api=False)

    # Direct testing
    python agent.py
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Demo directory (for resolving skills path)
DEMO_DIR = Path(__file__).parent

# Base system prompt for voice customer support agent
BASE_VOICE_PROMPT = """You are a friendly and professional voice customer support agent for a software company.

Your voice interaction style:
- Speak clearly and at a conversational pace
- Use natural pauses and intonation
- Be warm and empathetic in your responses
- Keep responses concise for voice delivery (avoid long monologues)
- Confirm understanding before proceeding

Your responsibilities:
- Welcome customers warmly
- Listen to their issues and concerns
- Diagnose technical problems systematically
- Create support tickets when issues need escalation
- Search the knowledge base for solutions

Remember: In voice interactions, clarity and brevity are essential.
"""

# Default skills for the voice customer support agent
VOICE_SUPPORT_SKILLS = [
    "greeting",
    "troubleshooting",
    "ticket-creation",
    "knowledge-search",
]


@dataclass
class CustomerSupportVoiceAgent:
    """Wrapper for an ElevenLabs agent with SkillForge skill support.

    This class provides a convenient wrapper that exposes the system prompt,
    KB references, and other metadata for validation and testing purposes.
    It uses SkillForge's ElevenLabs adapter to compose the prompt with skills.

    Attributes:
        agent_id: The ElevenLabs agent ID (None if mock mode).
        name: The agent's name.
        system_prompt: The composed system prompt including skill content.
        first_message: The initial message sent to users.
        skills: List of skill names used by this agent.
        kb_references: List of Knowledge Base reference dicts for skills.
        manifest_path: Path to the ElevenLabs manifest file.
        mock_mode: Whether this agent is running in mock mode.
    """

    agent_id: Optional[str]
    name: str
    system_prompt: str
    first_message: str
    skills: list[str]
    kb_references: list[dict] = field(default_factory=list)
    manifest_path: Optional[Path] = None
    mock_mode: bool = True

    def get_conversation_config(self) -> dict[str, Any]:
        """Get the conversation configuration for this agent.

        Returns:
            Dictionary with agent configuration suitable for ElevenLabs SDK.
        """
        config: dict[str, Any] = {
            "agent": {
                "first_message": self.first_message,
                "language": "en",
                "prompt": {
                    "prompt": self.system_prompt,
                    "llm": "gpt-4o-mini",
                },
            }
        }

        if self.kb_references:
            config["agent"]["prompt"]["knowledge_base"] = self.kb_references

        return config


class MockElevenLabsManifest:
    """Mock ElevenLabsManifest for testing without real files.

    Simulates the manifest behavior with in-memory storage.
    """

    def __init__(self) -> None:
        """Initialize mock manifest with sample data."""
        self._documents: dict[str, dict] = {}

    def set_document_id(
        self,
        skill_name: str,
        doc_id: str,
        content_hash: Optional[str] = None,
    ) -> None:
        """Set document ID for a skill."""
        self._documents[skill_name] = {
            "document_id": doc_id,
            "synced_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "content_hash": content_hash or f"mock_hash_{skill_name}",
        }

    def get_document_id(self, skill_name: str) -> Optional[str]:
        """Get document ID for a skill."""
        entry = self._documents.get(skill_name)
        return entry.get("document_id") if entry else None

    def has_skill(self, skill_name: str) -> bool:
        """Check if a skill has been synced."""
        return skill_name in self._documents

    def get_sync_info(self, skill_name: str) -> Optional[dict]:
        """Get full sync information for a skill."""
        return self._documents.get(skill_name, {}).copy() or None

    def list_synced_skills(self) -> list[str]:
        """List all synced skill names."""
        return sorted(self._documents.keys())

    def get_content_hash(self, skill_name: str) -> Optional[str]:
        """Get content hash for a skill."""
        entry = self._documents.get(skill_name)
        return entry.get("content_hash") if entry else None

    def save(self) -> None:
        """No-op for mock manifest."""
        pass


def _create_mock_manifest(skills: list[str]) -> MockElevenLabsManifest:
    """Create a mock manifest with document IDs for the given skills.

    Args:
        skills: List of skill names to populate.

    Returns:
        MockElevenLabsManifest with simulated document IDs.
    """
    manifest = MockElevenLabsManifest()
    for i, skill_name in enumerate(skills):
        # Generate deterministic mock document IDs
        mock_doc_id = f"doc_mock_{skill_name.replace('-', '_')}_{i:03d}"
        manifest.set_document_id(skill_name, mock_doc_id)
    return manifest


def _build_prompt_with_skills(
    core_prompt: str,
    skills: list[str],
    manifest: Any,
) -> str:
    """Build combined prompt: core identity + meta-skill + skill directory.

    This function composes the system prompt using either the real
    ElevenLabs adapter functions or a mock implementation.

    Args:
        core_prompt: The core identity/system prompt.
        skills: List of skill names to include.
        manifest: ElevenLabsManifest or MockElevenLabsManifest instance.

    Returns:
        Combined prompt string.
    """
    # Try to use real adapter functions
    try:
        from skillforge.adapters.elevenlabs import build_prompt

        return build_prompt(core_prompt, skills, manifest)
    except ImportError:
        pass

    # Fallback: Build prompt manually for mock mode
    # Simulate the meta-skill content structure
    skills_list_lines = []
    for skill_name in skills:
        skills_list_lines.append(
            f'- **{skill_name}**: (skill description) Query: "SKILL: {skill_name}"'
        )
    skills_list = "\n".join(skills_list_lines)

    meta_skill_content = f"""# Using Skills

You have access to specialized skills that provide expert guidance for specific situations.

## Before Acting on Complex Situations

1. Check the **Available Skills** list below
2. If a skill matches your situation, **load it first**
3. Announce: "Let me use my [skill-name] guidance for this"
4. Query your knowledge base for "SKILL: [skill-name]"
5. Follow the retrieved instructions precisely

## Important Guidelines

- Always load the skill before acting on its domain
- Follow skill instructions precisely - they are tested procedures
- One skill at a time - complete one before starting another

## Available Skills

{skills_list}"""

    return f"""{core_prompt.strip()}

---

{meta_skill_content}"""


def _get_kb_references_for_skills(
    skills: list[str],
    manifest: Any,
) -> list[dict]:
    """Get Knowledge Base references for skills.

    Args:
        skills: List of skill names.
        manifest: ElevenLabsManifest or MockElevenLabsManifest instance.

    Returns:
        List of KB reference dictionaries.
    """
    references = []
    for skill_name in skills:
        doc_id = manifest.get_document_id(skill_name)
        if doc_id:
            references.append({
                "type": "text",
                "name": f"SKILL: {skill_name}",
                "id": doc_id,
                "usage_mode": "auto",
            })
    return references


def sync_skills_to_elevenlabs(
    skills: list[str],
    mock_api: bool = True,
    force: bool = False,
) -> tuple[Any, dict[str, str]]:
    """Sync skills to ElevenLabs Knowledge Base.

    This is the key integration point: it ensures skills are uploaded to the KB
    before agent creation/configuration. Returns a manifest and document ID mapping.

    Args:
        skills: List of skill names to sync.
        mock_api: If True, use mock manifest with fake document IDs.
        force: If True, re-sync even if content hasn't changed.

    Returns:
        Tuple of (manifest, doc_ids) where:
        - manifest: ElevenLabsManifest or MockElevenLabsManifest instance
        - doc_ids: Dictionary mapping skill names to document IDs

    Raises:
        ImportError: If real mode requested but adapter not available.
        SyncError: If real sync operation fails.

    Example:
        >>> manifest, doc_ids = sync_skills_to_elevenlabs(["greeting"], mock_api=True)
        >>> "greeting" in doc_ids
        True
    """
    if mock_api:
        # Mock mode: create mock manifest with fake document IDs
        manifest = _create_mock_manifest(skills)
        doc_ids = {skill: manifest.get_document_id(skill) for skill in skills}
        return manifest, doc_ids

    # Real mode: use actual ElevenLabs adapter
    from skillforge.adapters.elevenlabs import (
        ElevenLabsManifest,
        sync_skills_to_kb,
    )
    from skillforge.core.loader import SkillLoader

    # Load skills from the demo's skills directory
    skills_dir = DEMO_DIR / "skills"
    loader = SkillLoader([str(skills_dir / "*")], base_path=DEMO_DIR)
    discovered_skills = loader.discover()

    # Filter to only requested skills and validate they exist
    skills_to_sync: dict[str, Any] = {}
    missing = []
    for skill_name in skills:
        if skill_name in discovered_skills:
            skills_to_sync[skill_name] = discovered_skills[skill_name]
        else:
            missing.append(skill_name)

    if missing:
        available = ", ".join(sorted(discovered_skills.keys())) or "(none)"
        raise ValueError(
            f"Skills not found: {', '.join(missing)}. Available: {available}"
        )

    # Sync to ElevenLabs KB
    manifest = ElevenLabsManifest()
    doc_ids = sync_skills_to_kb(skills_to_sync, manifest, force=force)

    # Track documents for cleanup
    try:
        from run import _created_resources
        for skill_name, doc_id in doc_ids.items():
            _created_resources["documents"].append((skill_name, doc_id))
    except ImportError:
        pass  # run.py not imported (direct agent.py usage)

    logger.info(f"Synced {len(doc_ids)} skills to ElevenLabs KB")
    return manifest, doc_ids


def create_voice_agent(
    name: str = "Voice Support Agent",
    core_prompt: str = BASE_VOICE_PROMPT,
    first_message: str = "Hello! I'm here to help you today. How can I assist you?",
    skills: Optional[list[str]] = None,
    voice_id: Optional[str] = None,
    mock_api: bool = True,
    force_sync: bool = False,
) -> CustomerSupportVoiceAgent:
    """Create a voice customer support agent with skills.

    Creates an ElevenLabs agent configured with the combined prompt
    (core + meta-skill + skill directory) and KB references for each skill.

    In real mode, this function:
    1. Syncs skills to ElevenLabs Knowledge Base (via sync_skills_to_elevenlabs)
    2. Builds the combined prompt with meta-skill instructions
    3. Creates the agent via ElevenLabs API

    Args:
        name: Name for the agent.
        core_prompt: The core identity/system prompt for the agent.
        first_message: Initial message the agent sends to users.
        skills: List of skill names to equip the agent with.
        voice_id: Optional ElevenLabs voice ID.
        mock_api: If True, skip real API calls and return mock agent.
        force_sync: If True, re-sync skills even if content unchanged.

    Returns:
        A CustomerSupportVoiceAgent wrapper instance.

    Example:
        >>> agent = create_voice_agent(mock_api=True)
        >>> agent.name
        'Voice Support Agent'
        >>> "greeting" in agent.skills
        True
    """
    if skills is None:
        skills = VOICE_SUPPORT_SKILLS.copy()

    manifest_path = None
    agent_id = None
    kb_references: list[dict] = []

    if mock_api:
        # Mock mode: create mock manifest and build prompt
        manifest = _create_mock_manifest(skills)
        system_prompt = _build_prompt_with_skills(core_prompt, skills, manifest)
        kb_references = _get_kb_references_for_skills(skills, manifest)
    else:
        # Real mode: use actual ElevenLabs adapter
        try:
            from skillforge.adapters.elevenlabs import (
                build_prompt,
                create_agent as elevenlabs_create_agent,
                get_kb_references,
            )

            # Step 1: Sync skills to KB first (required before agent creation)
            manifest, doc_ids = sync_skills_to_elevenlabs(
                skills, mock_api=False, force=force_sync
            )
            manifest_path = manifest.manifest_file
            logger.info(f"Skills synced to KB: {list(doc_ids.keys())}")

            # Step 2: Build prompt and get KB references
            system_prompt = build_prompt(core_prompt, skills, manifest)
            kb_references = get_kb_references(skills, manifest)

            # Step 3: Create the actual agent via ElevenLabs API
            agent_id = elevenlabs_create_agent(
                name=name,
                core_prompt=core_prompt,
                first_message=first_message,
                skills=skills,
                voice_id=voice_id,
                manifest=manifest,
            )
            logger.info(f"Created ElevenLabs agent: {agent_id}")

            # Track agent for cleanup
            try:
                from run import _created_resources
                _created_resources["agents"].append(agent_id)
            except ImportError:
                pass  # run.py not imported (direct agent.py usage)

        except ImportError as e:
            logger.warning(f"ElevenLabs adapter not available: {e}")
            # Fall back to mock mode
            manifest = _create_mock_manifest(skills)
            system_prompt = _build_prompt_with_skills(core_prompt, skills, manifest)
            kb_references = _get_kb_references_for_skills(skills, manifest)

    return CustomerSupportVoiceAgent(
        agent_id=agent_id,
        name=name,
        system_prompt=system_prompt,
        first_message=first_message,
        skills=skills,
        kb_references=kb_references,
        manifest_path=manifest_path,
        mock_mode=mock_api or agent_id is None,
    )


def configure_voice_agent(
    agent: CustomerSupportVoiceAgent,
    skills: list[str],
    core_prompt: Optional[str] = None,
    mock_api: bool = True,
    force_sync: bool = False,
) -> CustomerSupportVoiceAgent:
    """Configure an existing voice agent with new skills.

    Updates the agent's prompt and KB references with new skills.

    In real mode, this function:
    1. Syncs new skills to ElevenLabs Knowledge Base (via sync_skills_to_elevenlabs)
    2. Updates the agent's prompt and KB references via ElevenLabs API
    3. Returns an updated CustomerSupportVoiceAgent

    Args:
        agent: Existing CustomerSupportVoiceAgent to configure.
        skills: New list of skill names to equip the agent with.
        core_prompt: Optional new core prompt. If None, preserves existing.
        mock_api: If True, skip real API calls.
        force_sync: If True, re-sync skills even if content unchanged.

    Returns:
        Updated CustomerSupportVoiceAgent instance.

    Example:
        >>> agent = create_voice_agent(mock_api=True)
        >>> updated = configure_voice_agent(agent, ["greeting", "troubleshooting"])
        >>> len(updated.skills)
        2
    """
    if core_prompt is None:
        # Extract core prompt from existing system prompt
        existing_prompt = agent.system_prompt
        if "---" in existing_prompt:
            core_prompt = existing_prompt.split("---")[0].strip()
        else:
            core_prompt = existing_prompt

    if mock_api or agent.mock_mode:
        # Mock mode: rebuild with new skills
        manifest = _create_mock_manifest(skills)
        system_prompt = _build_prompt_with_skills(core_prompt, skills, manifest)
        kb_references = _get_kb_references_for_skills(skills, manifest)

        return CustomerSupportVoiceAgent(
            agent_id=agent.agent_id,
            name=agent.name,
            system_prompt=system_prompt,
            first_message=agent.first_message,
            skills=skills,
            kb_references=kb_references,
            manifest_path=agent.manifest_path,
            mock_mode=True,
        )

    # Real mode: use actual ElevenLabs adapter
    try:
        from skillforge.adapters.elevenlabs import (
            build_prompt,
            configure_agent as elevenlabs_configure_agent,
            get_kb_references,
        )

        # Step 1: Sync new skills to KB first (required before configuration)
        manifest, doc_ids = sync_skills_to_elevenlabs(
            skills, mock_api=False, force=force_sync
        )
        logger.info(f"Skills synced to KB for configuration: {list(doc_ids.keys())}")

        # Step 2: Configure the agent via ElevenLabs API
        if agent.agent_id:
            elevenlabs_configure_agent(
                agent_id=agent.agent_id,
                skills=skills,
                core_prompt=core_prompt,
                manifest=manifest,
            )
            logger.info(f"Configured ElevenLabs agent: {agent.agent_id}")

        # Step 3: Build prompt and get KB references for local wrapper
        system_prompt = build_prompt(core_prompt, skills, manifest)
        kb_references = get_kb_references(skills, manifest)

        return CustomerSupportVoiceAgent(
            agent_id=agent.agent_id,
            name=agent.name,
            system_prompt=system_prompt,
            first_message=agent.first_message,
            skills=skills,
            kb_references=kb_references,
            manifest_path=manifest.manifest_file,
            mock_mode=False,
        )
    except ImportError:
        # Fall back to mock mode
        return configure_voice_agent(agent, skills, core_prompt, mock_api=True)


# --- Validation Helper Functions ---


def verify_skills_synced(skills: list[str], mock_api: bool = True) -> dict[str, bool]:
    """Verify that skills have been synced to the Knowledge Base.

    Args:
        skills: List of skill names to verify.
        mock_api: If True, use mock manifest.

    Returns:
        Dictionary mapping skill names to sync status (True if synced).

    Example:
        >>> results = verify_skills_synced(["greeting", "troubleshooting"])
        >>> results["greeting"]
        True
    """
    if mock_api:
        manifest = _create_mock_manifest(skills)
    else:
        try:
            from skillforge.adapters.elevenlabs import ElevenLabsManifest
            manifest = ElevenLabsManifest()
        except ImportError:
            manifest = _create_mock_manifest(skills)

    return {skill: manifest.has_skill(skill) for skill in skills}


def verify_manifest_has_documents(
    skills: list[str],
    mock_api: bool = True,
) -> dict[str, Optional[str]]:
    """Verify that the manifest has document IDs for skills.

    Args:
        skills: List of skill names to verify.
        mock_api: If True, use mock manifest.

    Returns:
        Dictionary mapping skill names to document IDs (None if not found).

    Example:
        >>> results = verify_manifest_has_documents(["greeting"])
        >>> results["greeting"] is not None
        True
    """
    if mock_api:
        manifest = _create_mock_manifest(skills)
    else:
        try:
            from skillforge.adapters.elevenlabs import ElevenLabsManifest
            manifest = ElevenLabsManifest()
        except ImportError:
            manifest = _create_mock_manifest(skills)

    return {skill: manifest.get_document_id(skill) for skill in skills}


def verify_meta_skill_present(agent: CustomerSupportVoiceAgent) -> bool:
    """Verify that the ElevenLabs meta-skill is in the agent's system prompt.

    The ElevenLabs meta-skill teaches agents how to use skills via KB queries:
    - "Using Skills" header
    - "Query your knowledge base for" instructions
    - "Available Skills" section

    Args:
        agent: A CustomerSupportVoiceAgent instance.

    Returns:
        True if meta-skill content is present, False otherwise.

    Example:
        >>> agent = create_voice_agent(mock_api=True)
        >>> verify_meta_skill_present(agent)
        True
    """
    system_prompt = agent.system_prompt
    return all([
        "Using Skills" in system_prompt,
        "Query" in system_prompt or "knowledge base" in system_prompt.lower(),
        "Available Skills" in system_prompt,
    ])


def get_agent_prompt(agent: CustomerSupportVoiceAgent) -> str:
    """Extract the system prompt from a CustomerSupportVoiceAgent.

    Args:
        agent: A CustomerSupportVoiceAgent instance.

    Returns:
        The agent's system prompt string.

    Example:
        >>> agent = create_voice_agent(mock_api=True)
        >>> prompt = get_agent_prompt(agent)
        >>> "voice customer support" in prompt.lower()
        True
    """
    return agent.system_prompt


def get_kb_references_for_validation(
    agent: CustomerSupportVoiceAgent,
) -> list[dict]:
    """Get KB references from an agent for validation.

    Args:
        agent: A CustomerSupportVoiceAgent instance.

    Returns:
        List of KB reference dictionaries with type, name, id, usage_mode.

    Example:
        >>> agent = create_voice_agent(mock_api=True)
        >>> refs = get_kb_references_for_validation(agent)
        >>> len(refs) == 4  # Default 4 skills
        True
        >>> refs[0]["type"]
        'text'
    """
    return agent.kb_references


def verify_skill_in_prompt(agent: CustomerSupportVoiceAgent, skill_name: str) -> bool:
    """Verify that a skill is referenced in the agent's system prompt.

    Args:
        agent: A CustomerSupportVoiceAgent instance.
        skill_name: The name of the skill to verify.

    Returns:
        True if skill is present in system prompt, False otherwise.

    Example:
        >>> agent = create_voice_agent(mock_api=True)
        >>> verify_skill_in_prompt(agent, "greeting")
        True
    """
    return skill_name in agent.system_prompt


def verify_kb_references_match_skills(agent: CustomerSupportVoiceAgent) -> bool:
    """Verify that KB references match the agent's configured skills.

    Each skill should have a corresponding KB reference with:
    - type: "text"
    - name: "SKILL: {skill_name}"
    - usage_mode: "auto"

    Args:
        agent: A CustomerSupportVoiceAgent instance.

    Returns:
        True if all skills have matching KB references, False otherwise.

    Example:
        >>> agent = create_voice_agent(mock_api=True)
        >>> verify_kb_references_match_skills(agent)
        True
    """
    if not agent.kb_references:
        return len(agent.skills) == 0

    # Build set of skill names from KB references
    kb_skill_names = set()
    for ref in agent.kb_references:
        name = ref.get("name", "")
        if name.startswith("SKILL: "):
            kb_skill_names.add(name.replace("SKILL: ", ""))

    # Check all configured skills have KB references
    return set(agent.skills) == kb_skill_names


def get_manifest_sync_info(mock_api: bool = True) -> dict[str, dict]:
    """Get full sync information for all synced skills.

    Args:
        mock_api: If True, use mock manifest.

    Returns:
        Dictionary mapping skill names to sync info dicts.

    Example:
        >>> info = get_manifest_sync_info(mock_api=True)
        >>> "document_id" in info.get("greeting", {})
        True
    """
    if mock_api:
        manifest = _create_mock_manifest(VOICE_SUPPORT_SKILLS)
    else:
        try:
            from skillforge.adapters.elevenlabs import ElevenLabsManifest
            manifest = ElevenLabsManifest()
        except ImportError:
            manifest = _create_mock_manifest(VOICE_SUPPORT_SKILLS)

    result = {}
    for skill_name in manifest.list_synced_skills():
        info = manifest.get_sync_info(skill_name)
        if info:
            result[skill_name] = info
    return result


def compare_with_without_skills() -> dict[str, Any]:
    """Compare agent prompts with and without skills for demonstration.

    Returns:
        Dict with comparison data including prompt lengths and skill counts.

    Example:
        >>> comparison = compare_with_without_skills()
        >>> comparison["with_skills"]["prompt_length"] > comparison["without_skills"]["prompt_length"]
        True
    """
    # Agent without skills
    agent_no_skills = create_voice_agent(
        skills=[],
        mock_api=True,
    )

    # Agent with skills
    agent_with_skills = create_voice_agent(
        skills=VOICE_SUPPORT_SKILLS,
        mock_api=True,
    )

    return {
        "without_skills": {
            "prompt_length": len(agent_no_skills.system_prompt),
            "skills_count": len(agent_no_skills.skills),
            "kb_references_count": len(agent_no_skills.kb_references),
            "has_meta_skill": verify_meta_skill_present(agent_no_skills),
        },
        "with_skills": {
            "prompt_length": len(agent_with_skills.system_prompt),
            "skills_count": len(agent_with_skills.skills),
            "kb_references_count": len(agent_with_skills.kb_references),
            "has_meta_skill": verify_meta_skill_present(agent_with_skills),
        },
        "comparison": {
            "prompt_increase": (
                len(agent_with_skills.system_prompt)
                - len(agent_no_skills.system_prompt)
            ),
            "skills_configured": VOICE_SUPPORT_SKILLS,
        },
    }


# --- Main section for direct testing ---


def print_separator(title: str) -> None:
    """Print a section separator with title."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")


def main() -> None:
    """Run direct tests of the voice customer support agent."""
    import sys

    print_separator("ElevenLabs Demo - Voice Customer Support Agent")

    all_passed = True

    # Test 1: Create voice agent in mock mode
    print_separator("Test 1: Create Voice Agent (Mock Mode)")
    try:
        agent = create_voice_agent(mock_api=True)
        print(f"Agent created: {type(agent).__name__}")
        print(f"  Name: {agent.name}")
        print(f"  Mock mode: {agent.mock_mode}")
        print(f"  Agent ID: {agent.agent_id}")
        print(f"  System prompt length: {len(agent.system_prompt)} chars")
        print(f"  First message: {agent.first_message[:50]}...")
        print(f"  Skills configured: {agent.skills}")
        print(f"  KB references count: {len(agent.kb_references)}")

        # Verify each skill is referenced
        print("  Skills in prompt:")
        for skill in VOICE_SUPPORT_SKILLS:
            in_prompt = verify_skill_in_prompt(agent, skill)
            status = "[PASS]" if in_prompt else "[FAIL]"
            print(f"    {status} {skill}")
            if not in_prompt:
                all_passed = False

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test 2: Verify meta-skill presence
    print_separator("Test 2: Meta-Skill Verification")
    try:
        has_meta_skill = verify_meta_skill_present(agent)
        print(f"Meta-skill present: {has_meta_skill}")

        # Check specific markers
        prompt = agent.system_prompt
        markers = [
            ("'Using Skills' header", "Using Skills" in prompt),
            ("'Available Skills' section", "Available Skills" in prompt),
            ("KB query instructions", "Query" in prompt or "knowledge base" in prompt.lower()),
        ]
        for name, present in markers:
            status = "[PASS]" if present else "[FAIL]"
            print(f"  {status} {name}")
            if not present:
                all_passed = False

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test 3: Verify KB references
    print_separator("Test 3: KB Reference Verification")
    try:
        kb_refs = get_kb_references_for_validation(agent)
        print(f"KB references count: {len(kb_refs)}")

        refs_match = verify_kb_references_match_skills(agent)
        status = "[PASS]" if refs_match else "[FAIL]"
        print(f"{status} KB references match configured skills")
        if not refs_match:
            all_passed = False

        print("  KB references:")
        for ref in kb_refs:
            print(f"    - {ref.get('name')}: id={ref.get('id')}, mode={ref.get('usage_mode')}")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test 4: Verify manifest document IDs
    print_separator("Test 4: Manifest Document ID Verification")
    try:
        doc_ids = verify_manifest_has_documents(VOICE_SUPPORT_SKILLS, mock_api=True)
        print("Document IDs in manifest:")

        for skill, doc_id in doc_ids.items():
            has_id = doc_id is not None
            status = "[PASS]" if has_id else "[FAIL]"
            print(f"  {status} {skill}: {doc_id}")
            if not has_id:
                all_passed = False

        synced = verify_skills_synced(VOICE_SUPPORT_SKILLS, mock_api=True)
        print(f"\nAll skills synced: {all(synced.values())}")

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test 5: Configure agent with different skills
    print_separator("Test 5: Configure Agent with Different Skills")
    try:
        new_skills = ["greeting", "troubleshooting"]
        updated_agent = configure_voice_agent(agent, new_skills, mock_api=True)

        print(f"Original skills: {agent.skills}")
        print(f"Updated skills: {updated_agent.skills}")
        print(f"Updated KB refs: {len(updated_agent.kb_references)}")

        skills_match = set(updated_agent.skills) == set(new_skills)
        refs_match = len(updated_agent.kb_references) == len(new_skills)

        status = "[PASS]" if skills_match else "[FAIL]"
        print(f"{status} Skills updated correctly")
        if not skills_match:
            all_passed = False

        status = "[PASS]" if refs_match else "[FAIL]"
        print(f"{status} KB references updated correctly")
        if not refs_match:
            all_passed = False

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test 6: Compare with/without skills
    print_separator("Test 6: Compare With/Without Skills")
    try:
        comparison = compare_with_without_skills()

        without = comparison["without_skills"]
        with_skills = comparison["with_skills"]
        comp = comparison["comparison"]

        print("Without Skills:")
        print(f"  Prompt length: {without['prompt_length']} chars")
        print(f"  Skills count: {without['skills_count']}")
        print(f"  KB refs count: {without['kb_references_count']}")

        print("\nWith Skills:")
        print(f"  Prompt length: {with_skills['prompt_length']} chars")
        print(f"  Skills count: {with_skills['skills_count']}")
        print(f"  KB refs count: {with_skills['kb_references_count']}")
        print(f"  Has meta-skill: {with_skills['has_meta_skill']}")

        print("\nComparison:")
        print(f"  Prompt increase: {comp['prompt_increase']} chars")
        print(f"  Skills added: {comp['skills_configured']}")

        prompt_increased = comp['prompt_increase'] > 0
        status = "[PASS]" if prompt_increased else "[FAIL]"
        print(f"\n{status} Skills add content to prompt")
        if not prompt_increased:
            all_passed = False

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test 7: Conversation config output
    print_separator("Test 7: Conversation Config Format")
    try:
        config = agent.get_conversation_config()

        has_agent = "agent" in config
        has_prompt = "prompt" in config.get("agent", {})
        has_first_message = "first_message" in config.get("agent", {})
        has_kb = "knowledge_base" in config.get("agent", {}).get("prompt", {})

        status = "[PASS]" if has_agent else "[FAIL]"
        print(f"{status} Config has 'agent' section")

        status = "[PASS]" if has_prompt else "[FAIL]"
        print(f"{status} Config has 'prompt' section")

        status = "[PASS]" if has_first_message else "[FAIL]"
        print(f"{status} Config has 'first_message'")

        status = "[PASS]" if has_kb else "[FAIL]"
        print(f"{status} Config has 'knowledge_base' references")

        if not all([has_agent, has_prompt, has_first_message, has_kb]):
            all_passed = False

    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Final summary
    print_separator("Summary")
    if all_passed:
        print("All tests PASSED!")
        print("The ElevenLabs voice customer support agent is configured correctly.\n")
    else:
        print("Some tests FAILED.")
        print("Please check the output above for details.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
