#!/usr/bin/env node
/**
 * PreCompact hook: Save state before context compaction
 * Triggered: Before Claude compacts context
 * Purpose: Preserve state markers before summarization
 */

const path = require('path');
const fs = require('fs');
const os = require('os');

const sessionsDir = path.join(os.homedir(), '.claude', 'sessions');
const compactionLog = path.join(sessionsDir, 'compaction-log.txt');
const currentTime = new Date().toISOString();

fs.mkdirSync(sessionsDir, { recursive: true });
fs.appendFileSync(compactionLog, `[${currentTime}] Context compaction triggered\n`);

// Find active session file and append compaction marker
try {
  const files = fs.readdirSync(sessionsDir)
    .filter(f => f.endsWith('-session.tmp'))
    .sort()
    .reverse();

  if (files.length > 0) {
    const activeSession = path.join(sessionsDir, files[0]);
    const time = new Date().toTimeString().slice(0, 5);
    fs.appendFileSync(activeSession, `\n---\n**[Compaction at ${time}]** - Context was summarized\n`);
  }
} catch (e) {
  // Ignore errors
}

console.error('[PreCompact] State saved before compaction');
