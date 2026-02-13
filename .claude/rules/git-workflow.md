# Git Workflow

## Branch Naming Convention

```
{MMDD}{initials}
```

Examples:
- `0213jc` — February 13th, user jc
- `0215ab` — February 15th, user ab

## Commit Little and Often

Commit and push at every meaningful checkpoint — not just at session end. This is part of the process, not an afterthought.

**Meaningful checkpoints include:**
- Research brief created and scaffolded
- Consolidation written
- CLAUDE.md or rules updated
- Any code written or modified
- Hypothesis or state file updated

Don't accumulate. If work has been done, commit it.

## Session Start

When JC says "what's next" or starts a session:

1. **Check git status** — uncommitted changes? Ask whether to commit, stash, or discard
2. **Check current branch:**
   - On `main` → pull latest, create today's branch (e.g., `0213jc`)
   - On yesterday's branch → ask whether to continue or merge and start fresh
   - On today's branch → continue working
3. **Read CLAUDE.md** — understand current state, hypothesis status, phase
4. **Read `docs/research/_state.yaml`** — check session state and blockers
5. **Identify next action** — what's the next research brief, open question, or implementation task?
6. **Confirm with JC** — state what I plan to work on, ask if correct

## Session End

When JC says "done for today" or "wrap up":

1. **Commit and push** all changes to branch
2. **Update `docs/research/_state.yaml`** — record session state, progress, blockers
3. **Update CLAUDE.md** if project status has changed
4. **Summarise** what was done this session
5. **State next steps** — what should the next session pick up

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

For **code changes:**
1. Run type checker
2. Remove debug statements
3. Ensure changes match task scope

For **docs/research changes:**
1. Ensure CLAUDE.md reflects current state
2. Check naming conventions are followed
3. Verify file is in the correct location

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
- Config changes → Verify build still works

### Skip Deep Verification When
- Documentation-only changes
- Research brief scaffolding
- State file updates

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

## Pull Request Workflow

When creating PRs:
1. Analyse **full commit history** (not just latest commit)
2. Use `git diff [base-branch]...HEAD` to see all changes
3. Draft comprehensive PR summary
4. Include test plan with TODOs
5. Push with `-u` flag if new branch
