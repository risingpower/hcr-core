---
description: Fresh context execution. Manual mode generates handoff block; auto mode spawns Task subagent with fresh 200k context.
---

# /au-fresh Command

Execute tasks with fresh context - either manually (handoff block) or automatically (Task subagent).

## What This Command Does

**Manual Mode (default):**
1. Generate copyable handoff block
2. User starts new session and pastes

**Auto Mode:**
1. Pre-read relevant files (content inlining)
2. Spawn Task subagent with fresh context
3. Collect results and update STATE.md

## Usage

```
/au-fresh <task>                      # Prompt: Manual or Auto?
/au-fresh --manual <task>             # Generate handoff block
/au-fresh --auto <task>               # Spawn single Task subagent
/au-fresh --auto --parallel <tasks>   # Multiple parallel subagents
/au-fresh --team <task>               # Spawn Agent Team for complex interdependent work
/au-fresh --checkpoint <task>         # Create checkpoint first (either mode)
```

## When to Use Each Mode

| Mode | Best For |
|------|----------|
| Manual | Exploratory work, want to steer, learning codebase |
| Auto | Well-defined tasks, throughput, routine implementation |
| Auto + Parallel | Multiple independent tasks (e.g., "fix bugs #1, #2, #3") |
| Team | Complex interdependent tasks requiring coordination (e.g., refactors touching multiple modules) |

---

## Manual Mode

Generate a copyable handoff block for starting a new session.

### Workflow

```
You: /au-fresh --manual Implement form validation

Claude generates:
┌────────────────────────────────────────────────┐
│ ## Fresh Start: Implement form validation      │
│                                                │
│ **Context:**                                   │
│ Adding client-side validation to signup form.  │
│                                                │
│ **Relevant files:**                            │
│ - src/components/SignupForm.tsx                │
│ - src/utils/validation.ts                      │
│                                                │
│ **Key decisions:**                             │
│ - Using Zod for schema validation              │
│                                                │
│ **Continue with:**                             │
│ - Add email format validation                  │
│ - Add password strength rules                  │
│                                                │
│ **Uncommitted changes:** No                    │
└────────────────────────────────────────────────┘

Copy this block, start a new Claude session, and paste to begin.
```

### After Running Manual Mode

1. **Copy** the handoff block
2. **Start** a new Claude Code session
3. **Paste** the block as your first message
4. **Continue** working with fresh context

---

## Auto Mode

Spawn a Task subagent with fresh context to execute the task automatically.

### Workflow

```
You: /au-fresh --auto Implement form validation

Claude:
Spawning fresh executor for: Implement form validation

Reading context...
✓ STATE.md loaded (2 decisions)
✓ Relevant files identified: 3 files
✓ Content inlined for Task boundary

[Spawning Task subagent with au-executor...]

--- Executor Output ---
Completed: Implement form validation

Commits:
- abc1234: feat: add email validation to SignupForm
- def5678: feat: add password strength validation

Files modified:
- src/utils/validation.ts
- src/components/SignupForm.tsx

Verification:
- ✓ Build passes
- ✓ Types clean
-----------------------

✓ STATE.md updated with results
```

### How Auto Mode Works

1. **Gather Context:**
   - Read STATE.md for focus/decisions
   - Identify relevant files from git activity
   - Check for uncommitted changes

2. **Content Inlining (Critical):**
   - Pre-read all relevant files
   - Inline content into Task prompt
   - File references (`@file`) don't work across Task boundaries

3. **Spawn Executor:**
   ```
   Task(
     prompt="[Inlined context + task + files]",
     subagent_type="au-executor",
     description="Fresh execute: {task}"
   )
   ```

4. **Collect Results:**
   - Parse executor output (commits, files, verification)
   - Update STATE.md with completion status
   - Report summary to user

### Content Inlining Example

```markdown
## Task: Implement form validation

## Context
Adding client-side validation to signup form.

## Decisions (from STATE.md)
- Using Zod for schema validation
- Inline error messages

## File Contents

### src/utils/validation.ts
\`\`\`typescript
{actual file content here}
\`\`\`

### src/components/SignupForm.tsx
\`\`\`typescript
{actual file content here}
\`\`\`

## Instructions
1. Implement the task
2. Make atomic commits
3. Run verification
4. Return structured result
```

---

## Auto Parallel Mode

Execute multiple independent tasks simultaneously.

### Workflow

