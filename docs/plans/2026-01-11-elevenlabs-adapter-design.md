# ElevenLabs Adapter Design

## Overview

This document describes the SkillForge adapter for ElevenLabs Conversational AI agents. The adapter enables ElevenLabs voice agents to use SkillForge skills through a Knowledge Base integration pattern.

## Context

**ElevenLabs Conversational AI** is a managed voice agent platform that coordinates:
- Speech-to-Text (ASR)
- Language Model (LLM)
- Text-to-Speech (TTS)
- Proprietary turn-taking model

**Key constraint**: ElevenLabs agents cannot execute shell commands, so SkillForge's standard `skillforge read` CLI pattern does not work.

## Design Goals

1. **Consistent mental model** - Use meta-skill + skill directory pattern like CrewAI/LangChain adapters
2. **Progressive disclosure** - Agent sees skill directory upfront, loads full content on-demand
3. **No hosted infrastructure** - Use ElevenLabs Knowledge Base, not a custom server
4. **Dual workflow support** - Both create new agents and configure existing agents

## Architecture

### Comparison with Other Adapters

| Aspect | CrewAI / LangChain | ElevenLabs |
|--------|-------------------|------------|
| Skills location | Local filesystem | ElevenLabs Knowledge Base |
| Loading mechanism | Runtime via `skillforge read` | Pre-deployed, retrieved via RAG |
| Deployment step | None | Required (`sync` command) |
| Skill updates | Instant (edit file) | Requires re-sync |
| Injection point | Backstory / System prompt | System prompt + Knowledge Base |

### Data Flow

```
┌──────────────────┐         ┌──────────────────┐
│ Your Machine     │  sync   │ ElevenLabs Cloud │
│ ┌──────────────┐ │ ──────► │ ┌──────────────┐ │
│ │ skills/      │ │         │ │ Knowledge    │ │
│ │  skill-a/    │ │         │ │ Base         │ │
│ │  skill-b/    │ │         │ │ (account)    │ │
│ └──────────────┘ │         │ └──────────────┘ │
└──────────────────┘         │        │         │
                             │        ▼         │
                             │ ┌──────────────┐ │
                             │ │ Agent Config │ │
                             │ │ - prompt     │ │
                             │ │ - KB refs    │ │
                             │ └──────────────┘ │
                             │        │         │
                             │        ▼         │
                             │ ┌──────────────┐ │
                             │ │ Conversation │ │
                             │ │ (runtime)    │ │
                             │ └──────────────┘ │
                             └──────────────────┘
```

### Progressive Disclosure

```
┌─────────────────────────────────────────────────────────┐
│ What agent sees at conversation start:                  │
│                                                         │
│ • Core identity (full)                                  │
│ • Meta-skill (full)                                     │
│ • Skill directory (names + triggers only)               │
│                                                         │
│ NOT the full skill content                              │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Agent decides to use a skill
                          ▼
┌─────────────────────────────────────────────────────────┐
│ Agent queries KB: "SKILL: socratic-questioning"         │
│                                                         │
│ → Retrieves full skill instructions via RAG             │
│ → Follows them for this interaction                     │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. ElevenLabs Meta-Skill

A variant of the standard meta-skill that teaches agents to query Knowledge Base instead of calling CLI.

**Location**: `src/skillforge/meta/using-skillforge-elevenlabs/SKILL.md`

```markdown
---
name: using-skillforge-elevenlabs
description: Teaches ElevenLabs agents how to use SkillForge skills via Knowledge Base
---

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

## Available Skills

{available_skills}
```

### 2. Skill Document Format

Skills are formatted for optimal RAG retrieval when synced to Knowledge Base:

```markdown
# SKILL: socratic-questioning

## When to Use
- Guiding student toward discovery through questioning
- When student asks for direct answers
- When student needs to develop reasoning skills

## Instructions

[Full SKILL.md content here]
```

The `# SKILL: name` header ensures reliable retrieval when agent queries.

### 3. CLI Commands

```bash
# Store ElevenLabs API credentials
skillforge elevenlabs connect

# Sync skills to account-level Knowledge Base
skillforge elevenlabs sync

# Create new agent with skills
skillforge elevenlabs create \
  --name "Math Tutor" \
  --system-prompt ./prompts/tutor-identity.md \
  --skills socratic-questioning,adaptive-scaffolding,error-correction

# Configure existing agent (created via dashboard)
skillforge elevenlabs configure \
  --agent-id abc123 \
  --system-prompt ./prompts/tutor-identity.md \
  --skills socratic-questioning,adaptive-scaffolding
```

