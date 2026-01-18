# CrewAI Demo - SkillForge Multi-Agent Example

This example demonstrates SkillForge integration with CrewAI using a three-agent customer support crew. It validates multi-agent coordination, skill injection modes, and tool bundling.

## What This Validates

| Feature | Implementation |
|---------|----------------|
| Multi-agent crew | 3 specialized agents with task delegation |
| Progressive mode | Router agent loads skills on-demand |
| Inject mode | Specialist and escalation agents get full content |
| Shared skills | Skills loaded from `../shared-skills/` |
| Tool bundling | `create_ticket` and `search_kb` tools |
| Marketplace CLI | Add, list, and install skills |

## Architecture

```
Customer Message
       |
       v
+----------------+     +--------------------+     +-------------------+
|  Router Agent  | --> | Specialist Agent   | --> | Escalation Agent  |
|  (progressive) |     |     (inject)       |     |     (inject)      |
|  - greeting    |     | - troubleshooting  |     | - ticket-creation |
+----------------+     | - knowledge-search |     +-------------------+
                       +--------------------+
```

**Router Agent**: First contact, greets customers warmly using the greeting skill in progressive mode. Routes to specialist or escalation.

**Specialist Agent**: Technical troubleshooter using troubleshooting and knowledge-search skills in inject mode. Has access to the `search_kb` tool for knowledge base lookups.

**Escalation Agent**: Creates tickets for unresolved issues using ticket-creation skill in inject mode. Has access to the `create_ticket` tool.

## Quick Start

### 1. Install Dependencies

```bash
# From the examples/crewai-demo directory
pip install -r requirements.txt
```

Or install skillforge with CrewAI support:

```bash
pip install skillforge[crewai]
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

This runs the crew with actual LLM API calls.

## Manual Walkthrough

### Step 1: Verify Skill Discovery

```bash
cd examples/crewai-demo

# The .skillforge.yaml points to shared skills
cat .skillforge.yaml
# skill_paths:
#   - ../shared-skills/*
```

### Step 2: Add Marketplace

```bash
skillforge marketplace add ../shared-skills
# Output:
# Added marketplace: shared-skills
#   Source: ../shared-skills
#   Type: local
#   Skills: 4
```

### Step 3: List Available Skills

```bash
skillforge marketplace list
# Output:
#          Configured Marketplaces
# +---------------+-------+--------+------------------+
# | Name          | Type  | Skills | Source           |
# +---------------+-------+--------+------------------+
# | shared-skills | local | 4      | ../shared-skills |
# +---------------+-------+--------+------------------+
```

### Step 4: Test Crew Creation

```python
from crew import CustomerSupportCrew

support_crew = CustomerSupportCrew()

# Check router agent
router = support_crew.router_agent()
print(f"Router skills: {router.skills}")
print(f"Router mode: {router.skill_mode}")
# Output:
# Router skills: ['greeting']
# Router mode: progressive

# Check specialist agent
specialist = support_crew.specialist_agent()
print(f"Specialist skills: {specialist.skills}")
print(f"Specialist mode: {specialist.skill_mode}")
# Output:
# Specialist skills: ['troubleshooting', 'knowledge-search']
# Specialist mode: inject

# Verify skill content in backstory
print("Has meta-skill:" if "Using SkillForge Skills" in router.backstory else "No meta-skill")
print("Has full content:" if "## Available Skills" in specialist.backstory else "No full content")
```

### Step 5: Execute Crew (Requires API Key)

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"

from crew import CustomerSupportCrew

support_crew = CustomerSupportCrew()
crew = support_crew.crew(
    customer_message="Hi, I can't access my email",
    issue_description="Email login failing after password change",
    issue_summary="Email access issue needs escalation"
)

result = crew.kickoff()
print(result)
```

## Expected Output

### Quick Validation

