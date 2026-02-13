---
name: research-orchestration
description: R&D research coordination skill. Use this when managing research projects, creating briefs for LLM analysis, consolidating findings, or driving hypothesis-based discovery. For R&D projects only.
---

# Research Orchestration Skill

Autonomous command center for R&D research. Analyze state, create briefs, consolidate findings, drive research forward.

## When to Use

Use when the user says:
- "What's next?" - Strategic analysis mode
- "RB-XXX outputs saved" - Consolidation mode
- "What's the status?" - Status check mode
- "Create a brief for [topic]" - Brief creation mode
- "Analyze research state" - Full state analysis

## File Locations

Research state is tracked in:

```
docs/
├── research/
│   ├── _state.yaml           # Current research state
│   ├── hypotheses.md         # Beliefs + confidence levels
│   ├── briefs/
│   │   ├── active/           # Currently being worked
│   │   └── completed/        # Finished briefs
│   └── findings/             # Consolidated outputs
└── knowledge/
    ├── _taxonomy.yaml        # Pattern index
    ├── patterns/             # Documented patterns
    ├── contexts/             # Environmental factors
    ├── domains/              # Platform specifics
    └── edge-cases/           # Unique instances
```

---

## Mode 1: Strategic Analysis ("What's next?")

When user asks what to work on next:

### Step 1: Read Current State

```bash
# Read these files to understand current position
cat docs/research/_state.yaml
cat docs/research/hypotheses.md
cat docs/knowledge/_taxonomy.yaml
```

### Step 2: Analyze Gaps and Priorities

Evaluate:
1. **Critical Questions** - What's blocking progress?
2. **Confidence Gaps** - Which hypotheses have low confidence?
3. **Pattern Gaps** - What patterns are incomplete?
4. **Dependencies** - What unblocks other work?

### Step 3: Make Strategic Decision

Choose the highest-impact research activity:

| Priority | Criteria |
|----------|----------|
| 1 | Blocks other work / Critical path |
| 2 | High uncertainty, high impact |
| 3 | Fills knowledge gap |
| 4 | Validates/invalidates hypothesis |

### Step 4: Create Brief Automatically

Generate a research brief in `docs/research/briefs/active/`:

```markdown
# RB-XXX: [Title]

## Objective
[What this research aims to discover]

## Background
[Current state of knowledge]

## Questions
1. [Specific question to answer]
2. [Specific question to answer]

## Method
[How to investigate - e.g., LLM analysis, code review, testing]

## Success Criteria
- [ ] [What constitutes completion]

## Context
[Files to read, prior research to reference]
```

### Step 5: Give Clear Instructions

```
I've created RB-XXX: [Title]

WHY: [Strategic reason - what this unblocks]
UNBLOCKS: [What decisions/work this enables]

ACTION REQUIRED:
1. Brief is at: docs/research/briefs/active/RB-XXX.md
2. [Instructions for completing the brief]
3. When done, tell me: "RB-XXX outputs saved"
```

---

## Mode 2: Consolidation ("RB-XXX outputs saved")

When user reports brief outputs are ready:

### Step 1: Validate Outputs Exist

```bash
ls docs/research/findings/
cat docs/research/findings/RB-XXX-*.md
```

### Step 2: Read and Synthesize

Read all outputs and identify:
- Key findings
- Patterns discovered
- Hypotheses confirmed/rejected
- New questions raised
- Knowledge to document

### Step 3: Update Research State

Update `docs/research/_state.yaml`:
```yaml
last_updated: YYYY-MM-DD
current_focus: "[New focus based on findings]"
completed_briefs:
  - RB-XXX
active_briefs: []
blockers: []
```

### Step 4: Update Hypotheses

Update `docs/research/hypotheses.md`:
```markdown
## Hypothesis: [Name]
**Status:** CONFIRMED / REJECTED / MODIFIED
**Confidence:** X/10 (was Y/10)
**Evidence:** [From RB-XXX findings]
```

### Step 5: Update Knowledge Taxonomy

If patterns/contexts/domains discovered:
1. Create files in `docs/knowledge/`
2. Update `_taxonomy.yaml`
3. Cross-reference with existing patterns

### Step 6: Move Brief to Completed

```bash
mv docs/research/briefs/active/RB-XXX.md docs/research/briefs/completed/
```

### Step 7: Decide Next Action

Either:
- Recommend next brief (return to Mode 1)
- Identify implementation ready items
- Flag blockers requiring user input

---

## Mode 3: Status Check ("What's the status?")

Quick overview of research state:

```markdown
## Research Status

**Last Updated:** YYYY-MM-DD
**Current Focus:** [From _state.yaml]

### Completed Briefs
- RB-001: [Title] - [Key outcome]
- RB-002: [Title] - [Key outcome]

### Active Briefs
- RB-003: [Title] - [Status]

### Hypothesis Confidence
| Hypothesis | Confidence | Last Updated |
|------------|------------|--------------|
| H1 | 8/10 | YYYY-MM-DD |
| H2 | 3/10 | YYYY-MM-DD |

### Knowledge State
- Patterns: X documented
- Contexts: X documented
- Domains: X documented
- Edge Cases: X logged

### Blockers
- [Any blockers from _state.yaml]

### Recommended Next
[Brief recommendation or action]
```

---

## Brief Numbering

Use sequential numbering: RB-001, RB-002, etc.

To find next number:
```bash
ls docs/research/briefs/active/ docs/research/briefs/completed/ | grep -oE 'RB-[0-9]+' | sort -t'-' -k2 -n | tail -1
```

---

## File Size Management

**IMPORTANT:** Always check file size before reading large files.

```bash
wc -w docs/research/findings/*.md
```

If over 15k words:
1. Read in chunks
2. Summarize sections before combining
3. Ask user to split if necessary

---

## Research Quality Principles

### Good Briefs
- Single focused objective
- Specific, answerable questions
- Clear success criteria
- Context for whoever executes

### Good Consolidation
- Extract patterns, not just facts
- Update knowledge taxonomy
- Update hypothesis confidence
- Identify next questions

### Anti-Patterns
- Creating briefs without checking _state.yaml
- Forgetting to update hypotheses after findings
- Not documenting discovered patterns
- Leaving briefs in active/ after completion

---

## Integration with Commands

| Command | When to Use |
|---------|-------------|
| `/au-learn` | After discovering a reusable pattern |
| `/rnd-debug` | When stuck on a specific problem |
| `/au-checkpoint` | After major research milestone |

---

**Remember:** Research is systematic knowledge building. Every brief should either confirm/reject a hypothesis, discover a pattern, or refine understanding. Random exploration without documentation is waste.
