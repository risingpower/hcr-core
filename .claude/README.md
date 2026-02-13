# Claude Code Configuration (R&D Project)

This directory contains Claude Code configuration for this R&D repository.

## Getting Started

```bash
# Install Claude Code CLI (if not already installed)
npm install -g @anthropic-ai/claude-code

# Start a session in this repo
claude
```

Once running, try `/au-map` to understand the codebase or `/au-proto <task>` to start working.

## Available Commands

### Standard Commands

| Command | Description |
|---------|-------------|
| `/au-proto` | Rapid prototyping. Quick scan, skip planning, atomic commits. |
| `/au-discuss` | Capture preferences before planning. Outputs CONTEXT.md. |
| `/au-map` | Extract codebase conventions and patterns for context. |
| `/au-plan` | Create implementation plan before coding. **Waits for your confirmation.** |
| `/au-fresh` | Fresh context execution. Manual (handoff) or auto (subagent). |
| `/au-review` | Review uncommitted changes for quality and security issues. |
| `/au-verify` | Run full verification: mypy, ruff, pytest. |
| `/au-fix` | Incrementally fix type/lint errors with minimal changes. |
| `/au-checkpoint` | Create a checkpoint commit for session management. |

### R&D-Specific Commands

| Command | Description |
|---------|-------------|
| `/au-learn` | Extract and document learnings from current session. Captures patterns for future reference. |
| `/rnd-debug` | Invoke the 5-level debugging protocol when stuck on a problem. |

### When to Use Each Command

- **Small, clear task?** Run `/au-proto` for quick implementation
- **Unclear requirements?** Run `/au-discuss` to capture preferences
- **Unfamiliar codebase?** Run `/au-map` to understand conventions
- **Complex feature?** Run `/au-plan` for full planning
- **Context getting heavy?** Run `/au-fresh` for clean context
- **Stuck on a problem?** Run `/rnd-debug` to work through systematically
- **Solved something tricky?** Run `/au-learn` to capture the pattern
- **Before committing?** Run `/au-review`
- **Taking a break?** Run `/au-checkpoint`

## R&D Methodology

This project uses **pattern-centric knowledge tracking**:

```
Knowledge compounds when documented.
Track patterns, not individual instances.
```

### The Five Levels of Knowledge

1. **Patterns** - Recurring phenomena (e.g., "toggle", "drawer")
2. **Variants** - Pattern subtypes (e.g., "toolbar-toggle", "nav-drawer")
3. **Contexts** - Environmental factors (e.g., "dark-mode", "low-memory")
4. **Domains** - Platform specifics (e.g., "android-14", "samsung-one-ui")
5. **Edge Cases** - Truly unique instances (flag for review)

### Debugging Protocol (`/rnd-debug`)

When stuck, work through levels systematically:

```
Level 1: Does standard pattern handling work?
Level 2: Is this a known variant?
Level 3: What environmental factors are present?
Level 4: Are there platform-specific behaviors?
Level 5: Is this truly unique? (Document as edge case)
```

### Knowledge Structure

```
docs/
├── knowledge/           # Pattern taxonomy
│   ├── _taxonomy.yaml   # Machine-readable index
│   ├── patterns/        # Level 1
│   ├── contexts/        # Level 3
│   ├── domains/         # Level 4
│   └── edge-cases/      # Level 5
├── research/            # Hypothesis-driven discovery
│   ├── _state.yaml      # Current state
│   └── hypotheses.md    # Beliefs + confidence
└── decisions/           # ADRs
```

## Skills (Methodology Reference)

Detailed workflow documentation is available in `.claude/skills/`:

| Skill | When to Use |
|-------|-------------|
| `tdd-workflow.md` | Writing new features, fixing bugs, or refactoring. TDD methodology. |
| `security-review.md` | Implementing auth, handling user input, creating APIs, or working with sensitive data. |
| `research-orchestration.md` | Managing research briefs, consolidating findings, driving hypothesis-based discovery. |
| `pattern-navigator.md` | Navigating the knowledge taxonomy during debugging sessions. |

Read these files when you need detailed guidance on a methodology.

## Automated Hooks

| Hook | Trigger | What It Does |
|------|---------|--------------|
| **print() warning** | After editing `.py` files | Warns if print statements are added |
| **Session persistence** | Session start/end | Saves context for continuity |
| **Pre-compact** | Before context compaction | Preserves state |

### Session Continuity

R&D sessions benefit from context persistence:
- **Session start**: Loads previous session context
- **Session end**: Saves state and extracts patterns
- **Pre-compact**: Preserves state before summarization

## MCP Server Setup

MCP servers extend Claude Code with external integrations (GitHub, memory, etc.).

**Setup guide:** See `.claude/docs/mcp-setup.md` for:
- Recommended MCPs for this project
- How to configure `~/.claude.json`
- Per-project MCP settings

**Recommended for R&D projects:** GitHub + Memory MCPs
```json
// Add to ~/.claude.json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "your-pat" }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

## Personal Settings

Create `.claude/settings.local.json` (gitignored) for personal preferences:

```json
{
  "preferences": {
    "verbosity": "concise"
  }
}
```

## Contributing Improvements

You can improve `.claude/` files in this repo:

1. Make your improvement and test it works
2. Commit and push your changes
3. Central review will roll out good changes to other repos

Use `settings.local.json` (gitignored) for personal preferences that shouldn't be shared.

**R&D note:** Document patterns, not instances - use `/au-learn` after solving problems.

## Directory Structure

```
.claude/
├── agents/           # Specialized agents (planner, code-reviewer, au-executor, gsd-architect, etc.)
├── commands/         # Command definitions (includes R&D commands)
├── docs/             # Documentation (MCP setup, etc.)
├── rules/            # Always-active guidelines (includes rnd-methodology)
├── skills/           # Methodology reference docs (includes R&D skills)
├── scripts/hooks/    # Automation scripts
├── settings.json     # Team settings (don't modify)
├── settings.local.json  # Your personal settings (gitignored)
└── README.md         # This file
```

## Getting Help

- **Command not working?** Check that the file has correct frontmatter (`---` block)
- **Need a new feature?** Request changes to central templates
- **Hook causing issues?** Check `.claude/settings.json` for hook configuration
- **R&D methodology questions?** See `docs/knowledge/_taxonomy.md` or methodology docs
