---
name: ticket-creation
description: Create support tickets with proper categorization and priority
allowed-tools:
  - create_ticket
---

# Ticket Creation Skill

Create well-structured support tickets that capture all relevant information for efficient resolution.

## When to Use

- Issue cannot be resolved in current interaction
- Customer requests follow-up or tracking number
- Problem requires specialist attention
- Documenting resolved issues for records

## Instructions

1. **Gather information** - Collect all relevant details before creating ticket
2. **Determine priority** - Assess urgency based on impact and scope
3. **Write clear title** - Concise summary of the issue
4. **Provide description** - Include steps to reproduce, error messages, context
5. **Create ticket** - Use the `create_ticket` tool
6. **Confirm with customer** - Share ticket ID and set expectations

## Priority Guidelines

| Priority | Criteria | Response Time |
|----------|----------|---------------|
| **critical** | Service down, data loss risk, security issue | Immediate |
| **high** | Major feature broken, multiple users affected | Within 4 hours |
| **medium** | Feature degraded, workaround available | Within 24 hours |
| **low** | Minor issue, enhancement request | Within 72 hours |

## Tool Usage

Use the `create_ticket` tool with these parameters:
- `title`: Brief, descriptive summary (max 100 chars)
- `description`: Detailed context including steps, errors, customer info
- `priority`: One of: critical, high, medium, low

## Output Format

```
Ticket Created: [ticket ID from tool response]
Summary: [title of the ticket]
Priority: [priority level assigned]
Next Steps: [what customer should expect, timeline]
```

## Example

**Customer reports billing discrepancy:**

Tool call:
```
create_ticket(
    title="Billing discrepancy - double charge on subscription",
    description="Customer John Doe (account #12345) reports being charged twice for monthly subscription on Jan 15. Amount: $29.99 x2. Customer provided bank statement screenshot. Requesting refund for duplicate charge.",
    priority="high"
)
```

Output:
```
Ticket Created: TICK-4521
Summary: Billing discrepancy - double charge on subscription
Priority: high
Next Steps: Our billing team will review within 4 hours. You'll receive an email confirmation shortly with your ticket details. Expect resolution within 1 business day.
```
