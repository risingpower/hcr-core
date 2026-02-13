#!/usr/bin/env node
/**
 * Stop hook: Audit all git-modified Python files for print()
 * Triggered: After every Claude response
 * Purpose: Catch print() across all modified files, not just the one being edited
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function isGitRepo() {
  try {
    execSync('git rev-parse --git-dir', { stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

function getModifiedFiles() {
  try {
    // Get both staged and unstaged modified files
    const result = execSync('git diff --name-only HEAD 2>/dev/null || git diff --name-only', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe']
    });
    return result.split('\n').filter(Boolean);
  } catch {
    return [];
  }
}

function checkFile(filePath) {
  if (!fs.existsSync(filePath)) return [];

  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const matches = [];

  lines.forEach((line, idx) => {
    // Match print( but not if commented out or in legitimate contexts
    if (/\bprint\s*\(/.test(line) && !/^\s*#/.test(line) && !/def print/.test(line) && !/["'].*print.*["']/.test(line)) {
      matches.push({ line: idx + 1, content: line.trim() });
    }
  });

  return matches;
}

// Main
if (!isGitRepo()) {
  process.exit(0);
}

const modifiedFiles = getModifiedFiles().filter(f => f.endsWith('.py'));

if (modifiedFiles.length === 0) {
  process.exit(0);
}

const findings = [];

for (const file of modifiedFiles) {
  const matches = checkFile(file);
  if (matches.length > 0) {
    findings.push({ file, matches });
  }
}

if (findings.length > 0) {
  console.error(`[Hook] print() audit: ${findings.length} file(s) with print()`);
  findings.forEach(({ file, matches }) => {
    const fileName = path.basename(file);
    console.error(`  ${fileName}: ${matches.length} occurrence(s)`);
  });
}
