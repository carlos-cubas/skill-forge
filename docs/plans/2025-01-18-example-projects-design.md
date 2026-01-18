# Example Projects Design - Customer Support Bot

**Created:** 2025-01-18
**Purpose:** Comprehensive example projects that validate all SkillForge features while providing relatable user-facing demos

## Overview

Three separate focused examples demonstrating SkillForge across all supported frameworks (CrewAI, LangChain, ElevenLabs) using a customer support bot use case. Each example validates core functionality through automated scripts while serving as reference implementations for users.

**Goals:**
1. **Validation:** Verify all features work end-to-end (installation → CLI → adapters → execution)
2. **Documentation:** Provide relatable examples users can learn from
3. **CI Integration:** Automated validation scripts for regression testing

## Directory Structure

```
examples/
├── README.md                          # Overview of all examples
├── shared-skills/                     # Reusable across all examples
│   ├── greeting/
│   │   └── SKILL.md
│   ├── troubleshooting/
│   │   └── SKILL.md
│   ├── ticket-creation/
│   │   ├── SKILL.md
│   │   └── tools.py
│   └── knowledge-search/
│       ├── SKILL.md
│       └── tools.py
├── crewai-demo/
│   ├── README.md
│   ├── run.py
│   ├── requirements.txt
│   ├── .skillforge.yaml
│   └── agents/
│       ├── router/
│       ├── specialist/
│       └── escalation/
├── langchain-demo/
│   ├── README.md
│   ├── run.py
│   ├── requirements.txt
│   ├── .skillforge.yaml
│   └── agent.py
└── elevenlabs-demo/
    ├── README.md
    ├── run.py
    ├── requirements.txt
    ├── .skillforge.yaml
    └── agent.py
```

## Shared Skills (4 Skills)

All examples reference `../shared-skills/*` in their `.skillforge.yaml`, demonstrating skill reuse across projects.

### 1. greeting (Simple, No Tools)

```markdown
---
name: greeting
description: Welcome users warmly and set a helpful tone
allowed-tools: []
---

# Customer Greeting Skill

## When to Use
- First interaction with customer
- Setting supportive tone
- Building rapport

## Instructions
1. Acknowledge the customer warmly
2. Introduce yourself as their support agent
3. Ask how you can help today

## Output Format
Greeting: [warm welcome]
Introduction: [your role]
Offer: [ask how to help]
```

### 2. troubleshooting (Medium, No Tools)

Step-by-step diagnosis framework covering:
- Email sync issues
- Password reset problems
- Access/login issues

**Output Format:**
```
Problem: [restate customer's issue]
Diagnosis Steps:
1. [first check]
2. [second check]
3. [third check]
Resolution: [solution or escalation]
```

### 3. ticket-creation (Complex, With Tool)

Creates support ticket via bundled tool.

**tools.py:**
```python
def create_ticket(title: str, description: str, priority: str) -> dict:
    """Mock ticket creation tool."""
    return {
        "ticket_id": f"TICK-{random.randint(1000, 9999)}",
        "status": "created",
        "priority": priority
    }
```

**Output Format:**
```
Ticket Created: [ticket ID]
Summary: [title]
Priority: [level]
Next Steps: [what customer should expect]
```

### 4. knowledge-search (Complex, With Tool)

Searches mock knowledge base articles.

**tools.py:**
```python
def search_kb(query: str) -> list[dict]:
    """Mock KB search returning relevant articles."""
    kb = {
        "email sync": ["How to Fix Email Sync Issues", "Email Troubleshooting Guide"],
        "password": ["Password Reset Steps", "Account Security Best Practices"],
        "login": ["Login Issues Troubleshooting", "Two-Factor Authentication Setup"]
    }
    # Return matching articles
```

**Output Format:**
```
Articles Found: [count]
Best Match: [article title]
Summary: [key points]
Link: [article reference]
```

## CrewAI Demo - Multi-Agent Support Crew

**Purpose:** Validate CrewAI adapter with multi-agent crew, marketplace CLI, both skill modes, and tool bundling.

### Architecture

Three-agent crew with task delegation:
- **Router Agent** (progressive mode) - Uses greeting skill, routes to specialist
- **Specialist Agent** (inject mode) - Uses troubleshooting + knowledge-search skills
- **Escalation Agent** (inject mode) - Uses ticket-creation skill with bundled tool

### Files

