---
name: using-skillforge
description: |
  Teaches agents how to discover and use SkillForge skills.
  Auto-injected by SkillForge runtime.
allowed-tools:
  - Bash
version: 1.0.0
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
skillforge read <skill-name>
```

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

---
*To load any skill, use:* `skillforge read <skill-name>`
