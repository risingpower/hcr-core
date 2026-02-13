# MCP Server Setup Guide

MCP (Model Context Protocol) servers extend Claude Code's capabilities with external integrations. This guide covers setup for AUDITSU projects.

## Overview

MCP servers are configured in `~/.claude.json` (user-level) or `.claude/settings.json` (project-level).

**Key principle:** Only enable MCPs you actively use. Each MCP adds context overhead.

---

## Available MCPs

### Tier 2: As Needed

Enable these when you need them, disable when not in use.

| MCP | Purpose | When to Enable |
|-----|---------|----------------|
| `customerio` | Segments, user debugging, SDK setup | Working on Customer.io integration |
| `stripe` | Customers, subscriptions, refunds | Working on billing features |

### Tier 3: Evaluate

Try these if you hit specific problems they solve.

| MCP | Purpose | When to Try |
|-----|---------|-------------|
| `context7` | Live framework documentation | If Claude hallucinates APIs |
| `github` | PR/issue operations | If `gh` CLI feels limiting |

### Not Recommended for AUDITSU

| MCP | Why Not |
|-----|---------|
| `vercel` | We use Digital Ocean, not Vercel |
| `railway` | Not used |
| `supabase` | site-be uses PostgreSQL directly |
| `memory` | R&D uses git-versioned `docs/knowledge/` instead |
| `sequential-thinking` | Claude already does chain-of-thought |
| `filesystem` | Claude Code has built-in file operations |

---

## Setup Instructions

### Step 1: Create/Edit ~/.claude.json

```bash
# Check if file exists
cat ~/.claude.json

# If not, create it
echo '{}' > ~/.claude.json
```

### Step 2: Add MCP Configuration

**Customer.io (when needed):**

```json
{
  "mcpServers": {
    "customerio": {
      "type": "http",
      "url": "https://mcp.customer.io/mcp"
    }
  }
}
```

For EU accounts, use: `https://mcp-eu.customer.io/mcp`

**Prerequisites:**
- Paid Claude plan required
- Customer.io admin must enable in Settings > Privacy, Data, & AI

**Stripe (when needed):**

```json
{
  "mcpServers": {
    "stripe": {
      "type": "http",
      "url": "https://mcp.stripe.com"
    }
  }
}
```

**Context7 (for documentation lookup):**

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

Free tier available. Get API key at context7.com for higher rate limits.

**GitHub (if needed beyond gh CLI):**

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_PAT"
      }
    }
  }
}
```

Requires PAT with `repo`, `read:org`, `read:user` scopes.

---

## Per-Project Configuration

### Disabling MCPs for Specific Projects

Add to `.claude/settings.json`:

```json
{
  "disabledMcpServers": ["customerio"]
}
```

### Project-Specific MCPs

Add to `.claude/settings.local.json` (gitignored):

```json
{
  "mcpServers": {
    "stripe": {
      "type": "http",
      "url": "https://mcp.stripe.com"
    }
  }
}
```

---

## R&D Projects (ariadne)

**Don't use the memory MCP.** Ariadne has its own git-versioned knowledge system:

```
docs/knowledge/
├── _taxonomy.yaml    # Machine-readable pattern index
├── hypotheses.md     # Confidence tracking
├── patterns/         # Documented patterns
├── contexts/         # Environmental factors
└── domains/          # Platform specifics
```

This is better than the memory MCP because:
- Version controlled (git history)
- Structured for the domain
- Human-readable and editable
- Shared across sessions via commits

---

## Troubleshooting

### MCP Not Loading

1. Check `npx` is available: `which npx`
2. Verify JSON syntax: `cat ~/.claude.json | jq .`
3. Check Claude Code logs for errors

### Customer.io Permission Errors

1. Verify you have a paid Claude plan
2. Check Customer.io admin enabled MCP in Privacy settings
3. Verify correct URL (EU vs US)

### Context Window Issues

If Claude is running slow or hitting context limits:
1. Disable unused MCPs
2. Only enable MCPs when actively using them

---

## Documentation Links

- [Customer.io MCP](https://docs.customer.io/ai/mcp-server/)
- [Stripe MCP](https://docs.stripe.com/mcp)
- [Context7](https://upstash.com/blog/context7-mcp)
- [GitHub MCP](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/use-the-github-mcp-server)

---

*Last updated: 2026-01-24*
