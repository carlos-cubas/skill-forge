# ElevenLabs Demo - SkillForge Voice Agent Example

This example demonstrates SkillForge integration with ElevenLabs Conversational AI using a voice customer support agent. It validates Knowledge Base-backed skill retrieval, ElevenLabs-specific meta-skill injection, and the full sync-create-configure workflow.

## What This Validates

| Feature | Implementation |
|---------|----------------|
| Knowledge Base sync | Skills synced to ElevenLabs KB via `skillforge elevenlabs sync` |
| Manifest tracking | Document IDs stored in `.skillforge/elevenlabs-manifest.json` |
| Agent creation | Voice agent created with skills via ElevenLabs API |
| ElevenLabs meta-skill | Agent taught to query KB for skill instructions |
| KB references | Skill documents linked in agent conversation config |
| Agent configuration | Dynamic skill updates via reconfiguration |
| Local skill discovery | Skills loaded from `./skills/` directory |

## Architecture

```
Skill Files (SKILL.md)
       |
       v
+---------------------------+
|  skillforge elevenlabs    |
|       sync                |
+---------------------------+
       |
       v
+---------------------------+
| ElevenLabs Knowledge Base |
|  (skill documents)        |
+---------------------------+
       |
       v
+---------------------------+
| Voice Support Agent       |
|  - KB references          |
|  - Meta-skill prompt      |
|  - greeting               |
|  - troubleshooting        |
|  - ticket-creation        |
|  - knowledge-search       |
+---------------------------+
       |
       v
   Voice Response
```

**Voice Agent Design**: This example uses a single voice agent that can access all skills via ElevenLabs Knowledge Base queries. The agent's system prompt includes the ElevenLabs-specific meta-skill that teaches it to query the KB for skill instructions.

**Knowledge Base Pattern**: Unlike the LangChain demo which uses direct prompt injection or CLI commands, ElevenLabs uses a RAG-based approach where:
1. Skills are synced to ElevenLabs Knowledge Base as documents
2. The agent queries the KB when it needs skill guidance
3. Skill instructions are retrieved dynamically during conversations

**Meta-Skill Approach**: The ElevenLabs meta-skill teaches agents to:
1. Check Available Skills when facing complex situations
2. Query the Knowledge Base with "SKILL: [skill-name]"
3. Follow retrieved instructions precisely

## Prerequisites

### 1. ElevenLabs API Key

For `--real` mode (actual API calls), you need an ElevenLabs API key:

