#!/usr/bin/env node
/**
 * Contract test — destructive-command-guard.cjs must emit modern Claude
 * permissionDecision shape: "ask" (not "deny", not "allow" as a literal string)
 * on a destructive match + permissionDecisionReason populated, exit 0. Empty/
 * malformed input and non-Bash tools must fail open (silent {} + exit 0).
 */

const { describe, it } = require('node:test');
const assert = require('node:assert');
const { spawn } = require('child_process');
const path = require('path');

const HOOK_PATH = path.join(__dirname, '..', 'destructive-command-guard.cjs');

function runHook(payload, opts = {}) {
  return new Promise((resolve, reject) => {
    const proc = spawn(process.execPath, [HOOK_PATH], {
      stdio: ['pipe', 'pipe', 'pipe'],
      env: process.env,
    });

    let stdout = '';
    let stderr = '';
    let settled = false;

    proc.stdout.on('data', (d) => (stdout += d.toString()));
    proc.stderr.on('data', (d) => (stderr += d.toString()));

    if (opts.emptyInput) {
      proc.stdin.end();
    } else {
      proc.stdin.write(JSON.stringify(payload));
      proc.stdin.end();
    }

    const t = setTimeout(() => {
      if (!settled) {
        settled = true;
        proc.kill('SIGTERM');
        reject(new Error('Hook timed out'));
      }
    }, 1000);

    proc.on('close', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(t);
      let parsed = null;
      try { parsed = stdout.trim() ? JSON.parse(stdout.trim()) : null; } catch (_) {}
      resolve({ stdout, stderr, exitCode: code, parsed });
    });
  });
}

describe('destructive-command-guard.cjs — modern Claude ask shape + fail-open', () => {
  it('git reset --hard -> modern ask shape, exit 0', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Bash',
      tool_input: { command: 'git reset --hard' },
    };
    const { parsed, exitCode } = await runHook(payload);
    assert.strictEqual(exitCode, 0, 'must exit 0 (decision in JSON)');
    assert.ok(parsed && parsed.hookSpecificOutput, 'must emit hookSpecificOutput');
    assert.strictEqual(parsed.hookSpecificOutput.hookEventName, 'PreToolUse');
    assert.strictEqual(parsed.hookSpecificOutput.permissionDecision, 'ask');
    assert.ok(
      parsed.hookSpecificOutput.permissionDecisionReason,
      'must have permissionDecisionReason'
    );
  });

  it('this guard never denies -- only "ask" or allow', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Bash',
      tool_input: { command: 'kubectl delete pod foo' },
    };
    const { parsed } = await runHook(payload);
    assert.notStrictEqual(parsed.hookSpecificOutput.permissionDecision, 'deny');
  });

  it('empty input: fail-open (silent {} + exit 0)', async () => {
    const { stdout, stderr, exitCode } = await runHook(null, { emptyInput: true });
    assert.strictEqual(exitCode, 0, 'empty input must fail open with exit 0');
    assert.strictEqual(stdout.trim(), '{}', 'empty input must emit silent {}');
    assert.strictEqual(stderr, '', 'empty input must be silent on stderr');
  });

  it('passthrough: rm -rf node_modules (allowlisted) -> exit 0, no ask in stdout', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Bash',
      tool_input: { command: 'rm -rf node_modules' },
    };
    const { stdout, exitCode } = await runHook(payload);
    assert.strictEqual(exitCode, 0);
    assert.strictEqual(stdout.trim(), '{}');
  });

  it('passthrough: non-Bash tool -> exit 0, no ask in stdout', async () => {
    const payload = {
      hook_event_name: 'PreToolUse',
      tool_name: 'Read',
      tool_input: { file_path: 'src/index.ts' },
    };
    const { stdout, exitCode } = await runHook(payload);
    assert.strictEqual(exitCode, 0);
    if (stdout.trim()) {
      const parsed = JSON.parse(stdout.trim());
      if (parsed.hookSpecificOutput) {
        assert.notStrictEqual(parsed.hookSpecificOutput.permissionDecision, 'ask');
      }
    }
  });
});
