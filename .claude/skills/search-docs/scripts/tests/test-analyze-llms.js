#!/usr/bin/env node

/**
 * Tests for analyze-llms-txt.js
 */

const {
  analyzeLlmsTxt,
  parseUrls,
  groupByPriority,
  categorizeUrl,
  suggestAgentDistribution,
} = require('../analyze-llms-txt');

// Test counter
let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`✓ ${message}`);
    passed++;
  } else {
    console.error(`✗ ${message}`);
    failed++;
  }
}

function assertEqual(actual, expected, message) {
  if (actual === expected) {
    console.log(`✓ ${message}`);
    passed++;
  } else {
    console.error(`✗ ${message}`);
    console.error(`  Expected: ${expected}`);
    console.error(`  Actual: ${actual}`);
    failed++;
  }
}

console.log('Running analyze-llms-txt.js tests...\n');

// Test categorizeUrl
console.log('## Testing categorizeUrl()');
assertEqual(categorizeUrl('https://docs.example.com/getting-started'), 'critical', 'Categorize getting-started as critical');
assertEqual(categorizeUrl('https://docs.example.com/guide/routing'), 'important', 'Categorize routing guide as important');
assertEqual(categorizeUrl('https://docs.example.com/advanced/internals'), 'supplementary', 'Categorize internals as supplementary');
assertEqual(categorizeUrl('https://docs.example.com/api-reference'), 'important', 'Categorize API reference as important');

// Test parseUrls
console.log('\n## Testing parseUrls()');

const sampleContent = `# Documentation
https://docs.example.com/getting-started
https://docs.example.com/guide
# Comment line
https://docs.example.com/api-reference

https://docs.example.com/advanced
`;

const urls = parseUrls(sampleContent);
assertEqual(urls.length, 4, 'Parse 4 URLs from content');
assert(urls[0].includes('getting-started'), 'First URL is getting-started');

const emptyContent = '';
const emptyUrls = parseUrls(emptyContent);
assertEqual(emptyUrls.length, 0, 'Empty content returns 0 URLs');

// Test groupByPriority
console.log('\n## Testing groupByPriority()');

const testUrls = [
  'https://docs.example.com/getting-started',
  'https://docs.example.com/guide/routing',
  'https://docs.example.com/advanced/internals',
  'https://docs.example.com/installation',
];

const grouped = groupByPriority(testUrls);
assert(grouped.critical.length >= 2, 'Has critical URLs');
assert(grouped.important.length >= 1, 'Has important URLs');
assert(grouped.supplementary.length >= 1, 'Has supplementary URLs');

// Test suggestAgentDistribution
console.log('\n## Testing suggestAgentDistribution()');

const dist1 = suggestAgentDistribution(2);
assertEqual(dist1.agentCount, 1, 'Suggest 1 agent for 2 URLs');
assertEqual(dist1.strategy, 'single', 'Strategy is single for few URLs');

const dist2 = suggestAgentDistribution(8);
assert(dist2.agentCount >= 3 && dist2.agentCount <= 5, 'Suggest 3-5 agents for 8 URLs');
assertEqual(dist2.strategy, 'parallel', 'Strategy is parallel for medium URLs');

const dist3 = suggestAgentDistribution(15);
assertEqual(dist3.agentCount, 7, 'Suggest 7 agents for 15 URLs');

const dist4 = suggestAgentDistribution(25);
assertEqual(dist4.agentCount, 7, 'Suggest 7 agents for 25 URLs');
assertEqual(dist4.strategy, 'phased', 'Strategy is phased for many URLs');
assertEqual(dist4.phases, 2, 'Use 2 phases for large sets');

// Test analyzeLlmsTxt
console.log('\n## Testing analyzeLlmsTxt()');

const analysis = analyzeLlmsTxt(sampleContent);
assertEqual(analysis.totalUrls, 4, 'Analysis counts 4 URLs');
assert(analysis.grouped, 'Analysis includes grouped URLs');
assert(analysis.distribution, 'Analysis includes distribution suggestion');
assert(analysis.summary, 'Analysis includes summary');

// Test v2 index cases (generate-llms-txt v2 downstream compat — phase 4)
console.log('\n## Testing v2 index compatibility');

// v2 index with an absolute --base-url: one URL per link; a gap-advisory blockquote (repo-
// relative path in backticks, never an absolute URL — phase 2's index/full split, red-team F8)
// contributes none.
const V2_INDEX_ABS = [
  '# Acme Portal', '',
  '> One line about Acme Portal.', '',
  '## Installation', '',
  '- [Install](https://docs.acme.test/user-guide/install): set the portal up on web and desktop', '',
  '## Screens', '',
  '> Not documented in this repository. Export it into `docs/user-guide/screens.md` and re-run.', '',
].join('\n');

assertEqual(analyzeLlmsTxt(V2_INDEX_ABS).totalUrls, 1,
  'v2 index: one URL per link, advisory blockquote contributes none');

// v2 index with relative paths (no --base-url): 0 URLs — v1 behavior, unchanged.
const V2_INDEX_RELATIVE = [
  '# Acme Portal', '',
  '> One line about Acme Portal.', '',
  '## Installation', '',
  '- [Install](docs/user-guide/install.md): set the portal up on web and desktop', '',
].join('\n');

assertEqual(analyzeLlmsTxt(V2_INDEX_RELATIVE).totalUrls, 0,
  'v2 index with relative paths: 0 URLs (v1 behavior unchanged)');

// A gap-advisory index with more than one real link: the advisory must never be mistaken for
// a documentation URL (no phantom URL from the advisory blockquote).
const V2_INDEX_GAP_ADVISORY = [
  '# Acme Portal', '',
  '> One line about Acme Portal.', '',
  '## Installation', '',
  '- [Install](https://docs.acme.test/user-guide/install): set the portal up', '',
  '## Usage Guide', '',
  '- [Usage](https://docs.acme.test/user-guide/usage): how to use it', '',
  '## Screens', '',
  '> Not documented in this repository. Export it into `docs/user-guide/screens.md` and re-run.', '',
].join('\n');

assertEqual(analyzeLlmsTxt(V2_INDEX_GAP_ADVISORY).totalUrls, 2,
  'v2 index: gap advisory contributes no phantom URL');

// An index generated from a COMPLETE profile: the product URL/department/owner/support contact
// must never leak into the index blockquote — totalUrls stays exactly the real link count (F8).
const V2_INDEX_COMPLETE_PROFILE = [
  '# Acme Portal', '',
  '> A self-service portal for exporting and reviewing account activity.', '',
  '## Installation', '',
  '- [Install](https://docs.acme.test/user-guide/install): set the portal up', '',
].join('\n');

assertEqual(analyzeLlmsTxt(V2_INDEX_COMPLETE_PROFILE).totalUrls, 1,
  'v2 index from a complete profile: totalUrls unchanged, no product URL leaked into the blockquote (F8)');

// Summary
console.log('\n## Test Summary');
console.log(`Passed: ${passed}`);
console.log(`Failed: ${failed}`);
console.log(`Total: ${passed + failed}`);

process.exit(failed > 0 ? 1 : 0);