```
Working directory: /path/to/examples/crewai-demo

=== Running QUICK validation (mocked LLM) ===

[PASS] Installation: skillforge[crewai] importable
       crewai version: 0.41.0
[PASS] Marketplace CLI: add ../shared-skills
       Marketplace added successfully
       Output confirmed: 'Added marketplace:'
[PASS] Marketplace CLI: list shows shared-skills
       shared-skills marketplace found in list
[PASS] Skill Discovery: shared skills found via config
       Found skills: ['greeting', 'troubleshooting', 'ticket-creation', 'knowledge-search']
       Expected: ['greeting', 'troubleshooting', 'knowledge-search', 'ticket-creation']
[PASS] Crew Creation: 3 agents created
       Agents created: 3
       Tasks created: 3
[PASS] Router Agent: progressive mode with greeting skill
       Skills: ['greeting']
       Mode: progressive
       Has meta-skill in backstory: True
       Has skill list in backstory: True
[PASS] Specialist Agent: inject mode with troubleshooting + knowledge-search
       Skills: ['troubleshooting', 'knowledge-search']
       Mode: inject
       Has full skills section: True
       Has troubleshooting content: True
       Has knowledge-search content: True
[PASS] Escalation Agent: inject mode with ticket-creation
       Skills: ['ticket-creation']
       Mode: inject
       Has full skills section: True
       Has ticket-creation content: True
       Has create_ticket tool reference: True
[PASS] Greeting Skill: output format available
       Has Output Format section: True
       Has Greeting template: True
       Has Introduction template: True
       Has Offer template: True
[PASS] Troubleshooting Skill: output format available
       Has Output Format section: True
       Has Problem template: True
       Has Diagnosis Steps template: True
       Has Resolution template: True
[PASS] Ticket Creation: bundled create_ticket tool
       Tool result: {'ticket_id': 'TICK-1234', 'status': 'created', ...}
       Has ticket_id: True
       Has correct status: True
       Has correct priority: True
[PASS] Knowledge Search: bundled search_kb tool
       Results count: 3
       First result: {'id': 'KB-1001', 'title': 'How to Fix Email Sync Issues', ...}
       Is list: True
       Has results: True

============================================================
VALIDATION SUMMARY: 12/12 checkpoints passed
============================================================

All validations passed!
```

## Skill Modes Explained

### Progressive Mode (Router Agent)

The router agent uses **progressive mode**, which means:
1. Only the meta-skill is injected into the backstory
2. The agent sees a list of available skills
3. Skills are loaded on-demand via `skillforge read <skill-name>`
4. Best for: Agents that may not need all skills for every task

```python
# Progressive mode injection
router = Agent(
    role="Router",
    skills=["greeting"],
    skill_mode="progressive"
)

# Backstory contains:
# - Original backstory
# - Meta-skill with skill discovery instructions
# - List of available skills (greeting)
```

### Inject Mode (Specialist/Escalation Agents)

The specialist and escalation agents use **inject mode**, which means:
1. Full skill content is injected into the backstory
2. All instructions, examples, and output formats are immediately available
3. Best for: Agents that always need specific skill knowledge

```python
# Inject mode injection
specialist = Agent(
    role="Specialist",
    skills=["troubleshooting", "knowledge-search"],
    skill_mode="inject"
)

# Backstory contains:
# - Original backstory
# - ## Available Skills section
# - Full troubleshooting skill content
# - Full knowledge-search skill content
```

## Troubleshooting

### Import Errors

```
ImportError: No module named 'crewai'
```

**Solution**: Install CrewAI with `pip install crewai>=0.41.0`

### Skills Not Found

```
SkillNotFoundError: Skill 'greeting' not found
```

**Solution**: Ensure `.skillforge.yaml` exists and points to the correct path:
```yaml
skill_paths:
  - ../shared-skills/*
```

### Marketplace Add Fails

```
MarketplaceExistsError: Marketplace 'shared-skills' already exists
```

**Solution**: Remove first with `skillforge marketplace remove shared-skills -f`

### Real Mode Without API Key

```
[WARN] OPENAI_API_KEY not set. Real validation requires an API key.
```

**Solution**: Set your OpenAI API key:
```bash
export OPENAI_API_KEY=your-api-key
```

## Files

| File | Description |
|------|-------------|
| `.skillforge.yaml` | Configuration pointing to shared skills |
| `requirements.txt` | Python dependencies |
| `crew.py` | CustomerSupportCrew class implementation |
| `run.py` | Validation script with checkpoints |
| `README.md` | This documentation |

## Related Examples

- `examples/shared-skills/` - Shared skills used by this demo
- Future: `examples/langchain-demo/` - LangChain integration example
