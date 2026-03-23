# UX Validation Script - avatar

## Goal

Quickly validate the MVP core loop:
`request creation -> priority/status clarity -> progress + KPI communication`.

## Test Setup

- **Artifact to test:** `_bmad-output/planning-artifacts/ux-prototype.html`
- **Session length:** 15-20 minutes per participant
- **Target participants (MVP):**
  - 2-3 agency operators (Product Lead / delivery)
  - 2 client-side users (low/medium technical comfort)
- **Moderator role:** observe behavior, do not teach UI

## Success Metrics (Pass/Fail Thresholds)

- Task 1 (create request): <= 60 sec, no moderator intervention
- Task 2 (find urgent item): <= 15 sec, correct identification
- Task 3 (show progress + KPI): <= 30 sec, coherent explanation
- Subjective clarity score (1-5): average >= 4.0
- "Would use this in real workflow?" yes-rate >= 70%

## Moderator Intro (Read Verbatim)

"Thanks. We are testing the interface, not you.  
Please think aloud while you work.  
If something is unclear, still try your best first.  
I may ask follow-up questions, but I will avoid helping during tasks."

## Tasks

### Task 1 - Add a New Request

Prompt:
"You need a new campaign video request. Add it to the system."

Observe:
- First click target
- Time to completion
- Confusion points (labels, form fields, confirmation)

Success:
- User creates request without help
- User understands where request appears after save

### Task 2 - Identify What Is Urgent

Prompt:
"You joined quickly before a call. Show me what is urgent right now."

Observe:
- Scan path (where eyes/cursor go first)
- Whether urgency is detected from default surface
- Need for extra filters/navigation

Success:
- Urgent item identified correctly in <= 15 sec

### Task 3 - Present Progress to Client

Prompt:
"Imagine you are on a client call. Show current progress and KPI snapshot."

Observe:
- Can user find summary naturally?
- Can user tell a clear story (status + KPI + next step)?
- Any missing context for confident communication?

Success:
- User can present state without switching contexts

## Follow-Up Questions (2-4 min)

1. What felt easiest?
2. What felt slow or confusing?
3. Was request handling clear enough?
4. Did status labels feel trustworthy and understandable?
5. Would this replace your current chat/file coordination flow? Why/why not?
6. One thing you would change first?

## Notes Template (Fill During Session)

```markdown
## Participant
- ID:
- Role: Agency Operator / Client
- Technical level: Low / Medium / High

## Task Results
- Task 1 (Add request): time __ sec | success Y/N | notes:
- Task 2 (Find urgent): time __ sec | success Y/N | notes:
- Task 3 (Show progress+KPI): time __ sec | success Y/N | notes:

## Behavior Observations
- First-click behavior:
- Confusion points:
- Recovery behavior:

## Subjective Ratings (1-5)
- Clarity:
- Speed:
- Confidence:
- Trust in status/KPI:

## Quotes
- Positive:
- Negative:

## Top Issues (ranked)
1.
2.
3.

## Severity
- Critical:
- Major:
- Minor:
```

## Synthesis Template (After 5 Sessions)

```markdown
# UX Validation Summary - avatar

## Quantitative
- Avg time Task 1:
- Avg time Task 2:
- Avg time Task 3:
- Completion rate:
- Avg clarity score:

## Top Frictions
1.
2.
3.

## What Works Well
1.
2.
3.

## Decision
- Proceed to implementation: Yes / No
- Required fixes before implementation:
  1.
  2.
  3.
```

## Recommended Next Step

Run 5 sessions, synthesize results, then update:
- `ux-prototype.html` for quick UX iteration
- `ux-design-specification.md` if principles/patterns need adjustment