```
crewai-demo/
├── README.md              # Manual walkthrough
├── run.py                 # Automated validation
├── requirements.txt       # crewai, skillforge[crewai]
├── .skillforge.yaml       # Points to ../shared-skills
└── agents/
    ├── router/
    │   └── config.yaml    # Router agent config
    ├── specialist/
    │   └── config.yaml    # Specialist agent config
    └── escalation/
        └── config.yaml    # Escalation agent config
```

### Validation Flow (run.py)

```python
checkpoints = [
    ValidationCheckpoint("Installation verified"),
    ValidationCheckpoint("Marketplace CLI: add"),
    ValidationCheckpoint("Marketplace CLI: install"),
    ValidationCheckpoint("Marketplace CLI: list"),
    ValidationCheckpoint("Crew created (3 agents)"),
    ValidationCheckpoint("Router used greeting skill"),
    ValidationCheckpoint("Specialist used troubleshooting"),
    ValidationCheckpoint("Escalation created ticket"),
    ValidationCheckpoint("Tool called successfully"),
]

# Steps:
# 1. skillforge marketplace add ../shared-skills
# 2. skillforge install greeting@local troubleshooting@local
# 3. skillforge list (verify manifest)
# 4. Create crew with 3 agents
# 5. Execute task: "My email isn't syncing"
# 6. Verify outputs match expected formats
```

### Key Features Validated

- ✓ CLI: `marketplace add/install/list`
- ✓ Progressive mode (router agent)
- ✓ Inject mode (specialist, escalation)
- ✓ Tool bundling (ticket-creation)
- ✓ Multi-agent coordination
- ✓ `.skillforge.yaml` discovery
- ✓ Skill reuse from shared directory

## LangChain Demo - Conversational Support Agent

**Purpose:** Validate LangChain adapter with single-agent pattern, runtime skill loading (`skillforge read`), progressive mode emphasis, and system prompt building.

### Architecture

Single conversational agent that:
- Uses progressive mode by default
- Loads skills on-demand via `skillforge read`
- Demonstrates meta-skill teaching agent to load skills
- Shows system prompt composition

### Files

```
langchain-demo/
├── README.md              # Manual walkthrough
├── run.py                 # Automated validation
├── requirements.txt       # langchain, skillforge[langchain]
├── .skillforge.yaml       # Points to ./skills
├── agent.py               # Agent implementation
└── skills/                # Local copy of shared-skills
    ├── greeting/
    ├── troubleshooting/
    ├── ticket-creation/
    └── knowledge-search/
```

### Validation Flow (run.py)

```python
checkpoints = [
    ValidationCheckpoint("Installation verified"),
    ValidationCheckpoint("Skills copied locally"),
    ValidationCheckpoint("CLI read command works"),
    ValidationCheckpoint("Agent created (progressive mode)"),
    ValidationCheckpoint("System prompt includes meta-skill"),
    ValidationCheckpoint("Greeting skill used correctly"),
    ValidationCheckpoint("Troubleshooting skill used correctly"),
    ValidationCheckpoint("Ticket creation skill used correctly"),
    ValidationCheckpoint("Inject mode comparison works"),
]

# Steps:
# 1. Copy shared-skills to ./skills
# 2. Test: skillforge read greeting --from ./skills/
# 3. Create agent with progressive mode (all 4 skills)
# 4. Execute conversation:
#    - "Hello" → loads greeting
#    - "My password reset isn't working" → loads troubleshooting
#    - "This isn't helping" → loads ticket-creation
# 5. Verify system prompt structure
# 6. Create second agent in inject mode, compare prompts
```

### Key Features Validated

- ✓ CLI: `skillforge read` (runtime skill loading)
- ✓ Progressive mode (primary use case)
- ✓ Inject mode (comparison)
- ✓ System prompt composition
- ✓ Meta-skill instruction following
- ✓ Single-agent skill selection
- ✓ Local skill discovery

## ElevenLabs Demo - Voice Support Agent

**Purpose:** Validate ElevenLabs adapter's unique workflow: sync to KB, agent creation/configuration, RAG-based skill loading, credentials management.

### Architecture

Voice support agent with:
- Knowledge Base-backed skills
- Full ElevenLabs workflow (sync → create → configure)
- RAG-based skill retrieval
- ElevenLabs-specific meta-skill

### Files

```
elevenlabs-demo/
├── README.md              # Manual walkthrough
├── run.py                 # Automated validation
├── requirements.txt       # elevenlabs, skillforge[elevenlabs]
├── .skillforge.yaml       # Points to ./skills
├── agent.py               # Agent implementation
└── skills/                # Local copy of shared-skills
    ├── greeting/
    ├── troubleshooting/
    ├── ticket-creation/
    └── knowledge-search/
```

