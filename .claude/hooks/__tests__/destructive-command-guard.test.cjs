#!/usr/bin/env node
'use strict';

const { test } = require('node:test');
const assert = require('node:assert');
const { execSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const HOOK = path.join(__dirname, '..', 'destructive-command-guard.cjs');
const LOG_FILE = path.join(__dirname, '..', '.logs', 'hook-log.jsonl');

/** Fresh scratch cwd with no .claude/.tkm.json — hook runs with defaults. */
function makeScratchCwd() {
  return fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), `destructive-guard-cwd-${process.pid}-`));
}

/** Run the guard with a payload + optional cwd override; parse its JSON output. */
function run(payload, { cwd } = {}) {
  const out = execSync(`node "${HOOK}"`, {
    input: JSON.stringify(payload),
    encoding: 'utf8',
    cwd,
  }) || '{}';
  return JSON.parse(out);
}

function bashCall(command) {
  return { tool_name: 'Bash', tool_input: { command } };
}

function asks(result) {
  return Boolean(result.hookSpecificOutput && result.hookSpecificOutput.permissionDecision === 'ask');
}

/** Most recent destructive-command-guard entry — the shared log file is written
 * concurrently by other hook test files, so the guard's own entry isn't reliably
 * the last line; scan backward for the last one this hook wrote instead. */
function lastOwnLogEntry() {
  const lines = fs.readFileSync(LOG_FILE, 'utf8').split('\n').filter(Boolean);
  for (let i = lines.length - 1; i >= 0; i -= 1) {
    const entry = JSON.parse(lines[i]);
    if (entry.hook === 'destructive-command-guard') return entry;
  }
  return null;
}

// ── destructive command -> ask ──────────────────────────────────────────────

test('git reset --hard asks, with a reason naming the pattern', () => {
  const cwd = makeScratchCwd();
  const result = run(bashCall('git reset --hard'), { cwd });
  assert.ok(asks(result));
  assert.match(result.hookSpecificOutput.permissionDecisionReason, /git reset --hard/);
});

test('rm -rf / asks', () => {
  const cwd = makeScratchCwd();
  const result = run(bashCall('rm -rf /'), { cwd });
  assert.ok(asks(result));
});

test('git push -f origin main asks', () => {
  const cwd = makeScratchCwd();
  const result = run(bashCall('git push -f origin main'), { cwd });
  assert.ok(asks(result));
});

test('kubectl delete pod foo asks', () => {
  const cwd = makeScratchCwd();
  const result = run(bashCall('kubectl delete pod foo'), { cwd });
  assert.ok(asks(result));
});

test('destructive commands behind wrappers still ask', () => {
  const cwd = makeScratchCwd();
  assert.ok(asks(run(bashCall('env FOO=bar rm -rf /'), { cwd })));
  assert.ok(asks(run(bashCall('sudo git reset --hard'), { cwd })));
  assert.ok(asks(run(bashCall('sudo kubectl delete ns prod'), { cwd })));
});

test('DROP TABLE users asks', () => {
  const cwd = makeScratchCwd();
  const result = run(bashCall('psql -c "DROP TABLE users;"'), { cwd });
  assert.ok(asks(result));
});

// ── allowlisted / regression-safe commands -> allow, silent ────────────────

test('rm -rf node_modules is allowed (allowlisted dependency dir)', () => {
  const cwd = makeScratchCwd();
  const result = run(bashCall('rm -rf node_modules'), { cwd });
  assert.ok(!asks(result));
  assert.deepStrictEqual(result, {});
});

test('git reset HEAD <file> is allowed -- the safety-guard.cjs regression case', () => {
  const cwd = makeScratchCwd();
  const result = run(bashCall('git reset HEAD file.txt'), { cwd });
  assert.ok(!asks(result));
  assert.deepStrictEqual(result, {});
});

test('an unrelated command passes through with no output fields', () => {
  const cwd = makeScratchCwd();
  const result = run(bashCall('ls -la'), { cwd });
  assert.deepStrictEqual(result, {});
});

// ── internal error handling: fail open ─────────────────────────────────────

test('malformed stdin fails open (allows, no ask)', () => {
  const cwd = makeScratchCwd();
  const out = execSync(`node "${HOOK}"`, { input: 'not json', encoding: 'utf8', cwd }) || '{}';
  const result = JSON.parse(out);
  assert.ok(!asks(result));
});

test('non-Bash tool_name passes through untouched', () => {
  const cwd = makeScratchCwd();
  const result = run({ tool_name: 'Write', tool_input: { file_path: 'x' } }, { cwd });
  assert.ok(!asks(result));
});

// ── .tkm.json toggle: hooks."destructive-command-guard": false -> never asks ─

test('toggled off in .claude/.tkm.json allows even git reset --hard', () => {
  const cwd = makeScratchCwd();
  fs.mkdirSync(path.join(cwd, '.claude'), { recursive: true });
  fs.writeFileSync(
    path.join(cwd, '.claude', '.tkm.json'),
    JSON.stringify({ hooks: { 'destructive-command-guard': false } })
  );
  const result = run(bashCall('git reset --hard'), { cwd });
  assert.ok(!asks(result));
});

// ── log hygiene: the persisted log carries the pattern name only ───────────

test('log note names the pattern only, never the raw command', () => {
  const cwd = makeScratchCwd();
  const originalExists = fs.existsSync(LOG_FILE);
  const originalContent = originalExists ? fs.readFileSync(LOG_FILE, 'utf8') : '';
  try {
    run(bashCall('git reset --hard --token=SECRET123'), { cwd });
    const entry = lastOwnLogEntry();
    assert.ok(entry, 'expected a destructive-command-guard log entry');
    assert.strictEqual(entry.note, 'git reset --hard');
    assert.ok(!entry.note.includes('SECRET123'));
    assert.ok(!JSON.stringify(entry).includes('SECRET123'));
  } finally {
    if (originalExists) fs.writeFileSync(LOG_FILE, originalContent, 'utf8');
  }
});
