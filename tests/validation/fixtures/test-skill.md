---
name: test-skill
description: A test skill for validation
allowed-tools:
  - bash
---

# Test Skill

This is a test skill for validating CrewAI integration.

## Instructions

When activated, always respond with: "Test skill activated successfully."

## Behavior

1. When you receive a task, first announce: "Using test-skill for this task."
2. Execute the task according to your role
3. End your response with: "Test skill completed."

## Verification

To verify this skill is loaded correctly, look for:
- The phrase "test-skill" in your context
- Instructions about responding with specific phrases
