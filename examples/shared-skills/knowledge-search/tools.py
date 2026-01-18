"""Knowledge base search tools for support skill."""


# Mock knowledge base data
_KNOWLEDGE_BASE = {
    "email": [
        {
            "id": "KB-1001",
            "title": "How to Fix Email Sync Issues",
            "summary": "Troubleshooting guide for email synchronization problems across devices.",
            "keywords": ["email", "sync", "synchronization", "not syncing", "mail"],
        },
        {
            "id": "KB-1002",
            "title": "Email Troubleshooting Guide",
            "summary": "Comprehensive guide covering common email issues and solutions.",
            "keywords": ["email", "troubleshoot", "problems", "issues", "mail"],
        },
        {
            "id": "KB-1003",
            "title": "Setting Up Email on Mobile Devices",
            "summary": "Step-by-step instructions for configuring email on iOS and Android.",
            "keywords": ["email", "mobile", "phone", "ios", "android", "setup"],
        },
    ],
    "password": [
        {
            "id": "KB-2001",
            "title": "Password Reset Steps",
            "summary": "How to reset your password using email, SMS, or security questions.",
            "keywords": ["password", "reset", "forgot", "change", "recover"],
        },
        {
            "id": "KB-2002",
            "title": "Account Security Best Practices",
            "summary": "Tips for creating strong passwords and keeping your account secure.",
            "keywords": ["password", "security", "strong", "best practices", "secure"],
        },
        {
            "id": "KB-2003",
            "title": "Password Requirements and Policies",
            "summary": "Explanation of password complexity requirements and expiration policies.",
            "keywords": ["password", "requirements", "policy", "complexity", "rules"],
        },
    ],
    "login": [
        {
            "id": "KB-3001",
            "title": "Login Issues Troubleshooting",
            "summary": "Common login problems and their solutions including browser issues.",
            "keywords": ["login", "sign in", "access", "cant login", "trouble"],
        },
        {
            "id": "KB-3002",
            "title": "Two-Factor Authentication Setup",
            "summary": "Guide to enabling and using 2FA for enhanced account security.",
            "keywords": ["login", "2fa", "two-factor", "authentication", "mfa"],
        },
        {
            "id": "KB-3003",
            "title": "Account Locked - What To Do",
            "summary": "Steps to unlock your account after too many failed login attempts.",
            "keywords": ["login", "locked", "unlock", "blocked", "attempts"],
        },
    ],
    "billing": [
        {
            "id": "KB-4001",
            "title": "Understanding Your Invoice",
            "summary": "How to read your invoice, including charges, taxes, and discounts.",
            "keywords": ["billing", "invoice", "charges", "payment", "bill"],
        },
        {
            "id": "KB-4002",
            "title": "Updating Payment Methods",
            "summary": "How to add, remove, or change your payment method on file.",
            "keywords": ["billing", "payment", "credit card", "update", "method"],
        },
        {
            "id": "KB-4003",
            "title": "Refund Policy and Requests",
            "summary": "Our refund policy and how to request a refund for eligible purchases.",
            "keywords": ["billing", "refund", "money back", "cancel", "charge"],
        },
    ],
    "account": [
        {
            "id": "KB-5001",
            "title": "Managing Your Account Settings",
            "summary": "How to update profile information, preferences, and notifications.",
            "keywords": ["account", "settings", "profile", "preferences", "update"],
        },
        {
            "id": "KB-5002",
            "title": "Closing Your Account",
            "summary": "Steps to close your account and what happens to your data.",
            "keywords": ["account", "close", "delete", "cancel", "remove"],
        },
    ],
}


def search_kb(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the knowledge base for articles matching the query.

    Args:
        query: Search query string (2-5 keywords work best)
        max_results: Maximum number of results to return (default: 5)

    Returns:
        List of matching articles with id, title, summary, and relevance score
    """
    query_lower = query.lower()
    query_terms = query_lower.split()

    results = []

    # Search through all categories
    for category, articles in _KNOWLEDGE_BASE.items():
        for article in articles:
            # Calculate relevance score based on keyword matches
            score = 0

            # Check title match (highest weight)
            title_lower = article["title"].lower()
            for term in query_terms:
                if term in title_lower:
                    score += 10

            # Check keywords match (medium weight)
            for keyword in article["keywords"]:
                for term in query_terms:
                    if term in keyword or keyword in term:
                        score += 5

            # Check summary match (lower weight)
            summary_lower = article["summary"].lower()
            for term in query_terms:
                if term in summary_lower:
                    score += 2

            # Check category match
            if category in query_lower:
                score += 3

            if score > 0:
                results.append(
                    {
                        "id": article["id"],
                        "title": article["title"],
                        "summary": article["summary"],
                        "relevance_score": score,
                    }
                )

    # Sort by relevance score (highest first) and limit results
    results.sort(key=lambda x: x["relevance_score"], reverse=True)

    return results[:max_results]
