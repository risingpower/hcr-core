---
name: task-management
description: Use this skill for creating, viewing, and managing tasks in the central auditsu-tasks repository. Defines the workflow for task creation with smart inference.
---

# Task Management Workflow

Tasks are tracked centrally at [imaginaition-ltd/auditsu-tasks](https://github.com/imaginaition-ltd/auditsu-tasks).

## Labels

| Category | Labels |
|----------|--------|
| Priority | `must`, `should`, `could`, `wont` |
| Repo | `app-fe`, `site-fe-v2`, `site-be`, `ariadne` |
| Status | `ready` (cleared for pickup), `blocked` (needs input) |
| Type | `bug`, `feature`, `docs`, `tech-debt` |
| Size | `small`, `medium`, `large` |
| Assignee | `assigned:jason`, `assigned:simon`, `assigned:wilson` |

## Team

| Role | Person | Label |
|------|--------|-------|
| CTO | Simon | `assigned:simon` |
| Engineer | Jason | `assigned:jason` |
| Engineer | Wilson | `assigned:wilson` |

## Quick Commands

```bash
# View tasks for a repo
gh issue list -R imaginaition-ltd/auditsu-tasks --label <repo>

# View ready tasks
gh issue list -R imaginaition-ltd/auditsu-tasks --label <repo> --label ready

# View tasks assigned to someone
gh issue list -R imaginaition-ltd/auditsu-tasks --label assigned:jason

# Pick up a task
gh issue edit <number> -R imaginaition-ltd/auditsu-tasks --add-label assigned:jason

# Complete a task
gh issue close <number> -R imaginaition-ltd/auditsu-tasks
```

## Claude Workflow

### Brain Dump Mode (Batch Task Creation)

When user dumps multiple ideas at once:

1. **Parse ideas** into discrete tasks
2. **Batch infer** priority/type/repo for each
3. **Present summary table** for review:
   ```
   | # | Title | Priority | Type | Repo |
   |---|-------|----------|------|------|
   | 1 | Fix auth redirect loop | must | bug | app-fe |
   | 2 | Add dark mode toggle | could | feature | app-fe |
   | 3 | Update pricing copy | should | docs | site-fe-v2 |

   Any changes? Or create all?
   ```
4. **Apply edits** if user requests changes (e.g., "make #2 should")
5. **Batch create** all approved tasks

### When user asks to create a task

1. **Infer details intelligently:**
   - **Title**: Clear, actionable summary
   - **Priority**: `must` (urgent/blocking), `should` (normal), `could` (nice-to-have)
   - **Type**: `bug` (fix), `feature` (new), `docs` (documentation), `tech-debt` (refactor)
   - **Repo**: Assume current working repo
   - **Assignee**: Unassigned by default
   - **Context**: Brief description of why/what (from conversation context)
   - **Acceptance Criteria**: Obvious requirements if applicable

2. **Present for confirmation:**
   ```
   I'll add that now. Please confirm:

   **Title:** Fix login redirect loop
   **Priority:** should | **Type:** bug | **Repo:** app-fe

   **Context:**
   Users are getting stuck in a redirect loop after SSO login when session expires.

   **Acceptance Criteria:**
   - [ ] SSO login completes without redirect loop
   - [ ] Session expiry handled gracefully

   [Create] or let me know any changes.
   ```

3. **Create on confirmation:**
   ```bash
   gh issue create -R imaginaition-ltd/auditsu-tasks \
     --label <repo> --label <priority> --label <type> \
     --title "<title>" --body "## Context
   <context>

   ## Acceptance Criteria
   <criteria>"
   ```

### When user asks "what's next" or wants a task

1. Check for ready tasks: `gh issue list -R imaginaition-ltd/auditsu-tasks --label <repo> --label ready`
2. Show top task and ask if they want to work on it

### When user completes a task

1. Close the issue: `gh issue close <number> -R imaginaition-ltd/auditsu-tasks`

## Issue Template

```markdown
## Context
[Why this task exists]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Notes
[Optional: technical hints, links, related issues]
```

## CLI Tools (for non-Claude users)

Team members can use these shell commands (requires `~/Documents/dev/the-milf/bin` in PATH):

```bash
au-task               # Interactive task creator
au-tasks              # View all open tasks
au-tasks app-fe       # View tasks for a repo
au-tasks jason        # View tasks assigned to someone
au-tasks --help       # Show all filters
```
