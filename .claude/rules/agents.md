# Agent Usage Guidelines

## Available Agents

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| `planner` | Implementation planning | Before starting new features or major changes |
| `code-reviewer` | Code quality review | After writing code, before committing |
| `build-resolver` | Fix build/type errors | When build or type check fails |
| `tdd-guide` | Test-driven development | When writing tests or new features |
| `security-reviewer` | Security vulnerability scan | After auth, API, or data handling code |
| `architect` | System design decisions | For architectural changes or new features |

## When to Use Which Agent

### Starting New Work
1. **First:** Use `planner` to create implementation plan
2. **During:** Use `tdd-guide` for test-first development
3. **After:** Use `code-reviewer` before committing

### Fixing Issues
1. **Build errors:** Use `build-resolver`
2. **Security concerns:** Use `security-reviewer`
3. **Code quality:** Use `code-reviewer`

### Architectural Decisions
1. **New features:** Use `architect` then `planner`
2. **Major refactoring:** Use `architect` for design
3. **Technology choices:** Use `architect` for evaluation

## Agent Invocation via Commands

| Command | Invokes Agent | Purpose |
|---------|---------------|---------|
| `/au-plan` | planner | Create implementation plan |
| `/au-review` | code-reviewer | Review code quality |
| `/au-fix` | build-resolver | Fix build errors |
| `/au-tdd` | tdd-guide | Test-driven development |
| `/au-security` | security-reviewer | Security review |

## Agent Behavior Rules

### planner
- **WAITS** for user confirmation before any code changes
- Creates detailed step-by-step plans
- Identifies risks and dependencies

### code-reviewer
- Reviews changed files (via `git diff`)
- Classifies issues by severity
- Provides APPROVE/WARNING/BLOCK verdict

### build-resolver
- Focuses on minimal fixes
- One error at a time
- Verifies fix before moving on

### tdd-guide
- Writes tests BEFORE implementation
- Verifies test fails first
- Keeps implementation minimal

### security-reviewer
- **READ-ONLY** - reports only, no modifications
- Checks for OWASP vulnerabilities
- Provides remediation recommendations

### architect
- Analyzes trade-offs
- Considers existing patterns
- Documents decisions (ADRs)

## R&D Projects Only

Additional agents/commands for R&D:

| Command | Purpose |
|---------|---------|
| `/au-learn` | Extract patterns from debugging sessions |
| `/rnd-debug` | 5-level debugging escalation |

## Agent Model Selection

Opus 4.6 supports adaptive thinking with effort levels (low/medium/high/max) that control reasoning depth vs speed/cost tradeoffs. The `budget_tokens` parameter is deprecated in favor of adaptive thinking + effort.

| Agent | Model | Effort | Rationale |
|-------|-------|--------|-----------|
| planner | opus | high | Complex reasoning for plans |
| code-reviewer | opus | max | Security accuracy critical |
| build-resolver | opus | high | Code modification accuracy |
| tdd-guide | opus | high | Code generation quality |
| security-reviewer | opus | max | Security detection critical |
| architect | opus | high | Design decision quality |
| au-executor | opus | medium | Better quality at controlled cost |

## Agent Teams (Research Preview)

**What are Agent Teams?**
Agent Teams are independent Claude Code sessions that coordinate directly with each other, rather than subagents that return to a parent orchestrator. Each agent has its own context window and can message peers directly.

**Agent Teams vs Task Subagents**

| Aspect | Task Subagents | Agent Teams |
|--------|----------------|-------------|
| Use Case | Quick focused tasks | Complex parallel work |
| Context | Shared session context | Separate context per agent |
| Coordination | Parent orchestrates | Self-coordinating |
| Communication | Return results to parent | Peer-to-peer messaging |
| Best For | Single-file fixes, small scoped work | Multi-file refactors, distributed reviews |

**Best Use Cases for AUDITSU**
- Large codebase reviews (multiple reviewers working in parallel)
- Complex multi-file refactors (each agent owns a module)
- Cross-module feature implementation (frontend + backend + tests)

**Configuration**
Agent Teams is a research preview feature in Claude Code. Enable via your Claude Code settings when available.

**Best Practices**
- Start with 2-4 agents (avoid over-coordination overhead)
- Define clear scope boundaries for each agent
- Use cross-validation between agents for critical work
- Note: This is a research preview feature and may change

## Anti-Patterns

### Don't Skip Planning
```
BAD: "Just start coding the feature"
GOOD: "/au-plan Add user notifications"
```

### Don't Skip Review
```
BAD: Commit directly after writing code
GOOD: "/au-review" before every commit
```

### Don't Ignore Security
```
BAD: Skip security review on "simple" changes
GOOD: "/au-security" after any auth/API/data code
```
