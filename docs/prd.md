# LogLens MVP - Product Requirements Document

## Overview

**Product Name:** LogLens  
**Version:** MVP / Demo  
**Date:** January 2025

---

## Problem Statement

Customer Support escalates issues to engineers who must manually dig through Sentry logs to explain what went wrong. This wastes engineering time on repetitive translation work that could be automated.

**Current flow:**
1. CS receives customer complaint
2. CS escalates to engineering via Slack/email
3. Engineer stops work, opens Sentry
4. Engineer searches logs by timestamp/user
5. Engineer interprets error, writes explanation
6. Engineer sends response back to CS
7. CS relays to customer

**Time wasted:** 15-30 min per escalation

---

## Solution

AI-powered log analyzer that:
- Takes CS input (description, timestamp, customer ID)
- Fetches relevant Sentry logs automatically
- Analyzes against known workflows and error patterns
- Returns probable causes + suggested customer responses

---

## Users

| User | Role | Need |
|------|------|------|
| Customer Support | Primary | Quick answers without engineering escalation |
| Engineers | Secondary | Faster log triage when needed |

---

## Core User Flow

```
CS Input → Fetch Logs → LLM Analysis → Actionable Output
```

1. CS provides: problem description, timestamp, customer ID
2. System fetches Sentry events (±5 min window, filtered by user)
3. LLM analyzes against workflow doc + known errors doc
4. Returns: ranked causes, suggested response, log links

---

## Input Channels

### Web Form
- Simple 3-field form (description, timestamp, customer ID)
- Password-protected dashboard
- Hosted on Cloudflare Pages

### Slack Bot
- Slash command: `/loglens`
- Format: `/loglens [description] | [timestamp] | [customer_id]`
- Returns formatted response in Slack

---

## Output

Each analysis returns:

| Field | Description |
|-------|-------------|
| Causes | Top 3 ranked probable causes with confidence (high/medium/low) |
| Suggested Response | Draft message CS can send to customer |
| Sentry Links | Direct links to relevant log events |
| Logs Summary | Brief summary of what was found in logs |

### Example Output

```
🔍 Analysis Complete

PROBABLE CAUSES:
1. [HIGH] Payment token expired - user session timed out during checkout
2. [MEDIUM] Cart session timeout - items removed from cart
3. [LOW] Inventory conflict - item went out of stock

SUGGESTED RESPONSE:
"Hi [Customer], it looks like your payment session timed out after being 
idle for too long. This is a security measure. Please try checking out 
again - your cart items should still be there. Let me know if you run 
into any other issues!"

LOGS:
Found 3 error events between 14:25-14:35
→ View in Sentry: [link]
```

---

## Knowledge Base

### workflow.md
- Documents expected user flows
- Describes normal system behavior
- Defines what "success" looks like for each flow
- Maintained by engineering team

### known_errors.md
- Catalog of previously encountered errors
- Maps error patterns to root causes
- Includes proven customer responses
- Grows over time as new errors are resolved

---

## Authentication

- Single shared password for MVP
- Entered once, stored in browser
- Same password for all users
- No individual accounts

---

## Scope

### In Scope (MVP)
- Web form input
- Slack slash command
- Sentry log fetching (single project)
- OpenAI GPT-4o analysis
- Markdown-based knowledge base
- Basic password auth

### Out of Scope (MVP)
- CloudWatch integration
- Multi-project support
- Individual user accounts
- Automatic error pattern learning
- Audit trail / history
- Analytics dashboard

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to resolution | < 2 min (down from 15-30 min) |
| Engineering escalations | Reduce by 50% |
| CS satisfaction | Qualitative positive feedback |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LLM hallucination | Always include Sentry links for verification |
| Missing logs | Show "no events found" clearly, suggest widening time range |
| Wrong customer ID format | Validate format on input |
| Sentry rate limits | Cache responses, add backoff |

---

## Future Considerations (Post-MVP)

- CloudWatch integration for backend logs
- Auto-append new errors to known_errors.md
- Slack thread integration (respond in existing threads)
- Multi-project support
- Search history of past analyses
- Confidence threshold alerts (flag low-confidence for human review)