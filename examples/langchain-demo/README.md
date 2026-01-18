# LangChain Demo - SkillForge Single-Agent Example

This example demonstrates SkillForge integration with LangChain using a single conversational customer support agent. It validates progressive skill loading, inject mode comparison, and system prompt composition.

## What This Validates

| Feature | Implementation |
|---------|----------------|
| CLI `skillforge read` | Runtime skill loading via shell command |
| Progressive mode | Meta-skill teaches agent to load skills on-demand |
| Inject mode | Full skill content in system prompt (comparison) |
| System prompt composition | Skills integrated into agent prompts |
| Meta-skill instruction following | Agent learns skill discovery pattern |
| Single-agent architecture | Simpler than multi-agent patterns |
| Local skill discovery | Skills loaded from `./skills/` directory |

## Architecture

```
Customer Message
       |
       v
+---------------------------+
|  Customer Support Agent   |
|     (progressive mode)    |
|  - greeting               |
|  - troubleshooting        |
|  - ticket-creation        |
|  - knowledge-search       |
+---------------------------+
       |
       v
  Agent Response
```

**Single Agent Design**: Unlike the CrewAI multi-agent demo, this example uses a single conversational agent that can access all skills. This demonstrates a simpler integration pattern suitable for:
- Chatbots and conversational interfaces
- Single-purpose agents with multiple capabilities
- Applications where multi-agent coordination is unnecessary

**Progressive Mode**: The agent's system prompt includes the meta-skill, which teaches it to load skills on-demand using `skillforge read <skill-name>`. This keeps the initial context window smaller.

**Inject Mode**: For comparison, the demo also shows inject mode where full skill content is added directly to the system prompt.

## Quick Start

### 1. Install Dependencies

```bash
# From the examples/langchain-demo directory
pip install -r requirements.txt
```

Or install skillforge with LangChain support:

```bash
pip install skillforge[langchain]
```

### 2. Run Validation (Quick Mode)

```bash
python run.py --quick
```

This runs all validations with mocked LLM calls, suitable for CI/CD.

### 3. Run Validation (Real Mode)

```bash
export OPENAI_API_KEY=your-api-key
python run.py --real
```

This runs the agent with actual LLM API calls.

## Manual Walkthrough

### Step 1: Verify Skill Discovery

```bash
cd examples/langchain-demo

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

### Step 3: Test CLI Read Command

```bash
skillforge read greeting --from ./skills
# Output:
# # Customer Greeting Skill
#
# Welcome customers warmly and establish a supportive, professional tone...
```

### Step 4: Test Agent Creation (Python)

```python
from agent import create_support_agent, create_support_agent_inject_mode

# Create progressive mode agent (default)
agent = create_support_agent(mock_llm=True)
print(f"Mode: {agent.skill_mode}")
print(f"Skills: {agent.skills}")
print(f"Prompt length: {len(agent.system_prompt)} chars")
# Output:
# Mode: progressive
# Skills: ['greeting', 'troubleshooting', 'ticket-creation', 'knowledge-search']
# Prompt length: ~2346 chars

# Create inject mode agent
inject_agent = create_support_agent_inject_mode(mock_llm=True)
print(f"Mode: {inject_agent.skill_mode}")
print(f"Prompt length: {len(inject_agent.system_prompt)} chars")
# Output:
# Mode: inject
# Prompt length: ~8806 chars
```

### Step 5: Verify Meta-Skill in System Prompt

```python
from agent import create_support_agent, verify_meta_skill_present

agent = create_support_agent(mock_llm=True)
print(f"Has meta-skill: {verify_meta_skill_present(agent)}")
print(f"Contains 'skillforge read': {'skillforge read' in agent.system_prompt}")
# Output:
# Has meta-skill: True
# Contains 'skillforge read': True
```

### Step 6: Compare Mode Prompt Sizes

```python
from agent import compare_modes

comparison = compare_modes()
print(f"Progressive: {comparison['progressive']['prompt_length']} chars")
print(f"Inject: {comparison['inject']['prompt_length']} chars")
print(f"Difference: {comparison['comparison']['inject_larger_by']} chars")
# Output:
# Progressive: 2346 chars
# Inject: 8806 chars
# Difference: 6460 chars
```

### Step 7: Execute Agent (Requires API Key)

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"

from agent import create_support_agent

agent = create_support_agent()
response = agent.invoke({
    "messages": [("human", "Hi, I need help with my email not syncing.")]
})
print(response)
```

## Expected Output

### Quick Validation

