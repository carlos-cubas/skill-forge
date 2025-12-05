# SkillForge Design Document

## Overview

SkillForge is a Python toolkit that enables CrewAI and LangChain agents to be equipped with domain-specific skills using Anthropic's proven skill format. It is the generalized equivalent of OpenSkills—same format, any domain, targeting multi-agent frameworks.

## Problem Statement

Current agent frameworks (CrewAI, LangChain) lack a standardized way to equip agents with domain-specific capabilities. Anthropic has pioneered a skill format for Claude Code that works well, but it's limited to coding agents. SkillForge bridges this gap by:

1. Adopting Anthropic's skill format as the standard
2. Providing a CLI for skill/marketplace management (mirroring Claude Code's `/plugin`)
3. Providing runtime integration with CrewAI and LangChain
4. Enabling any domain—not just engineering

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Skill format | Anthropic's SKILL.md | Proven design, ecosystem compatibility |
| CLI model | Mirrors Claude Code `/plugin` | Familiar UX, marketplace support |
| Directory structure | User's choice | Flexibility, no imposed opinions |
| Target frameworks | CrewAI, LangChain | Most popular Python agent frameworks |
| Skill granularity | Capability-specific | Composable, reusable across agents |
| Tool handling | Hybrid | Skills can bundle tools or reference shared tools |

## Architecture

SkillForge is **tooling**, not a skill repository. It provides:
1. A CLI for managing marketplaces and installing skills
2. A runtime library for loading skills into agents

```
┌─────────────────────────────────────────────────────────┐
│                      MARKETPLACES                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ dearmarkus/  │  │ superpowers/ │  │ your-org/    │   │
│  │ event-skills │  │ skills       │  │ skills       │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────┬───────────────────────────────┘
                          │
                          │ skillforge install skill@marketplace --to <dest>
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   YOUR PROJECT                           │
│                   (structure is YOUR choice)             │
│                                                          │
│  Skills installed wherever you specify with --to         │
│  Agents configured to reference skills by path           │
└─────────────────────────┬───────────────────────────────┘
                          │
                          │ runtime: load skills → inject into agents
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   SKILLFORGE RUNTIME                     │
│  ┌─────────────────┐           ┌─────────────────────┐  │
│  │ Skill Loader    │           │ Framework Adapters  │  │
│  │ (parse SKILL.md)│           │ (CrewAI, LangChain) │  │
│  └─────────────────┘           └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**SkillForge's role:**
1. **CLI** - Manage marketplaces, install skills to wherever YOU specify
2. **Runtime** - Load skills and inject them into CrewAI/LangChain agents
3. **Not a skill repository** - Skills live in marketplaces or your project

## CLI (Mirrors Claude Code /plugin)

```bash
# Marketplace management
skillforge marketplace add [source]
skillforge marketplace list
skillforge marketplace update [marketplace-name]
skillforge marketplace remove [marketplace-name]

# Skill installation
skillforge install [skill-name]@[marketplace-name] --to <dest>
skillforge uninstall [skill-name]
skillforge list

# Skill loading (used by agents at runtime)
skillforge read [skill-name] --from <path>
```

The `skillforge read` command is how agents load skill content at runtime (similar to `openskills read`).

**Supported marketplace sources:**

| Source | Example |
|--------|---------|
| GitHub repo | `dearmarkus/event-skills` |
| Git URL | `https://github.com/org/skills.git` |
| Local directory | `./local-marketplace` |

**Example workflow:**

```bash
# 1. Add marketplaces
$ skillforge marketplace add dearmarkus/event-skills
Added marketplace: dearmarkus

$ skillforge marketplace add superpowers-marketplace/skills
Added marketplace: superpowers

# 2. Install skills to your chosen location
$ skillforge install rapid-interviewing@dearmarkus --to ./agents/coach/skills/
Installed rapid-interviewing to ./agents/coach/skills/

$ skillforge install goal-extraction@dearmarkus --to ./agents/coach/skills/
Installed goal-extraction to ./agents/coach/skills/

# 3. Configure your agents to use the skills (manually or via YAML)
```

**Marketplace JSON structure:**

```json
{
  "name": "dearmarkus-event-skills",
  "owner": "dearmarkus",
  "skills": [
    {
      "name": "rapid-interviewing",
      "description": "Techniques for 60-second discovery interviews",
      "source": "github:dearmarkus/event-skills/rapid-interviewing"
    }
  ]
}
```

## Meta-Skill: Teaching Agents How to Use Skills

CrewAI/LangChain agents don't natively understand skills. SkillForge ships a **`using-skillforge`** meta-skill that teaches agents:
1. That skills exist and what they are
2. When to check for relevant skills
3. How to load skill content
4. How to follow skill instructions

### How It Works

The meta-skill content is **auto-injected** into agent prompts at runtime:

```
┌─────────────────────────────────────────────────────────┐
│                 AGENT SYSTEM PROMPT                      │
├─────────────────────────────────────────────────────────┤
│ [Agent role, goal, backstory...]                        │
│                                                          │
│ ## SkillForge Skills                                    │
│ [using-skillforge meta-skill content]                   │
│                                                          │
│ ### Available Skills                                    │
│ - rapid-interviewing: 60-second discovery interviews    │
│ - goal-extraction: Extract goals from conversation      │
│                                                          │
│ To load a skill:                                        │
│ Bash("skillforge read <skill-name> --from <path>")      │
└─────────────────────────────────────────────────────────┘
```

### Draft: using-skillforge Meta-Skill

```markdown
---
name: using-skillforge
description: |
  Teaches agents how to discover and use SkillForge skills.
  Auto-injected by SkillForge runtime.
---

# Using SkillForge Skills

You have access to specialized skills that provide domain expertise and procedures.

## Before Starting Any Task

1. Review the **Available Skills** list below
2. If a skill matches your current task, **load it first**
3. Announce: "I'm using the [skill-name] skill for [purpose]"
4. Follow the skill's instructions exactly

## How to Load a Skill

Run this command to load a skill's full instructions:

```bash
Bash("skillforge read <skill-name> --from <skill-path>")
```

The skill path is provided in the Available Skills list.

## Important Guidelines

- **Check skills first** - Before starting work, check if a skill applies
- **Load before acting** - Always load the skill content before following it
- **Follow exactly** - Skill instructions are tested procedures; don't paraphrase
- **One at a time** - Load and complete one skill before starting another

## Common Mistakes to Avoid

- Assuming you know what a skill contains without loading it
- Skipping skills because the task "seems simple"
- Paraphrasing skill instructions instead of following them
- Not announcing which skill you're using

## Available Skills

{available_skills}

To load any skill above, use:
Bash("skillforge read <skill-name> --from {skill_path}")
```

### Customization

Configure via `.skillforge.yaml`:

```yaml
# .skillforge.yaml
skill_paths:
  - ./agents/**/skills/*
  - ./shared-skills/*

# Optional: custom meta-skill (defaults to built-in)
meta_skill: ./my-custom-using-skillforge/SKILL.md

# Optional: disable progressive loading (inject full content)
# skill_mode: inject
```

Or override in code:

```python
from skillforge.crewai import Agent

# Use default meta-skill
agent = Agent(skills=["rapid-interviewing"])

# Disable meta-skill (inject full skill content directly)
agent = Agent(skills=["rapid-interviewing"], skill_mode="inject")
```

## Skill Format (Anthropic Standard)

### Skill Directory Structure

```
rapid-interviewing/
├── SKILL.md           # Required: instructions + metadata
├── tools.py           # Optional: skill-specific tools
├── resources/         # Optional: supporting files
│   ├── templates/
│   └── examples/
└── scripts/           # Optional: executable scripts
```

### SKILL.md Format

```markdown
---
name: rapid-interviewing
description: |
  Techniques for conducting effective 60-second discovery interviews.
  Use when you need to quickly understand someone's goals, challenges,
  and priorities in a time-constrained setting.
allowed-tools: [conversation, goal-extraction]
---

# Rapid Interviewing Skill

## When to Use
- Time-constrained discovery conversations
- Initial attendee onboarding at events
- Quick needs assessment

## Technique
1. Open with a single powerful question
2. Listen for keywords indicating priorities
3. Probe once on the most important theme
4. Summarize and confirm understanding

## Output
Produce a structured profile containing:
- Primary goal
- Key challenge
- Success criteria
- Relevant context
```

## Integration Patterns

### Skill Discovery Configuration

SkillForge uses a hybrid approach for finding skills:

1. **Installed skills** → Auto-tracked in `.skillforge/manifest.json`
2. **Local skills** → Discovered via glob patterns in `.skillforge.yaml`

```yaml
# .skillforge.yaml (project root)
skill_paths:
  - ./agents/**/skills/*     # Glob: all skills under any agent
  - ./shared-skills/*        # All shared skills
```

Lookup order:
1. Check manifest first (installed skills)
2. Search skill_paths second (local skills)
3. Error if not found

### Pattern 1: YAML Configuration (CrewAI)

Agent config only specifies WHAT skills to use (not where):

```yaml
# config/agents.yaml
executive_coach:
  role: Executive Coach
  goal: Conduct effective 60-second discovery interviews
  backstory: Expert executive coach with decades of experience
  skills:                            # ← Just skill names, no paths
    - rapid-interviewing
    - goal-extraction

event_concierge:
  role: Event Concierge
  goal: Create personalized attendee success plans
  backstory: Expert event facilitator
  skills:
    - networking-matching
    - session-recommendation
```

```python
# crew.py
from skillforge.crewai import Agent  # ← Use SkillForge's Agent

@CrewBase
class EventExperienceCrew:
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def executive_coach(self) -> Agent:
        return Agent(config=self.agents_config['executive_coach'])
```

### Pattern 2: Drop-in Replacement (CrewAI)

```python
from skillforge.crewai import Agent  # ← Drop-in replacement for crewai.Agent

# Skills discovered via .skillforge.yaml + manifest
agent = Agent(
    role="Executive Coach",
    goal="Conduct 60-second discovery interviews",
    backstory="Expert executive coach",
    skills=["rapid-interviewing", "goal-extraction"]  # ← Just names
)
```

### Pattern 3: Drop-in Replacement (LangChain)

```python
from skillforge.langchain import create_agent  # ← Drop-in replacement

# Skills discovered via .skillforge.yaml + manifest
agent = create_agent(
    model="gpt-4o",
    tools=[...],
    system_prompt="You are an executive coach",
    skills=["rapid-interviewing", "goal-extraction"]  # ← Just names
)
```

### Pattern 4: Library Usage (Framework-agnostic)

```python
from skillforge import SkillForge

# Loads config from .skillforge.yaml + manifest automatically
sf = SkillForge()

# Get skill by name (discovered via configured paths)
skill = sf.get_skill("rapid-interviewing")
print(skill.instructions)  # The markdown content
print(skill.tools)         # Any bundled tools

# Or explicitly specify paths (overrides config)
sf = SkillForge(skill_paths=["./custom-location/*"])
```

## Core Components

### Skill Loader

Discovers and loads skills from configured directories.

```python
class SkillLoader:
    def __init__(self, paths: list[Path]):
        self.paths = paths
        self.skills: dict[str, Skill] = {}

    def discover_skills(self) -> dict[str, Skill]:
        """Scan directories for SKILL.md files and load them."""
        pass

    def get(self, skill_name: str) -> Skill:
        """Get a skill by name."""
        pass

    def load_skill(self, skill_path: Path) -> Skill:
        """Parse SKILL.md and load associated resources."""
        pass
```

### Tool Registry

Manages both shared tools and skill-bundled tools.

```python
class ToolRegistry:
    def __init__(self):
        self.shared_tools: dict[str, Tool] = {}
        self.skill_tools: dict[str, list[Tool]] = {}

    def register_shared_tool(self, name: str, tool: Tool):
        """Register a tool available to all skills."""
        pass

    def register_skill_tools(self, skill_name: str, tools: list[Tool]):
        """Register tools bundled with a specific skill."""
        pass

    def get_tools_for_skill(self, skill: Skill) -> list[Tool]:
        """Get all tools a skill can access (shared + bundled)."""
        pass
```

### Framework Adapters

Translate skills into framework-native constructs.

```python
class CrewAIAdapter:
    def inject_skills(self, agent: Agent, skills: list[Skill]) -> Agent:
        """Inject skill instructions into agent backstory and register tools."""
        pass

class LangChainAdapter:
    def inject_skills(self, prompt: str, skills: list[Skill]) -> str:
        """Compose system prompt with skill instructions."""
        pass

    def get_tools(self, skills: list[Skill]) -> list[BaseTool]:
        """Convert skill tools to LangChain BaseTool instances."""
        pass
```

## First Use Case: DearMarkus.ai Event Experience

### Agents and Their Skills

| Agent | Role | Skills |
|-------|------|--------|
| Executive Coach | 60-sec discovery interview | rapid-interviewing, goal-extraction, profiling |
| Event Concierge | Attendee Success Plan | networking-matching, session-recommendation, event-data-query |
| Executive Assistant | Mindful nudges | calendar-integration, contextual-nudging, personal-context |

### Example Skills

**rapid-interviewing**
- Instructions for effective 60-second interviews
- No tools required (conversation-based)

**networking-matching**
- Instructions for identifying valuable connections
- Tools: `attendee-search`, `profile-similarity`

**calendar-integration**
- Instructions for schedule-aware recommendations
- Tools: `calendar-read`, `calendar-write`, `availability-check`

**contextual-nudging**
- Instructions for timing-appropriate, non-intrusive reminders
- Tools: `notification-send`, `context-evaluate`

## Directory Structure

### SkillForge (the tooling)

```
skill-forge/
├── src/
│   └── skillforge/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py           # CLI entry point
│       │   ├── marketplace.py    # marketplace add/list/update/remove
│       │   ├── install.py        # install [skill]@[marketplace] --to
│       │   ├── uninstall.py      # uninstall [skill]
│       │   ├── list.py           # list installed skills
│       │   └── read.py           # read [skill] --from (agent runtime)
│       ├── core/
│       │   ├── __init__.py
│       │   ├── skill.py          # Skill data class
│       │   ├── loader.py         # Skill discovery and loading
│       │   ├── registry.py       # Tool registry
│       │   └── marketplace.py    # Marketplace registry and fetching
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── crewai.py         # CrewAI adapter
│       │   └── langchain.py      # LangChain adapter
│       ├── meta/
│       │   └── using-skillforge/
│       │       └── SKILL.md      # Default meta-skill (shipped)
│       └── utils/
│           ├── __init__.py
│           └── markdown.py       # SKILL.md parsing
├── tests/
├── docs/
│   └── plans/
├── pyproject.toml
└── README.md
```

### Your Project (structure is YOUR choice)

**Example A: Skills per agent**
```
your-event-crew/
├── .skillforge.yaml              # ← skill_paths: ["./agents/**/skills/*"]
├── .skillforge/
│   └── manifest.json             # ← Auto-generated by skillforge install
├── agents/
│   ├── executive_coach/
│   │   └── skills/
│   │       ├── rapid-interviewing/   # ← installed
│   │       │   └── SKILL.md
│   │       └── my-custom-skill/      # ← local
│   │           └── SKILL.md
│   └── event_concierge/
│       └── skills/
│           └── networking-matching/
│               └── SKILL.md
├── src/
│   └── event_crew/
│       ├── config/
│       │   └── agents.yaml       # ← skills: [rapid-interviewing, ...]
│       └── crew.py
└── pyproject.toml
```

```yaml
# .skillforge.yaml
skill_paths:
  - ./agents/**/skills/*
```

**Example B: Centralized skills**
```
your-event-crew/
├── .skillforge.yaml              # ← skill_paths: ["./skills/*"]
├── .skillforge/
│   └── manifest.json
├── skills/
│   ├── rapid-interviewing/
│   │   └── SKILL.md
│   ├── goal-extraction/
│   │   └── SKILL.md
│   └── networking-matching/
│       └── SKILL.md
├── src/
│   └── event_crew/
│       ├── config/
│       │   ├── agents.yaml
│       │   └── tasks.yaml
│       └── crew.py
└── pyproject.toml
```

```yaml
# .skillforge.yaml
skill_paths:
  - ./skills/*
```

**SkillForge doesn't impose structure** - configure `skill_paths` with globs to match your layout.

## Open Questions

1. **Tool translation:** How do we handle skills that reference tools not available in the target framework?

2. **Skill dependencies:** Should skills be able to declare dependencies on other skills?

3. **Skill versioning:** How do we handle skill version compatibility?

4. **Runtime context:** How do skills access runtime information (current user, session state, etc.)?

## Assumptions to Validate

Before implementation, we need to empirically validate these assumptions:

### CrewAI Validation

| Assumption | Validation Method |
|------------|-------------------|
| Agents can call Bash commands during execution | Create test crew, verify agent can run `Bash("echo test")` |
| Backstory content is included in LLM prompt | Inspect actual prompt sent to LLM (verbose mode or logging) |
| Custom fields in agents.yaml are accessible | Test adding `skill_paths` field, verify it's readable |
| Agent can read Bash output and act on it | Test `skillforge read` returning content that agent uses |
| Prompt injection doesn't break agent behavior | Test with meta-skill content injected |

### LangChain Validation

| Assumption | Validation Method |
|------------|-------------------|
| Agents can call shell commands via tool | Test with shell tool or subprocess tool |
| System prompt can be extended at runtime | Test dynamic prompt composition |
| Tool output is returned to agent context | Verify agent sees `skillforge read` output |
| create_agent supports custom parameters | Test extending with `skills`, `skill_paths` |

### General Validation

| Assumption | Validation Method |
|------------|-------------------|
| `skillforge read` CLI is fast enough | Benchmark CLI startup + read time |
| Skill content fits in context window | Test with realistic skill sizes |
| Agents follow meta-skill instructions | Test with real LLM, observe behavior |
| Announcement pattern works | Verify agents say "I'm using [skill]..." |

### Validation Plan

1. **Create minimal test fixtures** for both frameworks
2. **Test each assumption independently** before integration
3. **Document actual behavior** vs expected behavior
4. **Adjust design** based on findings before full implementation

## Next Steps

### Phase 0: Validate Assumptions
1. Create minimal CrewAI test fixture - validate Bash execution and backstory injection
2. Create minimal LangChain test fixture - validate shell tool and prompt composition
3. Document findings and adjust design if needed

### Phase 1: Core Implementation
4. Create SkillForge project scaffolding (CLI + core + adapters)
5. Implement core Skill data class and SKILL.md parser
6. Create default `using-skillforge` meta-skill
7. Implement CLI: `skillforge read [skill] --from <path>` (agent runtime)

### Phase 2: Framework Adapters
8. Implement CrewAI adapter (drop-in Agent with meta-skill injection)
9. Implement LangChain adapter (drop-in create_agent with meta-skill injection)
10. Validate end-to-end with test skills

### Phase 3: Marketplace Support
11. Implement core Marketplace registry and fetching
12. Implement CLI: `skillforge marketplace add/list/update/remove`
13. Implement CLI: `skillforge install [skill]@[marketplace] --to`
14. Implement CLI: `skillforge uninstall` and `skillforge list`

### Phase 4: Production Use Case
15. Create DearMarkus.ai event-skills marketplace (separate repo)
16. Test end-to-end with DearMarkus.ai use case
17. Document skill authoring guide

## References

- [Anthropic: Equipping Agents with Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) - Skill format specification
- [OpenSkills](https://github.com/numman-ali/openskills) - Reference implementation for coding agents (SkillForge is the generalized equivalent)
- [CrewAI Documentation](https://docs.crewai.com) - Target framework
- [LangChain Documentation](https://python.langchain.com) - Target framework
