# Plan: ElevenLabs Test Cleanup

## Problem

Running the ElevenLabs demo with `--real` creates resources in ElevenLabs that are never cleaned up:
1. **Knowledge Base Documents** - 4 skill documents remain after tests
2. **Agents** - Test agents remain in the ElevenLabs platform

The user discovered test agents accumulating in their ElevenLabs account.

## Resources Created

| Resource | Location | Created By | Current Cleanup |
|----------|----------|------------|-----------------|
| KB Documents | `sync.py:sync_skill_to_kb()` | `run.py` checkpoint 4 | `delete_skill_from_kb()` exists but unused |
| Agents | `agent.py:create_agent()` | `run.py` checkpoint 6 | **None - function missing** |

## Solution

### Phase 1: Add Agent Delete Function to Adapter

**File**: `src/skillforge/adapters/elevenlabs/agent.py`

Add `delete_agent()` function:
```python
def delete_agent(agent_id: str) -> bool:
    """Delete an ElevenLabs agent.

    Args:
        agent_id: ID of the agent to delete.

    Returns:
        True if deleted successfully, False if not found.
    """
    client = get_client()
    try:
        client.conversational_ai.agents.delete(agent_id)
        logger.info(f"Deleted agent: {agent_id}")
        return True
    except Exception as e:
        logger.warning(f"Could not delete agent {agent_id}: {e}")
        return False
```

Export from `__init__.py`.

### Phase 2: Add Cleanup to ElevenLabs Demo

**File**: `examples/elevenlabs-demo/run.py`

1. Track created resources during test run
2. Add `cleanup_elevenlabs_resources()` function
3. Call cleanup at end of `run_real_validation()`
4. Add `--no-cleanup` CLI flag to skip cleanup for inspection

Changes:
```python
# Track resources created during test
_created_resources = {
    "agents": [],      # List of agent_ids
    "documents": [],   # List of (skill_name, doc_id) tuples
}

def cleanup_elevenlabs_resources(report: ValidationReport) -> None:
    """Checkpoint 10: Clean up test resources from ElevenLabs."""
    cp = ValidationCheckpoint("Checkpoint 10: Cleanup test resources")

    # Delete agents
    for agent_id in _created_resources["agents"]:
        delete_agent(agent_id)

    # Delete KB documents
    manifest = ElevenLabsManifest()
    for skill_name, doc_id in _created_resources["documents"]:
        delete_skill_from_kb(skill_name, manifest)

    cp.check(True)
    report.add(cp)
```

**File**: `examples/elevenlabs-demo/agent.py`

Update `sync_skills_to_elevenlabs()` and `create_voice_agent()` to register resources in the tracker.

### Phase 3: Add CLI Cleanup Command (Optional)

**File**: `src/skillforge/cli/elevenlabs.py`

Add `skillforge elevenlabs cleanup` command for manual resource management:
- `--agents` - List/delete test agents
- `--documents` - List/delete KB documents
- `--force` - Actually delete (default: dry-run)

## Files to Modify

1. `src/skillforge/adapters/elevenlabs/agent.py` - Add `delete_agent()`
2. `src/skillforge/adapters/elevenlabs/__init__.py` - Export `delete_agent`
3. `examples/elevenlabs-demo/run.py` - Add cleanup checkpoint
4. `examples/elevenlabs-demo/agent.py` - Track created resources
5. `src/skillforge/cli/elevenlabs.py` - Add cleanup command (optional)

## Verification

1. Run `python run.py --real` in elevenlabs-demo
2. Verify checkpoint 10 (cleanup) passes
3. Check ElevenLabs dashboard - no orphaned resources
4. Run `python run.py --real` again - should work cleanly

## Decision

**Auto-cleanup** after tests, with `--no-cleanup` flag if user wants to inspect resources.

This keeps tests self-contained and prevents resource accumulation.
