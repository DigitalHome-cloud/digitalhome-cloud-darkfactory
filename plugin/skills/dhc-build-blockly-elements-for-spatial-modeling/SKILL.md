---
name: dhc-build-blockly-elements-for-spatial-modeling
description: Building, updating and previewing the Blockly artifacts for the SmartHome Designer's spatial design view - the workspace, block definitions and toolbox JSON under `blockly/dhc-spatial-*.json`, authored directly from the T-Box. Every class whose effective category (`dhc:blocklyCategory`, else `dhc:designView`) is "spatial" and that has `dhc:isInstantiated true` becomes a block shaped by its `dhc:blocklyBlockTemplate`; cross-view classes such as `rec:Level` appear under their own view's toolbox category. Use for "add a Blockly block for X", "rebuild the spatial toolbox", "regenerate dhc-spatial-blocks.json", "wire blocklyBlockTemplate for dhc:Foo", "preview the spatial workspace". Not for ontology authoring, the curator flow (`dhc-ontology-explorer`), or other design views (electrical: `dhc-electrical-installation-design`).
---

# DHC Spatial Blockly Builder

This skill governs the three JSON artifacts that the SmartHome Designer
loads to render the **spatial** Blockly workspace. **Claude writes the JSON
files directly** by reading the T-Box and `dhc-app-metadata.ttl` — there is
no intermediate code-generator script, and the Modeller pipeline consumes
these files unchanged.

The three artifacts:

| File                                    | Role                                                                |
|-----------------------------------------|---------------------------------------------------------------------|
| `blockly/dhc-spatial-blocks.json`       | Block **definitions** — shape, fields, inputs, outputs, colour, tooltip. |
| `blockly/dhc-spatial-toolbox.json`      | Toolbox **registration** — categories, ordering, default arguments.       |
| `blockly/dhc-spatial-workspace.json`    | Default workspace **state** — starter blocks for a fresh SmartHome.       |

## When to use this skill

Trigger on any of:

- "add a block for `dhc:Foo` to the spatial toolbox"
- "rebuild / regenerate the spatial Blockly artifacts"
- "wire up `dhc:blocklyBlockTemplate` for class X"
- "what should the block for `rec:Wing` look like?"
- editing files under `repos/core/blockly/` whose names match
  `dhc-spatial-*.json`
- previewing / debugging the spatial workspace
- adding the `@blockly/block-dynamic-connection` plugin behaviour to a
  spatial block (variable-arity `hasPart` slots)

Do **not** trigger for:

- T-Box authoring of new spatial classes — use `dhc-spatial-modeling`.
- Curator workflow (promote / delete / annotation review) — use
  `dhc-ontology-explorer`.
- Other design views. `electrical` is owned by
  `dhc-electrical-installation-design` (A-Box + NF C 15-100 shapes; it does not
  build Blockly artifacts). `plumbing`, `heating`, `network`, `automation` and
  `compliance` are not yet covered. This skill is scoped to
  `dhc:designView "spatial"` only.

## Inputs — what drives the build

Three TTL files in `repos/core/schema/tbox/`, in load order (later wins):

1. **`Brick+extensions.ttl`** (read-only baseline, Brick 1.4.4 distribution).
   Combines: Brick (equipment, sensors, points), RealEstateCore (spatial
   hierarchy: Building, Level, Room, Space), ASHRAE 223P / s223 (connection
   topology and medium flow). Defines the upstream classes that DHC
   subclasses.
2. **`dhc-core.ttl`** — DHC residential extension on top of REC. Adds
   `dhc:DetachedHouse`, `dhc:RowHouse`, `dhc:GrandTownhouse`,
   `dhc:SemiDetachedHouse`, `dhc:DigitalHome`, etc.
3. **`dhc-app-metadata.ttl`** — UI/UX overlay. The single source of truth
   for **which** classes become Blockly blocks and **how** they appear.
   **Every triple in the table below lives here**, never in `dhc-core.ttl`
   (the curator routes them automatically). When this skill talks about
   "the annotations on a class", it always means triples in
   `schema/tbox/dhc-app-metadata.ttl` — both for DHC-native classes
   (`dhc:DigitalHome`, `dhc:DetachedHouse`, `dhc:Garden`) and for whitelisted
   external classes (`rec:Hospital`, `rec:School`, `rec:Wing`).

