"""
LangChain assumption validation tests for SkillForge.

This package contains tests that validate critical assumptions about
LangChain's behavior that SkillForge depends on for its architecture.

Assumptions Being Validated:
1. Agents can call shell commands via tool - test_shell_execution.py
2. System prompt can be extended at runtime - test_system_prompt_extension.py
3. Tool output is returned to agent context - test_tool_output_usage.py
4. Custom agent parameters work as expected - test_custom_parameters.py

These tests require an API key (ANTHROPIC_API_KEY or OPENAI_API_KEY)
to run against real LLM providers.
"""
