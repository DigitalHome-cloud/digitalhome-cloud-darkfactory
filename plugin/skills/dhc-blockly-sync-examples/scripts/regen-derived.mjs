#!/usr/bin/env node
/**
 * Regenerate the DERIVED example files from the starter workspaces, so they never
 * need hand-migration. Currently one derived file:
 *   examples/dhc-designer-demo.json = { version, electrical, spatial }
 *     ← the exact no-edit combined Save of the two starters.
 *
 * Run this AFTER reconciling the starters to the new block schema. Add more
 * derived outputs here rather than editing them by hand.
 *
 * Usage: node regen-derived.mjs
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

// Find the checkout that holds blockly/: from where the script is run (it ships
// in a plugin, outside any checkout), else from the script itself.
const findRoot = (start) => {
  let d = start;
  while (d !== '/' && !existsSync(resolve(d, 'blockly/electrical-blocks.json'))) d = dirname(d);
  return d;
};
let d = findRoot(process.cwd());
if (d === '/') d = findRoot(dirname(fileURLToPath(import.meta.url)));
const BLK = resolve(d, 'blockly');

const electrical = JSON.parse(readFileSync(resolve(BLK, 'electrical-workspace.json'), 'utf8'));
const spatial = JSON.parse(readFileSync(resolve(BLK, 'spatial-workspace.json'), 'utf8'));
const out = resolve(BLK, 'examples/dhc-designer-demo.json');
writeFileSync(out, JSON.stringify({ version: 'dhc-blockly-designer/1', electrical, spatial }, null, 2) + '\n');
console.log('✓ regenerated', 'examples/dhc-designer-demo.json', '(from the two starters)');
