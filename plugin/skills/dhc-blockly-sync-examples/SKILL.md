---
name: dhc-blockly-sync-examples
description: >-
  Keep the DHC Blockly example / starter workspace files loadable after a block-
  definition change. When you edit blockly/{electrical,spatial}-blocks.json —
  rename a block type, add / remove / rename a field, change a mutator or its
  slots, flip inputsInline — the saved workspace JSON goes stale and Blockly shows
  "block incompatibility" on load. This skill reconciles every tracked workspace /
  example file to the new schema: lint for the exact breakages, fix them, backfill
  new fields, regenerate derived files, and verify. Trigger on "block
  incompatibility", "the demo / example won't load after my block change", "update
  / sync / migrate the example files", "regenerate the demo", "fix the starters
  after renaming a block", or right after any edit to *-blocks.json or the
  registerPlugins mutators. Confined to repos/core/blockly/. This is the pragmatic
  interim; the durable fix (persist the A-Box, regenerate the workspace) is parked
  in doc/parking-lot.md § 4.
---

# Sync Blockly example files to the current block schema

Block definitions are the **source of truth**. A saved workspace is welded to the
UI schema (block `type` strings, field names, mutator `extraState`/slot names), so
any change to `blockly/electrical-blocks.json`, `blockly/spatial-blocks.json`, or
the `registerPlugins-*.js` mutators can make older saved JSON fail to load. Run
this after every such change so the shipped examples stay green.

## What must stay in sync (canonical, tracked)

| File | Kind |
|---|---|
| `blockly/electrical-workspace.json` | Electrical starter (hand-authored) |
| `blockly/spatial-workspace.json` | Spatial starter (hand-authored) |
| `blockly/examples/board1.workspace.json`, `board2.workspace.json` | Worked 3-phase boards (single electrical states) |
| `blockly/examples/dhc-designer-demo.json` | **Derived** combined `{electrical,spatial}` — regenerated, never hand-edited |

Untracked `examples/dhc-electrical-*.json` / `dhc-designer-*.json` are user Save
snapshots — ignore them unless asked (they *are* the incompatibility, by design).

## Procedure

1. **Note what changed** in the def(s): a type rename, a field add/remove/rename,
   a mutator/slot change. Keep a small rename map (old→new) if you renamed things —
   the lint can't guess intent.

2. **Lint** to see the exact breakages per file:
   ```bash
   node <this skill's folder>/scripts/lint-examples.mjs     # from the repos/core checkout
   ```
   (append file paths to lint specific ones). It flags:

   | Finding | Meaning | Fix |
   |---|---|---|
   | `✗ unknown block type "X"` | type removed/renamed | rename the `type` in the file (your map), or delete the block if the concept is gone |
   | `⚠ stale field "f"` | field removed/renamed | rename the field key (keep its value) or drop it |
   | `⚠ input "k" doesn't match mutator … (expects P_N)` | mutator slots renamed | rename the input keys (e.g. `rail_0`→`row_0`) to the new prefix |
   | `⚠ extraState.itemCount=n < m filled slots` | extraState stale | set `itemCount` ≥ the number of filled slots |
   | `✗ references missing variable id "id"` | dangling token | fix the ref, or add the `variables` entry it points at |

3. **Fix** each file with the Edit tool. For a **new field**, don't just rely on
   Blockly's default — backfill a realistic value on the example blocks so the
   demo still reads well (e.g. when `quantity` was added to `dhcb:Socket`, the
   starter got `"quantity": 6`). Preserve cross-workspace links: a spatial
   `dhcb:Placement`'s `LEAF` must still match an electrical leaf id (a point leaf
   is keyed `"<consumer> / <point-name>"`; everything else by its `name`).

4. **Regenerate derived files** from the reconciled starters:
   ```bash
   node <this skill's folder>/scripts/regen-derived.mjs     # from the repos/core checkout
   ```

5. **Verify**:
   - re-run the lint → `✓ … compatible`;
   - `npm test` → the round-trip fixture (`tests/blockly/designer-roundtrip.test.js`)
     guards the combined-file shape + placement referential integrity;
   - load each file in the harness for the real proof — start
     `bash scripts/preview-blockly.sh`, then open
     `preview.html?load=./examples/<file>` and confirm the event log shows no
     `⚠ workspace restore` errors and the block count is preserved. (This is the
     only true loadability check; the lint is a fast first pass.)

## Keep the lint's embedded maps current

The lint mirrors two things the def files don't contain. Update them when they
change (both live at the top of `scripts/lint-examples.mjs`):

- **`CODE_BLOCKS`** — blocks defined in JS, not `*-blocks.json` (today just
  `dhcb:Placement` → field `LEAF`). Add a new one when you code-define a block.
- **`MUTATOR_PREFIX`** — each mutator's input-slot prefix (from
  `registerPlugins-*.js`), e.g. `dhc_points_mutator → point_`,
  `dhc_room_contents_mutator → hasPoint_`. Add a row when you add a mutator.

## Guardrails

- **Never hand-edit derived files** (`dhc-designer-demo.json`) — regenerate them.
- The lint catches schema breakages statically; it does **not** prove the file
  loads. Always finish with the harness load in step 5.
- This skill is the interim. The durable design — make the A-Box (TTL) the save
  format and **regenerate** the workspace from it, so one backward translator
  absorbs every schema change — is parked in `doc/parking-lot.md § 4`
  ("Persist the A-Box, regenerate the workspace"). When that lands, this skill's
  hand-reconciliation is replaced by that translator.