1. Create an account at [elevenlabs.io](https://elevenlabs.io)
2. Navigate to your Profile Settings
3. Generate an API key
4. Set it as an environment variable:

```bash
export ELEVENLABS_API_KEY=your-api-key
```

Or create a `.env` file in this directory:

```bash
ELEVENLABS_API_KEY=your-api-key
```

### 2. Install Dependencies

```bash
# From the examples/elevenlabs-demo directory
pip install -r requirements.txt
```

Or install skillforge with ElevenLabs support:

```bash
pip install skillforge[elevenlabs]
```

## Quick Start

### Run Validation (Quick Mode - Default)

```bash
python run.py --quick
```

This runs all validations with mocked API calls, suitable for CI/CD environments. No ElevenLabs API key required.

### Run Validation (Real Mode)

```bash
export ELEVENLABS_API_KEY=your-api-key
python run.py --real
```

This runs the agent with actual ElevenLabs API calls, creating real resources in your ElevenLabs account.

## Validation Checkpoints

The validation script runs 9 checkpoints that verify the complete ElevenLabs integration:

### Checkpoint 1: SkillForge Installation

Verifies that required packages are installed and importable.

**What it checks:**
- `skillforge` package is installed
- `elevenlabs` package is available (optional in mock mode)
- `skillforge.adapters.elevenlabs` module is accessible

**Expected output:**
```
[PASS] Checkpoint 1: Installation verified (skillforge[elevenlabs] importable)
       skillforge version: x.x.x
       elevenlabs version: x.x.x
       skillforge.adapters.elevenlabs: importable
```

### Checkpoint 2: Local Skills Discovery

Verifies that skills are present locally (symlinked or copied from shared-skills).

**What it checks:**
- `./skills/` directory exists
- Each skill directory contains a `SKILL.md` file
- All expected skills are present: greeting, troubleshooting, ticket-creation, knowledge-search

**Expected output:**
```
[PASS] Checkpoint 2: Skills copied locally (symlink or copy)
       greeting: symlink -> /path/to/examples/shared-skills/greeting
       troubleshooting: symlink -> /path/to/examples/shared-skills/troubleshooting
       ticket-creation: symlink -> /path/to/examples/shared-skills/ticket-creation
       knowledge-search: symlink -> /path/to/examples/shared-skills/knowledge-search
```

### Checkpoint 3: ElevenLabs Credentials Check

Validates that ElevenLabs API credentials are properly configured.

**What it checks:**
- In `--quick` mode: Skipped (credentials not required)
- In `--real` mode: `ELEVENLABS_API_KEY` environment variable is set
- API key format validation (optional)

**Expected output (quick mode):**
```
[PASS] Checkpoint 3: Credentials configured (from env or interactive)
       Running in mock mode - credentials not required
       ELEVENLABS_API_KEY: skipped (mock mode)
```

**Expected output (real mode):**
```
[PASS] Checkpoint 3: Credentials configured (from env or interactive)
       ELEVENLABS_API_KEY: sk_abc1...xyz9 (set)
       API key format: valid (starts with sk_)
```

### Checkpoint 4: Knowledge Base Sync

Verifies that skills have been synced to ElevenLabs Knowledge Base.

**What it checks:**
- Each skill has a sync entry in the manifest
- Sync status for all configured skills
- In `--quick` mode: Uses mock manifest with simulated sync
- In `--real` mode: Verifies actual KB documents via API

**Expected output:**
```
[PASS] Checkpoint 4: Skills synced to KB via `skillforge elevenlabs sync`
       Skills checked: 4
       Skills synced: 4/4
         - greeting: synced
         - troubleshooting: synced
         - ticket-creation: synced
         - knowledge-search: synced
       Mode: mock (simulated sync)
```

### Checkpoint 5: Manifest Documents Verification

Verifies that the manifest contains document IDs for all synced skills.

**What it checks:**
- Each skill has a document ID in the manifest
- Document IDs are valid (non-empty strings)
- Manifest file exists (in real mode)

**Expected output:**
```
[PASS] Checkpoint 5: Manifest created with document IDs
       Skills checked: 4
       Document IDs present: 4/4
         - greeting: doc_mock_greeting_00...
         - troubleshooting: doc_mock_troubles...
         - ticket-creation: doc_mock_ticket_c...
         - knowledge-search: doc_mock_knowled...
       Mode: mock (simulated manifest)
```

### Checkpoint 6: Voice Agent Creation

Verifies that the voice agent can be created with skills.

**What it checks:**
- Agent has a name
- Agent has a system prompt
- Agent has skills configured
- Agent has a first message
- In `--real` mode: Agent ID is returned from ElevenLabs API

**Expected output:**
```
[PASS] Checkpoint 6: Agent created via CLI with skills
       Agent type: CustomerSupportVoiceAgent
       Name: Voice Support Agent
       Mock mode: True
       Agent ID: None (mock)
       System prompt length: 1234 chars
       Skills count: 4
       Skills: ['greeting', 'troubleshooting', 'ticket-creation', 'knowledge-search']
       First message: Hello! I'm here to help you today. How can I...
```

### Checkpoint 7: Meta-Skill Present

Verifies that the ElevenLabs-specific meta-skill is in the agent's system prompt.

**What it checks:**
- "Using Skills" header is present
- KB query instructions are present
- "Available Skills" section is present
- All configured skills are mentioned in the prompt

**Expected output:**
```
[PASS] Checkpoint 7: System prompt includes ElevenLabs meta-skill
       Has meta-skill: True
       Contains 'Using Skills': True
       Contains KB query instructions: True
       Contains 'Available Skills': True
       Contains 'SKILL:' prefix: True
       All skills mentioned in prompt: True
```

### Checkpoint 8: Agent Configuration

Verifies that an agent can be reconfigured with different skills.

**What it checks:**
- Skills can be updated after agent creation
- KB references are updated to match new skills
- System prompt changes to reflect new skills

**Expected output:**
```
[PASS] Checkpoint 8: Agent configured via CLI (update skills)
       Initial skills: ['greeting', 'troubleshooting', 'ticket-creation', 'knowledge-search']
       New skills: ['greeting', 'troubleshooting']
       Initial KB refs: 4
       New KB refs: 2
       Skills updated correctly: True
       KB refs updated correctly: True
       Prompt changed: True
```

### Checkpoint 9: KB References Validation

Verifies that Knowledge Base references are correctly configured for the agent.

**What it checks:**
- KB references count matches skills count
- Each reference has correct structure (type, name, id, usage_mode)
- Reference names match "SKILL: [skill-name]" format
- Usage mode is "auto" for automatic retrieval

**Expected output:**
```
[PASS] Checkpoint 9: KB references verified via API
       KB references count: 4
       Configured skills count: 4
       References match skills: True
         - greeting: valid (id=doc_mock_greeti...)
         - troubleshooting: valid (id=doc_mock_troubl...)
         - ticket-creation: valid (id=doc_mock_ticket...)
         - knowledge-search: valid (id=doc_mock_knowle...)
       Mode: mock (simulated KB references)
```

## Manual Walkthrough

### Step 1: Verify Skill Discovery Configuration

```bash
cd examples/elevenlabs-demo

# The .skillforge.yaml points to local skills
cat .skillforge.yaml
# skill_paths:
#   - ./skills/*
```

### Step 2: Check Skills Are Symlinked

```bash
ls -la skills/
# Output:
# greeting -> ../../shared-skills/greeting
# knowledge-search -> ../../shared-skills/knowledge-search
# ticket-creation -> ../../shared-skills/ticket-creation
# troubleshooting -> ../../shared-skills/troubleshooting
```

### Step 3: Test Agent Creation (Python)

```python
from agent import create_voice_agent, VOICE_SUPPORT_SKILLS

# Create voice agent in mock mode
agent = create_voice_agent(mock_api=True)

print(f"Agent name: {agent.name}")
print(f"Skills: {agent.skills}")
print(f"KB references: {len(agent.kb_references)}")
print(f"Prompt length: {len(agent.system_prompt)} chars")

# Output:
# Agent name: Voice Support Agent
# Skills: ['greeting', 'troubleshooting', 'ticket-creation', 'knowledge-search']
# KB references: 4
# Prompt length: ~1500 chars
```

### Step 4: Verify Meta-Skill in System Prompt

```python
from agent import create_voice_agent, verify_meta_skill_present

agent = create_voice_agent(mock_api=True)
print(f"Has meta-skill: {verify_meta_skill_present(agent)}")
print(f"Contains 'Using Skills': {'Using Skills' in agent.system_prompt}")
print(f"Contains 'Available Skills': {'Available Skills' in agent.system_prompt}")

# Output:
# Has meta-skill: True
# Contains 'Using Skills': True
# Contains 'Available Skills': True
```

### Step 5: Verify KB References Structure

```python
from agent import create_voice_agent, get_kb_references_for_validation

agent = create_voice_agent(mock_api=True)
kb_refs = get_kb_references_for_validation(agent)

for ref in kb_refs:
    print(f"  - {ref['name']}: type={ref['type']}, mode={ref['usage_mode']}")

# Output:
#   - SKILL: greeting: type=text, mode=auto
#   - SKILL: troubleshooting: type=text, mode=auto
#   - SKILL: ticket-creation: type=text, mode=auto
#   - SKILL: knowledge-search: type=text, mode=auto
```

### Step 6: Test Agent Configuration Update

```python
from agent import create_voice_agent, configure_voice_agent

# Create agent with all skills
agent = create_voice_agent(mock_api=True)
print(f"Initial skills: {agent.skills}")

# Reconfigure with fewer skills
updated = configure_voice_agent(agent, ["greeting", "troubleshooting"])
print(f"Updated skills: {updated.skills}")
print(f"Updated KB refs: {len(updated.kb_references)}")

# Output:
# Initial skills: ['greeting', 'troubleshooting', 'ticket-creation', 'knowledge-search']
# Updated skills: ['greeting', 'troubleshooting']
# Updated KB refs: 2
```

### Step 7: Compare With and Without Skills

```python
from agent import compare_with_without_skills

comparison = compare_with_without_skills()

print(f"Without skills: {comparison['without_skills']['prompt_length']} chars")
print(f"With skills: {comparison['with_skills']['prompt_length']} chars")
print(f"Increase: {comparison['comparison']['prompt_increase']} chars")

# Output:
# Without skills: ~750 chars
# With skills: ~1500 chars
# Increase: ~750 chars
```

### Step 8: Get Conversation Config (for ElevenLabs SDK)

```python
from agent import create_voice_agent

agent = create_voice_agent(mock_api=True)
config = agent.get_conversation_config()

print(f"Has agent section: {'agent' in config}")
print(f"Has prompt: {'prompt' in config['agent']}")
print(f"Has KB refs: {'knowledge_base' in config['agent']['prompt']}")

# Output:
# Has agent section: True
# Has prompt: True
# Has KB refs: True
```

### Step 9: Run Direct Tests

```bash
python agent.py
```

This runs the agent module's built-in tests which verify all core functionality.

## Expected Output

### Quick Validation

```
Working directory: /path/to/examples/elevenlabs-demo

=== Running QUICK validation (mocked API) ===

[PASS] Checkpoint 1: Installation verified (skillforge[elevenlabs] importable)
       skillforge version: x.x.x
       elevenlabs version: x.x.x
       skillforge.adapters.elevenlabs: importable
[PASS] Checkpoint 2: Skills copied locally (symlink or copy)
       greeting: symlink -> /path/to/examples/shared-skills/greeting
       troubleshooting: symlink -> /path/to/examples/shared-skills/troubleshooting
       ticket-creation: symlink -> /path/to/examples/shared-skills/ticket-creation
       knowledge-search: symlink -> /path/to/examples/shared-skills/knowledge-search
[PASS] Checkpoint 3: Credentials configured (from env or interactive)
       Running in mock mode - credentials not required
       ELEVENLABS_API_KEY: skipped (mock mode)
[PASS] Checkpoint 4: Skills synced to KB via `skillforge elevenlabs sync`
       Skills checked: 4
       Skills synced: 4/4
         - greeting: synced
         - troubleshooting: synced
         - ticket-creation: synced
         - knowledge-search: synced
       Mode: mock (simulated sync)
[PASS] Checkpoint 5: Manifest created with document IDs
       Skills checked: 4
       Document IDs present: 4/4
         - greeting: doc_mock_greeting_00...
         - troubleshooting: doc_mock_troubles...
         - ticket-creation: doc_mock_ticket_c...
         - knowledge-search: doc_mock_knowled...
       Mode: mock (simulated manifest)
[PASS] Checkpoint 6: Agent created via CLI with skills
       Agent type: CustomerSupportVoiceAgent
       Name: Voice Support Agent
       Mock mode: True
       Agent ID: None (mock)
       System prompt length: 1500 chars
       Skills count: 4
       Skills: ['greeting', 'troubleshooting', 'ticket-creation', 'knowledge-search']
       First message: Hello! I'm here to help you today. How can I...
[PASS] Checkpoint 7: System prompt includes ElevenLabs meta-skill
       Has meta-skill: True
       Contains 'Using Skills': True
       Contains KB query instructions: True
       Contains 'Available Skills': True
       Contains 'SKILL:' prefix: True
       All skills mentioned in prompt: True
[PASS] Checkpoint 8: Agent configured via CLI (update skills)
       Initial skills: ['greeting', 'troubleshooting', 'ticket-creation', 'knowledge-search']
       New skills: ['greeting', 'troubleshooting']
       Initial KB refs: 4
       New KB refs: 2
       Skills updated correctly: True
       KB refs updated correctly: True
       Prompt changed: True
[PASS] Checkpoint 9: KB references verified via API
       KB references count: 4
       Configured skills count: 4
       References match skills: True
         - greeting: valid (id=doc_mock_greeti...)
         - troubleshooting: valid (id=doc_mock_troubl...)
         - ticket-creation: valid (id=doc_mock_ticket...)
         - knowledge-search: valid (id=doc_mock_knowle...)
       Mode: mock (simulated KB references)

============================================================
VALIDATION SUMMARY: 9/9 checkpoints passed
============================================================

All validations passed!
```

## How ElevenLabs Integration Differs

### vs. LangChain Demo

| Aspect | ElevenLabs Demo | LangChain Demo |
|--------|-----------------|----------------|
| Skill delivery | Knowledge Base (RAG) | Direct prompt injection or CLI |
| Skill loading | Automatic via KB query | On-demand via `skillforge read` |
| Meta-skill type | KB query instructions | CLI command instructions |
| API requirement | ElevenLabs API | OpenAI API (for real mode) |
| Agent type | Voice/Conversational | Text-based |
| Skill storage | ElevenLabs KB documents | Local files only |

### vs. CrewAI Demo

| Aspect | ElevenLabs Demo | CrewAI Demo |
|--------|-----------------|-------------|
| Agent pattern | Single voice agent | Multi-agent crew |
| Interaction mode | Voice conversation | Text task processing |
| Skill retrieval | RAG from KB | Direct injection |
| Coordination | None (single agent) | Task delegation |

## Troubleshooting

### Import Errors

```
ImportError: No module named 'elevenlabs'
```

**Solution**: Install the ElevenLabs SDK:
```bash
pip install elevenlabs>=1.0.0
```

Or install skillforge with ElevenLabs extras:
```bash
pip install skillforge[elevenlabs]
```

### Skills Not Found

```
SkillNotFoundError: Skill 'greeting' not found
```

**Solution**: Ensure `.skillforge.yaml` exists and points to the correct path:
```yaml
skill_paths:
  - ./skills/*
```

Verify skills directory contains symlinks or copies:
```bash
ls -la skills/
# Should show: greeting, troubleshooting, ticket-creation, knowledge-search
```

### Missing API Key (Real Mode)

```
[WARN] ELEVENLABS_API_KEY not set.
       Real validation requires a valid API key.
```

**Solution**: Set your ElevenLabs API key:
```bash
export ELEVENLABS_API_KEY=your-api-key
```

Or create a `.env` file:
```bash
ELEVENLABS_API_KEY=your-api-key
```

### API Connection Failed

```
Error: API error: Authentication failed
```

**Solution**:
1. Verify your API key is correct
2. Check that your ElevenLabs account is active
3. Ensure you have sufficient credits/quota

### Mock Mode Fallback

```
skillforge.adapters.elevenlabs: not yet implemented
```

**Note**: This is expected if the ElevenLabs adapter is not yet fully implemented. The demo will automatically fall back to mock mode for validation.

### KB Sync Failed

```
[FAIL] Checkpoint 4: Skills synced to KB
       Only 2/4 skills synced
```

**Solution**:
1. Verify all skill files exist and are valid SKILL.md format
2. Check ElevenLabs API connection
3. Review ElevenLabs KB quota limits
4. Re-run sync command: `skillforge elevenlabs sync`

## Files

| File | Description |
|------|-------------|
| `.skillforge.yaml` | Configuration pointing to `./skills/*` |
| `requirements.txt` | Python dependencies (elevenlabs, skillforge[elevenlabs]) |
| `agent.py` | CustomerSupportVoiceAgent class with KB integration |
| `run.py` | Validation script with 9 checkpoints |
| `skills/` | Symlinks to `../shared-skills/` |
| `README.md` | This documentation |

## Related Examples

- `examples/shared-skills/` - Shared skills used by this demo
- `examples/langchain-demo/` - LangChain single-agent integration example
- `examples/crewai-demo/` - CrewAI multi-agent integration example

## Key Concepts

### ElevenLabs Knowledge Base

The Knowledge Base is ElevenLabs' RAG (Retrieval-Augmented Generation) system that allows agents to access external information during conversations. SkillForge uses this to store skill instructions:

1. **Sync**: Skills are uploaded as text documents to the KB
2. **Reference**: Document IDs are stored in the manifest
3. **Query**: Agents query "SKILL: [name]" to retrieve instructions
4. **Execute**: Retrieved instructions guide agent behavior

### ElevenLabs Meta-Skill

The ElevenLabs meta-skill differs from the standard SkillForge meta-skill:

- **Standard**: Uses `skillforge read` CLI command
- **ElevenLabs**: Uses KB query with "SKILL: [name]" pattern

This allows voice agents to retrieve skill instructions without shell access.

### Manifest File

The ElevenLabs manifest (`.skillforge/elevenlabs-manifest.json`) tracks:

```json
{
  "skills": {
    "greeting": {
      "document_id": "doc_abc123...",
      "synced_at": "2024-01-18T12:00:00Z",
      "content_hash": "sha256:..."
    }
  }
}
```

This enables:
- Incremental sync (only changed skills)
- Document ID lookup for KB references
- Sync status verification
