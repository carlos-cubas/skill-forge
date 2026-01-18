# SkillForge Examples

Example projects demonstrating SkillForge integration with various agent frameworks.

## Shared Skills

The `shared-skills/` directory contains reusable skills for a customer support bot use case:

- **greeting** - Welcome users warmly and set a helpful tone
- **troubleshooting** - Step-by-step diagnosis framework for common issues
- **ticket-creation** - Create support tickets with bundled tool
- **knowledge-search** - Search knowledge base articles with bundled tool

## Framework Demos

### CrewAI Demo

The `crewai-demo/` directory contains a multi-agent customer support crew example:

- **Router Agent** (progressive mode) - Greets customers using greeting skill
- **Specialist Agent** (inject mode) - Troubleshoots issues with knowledge base
- **Escalation Agent** (inject mode) - Creates tickets for unresolved issues

```bash
cd examples/crewai-demo
python run.py --quick  # Mocked LLM for CI
python run.py --real   # Actual API calls (requires OPENAI_API_KEY)
```

### Coming Soon

- LangChain Demo
- ElevenLabs Demo

Each demo references the shared skills via their `.skillforge.yaml` configuration.
