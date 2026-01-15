"""
Secure credential management for ElevenLabs API integration.

This module provides functions for securely storing and retrieving
ElevenLabs API credentials. Credentials are stored in ~/.skillforge/elevenlabs.json
with restricted file permissions (0600).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default credentials directory
CREDENTIALS_DIR = Path.home() / ".skillforge"
CREDENTIALS_FILE = CREDENTIALS_DIR / "elevenlabs.json"


class CredentialsError(Exception):
    """Raised when there's an issue with credentials."""

    pass


class CredentialsNotFoundError(CredentialsError):
    """Raised when credentials are not found."""

    pass


class InvalidCredentialsError(CredentialsError):
    """Raised when credentials are invalid."""

    pass


def _ensure_credentials_dir() -> None:
    """Ensure the credentials directory exists with proper permissions."""
    if not CREDENTIALS_DIR.exists():
        CREDENTIALS_DIR.mkdir(parents=True, mode=0o700)
        logger.debug(f"Created credentials directory: {CREDENTIALS_DIR}")


def save_credentials(api_key: str) -> None:
    """Save ElevenLabs API key securely.

    The API key is stored in ~/.skillforge/elevenlabs.json with
    file permissions set to 0600 (owner read/write only).

    Args:
        api_key: The ElevenLabs API key to store.

    Raises:
        ValueError: If api_key is empty.
        CredentialsError: If credentials cannot be saved.

    Example:
        >>> save_credentials("sk-...")
        >>> # Credentials saved to ~/.skillforge/elevenlabs.json
    """
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be empty")

    _ensure_credentials_dir()

    credentials = {"api_key": api_key.strip()}

    try:
        # Write to temporary file first, then rename for atomic write
        temp_file = CREDENTIALS_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(credentials, f, indent=2)

        # Set restrictive permissions
        os.chmod(temp_file, 0o600)

        # Atomic rename
        temp_file.rename(CREDENTIALS_FILE)

        logger.info("ElevenLabs credentials saved successfully")

    except Exception as e:
        # Clean up temp file if it exists
        temp_file = CREDENTIALS_FILE.with_suffix(".tmp")
        if temp_file.exists():
            temp_file.unlink()
        raise CredentialsError(f"Failed to save credentials: {e}") from e


def load_credentials() -> str:
    """Load ElevenLabs API key from stored credentials.

    Returns:
        The stored API key.

    Raises:
        CredentialsNotFoundError: If no credentials are stored.
        CredentialsError: If credentials file is corrupt.

    Example:
        >>> api_key = load_credentials()
        >>> print(api_key[:10])
        'sk-...'
    """
    if not CREDENTIALS_FILE.exists():
        raise CredentialsNotFoundError(
            "ElevenLabs credentials not found. "
            "Run 'skillforge elevenlabs connect' to configure."
        )

    try:
        with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
            credentials = json.load(f)

        api_key = credentials.get("api_key")
        if not api_key:
            raise CredentialsError("Credentials file missing api_key")

        return api_key

    except json.JSONDecodeError as e:
        raise CredentialsError(f"Corrupt credentials file: {e}") from e


def get_client():
    """Get configured ElevenLabs client from stored credentials.

    This function first checks for an ELEVENLABS_API_KEY environment
    variable, falling back to stored credentials if not set.

    Returns:
        Configured ElevenLabs client instance.

    Raises:
        CredentialsNotFoundError: If no credentials available.
        InvalidCredentialsError: If credentials are invalid.
        ImportError: If elevenlabs package is not installed.

    Example:
        >>> client = get_client()
        >>> # client ready for API calls
    """
    # Check environment variable first
    api_key = os.environ.get("ELEVENLABS_API_KEY")

    if not api_key:
        api_key = load_credentials()

    try:
        from elevenlabs import ElevenLabs

        return ElevenLabs(api_key=api_key)
    except ImportError as e:
        raise ImportError(
            "ElevenLabs SDK not installed. Install with: pip install elevenlabs"
        ) from e


def verify_credentials(api_key: str) -> bool:
    """Verify that API credentials are valid.

    Makes a lightweight API call to verify the credentials work.

    Args:
        api_key: The API key to verify.

    Returns:
        True if credentials are valid.

    Raises:
        InvalidCredentialsError: If credentials are invalid.
        ImportError: If elevenlabs package is not installed.
    """
    try:
        from elevenlabs import ElevenLabs

        client = ElevenLabs(api_key=api_key)

        # Make a lightweight API call to verify credentials
        # List KB documents is a minimal call that verifies API access
        client.conversational_ai.knowledge_base.documents.get_all()

        return True

    except ImportError as e:
        raise ImportError(
            "ElevenLabs SDK not installed. Install with: pip install elevenlabs"
        ) from e
    except Exception as e:
        error_msg = str(e).lower()
        if "unauthorized" in error_msg or "401" in error_msg or "api key" in error_msg:
            raise InvalidCredentialsError(
                "Invalid API key. Please check your ElevenLabs credentials."
            ) from e
        # Re-raise other errors - might be network issues etc.
        raise


def delete_credentials() -> bool:
    """Delete stored credentials.

    Returns:
        True if credentials were deleted, False if they didn't exist.

    Example:
        >>> delete_credentials()
        True
    """
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
        logger.info("ElevenLabs credentials deleted")
        return True
    return False