### Validation Flow (run.py)

```python
checkpoints = [
    ValidationCheckpoint("Installation verified"),
    ValidationCheckpoint("Skills copied locally"),
    ValidationCheckpoint("Credentials configured"),
    ValidationCheckpoint("Skills synced to KB"),
    ValidationCheckpoint("Manifest created with document IDs"),
    ValidationCheckpoint("Agent created via CLI"),
    ValidationCheckpoint("System prompt includes meta-skill"),
    ValidationCheckpoint("Agent configured via CLI"),
    ValidationCheckpoint("KB references verified"),
]

# Steps:
# 1. Copy shared-skills to ./skills
# 2. skillforge elevenlabs connect (from env or interactive)
# 3. skillforge elevenlabs sync
#    - Verify skills uploaded with # SKILL: headers
#    - Verify manifest created with document IDs
# 4. skillforge elevenlabs create --name "Support Bot" --skills greeting,troubleshooting
#    - Verify agent created with KB references
#    - Verify system prompt includes ElevenLabs meta-skill
# 5. skillforge elevenlabs configure --agent-id <id> --skills greeting,troubleshooting,ticket-creation
# 6. Verify KB structure
# 7. Optional: Test conversation (requires API key, skippable)
```

### Key Features Validated

- ✓ CLI: `elevenlabs connect/sync/create/configure`
- ✓ Knowledge Base sync workflow
- ✓ ElevenLabs meta-skill injection
- ✓ Skill directory generation
- ✓ Manifest tracking with document IDs
- ✓ Python API: `Agent.create()`, `Agent.configure()`
- ✓ RAG-based skill loading (optional live test)

## Automated Validation Pattern

All `run.py` scripts follow a common pattern for consistent validation.

### ValidationCheckpoint Class

```python
class ValidationCheckpoint:
    """Represents a single validation step."""

    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None

    def check(self, condition: bool, error_msg: str = "") -> bool:
        """Check condition and record result."""
        self.passed = condition
        if not condition:
            self.error = error_msg

        # Print result
        print(f"{'✓' if self.passed else '✗'} {self.name}")
        if self.error:
            print(f"  Error: {self.error}")

        return self.passed
```

### Main Validation Structure

```python
def main():
    # Define checkpoints
    checkpoints = [
        ValidationCheckpoint("Installation verified"),
        ValidationCheckpoint("CLI commands work"),
        # ... more checkpoints
    ]

    # Run validation steps
    try:
        validate_installation(checkpoints[0])
        validate_cli(checkpoints[1])
        # ... more steps
    except Exception as e:
        print(f"\n✗ Validation failed with error: {e}")
        sys.exit(1)

    # Summary
    passed = sum(c.passed for c in checkpoints)
    total = len(checkpoints)
    print(f"\n{'='*60}")
    print(f"Validation Summary: {passed}/{total} checks passed")
    print(f"{'='*60}")

    sys.exit(0 if passed == total else 1)
```

### Validation Modes

- `python run.py --quick` - Mock APIs, fast validation (CI mode)
- `python run.py --real` - Real API calls, full validation (requires keys)
- `python run.py --interactive` - Step-by-step with pauses

### Error Handling

**Graceful failures with helpful messages:**
- Missing API keys → Skip real API tests, warn user
- Import errors → Clear message about which extras to install
- Skill not found → Show available skills, suggest fix
- CLI command fails → Show command output, suggest troubleshooting

**Example:**
```python
try:
    import crewai
except ImportError:
    print("✗ CrewAI not installed")
    print("  Fix: pip install skillforge[crewai]")
    sys.exit(1)
```

## README Structure

### Individual Example READMEs

Each demo has a README with this structure:

```markdown
# SkillForge [Framework] Demo - Customer Support Bot

## What This Validates
- ✓ Installation with [framework] extras
- ✓ CLI commands (marketplace, install, list, read)
- ✓ [Framework-specific features]
- ✓ Skill modes (progressive/inject)
- ✓ Tool bundling

## Quick Start
1. Install: `pip install -e ../../[<framework>]`
2. Run: `python run.py`

## Manual Walkthrough

### Step 1: Installation
```bash
pip install -e ../../[crewai]
```
**Expected:** SkillForge and CrewAI installed

### Step 2: Configure Skills
```bash
cat .skillforge.yaml
```
**Expected:** See skill_paths pointing to ../shared-skills

[More steps...]

## Files
- run.py - Automated validation
- .skillforge.yaml - Config
- requirements.txt - Dependencies
- [framework-specific files]

## Expected Output
```
✓ Installation verified
✓ CLI commands work
✓ Skills loaded
✓ Agent created
✓ Skills used correctly
✓ Output format matches

