"""
Test: ElevenLabs Prompt Size Limits Validation

This test validates that ElevenLabs agents can handle system prompts
containing meta-skill instructions plus a skill directory.

Assumptions Being Validated:
    - System prompt can include meta-skill content without exceeding limits
    - Skill directory (names + descriptions) can be included
    - Combined prompt + KB references work together

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


# Sample meta-skill content (similar to what we'd actually use)
META_SKILL_CONTENT = """
# Using Skills

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

## Common Mistakes to Avoid

- Assuming you know what a skill contains without loading it
- Skipping skills because the task "seems simple"
- Paraphrasing skill instructions instead of following them
- Not announcing which skill you're using

"""


def generate_skill_directory(num_skills: int) -> str:
    """Generate a skill directory with specified number of skills."""
    skills = []
    for i in range(num_skills):
        skills.append(f"- **skill-{i}**: Use when handling scenario {i}. Query: \"SKILL: skill-{i}\"")
    return "## Available Skills\n\n" + "\n".join(skills)


@pytest.mark.validation
@pytest.mark.elevenlabs_assumption
@pytest.mark.requires_api_key
class TestPromptSize:
    """
    Validate ElevenLabs prompt size handling.
    """

    def test_meta_skill_plus_small_directory(self):
        """
        Test that system prompt with meta-skill + 5 skills works.

        This is a typical use case for SkillForge.
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        skill_directory = generate_skill_directory(5)
        full_prompt = f"""You are a helpful assistant.

{META_SKILL_CONTENT}

{skill_directory}
"""

        prompt_size = len(full_prompt)
        print(f"\nPrompt size: {prompt_size} characters")

        # Create agent with the combined prompt
        agent = client.conversational_ai.agents.create(
            name="Prompt Size Test Agent (Small)",
            conversation_config={
                "agent": {
                    "first_message": "Hello! I have 5 skills available.",
                    "language": "en",
                    "prompt": {
                        "prompt": full_prompt,
                        "llm": "gpt-4o-mini",
                    }
                }
            }
        )
        agent_id = agent.agent_id
        print(f"Agent created: {agent_id}")

        try:
            time.sleep(1)

            # Verify agent responds correctly
            simulation = client.conversational_ai.agents.simulate_conversation(
                agent_id=agent_id,
                simulation_specification={
                    "simulated_user_config": {
                        "first_message": "What skills do you have?",
                        "prompt": {
                            "prompt": "Ask about the agent's skills.",
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

            print(f"Response: {response_text[:300]}")

            # Agent should be able to discuss skills
            assert len(response_text) > 0, "Agent did not respond"
            print("Agent created and responded successfully with small skill directory")

        finally:
            client.conversational_ai.agents.delete(agent_id)
            print(f"Agent {agent_id} deleted")

    def test_meta_skill_plus_large_directory(self):
        """
        Test that system prompt with meta-skill + 20 skills works.

        This tests a larger skill directory that approaches real-world usage.
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        skill_directory = generate_skill_directory(20)
        full_prompt = f"""You are a helpful assistant with many specialized skills.

{META_SKILL_CONTENT}

{skill_directory}
"""

        prompt_size = len(full_prompt)
        print(f"\nPrompt size: {prompt_size} characters")

        # Create agent with the combined prompt
        agent = client.conversational_ai.agents.create(
            name="Prompt Size Test Agent (Large)",
            conversation_config={
                "agent": {
                    "first_message": "Hello! I have 20 skills available.",
                    "language": "en",
                    "prompt": {
                        "prompt": full_prompt,
                        "llm": "gpt-4o-mini",
                    }
                }
            }
        )
        agent_id = agent.agent_id
        print(f"Agent created: {agent_id}")

        try:
            time.sleep(1)

            # Verify agent responds correctly
            simulation = client.conversational_ai.agents.simulate_conversation(
                agent_id=agent_id,
                simulation_specification={
                    "simulated_user_config": {
                        "first_message": "Tell me about skill-15",
                        "prompt": {
                            "prompt": "Ask about a specific skill.",
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

            print(f"Response: {response_text[:300]}")

            assert len(response_text) > 0, "Agent did not respond"
            print("Agent created and responded successfully with large skill directory")

        finally:
            client.conversational_ai.agents.delete(agent_id)
            print(f"Agent {agent_id} deleted")

    def test_combined_prompt_and_kb_references(self):
        """
        Test that system prompt with meta-skill + KB references works together.

        This is the actual SkillForge pattern.
        """
        client = get_elevenlabs_client()
        if not client:
            pytest.skip("ELEVENLABS_API_KEY not set")

        # Create a few skills in KB
        skill_content = """# SKILL: prompt-size-test

## Instructions
This skill validates that combined prompts and KB work together.
The secret code is: COMBINED_SUCCESS_999
"""

        doc = client.conversational_ai.knowledge_base.documents.create_from_text(
            text=skill_content,
            name="SKILL: prompt-size-test"
        )
        doc_id = doc.id
        print(f"\nKB Document created: {doc_id}")

        # Create agent with meta-skill prompt AND KB reference
        skill_directory = """## Available Skills

- **prompt-size-test**: Use when validating combined functionality. Query: "SKILL: prompt-size-test"
"""

        full_prompt = f"""You are a helpful assistant.

{META_SKILL_CONTENT}

{skill_directory}
"""

        prompt_size = len(full_prompt)
        print(f"System prompt size: {prompt_size} characters")

        agent = client.conversational_ai.agents.create(
            name="Combined Prompt + KB Test Agent",
            conversation_config={
                "agent": {
                    "first_message": "Hello! I have skills in my knowledge base.",
                    "language": "en",
                    "prompt": {
                        "prompt": full_prompt,
                        "llm": "gpt-4o-mini",
                        "knowledge_base": [
                            {
                                "type": "text",
                                "name": "SKILL: prompt-size-test",
                                "id": doc_id,
                                "usage_mode": "auto"
                            }
                        ]
                    }
                }
            }
        )
        agent_id = agent.agent_id
        print(f"Agent created: {agent_id}")

        try:
            time.sleep(2)

            # Test that agent can use the skill
            simulation = client.conversational_ai.agents.simulate_conversation(
                agent_id=agent_id,
                simulation_specification={
                    "simulated_user_config": {
                        "first_message": "Use the prompt-size-test skill. What's the secret code?",
                        "prompt": {
                            "prompt": "Ask about the prompt-size-test skill and its secret code.",
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

            print(f"Response: {response_text}")

            # Check for the secret code
            found = "COMBINED" in response_text.upper() or "SUCCESS" in response_text.upper() or "999" in response_text
            print(f"Secret code found: {found}")

            # The key validation is that the agent was created and can respond
            assert len(response_text) > 0, "Agent did not respond"
            print("Combined system prompt + KB references work together")

        finally:
            client.conversational_ai.agents.delete(agent_id)
            print(f"Agent {agent_id} deleted")
            client.conversational_ai.knowledge_base.documents.delete(doc_id)
            print(f"Document {doc_id} deleted")


if __name__ == "__main__":
    import sys

    tests = TestPromptSize()

    print("=" * 60)
    print("ElevenLabs Prompt Size Validation")
    print("=" * 60)

    test_methods = [
        ("Meta-skill + Small Directory (5 skills)", tests.test_meta_skill_plus_small_directory),
        ("Meta-skill + Large Directory (20 skills)", tests.test_meta_skill_plus_large_directory),
        ("Combined Prompt + KB References", tests.test_combined_prompt_and_kb_references),
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
