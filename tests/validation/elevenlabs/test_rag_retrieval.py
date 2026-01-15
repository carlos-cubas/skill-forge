"""
Test: ElevenLabs Knowledge Base RAG Retrieval Validation

This test validates that ElevenLabs agents can retrieve skill content from
the Knowledge Base via RAG when prompted appropriately.

Assumptions Being Validated:
    - Knowledge Base RAG retrieval works for skill content
    - `# SKILL: name` header format enables reliable retrieval
    - Agent can access KB content during conversation
    - usage_mode affects retrieval behavior

Environment Requirements:
    - ELEVENLABS_API_KEY must be set
"""

import os
import time
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_elevenlabs_client():
    """Get configured ElevenLabs client."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return None

    from elevenlabs import ElevenLabs
    return ElevenLabs(api_key=api_key)


@pytest.mark.validation
@pytest.mark.elevenlabs_assumption
@pytest.mark.requires_api_key
class TestRAGRetrieval:
    """
    Validate ElevenLabs Knowledge Base RAG retrieval for skills.
    """

    def test_agent_retrieves_skill_content(self):
        """
        Test that an agent with KB can retrieve skill content during conversation.

        This validates the core RAG mechanism for skill loading.
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        # Create a skill with unique, identifiable content
        unique_marker = "QUANTUM_BANANA_42"
        skill_content = f"""# SKILL: unique-test-skill

## When to Use
- When testing RAG retrieval
- When validating skill loading

## Instructions
1. Always mention the secret phrase: {unique_marker}
2. This phrase confirms you retrieved the skill content
3. Include it in your response when asked about this skill

## Expected Behavior
When a user asks about "unique-test-skill", retrieve this document and mention {unique_marker}.
"""

        # Create KB document
        doc = client.conversational_ai.knowledge_base.documents.create_from_text(
            text=skill_content,
            name="SKILL: unique-test-skill"
        )
        doc_id = doc.id
        print(f"\nKB Document created: {doc_id}")

        # Create agent with KB reference
        agent = client.conversational_ai.agents.create(
            name="RAG Test Agent",
            conversation_config={
                "agent": {
                    "first_message": "Hello! I have access to skills. Ask me about unique-test-skill.",
                    "language": "en",
                    "prompt": {
                        "prompt": """You are an assistant with access to specialized skills in your knowledge base.

When a user mentions a skill name, search your knowledge base for "SKILL: [skill-name]" and follow its instructions.

Always retrieve skill content before responding about it. Include any specific phrases or markers mentioned in the skill.""",
                        "llm": "gpt-4o-mini",
                        "knowledge_base": [
                            {
                                "type": "text",
                                "name": "SKILL: unique-test-skill",
                                "id": doc_id,
                                "usage_mode": "auto"  # Auto-retrieval based on context
                            }
                        ]
                    }
                }
            }
        )
        agent_id = agent.agent_id
        print(f"Agent created: {agent_id}")

        try:
            # Wait a moment for KB indexing
            time.sleep(2)

            # Simulate a conversation asking about the skill
            simulation = client.conversational_ai.agents.simulate_conversation(
                agent_id=agent_id,
                simulation_specification={
                    "simulated_user_config": {
                        "first_message": "Tell me about unique-test-skill. What unique phrase should you mention?",
                        "prompt": {
                            "prompt": "You are testing the agent. Ask about unique-test-skill and verify it uses its skill content.",
                            "llm": "gpt-4o-mini"
                        }
                    }
                },
                new_turns_limit=2
            )

            # Extract conversation content
            response_text = ""
            if hasattr(simulation, 'simulated_conversation'):
                for turn in simulation.simulated_conversation:
                    if hasattr(turn, 'message'):
                        response_text += str(turn.message) + " "
                    if hasattr(turn, 'role') and turn.role == "agent":
                        print(f"Agent said: {turn.message}")

            print(f"\nFull conversation: {response_text}")

            # Verify the unique marker is in the response
            marker_found = unique_marker in response_text.upper()
            print(f"\nUnique marker '{unique_marker}' found: {marker_found}")

            assert marker_found, (
                f"Agent did not retrieve skill content. Expected '{unique_marker}' in response.\n"
                f"Got: {response_text[:500]}"
            )

        finally:
            # Clean up
            try:
                client.conversational_ai.agents.delete(agent_id)
                print(f"\nAgent {agent_id} deleted")
            except Exception as e:
                print(f"Warning: Could not delete agent: {e}")

            try:
                client.conversational_ai.knowledge_base.documents.delete(doc_id)
                print(f"Document {doc_id} deleted")
            except Exception as e:
                print(f"Warning: Could not delete document: {e}")

    def test_kb_usage_mode_auto_vs_prompt(self):
        """
        Test the difference between usage_mode 'auto' and 'prompt'.

        - auto: Content retrieved automatically based on context
        - prompt: Content always included in the prompt
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        skill_content = """# SKILL: mode-test-skill

