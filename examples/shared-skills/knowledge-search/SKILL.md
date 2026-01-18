---
name: knowledge-search
description: Search knowledge base for relevant articles and documentation
allowed-tools:
  - search_kb
---

# Knowledge Search Skill

Find and present relevant knowledge base articles to help resolve customer issues efficiently.

## When to Use

- Customer asks a question that may have documented answer
- Before troubleshooting, check if solution exists
- Providing self-service resources to customer
- Finding official documentation for complex procedures

## Instructions

1. **Identify keywords** - Extract key terms from customer's question
2. **Search knowledge base** - Use `search_kb` tool with relevant query
3. **Review results** - Evaluate relevance of returned articles
4. **Present best match** - Share most relevant article with summary
5. **Offer alternatives** - Mention other relevant articles if available

## Search Strategy

- Use specific terms over generic ones
- Try alternative phrasings if first search yields poor results
- Combine related concepts (e.g., "email sync mobile")
- Search for error messages or codes directly

## Tool Usage

Use the `search_kb` tool with a search query:
- Keep queries focused (2-5 keywords work best)
- Include product/feature names when relevant
- Use terms the customer used when possible

## Output Format

```
Articles Found: [number of results]
Best Match: [title of most relevant article]
Summary: [key points that address customer's question]
Link: [article reference/ID]
```

If multiple relevant articles:
```
Articles Found: [number]
Best Match: [primary article title]
Summary: [key points]
Link: [reference]

Also Relevant:
- [second article title] - [brief relevance note]
- [third article title] - [brief relevance note]
```

## Example

**Customer asks about setting up two-factor authentication:**

Tool call:
```
search_kb(query="two-factor authentication setup")
```

Output:
```
Articles Found: 3
Best Match: Two-Factor Authentication Setup Guide
Summary: Step-by-step instructions for enabling 2FA on your account. Covers app-based authentication (recommended), SMS backup, and recovery codes. Estimated setup time: 5 minutes.
Link: KB-2341

Also Relevant:
- Account Security Best Practices - Overview of all security features
- Login Issues Troubleshooting - Help if 2FA is causing login problems
```

## Guidelines

- Always verify article is current and applicable
- Summarize key points rather than copying entire articles
- Offer to walk through article steps if customer prefers
- Note if article may be outdated or doesn't fully address the question
