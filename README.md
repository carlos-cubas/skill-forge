# SkillForge

## Overview

SkillForge is a Python toolkit that enables CrewAI and LangChain agents to be equipped with domain-specific skills using Anthropic's proven skill format. It is the generalized equivalent of OpenSkills—same format, any domain, targeting multi-agent frameworks.

## Problem Statement

Current agent frameworks (CrewAI, LangChain, ElevenLabs) lack a standardized way to equip agents with domain-specific capabilities. Anthropic has pioneered a skill format for Claude Code that works well, but it's limited to coding agents. SkillForge bridges this gap by:

1. Adopting Anthropic's skill format as the standard
2. Providing a CLI for skill/marketplace management (mirroring Claude Code's `/plugin`)
3. Providing runtime integration with CrewAI and LangChain
4. Enabling any domain—not just engineering

### Key Features

- **CLI** - Marketplace management and skill installation via the `skillforge` command
- **Runtime Library** - Load skills into CrewAI/LangChain agents dynamically
- **Framework Adapters** - Drop-in replacements for Agent classes (CrewAI, LangChain, ElevenLabs)
- **Voice Agent Support** - ElevenLabs Conversational AI integration via Knowledge Base
- **Meta-Skill System** - Teaches agents how to discover and use skills at runtime
- **Flexible Discovery** - Hybrid approach supporting both installed skills (marketplace) and local project skills

## Installation

```bash
# Basic installation
pip install skillforge

# With CrewAI support
pip install skillforge[crewai]

# With LangChain support
pip install skillforge[langchain]

# With ElevenLabs support
pip install skillforge[elevenlabs]

# For development
pip install -e ".[dev]"
```

## Quick Start

### CrewAI Integration

```python
from skillforge.crewai import Agent  # Drop-in replacement

agent = Agent(
    role="Executive Coach",
    goal="Help users achieve their professional goals",
    backstory="An experienced coach with deep expertise",
    skills=["rapid-interviewing", "goal-extraction"]  # Just skill names
)
```

### LangChain Integration

```python
from skillforge.langchain import create_agent

agent = create_agent(
    model="gpt-4o",
    skills=["rapid-interviewing"]
)
```

### ElevenLabs Voice Agent Integration

```python
from skillforge.elevenlabs import Agent, sync_skills

# First, sync skills to ElevenLabs Knowledge Base
sync_skills()

# Create new voice agent with skills
agent = Agent.create(
    name="Math Tutor",
    system_prompt="You are a dedicated math tutor...",
    first_message="Hi! What would you like to work on today?",
    voice_id="...",
    language="en",
    skills=["socratic-questioning", "adaptive-scaffolding"]
)

# Or configure existing agent
agent = Agent(agent_id="abc123")
agent.configure(
    system_prompt="You are a dedicated math tutor...",
    skills=["socratic-questioning"]
)
```

### Framework-Agnostic Usage

```python
from skillforge import SkillForge

sf = SkillForge()  # Auto-loads from .skillforge.yaml + manifest
skill = sf.get_skill("rapid-interviewing")
print(skill.instructions)  # Access skill content
```

## CLI Commands

### General Commands

```bash
# Add a skill marketplace
skillforge marketplace add <source>

# Install a skill from marketplace
skillforge install <skill>@<marketplace> --to <path>

# Read skill content (used by agents at runtime)
skillforge read <skill-name> --from <path>
```

### ElevenLabs Commands

```bash
# Connect ElevenLabs API credentials
skillforge elevenlabs connect

# Sync skills to ElevenLabs Knowledge Base
skillforge elevenlabs sync

# Create new agent with skills
skillforge elevenlabs create \
  --name "Math Tutor" \
  --system-prompt ./prompts/tutor-identity.md \
  --skills socratic-questioning,adaptive-scaffolding

# Configure existing agent
skillforge elevenlabs configure \
  --agent-id abc123 \
  --system-prompt ./prompts/tutor-identity.md \
  --skills socratic-questioning,adaptive-scaffolding
```

## Configuration

Create a `.skillforge.yaml` in your project root to configure skill discovery:

```yaml
skill_paths:
  - ./agents/**/skills/*  # Discover all skills under agent directories
  - ./shared-skills/*     # Shared skills available to all agents
```

Installed skills are tracked in `.skillforge/manifest.json` (auto-generated).

## Framework-Specific Notes

### ElevenLabs Integration

ElevenLabs voice agents work differently from CrewAI/LangChain:

- **Skills location**: ElevenLabs Knowledge Base (cloud) instead of local filesystem
- **Deployment step**: Skills must be synced via `skillforge elevenlabs sync` before use
- **Loading mechanism**: Agent retrieves skills via RAG queries instead of CLI commands
- **Updates**: Skill changes require re-sync (not instant like local frameworks)

This design enables voice agents to use SkillForge skills without requiring shell command execution.

## Skill Format

SkillForge uses [Anthropic's standardized skill format](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills):

```
skill-name/
├── SKILL.md          # Instructions + frontmatter metadata
├── tools.py          # (Optional) Skill-specific tools
└── resources/        # (Optional) Supporting files
```

## Project Status

**Status**: ✅ Complete - All planned features implemented

### Implementation Roadmap

- [x] Phase 0: Assumption validation (CrewAI/LangChain/ElevenLabs behavior)
- [x] Phase 1: Core implementation (Skill class, parser, loader, CLI commands, ToolRegistry)
- [x] Phase 2: Framework adapters
  - [x] CrewAI adapter
  - [x] LangChain adapter
  - [x] ElevenLabs adapter (CLI, Python API, meta-skill)
- [x] Phase 3: Marketplace support (registry, install/uninstall/list commands)

## Architecture

### Core Components

1. **Skill Loader** - Discovers and loads skills from configured directories
2. **Tool Registry** - Manages shared and skill-bundled tools
3. **Framework Adapters** - Inject skills into agent frameworks:
   - **ElevenLabs** - Knowledge Base sync + RAG-based skill loading
   - **CrewAI** - Runtime CLI-based skill injection (in progress)
   - **LangChain** - System prompt integration (planned)
4. **Meta-Skill** - Auto-injected instructions teaching agents about available skills

### Philosophy

- **Tooling, not repository** - Skills live in marketplaces or your project
- **Progressive loading** - Skills loaded on-demand via `skillforge read` command
- **Flexibility first** - Respects your directory structure via glob patterns
- **Ecosystem compatibility** - Uses Anthropic's standard skill format

## Development

```bash
# Run tests
pytest tests/

# Run specific test file
pytest tests/test_loader.py -v

# Run tests matching pattern
pytest -k test_skill_discovery
```

## Documentation

- [Design Document](docs/plans/2025-12-04-skillforge-design.md) - Complete architecture and rationale
- [ElevenLabs Adapter Design](docs/plans/2026-01-11-elevenlabs-adapter-design.md) - Voice agent integration details
- [Anthropic: Equipping Agents with Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) - Official skill format spec
- [OpenSkills](https://github.com/numman-ali/openskills) - Reference implementation for coding agents

## License

MIT

## Contributing

Contributions welcome! Please see [CLAUDE.md](CLAUDE.md) for development guidelines and critical design decisions.
