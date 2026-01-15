"""
Configuration and fixtures for ElevenLabs validation tests.
"""

import os
import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "elevenlabs_assumption: marks tests that validate ElevenLabs assumptions"
    )


@pytest.fixture(scope="session")
def elevenlabs_client():
    """Get configured ElevenLabs client."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        pytest.skip("ELEVENLABS_API_KEY not set")

    from elevenlabs import ElevenLabs
    return ElevenLabs(api_key=api_key)


@pytest.fixture(scope="session")
def has_elevenlabs_api_key():
    """Check if ElevenLabs API key is available."""
    return os.getenv("ELEVENLABS_API_KEY") is not None
