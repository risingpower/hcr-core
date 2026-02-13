#!/usr/bin/env node
/**
 * PostToolUse hook: Warn about print() in edited Python files
 * Triggered after: Edit on .py files
 */

const fs = require('fs');
const path = require('path');

let data = '';
process.stdin.on('data', chunk => data += chunk);
process.stdin.on('end', () => {
  try {
    const input = JSON.parse(data);
    const filePath = input.tool_input?.file_path;

    if (filePath && fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n');
      const matches = [];

      lines.forEach((line, idx) => {
        // Match print( but not if it's commented out or in a string definition
        // Also exclude common legitimate uses like print functions in classes
        if (/\bprint\s*\(/.test(line) && !/^\s*#/.test(line) && !/def print/.test(line) && !/["'].*print.*["']/.test(line)) {
          matches.push({ line: idx + 1, content: line.trim() });
        }
      });

      if (matches.length > 0) {
        const fileName = path.basename(filePath);
        console.error(`[Hook] WARNING: print() found in ${fileName}`);
        matches.slice(0, 3).forEach(m => {
          console.error(`  L${m.line}: ${m.content.substring(0, 60)}${m.content.length > 60 ? '...' : ''}`);
        });
        if (matches.length > 3) {
          console.error(`  ... and ${matches.length - 3} more`);
        }
        console.error(`  Consider using logging instead of print()`);
      }
    }
  } catch (err) {
    // Silently fail - don't break the tool
  }

  // Pass through the original input
  console.log(data);
});