The build is a pure projection of `dhc-app-metadata.ttl`. The driving
annotation set on each candidate class (all stored in that file):

| Annotation                       | Effect on the build                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------|
| `dhc:designView`                 | The class's primary domain (e.g. `"spatial"`, `"building"`). Used as the **toolbox category name** wherever the block is rendered. |
| `dhc:blocklyCategory`            | **Routing key** — names the design-view workspace this block appears in. Defaults to `dhc:designView` when unset (block lives only in its own primary view). When set to a different view (e.g. `"spatial"` for a class with `dhc:designView "building"`), the block also surfaces in *that* workspace, organized under a toolbox category named after its own `dhc:designView` (here, "Building"). Allowed values: the same enum as `dhc:designView`. |
| `dhc:isInstantiated true`        | Required — only instantiable classes become blocks. Abstract templates are skipped.  |
| `dhc:blocklyBlockTemplate <cls>` | The ancestor class whose properties define this block's I/O contract. Resolved via `dhc:choicesFrom "selfAndAncestors"` in the curator. |
| `dhc:blocklyDisposition`         | `block` (default), `variable` (cross-cutting), or `excluded` (hidden in the toolbox).     |
| `dhc:blocklyFieldType`           | On data properties: `text` / `number` / `dropdown` / `checkbox`.                         |
| `dhc:blocklyParentProperty`      | Object property that drives Blockly nesting (e.g. `dhc:hasCircuit`).                     |
| `rdfs:label @de` / `@fr`         | Localized block labels.                                                              |

> **Routing rule (cross-view inclusion).** The spatial workspace contains every
> class whose **effective category** is `"spatial"`, where the effective category
> is `dhc:blocklyCategory` if set, otherwise `dhc:designView`. The toolbox
> category *name* within the workspace is always the class's `dhc:designView`
> (capitalized). Concretely:
>
> - `dhc:DigitalHome` (`designView "spatial"`, no `blocklyCategory`) →
>   spatial workspace, **Spatial** category.
> - `rec:Level` (`designView "building"`, `blocklyCategory "spatial"`) →
>   spatial workspace, **Building** category.
> - `rec:Wing` (`designView "spatial"`, no `blocklyCategory`) →
>   spatial workspace, **Spatial** category.

