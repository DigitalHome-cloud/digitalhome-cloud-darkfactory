#!/usr/bin/env node
/**
 * Lint DHC Blockly example / workspace files against the CURRENT block schema.
 *
 * When you change block definitions in blockly/{electrical,spatial}-blocks.json
 * (rename a type, add/remove/rename a field, change a mutator), the saved
 * workspace JSON goes stale and Blockly reports "block incompatibility" on load.
 * This catches those breakages statically, per file, so you know exactly what to
 * fix — before opening the harness.
 *
 * Checks (per block instance):
 *   - unknown block `type`            → ERROR  (type removed/renamed)
 *   - `fields` key not in the def     → WARN   (field removed/renamed)
 *   - input slot name vs the block's mutator prefix → WARN (mutator changed)
 *   - extraState.itemCount < filled slots           → WARN (extraState stale)
 *   - field_variable ref → missing `variables` entry → ERROR (dangling token)
 *
 * It does NOT prove loadability (only Blockly can) — after fixing, load each file
 * in the harness (preview.html?load=…). But it catches the common breakages.
 *
 * Usage:
 *   node lint-examples.mjs                 # the canonical tracked set
 *   node lint-examples.mjs <file> [<file>] # specific files
 * Exit code: 0 clean, 1 issues found.
 */
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, relative } from 'node:path';

// Find the checkout that holds blockly/: from where the script is run (it ships
// in a plugin, outside any checkout), else from the script itself.
const findRoot = (start) => {
  let d = start;
  while (d !== '/' && !existsSync(resolve(d, 'blockly/electrical-blocks.json'))) d = dirname(d);
  return d;
};
let d = findRoot(process.cwd());
if (d === '/') d = findRoot(dirname(fileURLToPath(import.meta.url)));
const ROOT = d;
const BLK = resolve(ROOT, 'blockly');
if (!existsSync(resolve(BLK, 'electrical-blocks.json'))) {
  console.error('✗ could not locate blockly/electrical-blocks.json: run this from the repos/core checkout');
  process.exit(2);
}

// ── Blocks defined in code (not in *-blocks.json). Keep in step with the plugins.
const CODE_BLOCKS = {
  'dhcb:Placement': { fields: new Set(['LEAF']), mutator: null },
};
// ── Mutator → input-slot prefix (from registerPlugins-*.js). Keep in step.
const MUTATOR_PREFIX = {
  dhc_points_mutator: 'point_',
  dhc_board_mutator: 'row_',
  dhc_vdi_outlets_mutator: 'vdi_',
  dhc_home_places_mutator: 'hasPart_',
  dhc_building_levels_mutator: 'hasPart_',
  dhc_level_rooms_mutator: 'hasPart_',
  dhc_room_contents_mutator: 'hasPoint_',
};

// ── Build schema {type → {fields:Set, mutator}} from the def files ──────────
function loadDefs(file) {
  return (JSON.parse(readFileSync(resolve(BLK, file), 'utf8')).blocks) || [];
}
function fieldsOf(b) {
  const s = new Set();
  for (const k of Object.keys(b)) {
    if (/^args\d+$/.test(k) && Array.isArray(b[k])) for (const a of b[k]) if (a && a.name) s.add(a.name);
  }
  return s;
}
const schema = { ...CODE_BLOCKS };
for (const file of ['electrical-blocks.json', 'spatial-blocks.json']) {
  for (const b of loadDefs(file)) schema[b.type] = { fields: fieldsOf(b), mutator: b.mutator || null };
}

