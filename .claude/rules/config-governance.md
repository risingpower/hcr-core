# Claude Code Configuration Governance

## Source of Truth

All Claude Code configuration comes from the centralized templates at `/dev/_claude-templates/`.

**DO NOT:**
- Install marketplace plugins (`~/.claude/plugins/marketplaces/`)
- Add custom commands/agents/rules without approval
- Modify scaffolded `.claude/` files directly (changes will be overwritten)

**DO:**
- Use `/scaffold <repo>` to get the latest config
- Request new commands/agents via the template system
- Use `settings.local.json` for personal preferences only

## Why This Matters

1. **Consistency** - All engineers have identical Claude behavior
2. **No Conflicts** - Marketplace plugins can override project commands
3. **Maintainability** - One place to update, scaffold to all repos
4. **Onboarding** - New engineers get the same setup instantly

## Allowed Customization

### `settings.local.json` (gitignored)
Personal preferences only:
```json
{
  "preferences": {
    "verbosity": "concise"
  }
}
```

### NOT Allowed
- Installing plugins: `claude plugins install ...`
- Adding to `~/.claude/commands/`, `~/.claude/agents/`, etc.
- Modifying repo `.claude/` files directly

## Requesting New Features

If you need a command/agent that doesn't exist:

1. Check `_claude-templates/` for existing options
2. If missing, request addition via PR to `_claude-templates/`
3. Once merged, run `/scaffold <repo>` to get it

## Enforcement

If you see unexpected commands or behavior:
1. Check `~/.claude/plugins/` - should be empty or minimal
2. Run `/scaffold <repo>` to reset to standard config
3. Report conflicts to the team
