---
description: Create implementation plan for a feature. Restates requirements, assesses risks, and creates step-by-step plan. WAITS for confirmation before any code changes.
---

# /au-plan Command

This command invokes the **planner** agent to create a comprehensive implementation plan.

## What This Command Does

1. **Restate Requirements** - Clarify what needs to be built
2. **Identify Risks** - Surface potential issues and blockers
3. **Create Step Plan** - Break down implementation into phases
4. **Wait for Confirmation** - MUST receive user approval before proceeding

## When to Use

Use `/au-plan` when:
- Starting a new feature
- Making architectural changes
- Complex refactoring
- Multiple files/components affected
- Requirements are unclear

## How It Works

The planner agent will:

1. **Check for CONTEXT.md** - Load locked decisions from `/au-discuss` if present
2. **Analyze** the request and restate requirements
3. **Break down** into phases with specific steps
4. **Identify** dependencies between components
5. **Assess** risks and blockers
6. **Present** the plan and WAIT for confirmation

## Context Integration

If `docs/context/{feature}-CONTEXT.md` exists:
- Load locked decisions as constraints
- Reference them in the plan
- Do not contradict decided preferences

Run `/au-discuss {feature}` first to capture preferences before planning.

## Example

```
User: /plan Add user notifications when tasks complete

Agent (planner):
# Implementation Plan: Task Completion Notifications

## Requirements
- Send notification when task status changes to "completed"
- Support in-app and email channels
- Include task details in notification

## Implementation Steps
...

**WAITING FOR CONFIRMATION**: Proceed with this plan? (yes/no/modify)
```

## CRITICAL

The planner will **NOT** write any code until you explicitly confirm.

Modify with:
- "modify: [your changes]"
- "different approach: [alternative]"
- "skip phase X"

## After Planning

- Use `/au-verify` to check current state
- Use `/au-review` after implementation
- Use `/au-fix` if build errors occur
