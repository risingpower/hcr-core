#!/usr/bin/env node
/**
 * PostToolUse hook: Log PR URL after gh pr create
 * Triggered after: Bash command matching "gh pr create"
 * Purpose: Make the PR URL easy to find and copy
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

let data = '';
process.stdin.on('data', chunk => data += chunk);
process.stdin.on('end', () => {
  try {
    const input = JSON.parse(data);
    const toolResult = input.tool_result?.stdout || input.tool_result?.output || '';

    // Look for GitHub PR URL in the output
    const prUrlMatch = toolResult.match(/https:\/\/github\.com\/[^\s]+\/pull\/\d+/);

    if (prUrlMatch) {
      const prUrl = prUrlMatch[0];

      console.error(`[Hook] PR created successfully!`);
      console.error(`  URL: ${prUrl}`);
      console.error(`  View: gh pr view --web`);

      // Optionally log to a file for easy reference
      try {
        const logDir = path.join(os.homedir(), '.claude', 'pr-log');
        if (!fs.existsSync(logDir)) {
          fs.mkdirSync(logDir, { recursive: true });
        }

        const today = new Date().toISOString().split('T')[0];
        const logFile = path.join(logDir, `${today}.log`);
        const timestamp = new Date().toISOString();
        const cwd = process.cwd();

        fs.appendFileSync(logFile, `[${timestamp}] ${prUrl} (${cwd})\n`);
      } catch {
        // Ignore logging errors
      }
    }
  } catch (err) {
    // Silently fail - don't break the tool
  }

  // Pass through the original input
  console.log(data);
});
