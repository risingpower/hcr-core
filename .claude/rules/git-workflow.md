# Git Workflow

## Branch Naming Convention

```
{MMDD}{initials}
```

Examples:
- `0123jc` - January 23rd, user jc
- `0215ab` - February 15th, user ab

## Daily Workflow

### Before Starting New Work

**Run `/au-plan` before implementing any feature or fix.**

This creates a detailed implementation plan and WAITS for your confirmation before any code changes.

### Session Start (6-step process)

1. **Check git status** - Uncommitted changes? Commit/stash/discard
2. **Check current branch**:
   - On `main` → Create today's branch (e.g., `0123jc`)
   - On yesterday's branch → Ask: continue or merge and start fresh?
   - On today's branch → Continue working
3. **Read CLAUDE.md** - Understand current plan
4. **Pick next task** - Top unchecked "Must Have" item (or one assigned to me)
5. **Confirm** - Tell user what working on, ask if correct
6. **Run `/au-plan`** - Create implementation plan before coding

### Session End

1. **Commit and push** all changes
2. **Summarize** what was done
3. **Remind** to merge if ready, or note continuing tomorrow

## Post-Work Verification Protocol

After completing a task, use judgment to determine verification level:

### Significant Work (Prompt for /au-verify)
After completing any of these, ask: *"I've completed [X]. Would you like me to run /au-verify?"*

- New feature implementation
- Bug fix that touches multiple files
- Refactoring existing code
- Changes to API calls, auth, or data handling
- Any work touching 3+ files

### Light Work (Clean As You Go)
For smaller changes, verify inline without prompting:

- Single file edits → Run type check silently, fix any errors
- Component changes → Confirm no type errors before moving on
- Config changes → Verify build still works

### Always Before Commit
Regardless of task size, always:

1. Run type check
2. Remove any debug statements you added
3. Ensure changes match the task scope (no scope creep)

### Skip Deep Testing When
- Documentation-only changes
- Comment additions
- Single-line fixes with obvious correctness
- Styling/CSS-only changes

**Principle:** Quality is built in, not bolted on. Employees steer, Claude ensures standards.

## Context Management

Check context usage with `/context` when:
- Working on complex tasks
- After many file reads/edits
- Before starting something new

### When to Act

| Usage | Status | Action |
|-------|--------|--------|
| < 60% | Safe | Continue working |
| 60-75% | Warning | Plan next break point |
| > 75% | Critical | Act before autocompact |

### Compaction vs New Session

| Situation | Recommendation |
|-----------|----------------|
| **Mid-task**, can't stop | Use `/compact` to continue |
| **Logical break point** | Start **new session** (cleaner) |
| **Confusion/wrong assumptions** | Start **new session** (reset) |
| **End of work session** | Start **new session** next time |

**Why prefer new session at break points?**
- Clean context = no accumulated confusion
- Session hooks save/restore state automatically
- State files (`_state.yaml`, `CLAUDE.md`) are the real memory
- No risk of compaction losing important nuances

## Commit Rules

### Format
```
<type>: <description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

### CRITICAL: No Attribution

**NEVER add "Co-Authored-By: Claude" to commit messages. Ever.**

This is a universal rule across all repos.

### Before Every Commit

**Run `/au-review` to check for issues before committing.**

1. Run `/au-review` - Code quality and security check
2. Ensure `README.md` is up to date
3. Ensure `CLAUDE.md` is up to date with any changes made
4. Remove debug statements (console.log / print)
5. Run type checker

## Pull Request Workflow

When creating PRs:
1. Analyze **full commit history** (not just latest commit)
2. Use `git diff [base-branch]...HEAD` to see all changes
3. Draft comprehensive PR summary
4. Include test plan with TODOs
5. Push with `-u` flag if new branch

## Quick Commands

```bash
# Start of day
git checkout main && git pull
git checkout -b $(date +%m%d)jc

# End of day
git add -A && git commit -m "feat: [description]"
git push -u origin $(git branch --show-current)

# Check status
git status
git diff --name-only HEAD
```