```
You: /au-fresh --auto --parallel "Fix login bug" "Add logout button" "Update error messages"

Claude:
Spawning 3 parallel executors...

[Task 1: Fix login bug]
[Task 2: Add logout button]
[Task 3: Update error messages]

All tasks running in parallel...

--- Results ---

Task 1: Fix login bug
✓ Complete - 1 commit (abc1234)

Task 2: Add logout button
✓ Complete - 2 commits (def5678, ghi9012)

Task 3: Update error messages
✓ Complete - 1 commit (jkl3456)

Total: 3 tasks, 4 commits, 0 failures
```

### Parallel Execution Rules

1. **Independence Required** - Tasks must not depend on each other
2. **Single Message** - All Task calls in one message for true parallelism
3. **Isolated Contexts** - Each executor gets fresh 200k context
4. **Aggregated Results** - Orchestrator collects all outputs

---

## Team Mode

Leverage Agent Teams (Opus 4.6) for complex tasks where subtasks are interdependent and benefit from direct agent-to-agent coordination.

### How It Differs from Parallel Mode

| Aspect | Parallel Mode | Team Mode |
|--------|--------------|-----------|
| Independence | Tasks must be independent | Tasks can be interdependent |
| Communication | No inter-agent communication | Agents message directly |
| Coordination | Orchestrator aggregates results | Agents self-coordinate |
| Context | Isolated 200k per executor | Separate sessions, shared task list |
| Best for | "Fix bugs 1, 2, 3" | "Refactor auth across API + frontend" |

### Workflow

```
You: /au-fresh --team Refactor authentication to use JWT

Claude:
Spawning Agent Team for: Refactor authentication to use JWT

Team Lead analyzing task decomposition...
- Teammate 1: Backend JWT token service + middleware
- Teammate 2: Frontend auth context + token storage
- Teammate 3: API endpoint migration + tests

Agents coordinating...

--- Team Results ---
Teammate 1: Backend JWT service
✓ Complete - 3 commits

Teammate 2: Frontend auth updates
✓ Complete - 2 commits (coordinated with Teammate 1 on token format)

Teammate 3: API migration
✓ Complete - 4 commits (cross-validated with Teammates 1 & 2)

Total: 3 agents, 9 commits, 0 conflicts
```

### When to Use Team Mode

- Refactoring that spans multiple modules with shared interfaces
- Feature implementation requiring frontend + backend coordination
- Large code reviews benefiting from cross-validation
- Tasks where agents need to share discoveries and challenge findings

### Requirements

- Opus 4.6 model access
- Agent Teams enabled in Claude Code settings (research preview — expect iteration)

---

## Mode Selection Guide

If no flag provided, ask the user:

```
Fresh context for: Implement form validation

How would you like to proceed?

[1] Manual - Generate handoff block (you control the new session)
[2] Auto - Spawn executor subagent (runs autonomously)
[3] Team - Spawn Agent Team (agents coordinate directly, best for interdependent work)

Choose [1/2/3]:
```

### Decision Factors

| Factor | Suggests Manual | Suggests Auto | Suggests Team |
|--------|-----------------|---------------|---------------|
| Task clarity | Exploratory, unclear | Well-defined | Well-defined, multi-part |
| User involvement | Want to steer/learn | Trust automation | Trust automation |
| Task count | Single complex task | Multiple routine tasks | Multiple interdependent tasks |
| Risk level | High-risk changes | Low-risk, reversible | Medium-risk, coordinated |
| Dependencies | N/A | Tasks independent | Tasks share interfaces |

---

## Flags Reference

| Flag | Effect |
|------|--------|
| `--manual` | Generate handoff block only |
| `--auto` | Spawn Task subagent |
| `--parallel` | With --auto, spawn multiple subagents |
| `--team` | Spawn Agent Team (Opus 4.6, research preview) |
| `--checkpoint` | Create checkpoint before execution |

---

## What Transfers to Fresh Context

**Both modes transfer:**
- Task description
- Key decisions from STATE.md
- Relevant file paths

**Auto mode additionally transfers:**
- Actual file contents (inlined)
- Verification expectations

**Never transfers:**
- Full conversation history
- Debugging context
- Accumulated assumptions

---

## STATE.md Updates

### After Manual Mode
```markdown
## Next Session
- Handoff prepared: Implement form validation
- Mode: manual
- Checkpoint: pre-fresh-20260130-1430 (if used)
```

### After Auto Mode
```markdown
## Decisions This Session
- [Auto] Implement form validation: Complete
  - Commits: abc1234, def5678
  - Files: validation.ts, SignupForm.tsx

## Next Session
- Continue from auto-executed task
```

---

## Related Commands

- `/au-checkpoint` - Create point-in-time snapshot
- `/au-proto` - Quick implementation without fresh context
- `/au-plan` - Full planning before implementation
- `/context` - Check current context usage
