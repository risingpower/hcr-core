---
description: Create or verify a checkpoint. Saves current state for comparison. Use for session management.
---

# /au-checkpoint Command

Create or verify a checkpoint in your workflow.

## Usage

`/au-checkpoint [action] [name]`

Actions:
- `create <name>` - Create named checkpoint
- `verify <name>` - Compare current state to checkpoint
- `list` - Show all checkpoints
- `clear` - Remove old checkpoints (keeps last 5)

## Create Checkpoint

When creating:

1. Run `/au-verify quick` to ensure clean state
2. Record current git state
3. Log to `.claude/checkpoints.log`:
   ```
   2026-01-23-14:30 | feature-start | abc1234
   ```
4. Report checkpoint created

## Verify Checkpoint

When verifying:

1. Read checkpoint from log
2. Compare current state:
   - Files added/modified since checkpoint
   - Test pass rate now vs then
   - Coverage now vs then
3. Report comparison

```
CHECKPOINT COMPARISON: feature-start
====================================
Files changed: 12
Tests: +5 passed / -0 failed
Coverage: +2%
Build: PASS
```

## List Checkpoints

Show all checkpoints with:
- Name
- Timestamp
- Git SHA
- Status (current, behind, ahead)

## Typical Workflow

```
[Start]     → /checkpoint create "feature-start"
    ↓
[Implement] → /checkpoint create "core-done"
    ↓
[Test]      → /checkpoint verify "core-done"
    ↓
[Refactor]  → /checkpoint create "refactor-done"
    ↓
[PR]        → /checkpoint verify "feature-start"
```

## Session End Usage

At end of session:

1. `/au-checkpoint create "session-end-0123"`
2. Update CLAUDE.md with progress
3. Commit and push
4. Note what to continue tomorrow

## When to Use

- Before major changes
- After completing a phase
- Before risky operations
- At end of work session

## Related Commands

- `/au-verify` - Check current state
- `/au-plan` - Plan next phase
- `/au-review` - Review changes
