# LogLens MVP - Discovery Conversation

**Date:** January 2025  
**Participants:** Kuba (Product Owner), Claude (AI Assistant)

---

## Initial Problem Statement

**Kuba:**

I want you to help me with a simple MVP idea like it has to be extremely minimalistic. Do not let the scope creep. The problem I have is that everytime something happens with customer support, they reach out to engineers to find out what the problem was, why something failed, why customer couldn't complete an action, etc. This wastes engineers time, since they have to check the logs on the backend, frontend, pinpoint when the error happened, and then say for example that it was a state error, or that customer had no permissions, etc. They have to do that, then go back to the customer support with the solution. 

I was thinking this could be all automated with a simple markdown document that basically makes the agent aware of what the proper workflow and behaviors are, then check frontend and backend logs, digests the error that CS person feeds it, and gives a list of most likely reasons for the error / problem. It could take logs from frontend via sentry, backend via amazon cloud watch. And then openai api, like a strong enough model, then html/css/js frontend like very simple and fetch for api, made with like fastAPi, like im thiking minimal as fuck. 

Ask additional questions before giving me the PRD and tech spec.

---

## Discovery Questions - Round 1

**Claude:**

Love the problem framing - engineers as log translators is a huge time sink. Before I draft anything, let me nail down a few things to keep this razor-thin:

**Input/Trigger:**
1. What does CS typically provide when they escalate? Just a text description, or also customer ID, timestamp, email, session ID?
2. Is there a consistent format they use today (Slack message, ticket, email)?

**Log Access:**
3. Sentry + CloudWatch - are these already set up with reasonable retention? Any auth complexity (SSO, IAM roles)?
4. How do you correlate frontend/backend logs today? User ID? Request ID? Session?

**Scope:**
5. Single product/service, or does this need to work across multiple projects from day one?
6. Who uses this - just CS, or do you want engineers to use it too as a faster log viewer?

**Output:**
7. Is "most likely reasons" enough, or do they also need suggested responses to send to customers?
8. Should it link to the actual log entries for verification, or just summarize?

**Deployment:**
9. Internal tool only (no public auth needed, maybe just behind VPN or basic password)?
10. Any hard constraints - specific cloud, budget for OpenAI API?

Answer these and I'll give you a brutally minimal PRD + tech spec that you could ship in a weekend.

---

## Answers - Round 1

**Kuba:**

1. Text description, timestamp, customerID.
2. Yeah slack, or email.
3. Yeah those are set up already. For mvp lets just test sentry, since its going to be more of the same for cloudwatch, and will remove some complexity, limit scope, and make dev faster.
4. You tell me whats the market standard for this
5. Single product / service for now
6. Can be both
7. Yeah suggested too.
8. Yes.
9. Simple dashboard on cloudflare pages, backend on railway.
10. Nope

---

## Discovery Questions - Round 2

**Claude:**

Good, that's tight. Few more to lock it down:

**Correlation (you asked):**
Market standard is trace/request ID propagated from frontend → backend, but since you're Sentry-only for MVP, you can just filter by:
- User ID (Sentry captures this if you've set it up)
- Timestamp range (±5 min from reported time)

Is user ID already being sent to Sentry events? If not, we can work with timestamp + error message fuzzy matching.

**Final scoping questions:**

1. The "workflow markdown" - is this a single doc that describes expected user flows + known error patterns, or do you want the LLM to learn from your codebase? (I'd strongly recommend single doc for MVP)

2. Auth - literally just a shared password, or do you need individual logins? (Shared password = ship faster)

3. Input interface - simple form where CS pastes their info, or do you want a Slack bot that intercepts messages? (Form = way simpler for MVP)

4. How many Sentry projects are we talking? Just one?

5. Do you have existing error-to-explanation mappings anywhere (wiki, runbook, past Slack threads)? That becomes your seed markdown doc.

Once you answer these I'll write the PRD + spec - aiming for something you can build in 2-3 days max.

---

## Answers - Round 2

**Kuba:**

1. Yeah keep it simple, and then second markdown file to keep the errors, so in the future we know if we already encountered this kind of errror, and can give quicker answer.
2. Yeah just password
3. Both form and slack bot.
4. 1 project
5. Not yet

---

## Scope Pushback

**Claude:**

Pushing back on one thing:

**Form OR Slack bot for MVP, not both.**

Slack bot adds: app registration, bot token handling, message parsing, different response formatting, webhook setup. That's easily +1-2 days and a different deployment surface.

My recommendation: **Form first.** It's:
- Faster to build
- Easier to iterate on UX
- No Slack admin approval needed
- You can always paste the output INTO Slack

Slack bot becomes v1.1 once you've validated the core logic works.

Deal?

If yes, I'll write the PRD + tech spec now.

---

## Final Decision

**Kuba:**

Like this is not really for prod, more like a demo showcase, so we will do both still.

**Claude:**

Got it - demo showcase. Both it is.

---

## Final Deliverables

PRD and Tech Spec were generated covering:

### PRD Summary
- Problem statement (engineers as log translators)
- Solution (AI-powered log analyzer)
- Users (CS primary, Engineers secondary)
- Core flow (input → fetch → analyze → output)
- Input channels (Web form + Slack bot)
- Output format (causes, suggested response, Sentry links)
- Knowledge base (workflow.md + known_errors.md)
- Scope boundaries (in/out of scope)
- Success metrics

### Tech Spec Summary
- Architecture diagram
- Tech stack (FastAPI, Cloudflare Pages, Railway, OpenAI, Sentry API, Slack Bolt)
- Project structure
- API endpoints with request/response schemas
- Authentication middleware
- Sentry integration details
- LLM prompt templates
- Slack bot command format
- Frontend UI wireframe
- Deployment instructions (Railway, Cloudflare Pages, Slack app setup)
- Build order with time estimates (~14 hours total)
- Starter markdown templates for workflow.md and known_errors.md
- Manual test cases

---

## Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Log source | Sentry only | Reduce scope, same pattern for CloudWatch later |
| Correlation | User ID + timestamp (±5 min) | Simple, works without trace IDs |
| Knowledge base | 2 markdown files | Simple, no DB needed |
| Auth | Shared password | Ship faster for demo |
| Input channels | Form + Slack bot | Demo showcase (despite scope concern) |
| Projects | Single Sentry project | MVP simplicity |
| Hosting | Cloudflare Pages + Railway | Free/cheap, easy deploy |
| LLM | GPT-4o | Best speed/quality balance |

---

## Estimated Build Time

**2-3 days** for demo-ready version

| Step | Task | Time |
|------|------|------|
| 1 | Backend skeleton | 1 hour |
| 2 | Sentry client | 2 hours |
| 3 | Analyzer (LLM) | 2 hours |
| 4 | API endpoint | 1 hour |
| 5 | Frontend | 3 hours |
| 6 | Slack bot | 2 hours |
| 7 | Deploy + test | 2 hours |
| 8 | Polish | 1 hour |

---

## Next Steps

1. Review PRD.md and TECH_SPEC.md
2. Scaffold the code
3. Set up Sentry API access
4. Set up OpenAI API key
5. Create Slack app
6. Deploy and test