// ── Walk a Blockly state, collecting issues ─────────────────────────────────
function lintState(state, tag, issues) {
  const varIds = new Set((state.variables || []).map((v) => v.id));
  const walk = (b) => {
    if (!b || typeof b !== 'object') return;
    const t = b.type;
    const def = schema[t];
    if (!def) { issues.push(['ERROR', tag, `unknown block type "${t}" (removed or renamed?)`]); }
    else {
      for (const f of Object.keys(b.fields || {})) {
        if (!def.fields.has(f)) issues.push(['WARN', tag, `"${t}" has stale field "${f}" (removed/renamed in the def)`]);
        // field_variable refs: {id} must exist in `variables`
        const v = b.fields[f];
        if (v && typeof v === 'object' && v.id && !varIds.has(v.id)) issues.push(['ERROR', tag, `"${t}".${f} references missing variable id "${v.id}"`]);
      }
      const prefix = MUTATOR_PREFIX[def.mutator];
      const inKeys = Object.keys(b.inputs || {});
      if (def.mutator && prefix) {
        for (const k of inKeys) if (!k.startsWith(prefix)) issues.push(['WARN', tag, `"${t}" input "${k}" doesn't match mutator ${def.mutator} (expects ${prefix}N)`]);
        if (b.extraState && typeof b.extraState.itemCount === 'number') {
          const filled = inKeys.filter((k) => k.startsWith(prefix)).length;
          if (b.extraState.itemCount < filled) issues.push(['WARN', tag, `"${t}" extraState.itemCount=${b.extraState.itemCount} < ${filled} filled slots`]);
        }
      }
    }
    for (const k of Object.keys(b.inputs || {})) { if (b.inputs[k].block) walk(b.inputs[k].block); if (b.inputs[k].shadow) walk(b.inputs[k].shadow); }
    if (b.next && b.next.block) walk(b.next.block);
  };
  for (const tb of (state.blocks && state.blocks.blocks) || []) walk(tb);
}

// ── A file may be a single Blockly state or a combined {electrical, spatial} ─
function lintFile(path, issues) {
  const rel = relative(ROOT, path);
  let doc;
  try { doc = JSON.parse(readFileSync(path, 'utf8')); }
  catch (e) { issues.push(['ERROR', rel, `not valid JSON: ${e.message}`]); return; }
  if (doc.electrical || doc.spatial) {
    if (doc.electrical) lintState(doc.electrical, rel + ' [electrical]', issues);
    if (doc.spatial) lintState(doc.spatial, rel + ' [spatial]', issues);
  } else if (doc.blocks && doc.blocks.blocks) {
    lintState(doc, rel, issues);
  } else {
    issues.push(['WARN', rel, 'unrecognised file shape (not a Blockly state nor a combined {electrical,spatial})']);
  }
}

// ── Targets: CLI args, else the canonical tracked set ───────────────────────
const DEFAULTS = [
  'blockly/electrical-workspace.json',
  'blockly/spatial-workspace.json',
  'blockly/examples/dhc-designer-demo.json',
  'blockly/examples/board1.workspace.json',
  'blockly/examples/board2.workspace.json',
  'blockly/examples/t1-pac-airair.designer.json',
  'blockly/examples/t2-chauffage-filpilote.designer.json',
  'blockly/examples/t3-gaz.designer.json',
  'blockly/examples/t4-maison-pac-aireau.designer.json',
  'blockly/examples/comm-grade3.designer.json',
];
const targets = (process.argv.slice(2).length ? process.argv.slice(2) : DEFAULTS)
  .map((p) => resolve(process.cwd(), p))
  .filter((p) => { if (existsSync(p)) return true; console.error('… skip (not found):', relative(ROOT, p)); return false; });

const issues = [];
for (const p of targets) lintFile(p, issues);

if (!issues.length) { console.log(`✓ ${targets.length} file(s) compatible with the current block schema`); process.exit(0); }
const errs = issues.filter((i) => i[0] === 'ERROR').length;
for (const [lvl, tag, msg] of issues) console.log(`${lvl === 'ERROR' ? '✗' : '⚠'} [${tag}] ${msg}`);
console.log(`\n${errs} error(s), ${issues.length - errs} warning(s)`);
process.exit(errs ? 1 : 0);
