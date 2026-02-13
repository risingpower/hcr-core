#!/usr/bin/env node
/**
 * SessionEnd hook: Evaluate session for extractable patterns
 * Triggered: When a Claude session ends (after session-end.js)
 * Purpose: Prompt for pattern extraction via /au-learn
 */

const path = require('path');
const fs = require('fs');
const os = require('os');

const learnedDir = path.join(os.homedir(), '.claude', 'skills', 'learned');
const configFile = path.join(os.homedir(), '.claude', 'continuous-learning.json');

// Default config
const defaultConfig = {
  min_session_length: 10,
  auto_approve: false,
  patterns_to_detect: ['error_resolution', 'user_corrections', 'workarounds', 'debugging_techniques']
};

// Load config or use defaults
let config = defaultConfig;
if (fs.existsSync(configFile)) {
  try {
    config = { ...defaultConfig, ...JSON.parse(fs.readFileSync(configFile, 'utf8')) };
  } catch (e) {
    // Use defaults
  }
}

// Ensure learned directory exists
fs.mkdirSync(learnedDir, { recursive: true });

// For now, just log that evaluation would happen
// Full implementation would analyze session transcript
console.error('[EvaluateSession] Session ended - pattern extraction available');
console.error('[EvaluateSession] Use /au-learn to manually extract patterns');
