"""Ticket creation tools for support skill."""

import random
from typing import Literal


def create_ticket(
    title: str,
    description: str,
    priority: Literal["critical", "high", "medium", "low"] = "medium",
) -> dict:
    """
    Create a support ticket in the ticketing system.

    Args:
        title: Brief summary of the issue (max 100 chars recommended)
        description: Detailed description including context, steps to reproduce,
                    customer information, and any relevant error messages
        priority: Ticket priority level
            - critical: Service down, data loss, security issues
            - high: Major feature broken, multiple users affected
            - medium: Feature degraded, workaround available
            - low: Minor issues, enhancement requests

    Returns:
        dict with ticket_id, status, and priority confirmation
    """
    # Generate mock ticket ID
    ticket_id = f"TICK-{random.randint(1000, 9999)}"

    return {
        "ticket_id": ticket_id,
        "status": "created",
        "priority": priority,
        "title": title[:100],  # Truncate if too long
        "message": f"Ticket {ticket_id} created successfully with {priority} priority",
    }
