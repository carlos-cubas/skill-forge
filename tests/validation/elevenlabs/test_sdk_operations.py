"""
Test: ElevenLabs SDK Operations Validation

This test validates the ElevenLabs SDK operations required for the SkillForge adapter:
1. Knowledge Base document creation from text
2. Agent creation with system prompt
3. Agent update with KB references
4. Agent deletion (cleanup)

Assumptions Being Validated:
    - SDK supports KB document creation via create_from_text
    - SDK supports agent creation with ConversationalConfig
    - SDK supports agent update with KB references
    - KnowledgeBaseLocator can reference text documents

Environment Requirements:
    - ELEVENLABS_API_KEY must be set
"""

import os
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
class TestSDKOperations:
    """
    Validate ElevenLabs SDK operations for SkillForge adapter.
    """

    def test_knowledge_base_document_creation(self):
        """
        Test that we can create a KB document from text.

        This is the core mechanism for uploading skills to ElevenLabs.
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        # Create a test skill document
        skill_content = """# SKILL: test-skill

## When to Use
- Testing SkillForge adapter
- Validating KB document creation

## Instructions
1. This is a test skill
2. It validates KB creation
3. Used for SkillForge validation

## Expected Behavior
The agent should retrieve this content when querying for "SKILL: test-skill"
"""

        # Create the document
        doc = client.conversational_ai.knowledge_base.documents.create_from_text(
            text=skill_content,
            name="SKILL: test-skill"
        )

        # Verify document was created
        assert doc is not None, "Document creation returned None"
        assert hasattr(doc, 'id') or hasattr(doc, 'document_id'), f"Document has no ID. Got: {doc}"

        # Get the document ID
        doc_id = getattr(doc, 'id', None) or getattr(doc, 'document_id', None)
        print(f"\nDocument created successfully!")
        print(f"Document ID: {doc_id}")
        print(f"Response type: {type(doc)}")
        print(f"Response attributes: {[a for a in dir(doc) if not a.startswith('_')]}")

        # Clean up - delete the document
        try:
            client.conversational_ai.knowledge_base.documents.delete(doc_id)
            print(f"Document {doc_id} deleted successfully")
        except Exception as e:
            print(f"Warning: Could not delete document {doc_id}: {e}")

    def test_agent_creation(self):
        """
        Test that we can create an agent with a system prompt.

        This validates the agent creation API used by SkillForge.

        Note: The SDK requires dict-based configuration, not Pydantic models.
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        # Create agent with dict-based config (SDK requirement)
        agent = client.conversational_ai.agents.create(
            name="SkillForge Test Agent",
            conversation_config={
                "agent": {
                    "first_message": "Hello, I'm a test agent for SkillForge validation.",
                    "language": "en",
                    "prompt": {
                        "prompt": "You are a test agent. Your purpose is to validate the SkillForge ElevenLabs adapter. Be helpful and concise.",
                        "llm": "gpt-4o-mini",
                    }
                }
            }
        )

        # Verify agent was created
        assert agent is not None, "Agent creation returned None"
        agent_id = getattr(agent, 'agent_id', None)
        assert agent_id is not None, f"Agent has no ID. Got: {agent}"

        print(f"\nAgent created successfully!")
        print(f"Agent ID: {agent_id}")
        print(f"Response type: {type(agent)}")
        print(f"Response attributes: {[a for a in dir(agent) if not a.startswith('_')]}")

        # Clean up - delete the agent
        try:
            client.conversational_ai.agents.delete(agent_id)
            print(f"Agent {agent_id} deleted successfully")
        except Exception as e:
            print(f"Warning: Could not delete agent {agent_id}: {e}")

    def test_agent_creation_with_knowledge_base(self):
        """
        Test creating an agent with a Knowledge Base reference.

        This validates the core mechanism for skill injection in ElevenLabs.
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        # First, create a KB document
        skill_content = """# SKILL: socratic-questioning

## When to Use
- Guiding someone toward discovery through questioning
- When someone asks for direct answers
- When someone needs to develop reasoning skills

## Instructions
1. Never give direct answers
2. Ask probing questions instead
3. Guide them to discover the answer themselves
"""

        doc = client.conversational_ai.knowledge_base.documents.create_from_text(
            text=skill_content,
            name="SKILL: socratic-questioning"
        )
        doc_id = getattr(doc, 'id', None) or getattr(doc, 'document_id', None)
        print(f"\nKB Document created: {doc_id}")

        try:
            # Create agent with KB reference using dict-based config
            agent = client.conversational_ai.agents.create(
                name="SkillForge KB Test Agent",
                conversation_config={
                    "agent": {
                        "first_message": "Hello! What would you like to explore today?",
                        "language": "en",
                        "prompt": {
                            "prompt": """You are a test tutor agent. You have access to specialized skills in your knowledge base.