========================================
Validation Summary: 6/6 checks passed
========================================
```

## Troubleshooting
[Common issues and fixes]
```

### Top-Level examples/README.md

```markdown
# SkillForge Examples

Comprehensive examples demonstrating SkillForge across all supported frameworks.

## Examples

| Example | Framework | Features |
|---------|-----------|----------|
| [crewai-demo](./crewai-demo/) | CrewAI | Multi-agent crew, marketplace CLI, tool bundling |
| [langchain-demo](./langchain-demo/) | LangChain | Progressive loading, runtime skill reading |
| [elevenlabs-demo](./elevenlabs-demo/) | ElevenLabs | KB sync, voice agent, RAG loading |

## Quick Start

Each example is self-contained. Pick your framework:

```bash
# CrewAI
cd crewai-demo && python run.py

# LangChain
cd langchain-demo && python run.py

# ElevenLabs (requires API key)
cd elevenlabs-demo && python run.py
```

## What Gets Validated

All examples validate:
- ✓ Installation from README instructions
- ✓ Configuration file setup
- ✓ CLI commands
- ✓ Agent creation and execution
- ✓ Skill loading and usage
- ✓ Output format compliance

Plus framework-specific features (see individual READMEs).

## Running in CI

```bash
# Quick validation (mocked APIs)
python run.py --quick

# Full validation (requires API keys)
OPENAI_API_KEY=xxx ELEVENLABS_API_KEY=xxx python run.py --real
```

## Use Case: Customer Support Bot

All examples implement the same use case with different architectures:

**Shared Skills:**
- greeting - Welcome users warmly
- troubleshooting - Step-by-step diagnosis
- ticket-creation - Create support tickets (with tool)
- knowledge-search - Search KB articles (with tool)

**Framework Approaches:**
- **CrewAI:** Multi-agent crew (router → specialist → escalation)
- **LangChain:** Single agent with skill switching
- **ElevenLabs:** Voice agent with KB-backed skills

## Troubleshooting

[Common issues across all examples]
```

## Implementation Checklist

### Phase 1: Shared Skills
- [ ] Create `examples/shared-skills/` directory
- [ ] Write `greeting/SKILL.md`
- [ ] Write `troubleshooting/SKILL.md`
- [ ] Write `ticket-creation/SKILL.md` + `tools.py`
- [ ] Write `knowledge-search/SKILL.md` + `tools.py`

### Phase 2: CrewAI Demo
- [ ] Create directory structure
- [ ] Write `run.py` with validation checkpoints
- [ ] Write `.skillforge.yaml`
- [ ] Write agent configs
- [ ] Write `README.md` with manual walkthrough
- [ ] Test validation script

### Phase 3: LangChain Demo
- [ ] Create directory structure
- [ ] Write `run.py` with validation checkpoints
- [ ] Write `.skillforge.yaml`
- [ ] Write `agent.py`
- [ ] Write `README.md` with manual walkthrough
- [ ] Test validation script

### Phase 4: ElevenLabs Demo
- [ ] Create directory structure
- [ ] Write `run.py` with validation checkpoints
- [ ] Write `.skillforge.yaml`
- [ ] Write `agent.py`
- [ ] Write `README.md` with manual walkthrough
- [ ] Test validation script (requires API key)

### Phase 5: Documentation
- [ ] Write top-level `examples/README.md`
- [ ] Add troubleshooting section
- [ ] Add CI integration instructions
- [ ] Update main project README to link to examples

### Phase 6: CI Integration
- [ ] Add GitHub Actions workflow for example validation
- [ ] Configure secrets for API keys
- [ ] Set up quick mode (mocked) as required check
- [ ] Set up real mode (API keys) as optional check

## Success Criteria

- [ ] All three examples run successfully with `--quick` mode
- [ ] All validation checkpoints pass
- [ ] READMEs are clear and complete
- [ ] Manual walkthrough instructions work
- [ ] CI workflow validates examples automatically
- [ ] Examples serve as reference implementations for users
- [ ] All SkillForge features are exercised at least once

## Future Enhancements

- Advanced examples showing error handling
- Performance benchmarking examples
- Custom marketplace example
- Skill authoring tutorial based on shared-skills
