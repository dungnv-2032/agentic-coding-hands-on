'use strict';

/**
 * sweep-stray-temp-files.cjs — pre-walk cleanup for build_client_package.cjs.
 *
 * Belt-and-suspenders alongside the package-denylist.cjs pattern:
 * render-sanitized.cjs's try/finally is NOT guaranteed to run on a hard
 * process kill (e.g. SIGKILL, or SIGINT racing the signal handler) mid-render,
 * which can strand a `.rebuild-package-tmp.*.md` sanitized copy inside the
 * real docs/ source tree. Sweep and delete any stray ones BEFORE the walk, so
 * a crash on a prior run can never leak a bogus extra page into the next
 * build (the denylist alone only stops a *future* stray file from being
 * globbed — it doesn't clean up one left behind from before).
 */

const fs = require('fs');
const path = require('path');

const STRAY_TEMP_RE = /^\.rebuild-package-tmp\..*\.md$/i;

function sweepStrayTempFiles(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!entry.name.startsWith('.')) sweepStrayTempFiles(full);
      continue;
    }
    if (entry.isFile() && STRAY_TEMP_RE.test(entry.name)) {
      fs.rmSync(full, { force: true });
    }
  }
}

module.exports = { sweepStrayTempFiles, STRAY_TEMP_RE };