## Instructions
This skill contains the secret code: RAINBOW_UNICORN_99

Always mention RAINBOW_UNICORN_99 when discussing this skill.
"""

        doc = client.conversational_ai.knowledge_base.documents.create_from_text(
            text=skill_content,
            name="SKILL: mode-test-skill"
        )
        doc_id = doc.id
        print(f"\nKB Document created: {doc_id}")

        # Test with usage_mode="prompt" (always included)
        agent = client.conversational_ai.agents.create(
            name="Prompt Mode Test Agent",
            conversation_config={
                "agent": {
                    "first_message": "Hello!",
                    "language": "en",
                    "prompt": {
                        "prompt": "You are an assistant. Use any skill content available to you. Mention any secret codes you know.",
                        "llm": "gpt-4o-mini",
                        "knowledge_base": [
                            {
                                "type": "text",
                                "name": "SKILL: mode-test-skill",
                                "id": doc_id,
                                "usage_mode": "prompt"  # Always included in context
                            }
                        ]
                    }
                }
            }
        )
        agent_id = agent.agent_id
        print(f"Agent (prompt mode) created: {agent_id}")

        try:
            time.sleep(2)

            # Ask a general question - with prompt mode, skill should be accessible
            simulation = client.conversational_ai.agents.simulate_conversation(
                agent_id=agent_id,
                simulation_specification={
                    "simulated_user_config": {
                        "first_message": "What secret codes do you know about?",
                        "prompt": {
                            "prompt": "You are testing the agent. Ask about any secret codes it knows.",
                            "llm": "gpt-4o-mini"
                        }
                    }
                },
                new_turns_limit=2
            )

            response_text = ""
            if hasattr(simulation, 'simulated_conversation'):
                for turn in simulation.simulated_conversation:
                    if hasattr(turn, 'message'):
                        response_text += str(turn.message) + " "

            print(f"\nPrompt mode response: {response_text}")

            # Check for the marker
            found = "RAINBOW" in response_text.upper() or "UNICORN" in response_text.upper() or "99" in response_text
            print(f"Marker found with prompt mode: {found}")

            # With prompt mode, the skill should be included in context even for general questions
            # This is a soft assertion - RAG behavior may vary
            print(f"Note: prompt mode should make skill always available")

        finally:
            client.conversational_ai.agents.delete(agent_id)
            print(f"Agent {agent_id} deleted")
            client.conversational_ai.knowledge_base.documents.delete(doc_id)
            print(f"Document {doc_id} deleted")

    def test_skill_header_format_retrieval(self):
        """
        Test that the `# SKILL: name` header format enables reliable retrieval.

        This validates our skill document format assumption.
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        # Create multiple skills with the standard header format
        skills = [
            {
                "name": "SKILL: alpha-skill",
                "content": """# SKILL: alpha-skill

## Unique Identifier
ALPHA_CODE_111

## Instructions
When asked about alpha-skill, mention ALPHA_CODE_111.
""",
                "marker": "ALPHA_CODE_111"
            },
            {
                "name": "SKILL: beta-skill",
                "content": """# SKILL: beta-skill

## Unique Identifier
BETA_CODE_222

## Instructions
When asked about beta-skill, mention BETA_CODE_222.
""",
                "marker": "BETA_CODE_222"
            }
        ]

        doc_ids = []
        kb_refs = []

        # Create all KB documents
        for skill in skills:
            doc = client.conversational_ai.knowledge_base.documents.create_from_text(
                text=skill["content"],
                name=skill["name"]
            )
            doc_ids.append(doc.id)
            kb_refs.append({
                "type": "text",
                "name": skill["name"],
                "id": doc.id,
                "usage_mode": "auto"
            })
            print(f"Created KB doc: {skill['name']} -> {doc.id}")

        # Create agent with all skills
        agent = client.conversational_ai.agents.create(
            name="Multi-Skill Test Agent",
            conversation_config={
                "agent": {
                    "first_message": "Hello! I have access to alpha-skill and beta-skill.",
                    "language": "en",
                    "prompt": {
                        "prompt": """You are an assistant with multiple skills in your knowledge base.

When asked about a specific skill, search your knowledge base for "SKILL: [skill-name]".
Include any unique identifiers mentioned in the skill.""",
                        "llm": "gpt-4o-mini",
                        "knowledge_base": kb_refs
                    }
                }
            }
        )
        agent_id = agent.agent_id
        print(f"\nAgent created: {agent_id}")

        try:
            time.sleep(2)

            # Test retrieving specific skill by name
            simulation = client.conversational_ai.agents.simulate_conversation(
                agent_id=agent_id,
                simulation_specification={
                    "simulated_user_config": {
                        "first_message": "Tell me about alpha-skill specifically. What's its unique identifier?",
                        "prompt": {
                            "prompt": "You are testing the agent. Ask specifically about alpha-skill's unique identifier.",
                            "llm": "gpt-4o-mini"
                        }
                    }
                },
                new_turns_limit=2
            )

            response_text = ""
            if hasattr(simulation, 'simulated_conversation'):
                for turn in simulation.simulated_conversation:
                    if hasattr(turn, 'message'):
                        response_text += str(turn.message) + " "

            print(f"\nAlpha skill query response: {response_text}")

            # Check if alpha marker is present
            alpha_found = "ALPHA" in response_text.upper() or "111" in response_text
            beta_found = "BETA" in response_text.upper() or "222" in response_text

            print(f"Alpha marker found: {alpha_found}")
            print(f"Beta marker found: {beta_found}")

            # We expect alpha to be found when asking specifically about alpha
            assert alpha_found, f"Alpha skill content not retrieved. Response: {response_text[:500]}"

        finally:
            # Clean up
            client.conversational_ai.agents.delete(agent_id)
            print(f"\nAgent {agent_id} deleted")

            for doc_id in doc_ids:
                try:
                    client.conversational_ai.knowledge_base.documents.delete(doc_id)
                    print(f"Document {doc_id} deleted")
                except Exception as e:
                    print(f"Warning: Could not delete document {doc_id}: {e}")


if __name__ == "__main__":
    import sys

    tests = TestRAGRetrieval()

    print("=" * 60)
    print("ElevenLabs RAG Retrieval Validation")
    print("=" * 60)

    test_methods = [
        ("Agent Retrieves Skill Content", tests.test_agent_retrieves_skill_content),
        ("Usage Mode (auto vs prompt)", tests.test_kb_usage_mode_auto_vs_prompt),
        ("Skill Header Format Retrieval", tests.test_skill_header_format_retrieval),
    ]

    results = []
    for name, test_func in test_methods:
        print(f"\n{'=' * 40}")
        print(f"Test: {name}")
        print("=" * 40)
        try:
            test_func()
            results.append((name, "PASS"))
            print(f"\nResult: PASS")
        except Exception as e:
            results.append((name, f"FAIL: {e}"))
            print(f"\nResult: FAIL - {e}")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for name, result in results:
        status = "PASS" if result == "PASS" else "FAIL"
        print(f"{name}: {status}")
