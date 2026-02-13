#!/usr/bin/env node
/**
 * SessionStart hook: Personal session continuity
 * Shows working state, uncommitted changes, and previous session context
 */

const path = require('path');
const fs = require('fs');
const os = require('os');
const { execSync } = require('child_process');

// Get repo name
function getRepoName() {
  try {
    const toplevel = execSync('git rev-parse --show-toplevel', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
    return path.basename(toplevel);
  } catch (e) {
    return path.basename(process.cwd());
  }
}

// Get current uncommitted changes
function getUncommitted() {
  try {
    return execSync('git status --short', { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
  } catch (e) {
    return '';
  }
}

const repoName = getRepoName();
const sessionsDir = path.join(os.homedir(), '.claude', 'sessions', repoName);
const stateFile = path.join(sessionsDir, 'STATE.md');

// Reset edit counter for fresh session
const editCountFile = path.join(os.homedir(), '.claude', 'sessions', '.edit-count');
try {
  if (fs.existsSync(editCountFile)) {
    fs.unlinkSync(editCountFile);
  }
} catch (e) {
  // Ignore
}

let hasOutput = false;

// --- STATE.md: Show working state first (most important context) ---
if (fs.existsSync(stateFile)) {
  const stateContent = fs.readFileSync(stateFile, 'utf8');

  // Extract focus
  const focusMatch = stateContent.match(/\*\*Focus:\*\* (.+)/);
  if (focusMatch && focusMatch[1]) {
    console.error(`\n[State] Focus: ${focusMatch[1]}`);
    hasOutput = true;
  }

  // Extract blockers (only show if not "- None")
  const blockersMatch = stateContent.match(/## Blockers\n([\s\S]*?)(?=\n##|$)/);
  if (blockersMatch) {
    const blockers = blockersMatch[1].trim().split('\n').filter(l => l.trim() && l.trim() !== '- None' && l.trim() !== '-');
    if (blockers.length > 0) {
      console.error(`[State] Blockers:`);
      blockers.forEach(line => console.error(`  ${line}`));
      hasOutput = true;
    }
  }

  // Extract next session hints
  const nextMatch = stateContent.match(/## Next Session\n([\s\S]*?)(?=\n##|$)/);
  if (nextMatch) {
    const nextItems = nextMatch[1].trim().split('\n').filter(l => l.trim() && l.trim() !== '-');
    if (nextItems.length > 0) {
      console.error(`[State] Continue with:`);
      nextItems.slice(0, 3).forEach(line => console.error(`  ${line}`));
      if (nextItems.length > 3) {
        console.error(`  ... and ${nextItems.length - 3} more`);
      }
      hasOutput = true;
    }
  }
}

// Show current uncommitted changes
const uncommitted = getUncommitted();
if (uncommitted) {
  console.error(`\n[Session] Uncommitted changes in ${repoName}:`);
  uncommitted.split('\n').slice(0, 5).forEach(line => {
    console.error(`  ${line}`);
  });
  const lines = uncommitted.split('\n');
  if (lines.length > 5) {
    console.error(`  ... and ${lines.length - 5} more`);
  }
  hasOutput = true;
}

// Find most recent session file for this repo (excluding STATE.md)
let sessionFile = null;
if (fs.existsSync(sessionsDir)) {
  try {
    const files = fs.readdirSync(sessionsDir)
      .filter(f => f.endsWith('.md') && f !== 'STATE.md')
      .sort()
      .reverse();
    if (files.length > 0) {
      sessionFile = path.join(sessionsDir, files[0]);
    }
  } catch (e) {
    // Ignore
  }
}

// Show previous session notes if they exist
if (sessionFile && fs.existsSync(sessionFile)) {
  const content = fs.readFileSync(sessionFile, 'utf8');
  const fileName = path.basename(sessionFile, '.md');

  // Extract notes section
  const notesMatch = content.match(/## Notes\n([\s\S]*?)(?=\n##|$)/);
  if (notesMatch) {
    const notes = notesMatch[1].trim().split('\n').filter(l => l.trim() && l.trim() !== '-');
    if (notes.length > 0) {
      console.error(`\n[Session] Notes from ${fileName}:`);
      notes.forEach(line => console.error(`  ${line}`));
      hasOutput = true;
    }
  }
}

if (hasOutput) {
  console.error('');
}
