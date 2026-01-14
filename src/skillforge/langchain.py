"""
Convenience module for LangChain adapter imports.

This module provides a clean import path for using SkillForge with LangChain:

    from skillforge.langchain import create_agent

Instead of the longer:

    from skillforge.adapters.langchain import create_agent
"""

from skillforge.adapters.langchain import create_agent

__all__ = ["create_agent"]
