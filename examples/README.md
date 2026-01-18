# SkillForge Examples

Comprehensive examples demonstrating SkillForge across all supported frameworks.

## Examples

| Example | Framework | Features | Checkpoints |
|---------|-----------|----------|-------------|
| [crewai-demo](./crewai-demo/) | CrewAI | Multi-agent crew, progressive/inject modes, marketplace CLI, tool bundling | 13 |
| [langchain-demo](./langchain-demo/) | LangChain | Single agent, progressive loading via CLI, inject mode comparison | 9 |
| [elevenlabs-demo](./elevenlabs-demo/) | ElevenLabs | Voice agent, KB sync, RAG-based skill loading, manifest tracking | 9 |

## Quick Start

### CrewAI Demo
```bash
cd examples/crewai-demo
pip install -r requirements.txt
python run.py --quick  # Mocked LLM for CI
python run.py --real   # Requires OPENAI_API_KEY
```

### LangChain Demo
```bash
cd examples/langchain-demo
pip install -r requirements.txt
python run.py --quick  # Mocked LLM for CI
python run.py --real   # Requires OPENAI_API_KEY
```

### ElevenLabs Demo
```bash
cd examples/elevenlabs-demo
pip install -r requirements.txt
python run.py --quick  # Mocked API for CI
python run.py --real   # Requires ELEVENLABS_API_KEY
```

## What Gets Validated

### Core Features (All Demos)
- Skill discovery via `.skillforge.yaml`
- Local skill loading from `./skills/` directory
- Meta-skill injection into agent prompts
- Skill content verification (output formats, templates)

### CrewAI-Specific
- Multi-agent crew coordination (3 agents, 3 tasks)
- Progressive mode (Router) vs inject mode (Specialist, Escalation)
- Marketplace CLI (`add`, `list`, `install`)
- Tool bundling (`create_ticket`, `search_kb`)

### LangChain-Specific
- Single-agent architecture with all skills
- Progressive mode with `skillforge read` CLI command
- Inject mode comparison (prompt size analysis)
- System prompt composition

### ElevenLabs-Specific
- Knowledge Base sync via `skillforge elevenlabs sync`
- Manifest tracking with document IDs
- Voice agent creation with KB references
- Agent reconfiguration with skill updates

## Running in CI

All demos support `--quick` mode for CI/CD pipelines:

```bash
python run.py --quick
```

### GitHub Actions Setup

For real API validation in CI (main branch only), configure these repository secrets:

| Secret | Required By | How to Get |
|--------|------------|------------|
| `OPENAI_API_KEY` | CrewAI, LangChain demos | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `ELEVENLABS_API_KEY` | ElevenLabs demo | [ElevenLabs Profile](https://elevenlabs.io/app/settings/api-keys) |

To configure secrets:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add each secret with its API key value

The CI workflow runs `--quick` mode on all PRs, and `--real` mode on main branch pushes when secrets are configured.

**Quick mode features:**
- Mocked LLM/API calls (no API keys required)
- Full validation checkpoint execution
- Deterministic results suitable for automated testing
- Same validation logic as real mode

**Expected CI output:**
```
=== Running QUICK validation (mocked LLM) ===

[PASS] Checkpoint 1: Installation verified
[PASS] Checkpoint 2: Skills discovered
...
============================================================
VALIDATION SUMMARY: X/X checkpoints passed
============================================================
```

## Shared Skills

The `shared-skills/` directory contains reusable skills for a customer support bot use case:

| Skill | Description | Bundled Tool |
|-------|-------------|--------------|
| **greeting** | Welcome users warmly and set a helpful tone | - |
| **troubleshooting** | Step-by-step diagnosis framework for common issues | - |
| **ticket-creation** | Create support tickets with proper categorization | `create_ticket` |
| **knowledge-search** | Search knowledge base articles | `search_kb` |

Each demo references these shared skills via symlinks in their local `./skills/` directory.

## Troubleshooting

### Skills Not Found
```
SkillNotFoundError: Skill 'greeting' not found
```
**Solution**: Verify `.skillforge.yaml` exists and `skill_paths` points to correct location.

### Import Errors
```
ImportError: No module named 'crewai'
```
**Solution**: Install framework extras:
```bash
pip install skillforge[crewai]    # For CrewAI
pip install skillforge[langchain] # For LangChain
pip install skillforge[elevenlabs] # For ElevenLabs
```

### Marketplace Already Exists
```
MarketplaceExistsError: Marketplace 'shared-skills' already exists
```
**Solution**: Remove first with `skillforge marketplace remove shared-skills -f`

### Missing API Key (Real Mode)
```
[WARN] OPENAI_API_KEY not set
```
**Solution**: Set required environment variable:
```bash
export OPENAI_API_KEY=your-key      # CrewAI, LangChain
export ELEVENLABS_API_KEY=your-key  # ElevenLabs
```

### Shell Tool Not Available (LangChain)
```
Warning: Shell tool not available for progressive mode
```
**Solution**: Install langchain-community:
```bash
pip install langchain-community
```

## Architecture Comparison

| Aspect | CrewAI | LangChain | ElevenLabs |
|--------|--------|-----------|------------|
| Agent pattern | Multi-agent crew | Single agent | Single voice agent |
| Skill delivery | Direct injection | CLI read or injection | KB RAG query |
| Coordination | Task delegation | None | None |
| Interaction | Text tasks | Text conversation | Voice conversation |
| Best for | Workflows, pipelines | Chatbots, simple agents | Voice interfaces |

## Related Documentation

- Individual demo READMEs contain detailed manual walkthroughs
- See `CLAUDE.md` in project root for development guidance
- Anthropic skill format: [Equipping Agents with Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
