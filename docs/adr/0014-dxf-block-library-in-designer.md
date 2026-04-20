# ADR 0014: DXF block library lives in the Designer repo

Status: Accepted · 2026-04-15

## Context

The Designer app (`repos/designer`) generates NF C 15-100-compliant DXF drawings (`schéma unifilaire` today; panel layout and architectural views planned) from the Blockly workspace. The generator needs a catalogue of reusable DXF BLOCKs — ISO 216 paper frames with DLAB5 cartouche, IEC 60617 symbols, NF C 15-100 circuit mini-schematics, and (later) raster photographs of tableau installations.

The long-term vision is for this catalogue to be versioned alongside the DHC ontology in `semantic-core/`, synced to S3, and referenced by the Blockly→DXF compiler via T-box class IRIs. In the short term we need to decide **where the library lives while the generator is being stabilised**, and **how blocks are declared** so that adding, modifying, or swapping a block (vector ↔ raster) is a one-file change that a bureau d'études can review in a PR.

## Decision

1. **Library location.** The DXF block library lives inside `repos/designer/src/export/dxf/library/` for the current phase. Moving it to `repos/modeler/semantic-core/` alongside the ontology is deferred until (a) the public API of the generator stabilises and (b) the S3 sync pipeline is in place. Rationale: the library and the generator co-evolve; a split would force a cross-repo PR every time a block is added.

2. **JSON manifest as single source of truth.** `library/manifest.json` lists every block with normative metadata:
   - `name`, `kind` (`frame` · `symbol` · `circuit` · `picture`), `category`
   - `label` (`fr`, `en`)
   - `iec60617`, `nfc15100` (standard references)
   - `tbox` (ontology class IRI — `dhc-nfc15100:SocketCircuit16A`, etc.)
   - `abox` (hint values — rating, section, terminal symbol, RCD type …)
   - `source` — either `{ kind: "vector", module }` pointing at the draw code, or `{ kind: "raster", file, widthMm, heightMm }` for pictures.

   JS modules (`frames.js`, `symbolsNfc15100.js`, `circuits.js`) hold the draw implementations and derive their exported catalogues (`NFC15100_SYMBOLS`, `CIRCUIT_CATALOGUE`) from the manifest. A parity check in the test suite asserts that every manifest entry has a registered draw function and vice versa.

3. **Frames are BLOCKs.** `FRAME_A4`, `FRAME_A3`, `FRAME_A2`, `FRAME_A1` are registered as DXF BLOCKs containing the static parts of the cartouche (grid + DLAB5 logo). `drawDlab5Frame(dxf, { size, origin, cartouche })` INSERTs the block and overlays the variable cartouche fields (title, project, date …) as TEXT entities. Consequence: bureaux d'études can redefine the cartouche graphics once inside LibreCAD and every drawing that INSERTs `FRAME_A3` picks up the change.

4. **Raster pictures supported via manifest + placeholder rendering.** The manifest schema accepts `"kind": "picture"` entries pointing to a PNG under `library/pictures/`. The DXF writer currently renders pictures as a **placeholder block** (bounding rect + filename + size annotation) because the AC1009 (R12) output format does not support raster images. A follow-up will bump the writer to AC1015 (R2000) and replace the placeholder with real `IMAGE`/`IMAGEDEF` entities.

5. **S3 sync deferred.** The GitHub Action to upload `library.dxf` + `manifest.json` to `s3://dhc-ontology/<manifest.version>/dxf/` is planned but not in this change. The manifest already carries a `version` field so the future Action can detect bumps.

## Alternatives considered

- **Library in modeler repo now.** Rejected: generator and library co-evolve during stabilisation; cross-repo PRs would slow every iteration. Will revisit once the public API is stable and the S3 pipeline is ready.
- **Hard-coded JS arrays (status quo before this ADR).** Rejected: no place to attach IEC 60617 codes, T-box IRIs, or per-block `abox` hints; the Blockly→DXF compiler would need to duplicate this metadata elsewhere.
- **Full AC1015 (R2000) writer for IMAGE support now.** Rejected for this iteration: the IMAGE entity requires an `OBJECTS` section + `IMAGEDEF` dictionary, ~60 LOC of non-trivial DXF plumbing. Placeholder rendering keeps the manifest schema honest (a picture entry produces a visible artifact) without the format bump.

## Consequences

- A bureau d'études adds a block in one PR: manifest entry + either a draw function (vector) or a PNG drop (picture).
- The future Blockly→DXF compiler resolves a T-box class directly from `manifest.blocks[*].tbox` → block name, retiring the regex heuristics in `fromAbox.js`.
- When the library moves to `semantic-core/`, consumers import `MANIFEST` from the published S3 URL rather than from `repos/designer`; the path is a search-and-replace.
- Placeholder pictures render visibly different from real images — we accept this short-term until the AC1015 bump lands. Downstream automation should treat the placeholder as a TODO marker.

## Related

- README: `repos/designer/src/export/dxf/README.md`
- Plan file: `.claude/plans/wise-sprouting-wozniak.md` (session plan, not normative)
- Prior ADRs: 0007 (semantic-core in modeler), 0010 (S3 structure), 0012 (modular ontology)
