#!/usr/bin/env node
/**
 * SessionEnd hook: Save personal session context
 * Captures your commits, uncommitted work, and working state for next session
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

// Run git command safely
function git(cmd) {
  try {
    return execSync(`git ${cmd}`, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }).trim();
  } catch (e) {
    return '';
  }
}

const repoName = getRepoName();
const today = new Date().toISOString().split('T')[0];
const currentTime = new Date().toTimeString().slice(0, 5);

// Create repo-specific sessions directory
const sessionsDir = path.join(os.homedir(), '.claude', 'sessions', repoName);
fs.mkdirSync(sessionsDir, { recursive: true });

const sessionFile = path.join(sessionsDir, `${today}.md`);
const stateFile = path.join(sessionsDir, 'STATE.md');

// Gather context
const branch = git('branch --show-current');
const uncommitted = git('status --short');
const myCommits = git('log --oneline -10 --since="12 hours ago"');

// Format sections
const uncommittedSection = uncommitted
  ? uncommitted.split('\n').map(f => `- ${f}`).join('\n')
  : '- None';

const commitsSection = myCommits
  ? myCommits.split('\n').map(c => `- ${c}`).join('\n')
  : '- None today';

// Check if file exists to preserve notes
let existingNotes = '-';
if (fs.existsSync(sessionFile)) {
  const content = fs.readFileSync(sessionFile, 'utf8');
  const notesMatch = content.match(/## Notes\n([\s\S]*?)$/);
  if (notesMatch && notesMatch[1].trim()) {
    existingNotes = notesMatch[1].trim();
  }
}

const template = `# ${today} - ${repoName}
**Branch:** ${branch || 'N/A'}
**Last updated:** ${currentTime}

## Uncommitted Changes
${uncommittedSection}

## Today's Commits
${commitsSection}

## Notes
${existingNotes}
`;

fs.writeFileSync(sessionFile, template);
console.error(`[Session] Saved to ~/.claude/sessions/${repoName}/${today}.md`);

// --- STATE.md: Persistent working memory ---

// Read existing STATE.md to preserve manually-added content
let existingState = {
  focus: null,
  blockers: '- None',
  decisions: '- None',
  nextSession: '- Continue from current branch'
};

if (fs.existsSync(stateFile)) {
  const stateContent = fs.readFileSync(stateFile, 'utf8');

  // Extract existing sections
  const focusMatch = stateContent.match(/\*\*Focus:\*\* (.+)/);
  if (focusMatch) existingState.focus = focusMatch[1];

  const blockersMatch = stateContent.match(/## Blockers\n([\s\S]*?)(?=\n##|$)/);
  if (blockersMatch && blockersMatch[1].trim()) existingState.blockers = blockersMatch[1].trim();

  const decisionsMatch = stateContent.match(/## Decisions This Session\n([\s\S]*?)(?=\n##|$)/);
  if (decisionsMatch && decisionsMatch[1].trim()) existingState.decisions = decisionsMatch[1].trim();

  const nextMatch = stateContent.match(/## Next Session\n([\s\S]*?)(?=\n##|$)/);
  if (nextMatch && nextMatch[1].trim()) existingState.nextSession = nextMatch[1].trim();
}

// Auto-detect focus from branch name if not manually set
let focus = existingState.focus;
if (!focus && branch) {
  // Convert branch name to readable format
  // e.g., "feat/add-user-auth" -> "Add user auth (feat)"
  const branchParts = branch.split('/');
  if (branchParts.length > 1) {
    const type = branchParts[0];
    const description = branchParts.slice(1).join('/').replace(/-/g, ' ');
    focus = `${description.charAt(0).toUpperCase() + description.slice(1)} (${type})`;
  } else if (branch !== 'main' && branch !== 'master') {
    focus = branch.replace(/-/g, ' ');
  } else {
    focus = 'General work on main branch';
  }
}

const stateTemplate = `# Working State: ${repoName}

**Last updated:** ${today} ${currentTime}
**Focus:** ${focus}

## Blockers
${existingState.blockers}

## Decisions This Session
${existingState.decisions}

## Next Session
${existingState.nextSession}
`;

fs.writeFileSync(stateFile, stateTemplate);
console.error(`[Session] State saved to ~/.claude/sessions/${repoName}/STATE.md`);

// Cleanup old session files (keep last 7 days, but never delete STATE.md)
try {
  const files = fs.readdirSync(sessionsDir)
    .filter(f => f.endsWith('.md') && f !== 'STATE.md')
    .sort()
    .reverse();
  files.slice(7).forEach(oldFile => {
    fs.unlinkSync(path.join(sessionsDir, oldFile));
  });
  if (files.length > 7) {
    console.error(`[Session] Cleaned up ${files.length - 7} old session file(s)`);
  }
} catch (e) {
  // Ignore cleanup errors
}
