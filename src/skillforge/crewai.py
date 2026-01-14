"""
Convenience module for CrewAI adapter imports.

This module provides a clean import path for using SkillForge with CrewAI:

    from skillforge.crewai import Agent

Instead of the longer:

    from skillforge.adapters.crewai import Agent
"""

from skillforge.adapters.crewai import Agent, agent_from_config

__all__ = ["Agent", "agent_from_config"]
