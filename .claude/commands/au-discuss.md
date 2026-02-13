---
description: Capture implementation preferences before planning. Asks targeted questions to reduce rework and lock decisions in CONTEXT.md.
---

# /au-discuss Command

Capture implementation preferences before planning to reduce iteration cycles.

## What This Command Does

1. **Analyze Feature Type** - Determine if it's UI, API, Config, or Research
2. **Ask Targeted Questions** - 3-5 questions based on feature type
3. **Lock Decisions** - Output to `docs/context/{feature}-CONTEXT.md`
4. **Feed into Planning** - /au-plan references CONTEXT.md if present

## When to Use

Use `/au-discuss` when:
- Starting a feature with design decisions
- Requirements have multiple valid approaches
- You want to reduce back-and-forth during implementation
- The feature affects UX, API contracts, or architecture

## When NOT to Use

Skip `/au-discuss` when:
- Task is straightforward (use `/au-proto`)
- Requirements are already fully specified
- It's a bug fix with clear expected behavior
- Refactoring with no behavioral changes

## Workflow

```
/au-discuss user notifications

1. Analyze: This is a UI + API feature (notification display + backend triggers)
2. Questions:
   - In-app only, email, or both?
   - Toast notifications or notification center?
   - Real-time (WebSocket) or polling?
3. Lock: Write decisions to docs/context/user-notifications-CONTEXT.md
4. Next: "Run /au-plan user notifications to create implementation plan"
```

## Question Taxonomy

<!-- REPO-CONTEXT-START -->
<!-- This section is replaced during scaffolding with repo-specific questions -->
<!-- Example for app-fe (Frontend):
### Frontend Questions

| Category | Questions |
|----------|-----------|
| Layout | Where should this live? Modal, page, sidebar, inline? |
| Density | Compact, comfortable, or spacious? |
| Empty States | What shows when there's no data? |
| Error Presentation | Inline errors, toast, or error page? |
| Mobile Behavior | Same as desktop, simplified, or hidden? |
| Loading States | Skeleton, spinner, or progressive? |
-->
<!-- Example for site-be (Backend):
### Backend Questions

| Category | Questions |
|----------|-----------|
| Response Format | Envelope style? Pagination approach? |
| Error Handling | Error codes? Retry hints? |
| Auth Model | Who can access? Role-based or resource-based? |
| Idempotency | Needed? How to implement? |
| Rate Limiting | Limits? Per-user or global? |
-->
<!-- Example for ariadne (R&D):
### R&D Questions

| Category | Questions |
|----------|-----------|
| Hypothesis | What are we trying to prove? |
| Success Criteria | How do we know it worked? |
| Validation | How will we test the hypothesis? |
| Constraints | Time, compute, or scope limits? |
| Failure Mode | What if it doesn't work? |
-->
<!-- REPO-CONTEXT-END -->

## Question Strategy

Ask 3-5 questions maximum. Focus on:

1. **High-impact decisions** - Things that are hard to change later
2. **Ambiguous requirements** - Where multiple approaches are valid
3. **User preferences** - Style, behavior, density choices
4. **Integration points** - How it connects to existing systems

Do NOT ask about:
- Implementation details (that's for planning)
- Technology choices (unless user must decide)
- Obvious requirements already stated

## Output Format

Create `docs/context/{feature}-CONTEXT.md`:

```markdown
# Feature Context: {feature-name}

**Created:** {date}
**Status:** Locked

## Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Where should notifications appear? | Toast + notification center | User wants both immediate feedback and history |
| Real-time or polling? | Real-time via SSE | Already have SSE infrastructure |
| Email notifications? | Phase 2 | Focus on in-app first |

## Out of Scope

- Push notifications (mobile app not ready)
- Notification preferences UI (separate feature)

## Notes

User prefers minimal disruption - toasts should auto-dismiss after 5s.
```

## After Discuss

Suggest next steps:

```
Decisions locked in docs/context/{feature}-CONTEXT.md

Next steps:
- Run `/au-plan {feature}` to create implementation plan
- Or `/au-proto {feature}` for quick implementation
```

## Integration with /au-plan

When /au-plan runs, it should:
1. Check for existing `docs/context/{feature}-CONTEXT.md`
2. Load decisions as constraints
3. Reference locked decisions in the plan

## Related Commands

- `/au-plan` - Full planning (references CONTEXT.md if present)
- `/au-proto` - Quick implementation (skip discuss for simple tasks)