```
Working directory: /path/to/examples/langchain-demo

=== Running QUICK validation (mocked LLM) ===

[PASS] Checkpoint 1: Installation verified (skillforge[langchain] importable)
       langchain version: 1.2.3
       skillforge.langchain adapter importable: True
[PASS] Checkpoint 2: Skills copied locally (symlink or copy)
       greeting: symlink -> /path/to/examples/shared-skills/greeting
       troubleshooting: symlink -> /path/to/examples/shared-skills/troubleshooting
       ticket-creation: symlink -> /path/to/examples/shared-skills/ticket-creation
       knowledge-search: symlink -> /path/to/examples/shared-skills/knowledge-search
[PASS] Checkpoint 3: CLI `skillforge read` command works
       skillforge read greeting: success
       Output contains expected skill content
       Preview: # Customer Greeting Skill  Welcome customers warmly and establish a supportive, professional tone fo...
[PASS] Checkpoint 4: Agent created in progressive mode
       Agent type: CustomerSupportAgent
       Mode: progressive
       Skills count: 4
       Skills: ['greeting', 'troubleshooting', 'ticket-creation', 'knowledge-search']
       System prompt length: 2346 chars
[PASS] Checkpoint 5: System prompt includes meta-skill
       Has meta-skill: True
       Contains 'Using SkillForge Skills': True
       Contains 'skillforge read': True
       Contains all skill names: True
[PASS] Checkpoint 6: Greeting skill used correctly (output format matches)
       Skill name: greeting
       Has Output Format section: True
       Has Greeting template: True
       Has Introduction template: True
       Has Offer template: True
[PASS] Checkpoint 7: Troubleshooting skill used correctly
       Skill name: troubleshooting
       Has Output Format section: True
       Has Problem template: True
       Has Diagnosis Steps template: True
       Has Resolution template: True
       Has Email Sync framework: True
       Has Password Reset framework: True
[PASS] Checkpoint 8: Ticket creation skill used correctly
       Skill name: ticket-creation
       Has Output Format: True
       Has create_ticket reference: True
       Has Priority Guidelines: True
       Tool test result: {'ticket_id': 'TICK-1234', 'status': 'created', ...}
       Has ticket_id: True
       Has correct status: True
       Has correct priority: True
[PASS] Checkpoint 9: Inject mode comparison works (compare prompt sizes)
       Progressive agent mode verified: True
       Inject agent mode verified: True
       Progressive prompt length: 2346 chars
       Inject prompt length: 8806 chars
       Inject larger by: 6460 chars
       Inject mode is larger (expected): True
       compare_modes() helper works: True

============================================================
VALIDATION SUMMARY: 9/9 checkpoints passed
============================================================

All validations passed!
```

## Skill Modes Explained

### Progressive Mode (Default)

Progressive mode is the recommended approach for production use:

1. Only the meta-skill is injected into the system prompt
2. The agent sees a list of available skills
3. Skills are loaded on-demand via `skillforge read <skill-name>`
4. Best for: Keeping context window small, dynamic skill selection

```python
# Progressive mode injection
agent = create_support_agent(
    skills=["greeting", "troubleshooting", "ticket-creation", "knowledge-search"],
    # skill_mode="progressive" is the default
)

# System prompt contains:
# - Original system prompt
# - Meta-skill with skill discovery instructions
# - List of available skills as bullets
```

### Inject Mode (Comparison)

Inject mode provides immediate access to all skill content:

1. Full skill content is injected into the system prompt
2. All instructions, examples, and output formats are immediately available
3. Best for: Static skill sets, environments without shell access

```python
# Inject mode injection
agent = create_support_agent_inject_mode(
    skills=["greeting", "troubleshooting", "ticket-creation", "knowledge-search"]
)

# System prompt contains:
# - Original system prompt
# - ## Available Skills section
# - Full content for each skill with ### headers
```

### Mode Comparison

| Aspect | Progressive | Inject |
|--------|-------------|--------|
| Initial prompt size | Smaller (~2.3k chars) | Larger (~8.8k chars) |
| Skill access | On-demand via CLI | Immediate |
| Context window usage | Lower | Higher |
| Requires shell tool | Yes | No |
| Dynamic skill selection | Yes | No |

## Troubleshooting

### Import Errors

```
ImportError: No module named 'langchain'
```

**Solution**: Install LangChain with `pip install langchain>=0.3.0 langchain-openai>=0.2.0`

### Skills Not Found

```
SkillNotFoundError: Skill 'greeting' not found
```

**Solution**: Ensure `.skillforge.yaml` exists and points to the correct path:
```yaml
skill_paths:
  - ./skills/*
```

### CLI Read Fails

```
Error: Skill 'greeting' not found in /path/to/skills
```

**Solution**: Verify skills directory contains symlinks or copies:
```bash
ls -la skills/
# Should show: greeting, troubleshooting, ticket-creation, knowledge-search
```

### Real Mode Without API Key

```
[WARN] OPENAI_API_KEY not set or is dummy key.
       Real validation requires a valid API key.
```

**Solution**: Set your OpenAI API key:
```bash
export OPENAI_API_KEY=your-api-key
```

### Shell Tool Not Available

```
Warning: Shell tool not available for progressive mode
```

**Solution**: Install langchain-community:
```bash
pip install langchain-community
```

The shell tool is required for progressive mode to execute `skillforge read` commands.

## Files

| File | Description |
|------|-------------|
| `.skillforge.yaml` | Configuration pointing to `./skills/*` |
| `requirements.txt` | Python dependencies (langchain, skillforge) |
| `agent.py` | CustomerSupportAgent class with progressive/inject modes |
| `run.py` | Validation script with 9 checkpoints |
| `skills/` | Symlinks to `../shared-skills/` |
| `README.md` | This documentation |

## Related Examples

- `examples/shared-skills/` - Shared skills used by this demo
- `examples/crewai-demo/` - CrewAI multi-agent integration example

## Key Differences from CrewAI Demo

| Aspect | LangChain Demo | CrewAI Demo |
|--------|----------------|-------------|
| Agent pattern | Single agent | Multi-agent crew |
| Skill distribution | All skills on one agent | Skills distributed across agents |
| Coordination | None needed | Task delegation |
| Complexity | Simpler | More complex |
| Use case | Chatbots, simple agents | Workflows, pipelines |
