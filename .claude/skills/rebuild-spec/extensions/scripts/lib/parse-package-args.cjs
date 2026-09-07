'use strict';

/**
 * parse-package-args.cjs — CLI argument parsing for build_client_package.cjs.
 * Split out to keep the main script under the repo's ~200-line file guideline.
 */

/**
 * @param {string[]} argv
 * @returns {{docsRoot: string, lang: string|null, out: string|null, projectName: string|null, repoRoot: string}}
 */
function parseArgs(argv) {
  const args = { docsRoot: 'docs', lang: null, out: null, projectName: null, repoRoot: process.cwd() };
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    const value = () => {
      i += 1;
      return argv[i];
    };
    switch (flag) {
      case '--docs-root':
        args.docsRoot = value();
        break;
      case '--lang':
        args.lang = value();
        break;
      case '--out':
        args.out = value();
        break;
      case '--project-name':
        args.projectName = value();
        break;
      case '--repo-root':
        args.repoRoot = value();
        break;
      default:
        throw new Error(`Unknown argument: ${flag}`);
    }
  }
  return args;
}

module.exports = { parseArgs };
