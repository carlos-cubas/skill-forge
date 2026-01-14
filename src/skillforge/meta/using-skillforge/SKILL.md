---
name: using-skillforge
description: Meta-skill that teaches agents how to discover and use skills via SkillForge
allowed-tools:
  - Bash
version: 0.1.0
---

# Using SkillForge

You have access to domain-specific skills through SkillForge. Skills provide specialized knowledge and capabilities for specific tasks.

## When to Use Skills

Before starting a task, check if relevant skills are available. Skills help with:
- Domain-specific knowledge (e.g., interviewing techniques, event management)
- Specialized workflows (e.g., profiling, recommendation generation)
- Tool-specific procedures (e.g., calendar integration, data queries)

## How to Load Skills

To load a skill, use the `skillforge read` command:

```bash
skillforge read <skill-name>
```

This outputs the skill's instructions, which you should follow for that domain.

## Announcing Skill Usage

When using a skill, announce it:
- "I'm using the [skill-name] skill to [purpose]"
- This helps maintain transparency about your approach

## Available Skills

Skills are configured in the project's `.skillforge.yaml` file. Use `skillforge list` to see available skills.

---

*This is a placeholder meta-skill. Full implementation will include skill discovery and progressive loading instructions.*
