#!/usr/bin/env node
/**
 * PreToolUse hook: Suggest checkpoint/compaction at logical intervals
 * Triggered: Before Edit or Write operations
 * Purpose: Remind about checkpoints at natural break points
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const stateFile = path.join(os.homedir(), '.claude', 'sessions', '.edit-count');

let data = '';
process.stdin.on('data', chunk => data += chunk);
process.stdin.on('end', () => {
  try {
    // Track edit count
    let editCount = 0;

    try {
      if (fs.existsSync(stateFile)) {
        editCount = parseInt(fs.readFileSync(stateFile, 'utf8'), 10) || 0;
      }
    } catch (e) {
      // Ignore
    }

    editCount++;

    // Save updated count
    try {
      fs.mkdirSync(path.dirname(stateFile), { recursive: true });
      fs.writeFileSync(stateFile, String(editCount));
    } catch (e) {
      // Ignore
    }

    // Suggest checkpoint every 20 edits
    if (editCount > 0 && editCount % 20 === 0) {
      console.error(`[Hook] ${editCount} edits this session. Consider /au-checkpoint if at a logical break point.`);
    }

    // Suggest compaction every 50 edits
    if (editCount > 0 && editCount % 50 === 0) {
      console.error(`[Hook] ${editCount} edits. If context is getting long, consider /compact or starting a new session.`);
    }
  } catch (err) {
    // Silently fail
  }

  // Pass through the original input
  console.log(data);
});