When a conversation topic matches a skill, query your knowledge base for "SKILL: [skill-name]" to retrieve guidance.

Be helpful and use your skills when appropriate.""",
                            "llm": "gpt-4o-mini",
                            "knowledge_base": [
                                {
                                    "type": "text",
                                    "name": "SKILL: socratic-questioning",
                                    "id": doc_id,
                                    "usage_mode": "auto"
                                }
                            ]
                        }
                    }
                }
            )

            agent_id = getattr(agent, 'agent_id', None)
            assert agent_id is not None, "Agent creation with KB failed"

            print(f"Agent with KB created: {agent_id}")

            # Verify by retrieving the agent
            retrieved = client.conversational_ai.agents.get(agent_id)
            print(f"Agent retrieved. Has conversation_config: {hasattr(retrieved, 'conversation_config')}")

            # Clean up agent
            client.conversational_ai.agents.delete(agent_id)
            print(f"Agent {agent_id} deleted")

        finally:
            # Clean up KB document
            try:
                client.conversational_ai.knowledge_base.documents.delete(doc_id)
                print(f"Document {doc_id} deleted")
            except Exception as e:
                print(f"Warning: Could not delete document: {e}")

    def test_agent_update_with_knowledge_base(self):
        """
        Test updating an existing agent to add KB references.

        This validates the `skillforge elevenlabs configure` workflow.
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        # Create a simple agent first (no KB) using dict-based config
        agent = client.conversational_ai.agents.create(
            name="SkillForge Update Test Agent",
            conversation_config={
                "agent": {
                    "first_message": "Hello!",
                    "language": "en",
                    "prompt": {
                        "prompt": "You are a helpful assistant.",
                        "llm": "gpt-4o-mini",
                    }
                }
            }
        )
        agent_id = getattr(agent, 'agent_id', None)
        print(f"\nAgent created for update test: {agent_id}")

        # Create a KB document
        skill_content = """# SKILL: update-test-skill

## Instructions
This skill was added via update operation.
"""

        doc = client.conversational_ai.knowledge_base.documents.create_from_text(
            text=skill_content,
            name="SKILL: update-test-skill"
        )
        doc_id = getattr(doc, 'id', None) or getattr(doc, 'document_id', None)
        print(f"KB Document created: {doc_id}")

        try:
            # Update the agent to add KB reference using dict-based config
            updated_agent = client.conversational_ai.agents.update(
                agent_id=agent_id,
                conversation_config={
                    "agent": {
                        "first_message": "Hello! I now have skills.",
                        "language": "en",
                        "prompt": {
                            "prompt": """You are a helpful assistant with access to skills.

## Using Skills
Query your knowledge base for "SKILL: [skill-name]" when relevant.

## Available Skills
- update-test-skill: Testing update operations
""",
                            "llm": "gpt-4o-mini",
                            "knowledge_base": [
                                {
                                    "type": "text",
                                    "name": "SKILL: update-test-skill",
                                    "id": doc_id,
                                    "usage_mode": "auto"
                                }
                            ]
                        }
                    }
                }
            )

            assert updated_agent is not None, "Agent update failed"
            print(f"Agent updated successfully")

            # Verify the update
            retrieved = client.conversational_ai.agents.get(agent_id)
            print(f"Agent retrieval successful: {retrieved is not None}")

        finally:
            # Clean up
            try:
                client.conversational_ai.agents.delete(agent_id)
                print(f"Agent {agent_id} deleted")
            except Exception as e:
                print(f"Warning: Could not delete agent: {e}")

            try:
                client.conversational_ai.knowledge_base.documents.delete(doc_id)
                print(f"Document {doc_id} deleted")
            except Exception as e:
                print(f"Warning: Could not delete document: {e}")


if __name__ == "__main__":
    # Run tests directly for quick validation
    import sys

    tests = TestSDKOperations()

    print("=" * 60)
    print("ElevenLabs SDK Operations Validation")
    print("=" * 60)

    test_methods = [
        ("KB Document Creation", tests.test_knowledge_base_document_creation),
        ("Agent Creation", tests.test_agent_creation),
        ("Agent + KB Creation", tests.test_agent_creation_with_knowledge_base),
        ("Agent Update with KB", tests.test_agent_update_with_knowledge_base),
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
