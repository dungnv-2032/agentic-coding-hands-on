'use strict';

/**
 * safe-rimraf.cjs — a safety floor in front of the idempotent-rebuild wipe
 * (`--package` deletes `outRoot` before rewriting it on every run). Guards
 * against a misconfigured/attacker-influenced `--out`/`--repo-root` pair
 * resolving to something catastrophic to delete.
 *
 * Allowed to delete `resolved` iff:
 *   - it is NOT the filesystem root, the caller's home directory, or the
 *     resolved repo root itself, AND
 *   - it has a non-empty basename, AND
 *   - it is either under the repo root OR was an explicitly-passed `--out`
 *     (a user who explicitly names a custom location is trusted for that
 *     location, once the hard-denied roots above are excluded).
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

function assertSafeToDelete(outRoot, { repoRoot, isExplicitOut }) {
  const resolved = path.resolve(outRoot);
  const fsRoot = path.parse(resolved).root;
  const home = path.resolve(os.homedir());
  const repo = path.resolve(repoRoot);

  if (resolved === fsRoot) {
    throw new Error(`refusing to delete the filesystem root: ${resolved}`);
  }
  if (resolved === home) {
    throw new Error(`refusing to delete the home directory: ${resolved}`);
  }
  if (resolved === repo) {
    throw new Error(`refusing to delete the repo root itself: ${resolved}`);
  }
  if (path.basename(resolved) === '') {
    throw new Error(`refusing to delete a path with an empty basename: ${resolved}`);
  }

  const underRepoRoot = resolved.startsWith(repo + path.sep);
  if (!underRepoRoot && !isExplicitOut) {
    throw new Error(
      `refusing to delete ${resolved}: not under the repo root (${repo}) and no explicit --out was given`
    );
  }
}

function rimraf(dir, safety) {
  assertSafeToDelete(dir, safety);
  if (fs.existsSync(dir)) fs.rmSync(dir, { recursive: true, force: true });
}

module.exports = { assertSafeToDelete, rimraf };