The current spatial cohort (run the curator's option [3] on each to verify):

| Class                  | designView | blocklyCategory | Template       | Disposition | Notes                                  |
|------------------------|------------|-----------------|----------------|-------------|----------------------------------------|
| `dhc:DetachedHouse`    | spatial    | (default)       | `rec:Building` | block       |                                        |
| `dhc:DigitalHome`      | spatial    | (default)       | `dhc:DigitalHome` | block    | Tenant root; self-template.            |
| `dhc:GrandTownhouse`   | spatial    | (default)       | `rec:Building` | block       |                                        |
| `dhc:RowHouse`         | spatial    | (default)       | `rec:Building` | block       |                                        |
| `dhc:SemiDetachedHouse`| spatial    | (default)       | `rec:Building` | block       |                                        |
| `rec:Hospital`         | spatial    | (default)       | `rec:Building` | block       |                                        |
| `rec:School`           | spatial    | (default)       | `rec:Building` | block       |                                        |
| `rec:Wing`             | spatial    | (default)       | `rec:Wing`     | block       | Self-template.                         |
| `rec:Level`            | building   | **spatial**     | `rec:Level`    | block       | Cross-view: rendered in spatial workspace under "Building" category. |

Templates referenced but **not** themselves blocks (`isInstantiated false`):
`rec:Apartment`, `rec:Architecture`, `rec:Building`, `rec:Space`. They
contribute *shape* (object/data properties) but never appear in the toolbox.

## Workflow

When asked to add or rebuild a spatial block:

1. **Identify the candidate set.** Read `dhc-app-metadata.ttl` and select
   classes where the **effective category** is `"spatial"` AND
   `dhc:isInstantiated = true`. Effective category =
   `dhc:blocklyCategory` if set, otherwise `dhc:designView`. This pulls in
   foreign-domain classes (e.g. `rec:Level` with `designView "building"`
   and `blocklyCategory "spatial"`). See the table above.
2. **Resolve each block's template.** For class `cls`, follow
   `dhc:blocklyBlockTemplate` to get the template class. The template is
   one of `cls` itself or an ancestor (`rdfs:subClassOf*`) — enforced by
   `dhc:choicesFrom "selfAndAncestors"` in the curator.
3. **Derive the I/O contract from the template.** Walk
   `rdfs:subClassOf*` from the template up to `rec:Space`, collecting:
   - **Object properties** with the template (or an ancestor) as
     `rdfs:domain` → become Blockly **inputs/outputs** (statement or value
     connections, depending on the property's range).
   - **Data properties** with the template (or an ancestor) as
     `rdfs:domain` → become Blockly **fields**, widget chosen by
     `dhc:blocklyFieldType` on the property.
4. **Author the block definition** in `blockly/dhc-spatial-blocks.json`.
   Reuse an existing template entry if one already covers this contract;
   otherwise add a new template record and reference it.
5. **Register the block** in `blockly/dhc-spatial-toolbox.json` under a
   category named after the class's `dhc:designView` (capitalized — e.g.
   "Spatial", "Building"). Native classes (effective category =
   `dhc:designView` = "spatial") land under "Spatial"; cross-view classes
   pulled in via `dhc:blocklyCategory "spatial"` land under their own
   `dhc:designView` (e.g. `rec:Level` → "Building"). Honour
   `dhc:blocklyDisposition`: skip if `excluded`; render under the
   "Variables" group if `variable`.
6. **Update the workspace seed** in `blockly/dhc-spatial-workspace.json`
   only when the change affects the starter layout (rare — usually only
   when adding/removing a tenant-root block like `dhc:DigitalHome`).
7. **Verify.** See `## Verification protocol` below.

## Output file schemas

Claude writes these files to match the Blockly JSON conventions consumed
by the Designer's `BlocklyWorkspace` component.

### `dhc-spatial-blocks.json`

A single object with a `blocks` array. Each entry is one block definition.
Block `type` is the CURIE of the class (`dhc:DetachedHouse`,
`rec:Wing`, …) so the runtime can dereference back into the T-Box.

```json
{
  "blocks": [
    {
      "type": "dhc:DetachedHouse",
      "message0": "%1 detached house",
      "args0": [
        { "type": "field_input", "name": "name", "text": "House" }
      ],
      "previousStatement": "rec:Architecture",
      "nextStatement":     "rec:Architecture",
      "inputsInline": false,
      "colour": 230,
      "tooltip": "A detached single-family residence.",
      "helpUrl": "",
      "extensions": ["dhc_spatial_extension"],
      "mutator":   "dhc_dynamic_haspart",
      "data":      "dhc:blocklyBlockTemplate=rec:Building"
    }
  ]
}
```

Notes:
- `previousStatement` / `nextStatement` typing comes from the template's
  `rdfs:subClassOf` chain — `rec:Building` → `rec:Architecture` →
  `rec:Space`. Use the most-specific shared parent that captures the
  intended attachment surface (typically `rec:Architecture` for buildings,
  `rec:Space` for rooms).
- The `data` field carries the template provenance so the Modeller pipeline
  can re-link to the T-Box without re-parsing the toolbox.
- `mutator: "dhc_dynamic_haspart"` opts the block into the
  `@blockly/block-dynamic-connection` plugin (variable-arity `hasPart`
  slots — see *Plugins* below).

### `dhc-spatial-toolbox.json`

```json
{
  "kind": "categoryToolbox",
  "contents": [
    {
      "kind": "category",
      "name": "Spatial",
      "colour": 230,
      "contents": [
        { "kind": "block", "type": "dhc:DigitalHome" },
        { "kind": "block", "type": "dhc:DetachedHouse" },
        { "kind": "block", "type": "dhc:RowHouse" },
        { "kind": "block", "type": "dhc:Wing" },
        { "kind": "label", "text": "Public buildings" },
        { "kind": "block", "type": "rec:Hospital" },
        { "kind": "block", "type": "rec:School" }
      ]
    },
    {
      "kind": "category",
      "name": "Building",
      "colour": 230,
      "contents": [
        { "kind": "block", "type": "rec:Level" }
      ]
    }
  ]
}
```

- One category per **distinct `dhc:designView` value across the candidate
  set**. Native classes (`dhc:designView "spatial"`) → "Spatial".
  Cross-view classes pulled in via `dhc:blocklyCategory "spatial"` →
  category named after their own `dhc:designView` (e.g. `rec:Level`
  contributes a "Building" category in the spatial workspace).
- Order within a category follows `dhc-app-metadata.ttl` declaration order
  (use the same file-order discipline that drives the curator's prompt
  loop). When in doubt, group residential first, public buildings second,
  outbuildings last.
- Skip any class with `dhc:blocklyDisposition "excluded"`. Render
  `variable`-disposition entries under a separate `<sep></sep>` divider.

### `dhc-spatial-workspace.json`

Default seed for a fresh SmartHome — minimal, just enough to kick off
modelling. Typically a single `dhc:DigitalHome` root with one nested
`dhc:DetachedHouse` placeholder.

```json
{
  "blocks": {
    "languageVersion": 0,
    "blocks": [
      {
        "type": "dhc:DigitalHome",
        "x": 40, "y": 40,
        "fields": { "name": "MyHome" },
        "inputs": {
          "hasPart": {
            "block": { "type": "dhc:DetachedHouse",
                       "fields": { "name": "House" } }
          }
        }
      }
    ]
  }
}
```

Block IDs may be omitted in the seed — Blockly assigns them at load. Add
explicit IDs only when the workspace must reference a block by ID (rare
for the seed).

## Plugins

Spatial blocks use **`@blockly/block-dynamic-connection`** so the
`hasPart` input accepts a variable number of children without the user
having to add inputs by hand.

- Registered once in `blockly/registerPlugins.js` (create the file if it
  doesn't exist; `import` it from the Designer's Blockly bootstrap).
- Per-block opt-in via `"mutator": "dhc_dynamic_haspart"` in the block
  definition. The mutator name is project-local; map it to
  `Blockly.Extensions.registerMutator(...)` in the same registration file.

Reference: <https://github.com/google/blockly-samples/tree/master/plugins/block-dynamic-connection>

## Style

Spatial blocks share one colour family (suggested hue: **230** — the
slate/blue used elsewhere in the Designer). Keep `inputsInline: false`
for hierarchical blocks (Building / Wing / Level), `true` for leaf-ish
blocks (Room / Space).

For visual reference, see `./spatial.png` (the spatial relationship
diagram) and `./blockly-dynamic-connection-demo.png` (the live
Blockly preview style).

## Worked example — `dhc:DetachedHouse` with template `rec:Building`

Inputs from the T-Box:

```turtle
dhc:DetachedHouse a owl:Class ;
    rdfs:subClassOf rec:Building ;
    rdfs:label "Detached House"@en, "Freistehendes Haus"@de, "Maison isolée"@fr ;
    dhc:designView "spatial" ;
    dhc:isInstantiated true ;
    dhc:blocklyBlockTemplate "rec:Building" .
```

Walking the template:

```
rec:Building   ─ subClassOf →  rec:Architecture  ─ subClassOf →  rec:Space
   │                                                                  │
   ├─ rec:hasPart        (Space)        — variable-arity input        │
   ├─ rec:isPartOf       (Space)        — output / parent connector   │
   ├─ rec:hasGeometry    (xsd:string)   — field, JSON GeoJSON         │
   └─ rec:levelNumber    (xsd:integer)  — field, number widget        │
```

The resulting block definition (one entry inside
`dhc-spatial-blocks.json`):

```json
{
  "type": "dhc:DetachedHouse",
  "message0": "%1 %2 detached house  level %3  geometry %4",
  "args0": [
    { "type": "field_image", "src": "icons/spatial/detached_house.svg",
      "width": 16, "height": 16, "alt": "🏠", "flipRtl": false },
    { "type": "field_input",  "name": "name",        "text": "House" },
    { "type": "field_number", "name": "levelNumber", "value": 1, "min": 0 },
    { "type": "field_input",  "name": "geometry",    "text": "" }
  ],
  "message1": "rooms %1",
  "args1": [
    { "type": "input_statement", "name": "hasPart", "check": "rec:Space" }
  ],
  "previousStatement": "rec:Architecture",
  "nextStatement":     "rec:Architecture",
  "inputsInline": false,
  "colour": 230,
  "tooltip": "A detached single-family residence.",
  "helpUrl": "",
  "mutator": "dhc_dynamic_haspart",
  "data":    "dhc:blocklyBlockTemplate=rec:Building"
}
```

Toolbox registration appended to `dhc-spatial-toolbox.json` under the
"Spatial" category, in the position dictated by file order in
`dhc-app-metadata.ttl`:

```json
{ "kind": "block", "type": "dhc:DetachedHouse" }
```

No workspace seed change required — `dhc:DetachedHouse` is already the
default child of `dhc:DigitalHome` in the seed.

## Files this skill touches

| Path                                          | Read | Write |
|-----------------------------------------------|------|-------|
| `schema/tbox/Brick+extensions.ttl`            | yes  | **no** (read-only baseline) |
| `schema/tbox/dhc-core.ttl`                    | yes  | no — owned by `dhc-spatial-modeling` |
| `schema/tbox/dhc-app-metadata.ttl`            | yes  | no — owned by `dhc-ontology-explorer` |
| `blockly/dhc-spatial-blocks.json`             | yes  | yes — created on first run |
| `blockly/dhc-spatial-toolbox.json`            | yes  | yes — created on first run |
| `blockly/dhc-spatial-workspace.json`          | yes  | yes — created on first run |
| `blockly/registerPlugins.js`                  | yes  | yes — only when adding plugin extensions/mutators |

The `blockly/` directory does not exist yet at the time this skill was
authored — the first invocation creates it.

## Verification protocol

After authoring or updating any of the three JSON files:

1. **JSON parses.** `python3 -c "import json; json.load(open('blockly/dhc-spatial-blocks.json'))"`
   on each file. No silent corruption.
2. **Every spatial block has a definition.** For every class with
   `dhc:designView "spatial"` AND `dhc:isInstantiated true` AND
   `dhc:blocklyDisposition != "excluded"`: there is one entry in
   `dhc-spatial-blocks.json` with matching `type` and one entry in
   `dhc-spatial-toolbox.json`.
3. **No orphaned toolbox entries.** Every `type` referenced in
   `dhc-spatial-toolbox.json` is defined in `dhc-spatial-blocks.json`.
4. **Templates resolve.** Every block's `data` field points at a class
   that exists in the T-Box (`dhc:`/`rec:`/`brick:` namespaces).
5. **Preview.** `npm run blockly:preview-spatial` — starts a local static
   server (Python's stdlib `http.server`) on port 8765 and opens
   `blockly/preview.html`, which loads Blockly from a CDN and `fetch()`es
   the three JSON files from the same directory. Stop with Ctrl-C.

## Common pitfalls

- **Including a `isInstantiated false` class as a block.** Templates like
  `rec:Building`, `rec:Space`, `rec:Architecture`, `rec:Apartment` provide
  shape but are **not** draggable blocks. Filter them out before writing.
- **Hard-coding the template's properties on every subclass.** Walk
  `rdfs:subClassOf*` from the template and merge — duplicating fields
  per-subclass causes drift the first time a property is renamed in the
  T-Box.
- **Routing edits through `dhc-app-metadata.ttl` directly.** Don't.
  Annotations like `dhc:blocklyBlockTemplate` and `dhc:blocklyDisposition`
  are owned by the curator (`ontology_explorer.py` option [4]). Edit the
  TTL only when bootstrapping a new annotation property; otherwise the
  curator's structured serializer will overwrite ad-hoc edits.
- **Mixing categories.** `dhc:designView` is the partition key. A spatial
  block must not appear in the electrical toolbox even if it has
  electrical sub-relationships — those land in the electrical view's
  block contract instead.
- **Writing IDs into the workspace seed.** Let Blockly assign them on
  load unless a downstream tool needs to address a block by ID.

## Out of scope

- T-Box authoring (parent-class choice, new `dhc:` classes, `@de`/`@fr`
  labels, `dhc:designView` assignment) → `dhc-spatial-modeling`.
- Curator workflow (promote / delete / annotation review / order in the
  `§ Application annotation property definitions` section) →
  `dhc-ontology-explorer`.
- Other design views — each gets its own `dhc-build-blockly-elements-for-*`
  skill.
- A-Box instance authoring — Designer's responsibility, S3-stored.
- `ontology-graph.json` and `cbox-registry.json` — Modeller's
  responsibility.