### 4. Python API

```python
from skillforge.elevenlabs import Agent

# Pattern 1: Create new agent
agent = Agent.create(
    name="Math Tutor",
    system_prompt="You are a dedicated math tutor...",
    first_message="Hi! What would you like to work on today?",
    voice_id="...",
    language="en",
    skills=["socratic-questioning", "adaptive-scaffolding", "error-correction"]
)

# Pattern 2: Configure existing agent
agent = Agent(agent_id="abc123")
agent.configure(
    system_prompt="You are a dedicated math tutor...",
    skills=["socratic-questioning", "adaptive-scaffolding"]
)

# Skills must be synced first
from skillforge.elevenlabs import sync_skills
sync_skills()  # Uploads all skills to account KB
```

## Implementation Details

### Sync Process

The `sync` command:

1. Discovers skills from configured `skill_paths`
2. Formats each skill with `# SKILL: name` header
3. Uploads to ElevenLabs Knowledge Base via SDK:
   ```python
   client.conversational_ai.knowledge_base.documents.create_from_text(
       text=formatted_skill_content,
       name="SKILL: skill-name"
   )
   ```
4. Tracks uploaded document IDs in local manifest

### Agent Configuration

The `configure` command:

1. Reads user's core identity prompt
2. Appends ElevenLabs meta-skill
3. Generates skill directory from skill metadata
4. Updates agent via SDK:
   ```python
   client.conversational_ai.agents.update(
       agent_id=agent_id,
       conversation_config={
           "agent": {
               "prompt": {"prompt": combined_prompt},
               "prompt": {"knowledge_base": [{"id": doc_id, ...} for skill]}
           }
       }
   )
   ```

### Skill Directory Generation

Generated from skill frontmatter:

```markdown
## Available Skills

- **socratic-questioning**: Use when guiding student toward discovery through questioning. Query: "SKILL: socratic-questioning"
- **adaptive-scaffolding**: Use when adjusting support level based on student's demonstrated understanding. Query: "SKILL: adaptive-scaffolding"
- **error-correction**: Use when student makes a mathematical or logical error. Query: "SKILL: error-correction"
```

## Limitations

### Knowledge Base Scope

- Knowledge Base assignment is per-agent, not per-conversation
- Cannot dynamically change skills at conversation runtime
- Different skill sets require different agents

### RAG Retrieval

- Less precise than explicit skill loading
- Agent must query with correct skill name
- Retrieved content may include surrounding context

### Deployment Requirement

- Skills must be synced before agent can use them
- Local skill edits require re-sync
- Unlike CrewAI/LangChain, not instant

## Use Case: Math Tutor

The design was validated against a math tutor use case:

**Core Identity** (in system prompt):
- Tutor personality and philosophy
- Fundamental principles
- Critical don'ts
- Mathematical accuracy requirements

**Skills** (in Knowledge Base):
- `socratic-questioning` - Six question types for guided discovery
- `adaptive-scaffolding` - Adjusting support to student level
- `error-correction` - Responding to student errors
- `frustration-support` - Handling student frustration
- `adversarial-resistance` - Handling manipulation attempts
- `understanding-verification` - Verifying genuine understanding
- `direct-vs-guided` - When to teach vs guide

**Student Context** (via dynamic variables):
- Recent practice results
- Identified weak areas
- Session history

## Future Considerations

### MCP Server Alternative

ElevenLabs supports MCP (Model Context Protocol). A future enhancement could:
- Build SkillForge as an MCP server
- Connect ElevenLabs agents to it
- Provide more precise skill retrieval than RAG

This would require hosting infrastructure but offer better control.

### Per-Conversation Skills

If ElevenLabs adds `knowledge_base` to conversation overrides, the adapter could support:
- Same agent with different skills per session
- True runtime skill selection
- More alignment with CrewAI/LangChain model

## Summary

The ElevenLabs adapter brings SkillForge's skill system to voice agents by:

1. **Syncing skills** to ElevenLabs Knowledge Base (deployment step)
2. **Injecting meta-skill** that teaches RAG-based skill loading
3. **Configuring agents** with skill directory + KB references
4. **Maintaining consistency** with other adapters' mental model

The main trade-off is the deployment requirement - skills must be synced before use, unlike the instant local loading of CrewAI/LangChain.
