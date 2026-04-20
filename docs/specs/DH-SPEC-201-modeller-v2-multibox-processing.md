# DH-SPEC-004 — DHC Modeller v2: Processing the Multi-Box Ontology

| Field          | Value                                      |
|----------------|--------------------------------------------|
| **Spec ID**    | DH-SPEC-201                              |
| **Version**    | 0.1.0 (draft)                              |
| **Status**     | Draft                                      |
| **Author**     | D-LAB-5 / DigitalHome.Cloud                |
| **Created**    | 2026-04-19                                 |
| **Depends on** | DH-SPEC-201 (Ontology v2.0.0 Multi-Box Architecture) |
| **Consumers**  | DHC Smart Home Designer, DHC Portal        |

---

## §1 — Purpose

This specification defines the DHC Modeller v2 — the processing pipeline that reads the v2.0.0 Multi-Box ontology from `digitalhome-cloud-core` [git] and produces the artifacts consumed by the DHC Smart Home Designer.

The Modeller is the **bridge** between the schema repository (T-Box + C-Box in Turtle) and the runtime design environment (3D graph viewer + Blockly workspace).

## §2 — Scope

### In scope

- Ingestion: **raw-file read** of `schema/*.ttl` and `schema/*.json` from a selected branch of `digitalhome-cloud-core` via `raw.githubusercontent.com` (no git clone; no local checkout). Branch selection is a user action in the Modeller Config page.
- RDF processing: parse Turtle, convert between Turtle ↔ JSON-LD in the workdir
- 3D graph generation: T-Box → `ontology-graph.json` for the Three.js viewer
- C-Box overlay on 3D graph: norm governance indicators on graph nodes
- Blockly generation: T-Box + C-Box → `blockly-blocks.json` + `blockly-toolbox.json`
- C-Box registry: `cbox-registry.json` for the Designer's norm activation UI
- Publication: upload all generated artifacts to S3

### Out of scope

- A-Box creation (Designer's responsibility)
- A-Box validation at runtime (Designer's responsibility, using C-Box shapes)
- Schema authoring (AI Agent + git workflow)
- The SmartHome Manager UI (DH-SPEC-002)

## §3 — Data Flow

```
┌──────────────────────────────────────────────────────────┐
│  digitalhome-cloud-core [git v2.0.0]                     │
│                                                          │
│  schema/tbox/                                            │
│    dhc-core.schema.ttl   ← T-Box + R-Box                │
│    dhc-roles.ttl         ← Role instances                │
│    context.jsonld        ← JSON-LD context               │
│                                                          │
│  schema/cbox/                                            │
│    cbox-manifest.json    ← Norm registry                 │
│    electrical/                                           │
│      nfc14100.shapes.ttl ← C-Box: SHACL shapes          │
│      nfc15100.shapes.ttl                                 │
│      ...                                                 │
└──────────────────┬───────────────────────────────────────┘
                   │ HTTPS raw read per branch
                   ▼
┌──────────────────────────────────────────────────────────┐
│  DHC Modeller                                            │
│  (workdir in S3: public/ontology/workdir/{branch}/)      │
│                                                          │
│  Step 1: Parse TTL → in-memory RDF graph                 │
│  Step 2: TTL ↔ JSON-LD conversion (in memory)            │
│  Step 3: T-Box → ontology-graph.json (3D viewer)         │
│  Step 4: C-Box → norm overlay metadata (graph + Blockly) │
│  Step 5: T-Box + C-Box → Blockly blocks + toolbox        │
│  Step 6: C-Box → cbox-registry.json                      │
│                                                          │
└──────────────────┬───────────────────────────────────────┘
                   │ publish to S3
                   ▼
┌──────────────────────────────────────────────────────────┐
│  S3 Bucket                                               │
│                                                          │
│  ontology-graph.json      ← 3D viewer data               │
│  blockly-blocks.json      ← Block definitions            │
│  blockly-toolbox.json     ← Toolbox categories           │
│  cbox-registry.json       ← Norm profiles + constraints  │
│  context.jsonld           ← JSON-LD context (copy)       │
│                                                          │
└──────────────────┬───────────────────────────────────────┘
                   │ fetched at runtime
                   ▼
┌──────────────────────────────────────────────────────────┐
│  DHC Smart Home Designer                                 │
│                                                          │
│  Three.js Viewer    ← ontology-graph.json + C-Box overlay│
│  Blockly Workspace  ← blockly-blocks + toolbox + cbox    │
│  Norm Validation    ← cbox-registry.json (SHACL shapes)  │
│                                                          │
│  Produces: A-Box [S3 / IndexedDB]                        │
└──────────────────────────────────────────────────────────┘
```

## §4 — Step 1: TTL Ingestion & RDF Parsing

### §4.1 — Source Files

The Modeller reads each source file over HTTPS from
`https://raw.githubusercontent.com/<org>/digitalhome-cloud-core/<branch>/<path>`.
No git clone or local checkout is performed; the Modeller is a browser app and
the repo is fetched file-by-file against the raw-content host. Branch selection
is persisted client-side (`localStorage["dhc-modeler-branch"]`) and chosen in
the Modeller Config page.

**Authentication prerequisite.** The user must be signed in via Cognito
(Amplify Auth) and belong to the `dhc-modelers` or `dhc-admins` group. This
gates write access to the S3 workdir; the raw GitHub read itself is public and
unauthenticated. Any fetch failure surfaces to the user — there is no silent
fallback chain.

The Modeller reads from the `schema/` directory of `digitalhome-cloud-core`:

| File | Box | Purpose |
|------|-----|---------|
| `schema/tbox/dhc-core.schema.ttl` | T-Box + R-Box | Classes, properties, axioms, enum instances |
| `schema/tbox/dhc-roles.ttl` | T-Box | Role instances |
| `schema/tbox/context.jsonld` | — | JSON-LD context for serialization |
| `schema/cbox/cbox-manifest.json` | — | Norm profile registry |
| `schema/cbox/<domain>/*.shapes.ttl` | C-Box | SHACL shapes per norm |

### §4.2 — Parser

Use [N3.js](https://github.com/rdfjs/N3.js) (same as tests in the core repo). The Modeller builds an in-memory quad store from all T-Box and C-Box files combined.

### §4.3 — Working Directory

The Modeller's working directory lives in S3, not on disk. Each branch has its
own subdirectory so that users can switch branches without clobbering an
in-progress build.

```
S3 workdir (per branch):
  public/ontology/workdir/{branch}/
    ontology-graph.json          ← 3D viewer
    blockly-blocks.json          ← Block definitions (with normConstraints)
    blockly-toolbox.json         ← Toolbox structure
    cbox-registry.json           ← NEW in v2 — norm metadata + constraints
    context.jsonld               ← NEW in v2 — copy from source
    build-meta.json              ← { builtBy, builtAt, branch, version,
                                     sourceCommitShas?, pipelineVersion }
```

Parsed N-Quads and intermediate JSON-LD representations are held **in memory
only** during a build run and are not persisted. Only the final output
artifacts above are written to the workdir.

No files are written back to git from the Modeller; git stays read-only via
the raw-content host.

### §4.4 — Workdir as Build Cache (enhancement)

The per-branch workdir subdirectory already exists (see §4.3); the caching
logic on top of it does not. Today every "Fetch" + "Build" action re-fetches
every raw file and re-runs the full pipeline, overwriting the workdir.

**Enhancement.** Extend `build-meta.json` with source fingerprints — either the
GitHub commit SHA of the branch tip (one API call against
`api.github.com/repos/<org>/digitalhome-cloud-core/commits/<branch>`) or a
per-file content hash / `ETag` captured from the raw-fetch responses. On the
next Fetch:

1. Recompute the fingerprint for the selected branch.
2. If it matches the fingerprint in `build-meta.json` **and** the Modeller's
   own `pipelineVersion` matches, skip parsing and reuse the existing workdir
   artifacts.
3. Otherwise, rebuild.

**Scope.** The cache is per-branch by construction — switching branches in the
Config UI selects the corresponding cached workdir; a stale branch just
triggers a rebuild. Changing Modeller build code must bump `pipelineVersion`
so caches are invalidated even if source is unchanged.

## §5 — Step 2: TTL ↔ JSON-LD Conversion

The Modeller performs bidirectional conversion using the `context.jsonld` from the T-Box:

- **TTL → JSON-LD**: For downstream consumers that prefer JSON-LD (Portal, Designer runtime).
- **JSON-LD → TTL**: Not needed in the standard pipeline but available as a utility for roundtrip validation.

Library: [jsonld.js](https://github.com/digitalbazaar/jsonld.js) for compaction/expansion, N3.js for serialization.

The `context.jsonld` is copied to S3 as-is, since it is the canonical mapping for A-Box serialization.

## §6 — Step 3: T-Box → 3D Graph (ontology-graph.json)

### §6.1 — Graph Structure

Same as v1 — the `ontology-graph.json` is a node-link graph for the Three.js viewer. Each OWL class becomes a node, each ObjectProperty becomes an edge.

```json
{
  "version": "2.0.0",
  "nodes": [
    {
      "id": "dhc:RealEstate",
      "label": { "en": "Real Estate", "de": "Immobilie", "fr": "Bien immobilier" },
      "designView": "spatial",
      "type": "class",
      "superClass": null,
      "governedByNorms": []
    },
    {
      "id": "dhc:Circuit",
      "label": { "en": "Circuit", "de": "Stromkreis", "fr": "Circuit" },
      "designView": "electrical",
      "type": "class",
      "superClass": null,
      "governedByNorms": ["nfc14100", "nfc15100", "din-vde-0100", "arei-rgie", "bs7671"]
    },
    {
      "id": "dhc:CircuitType_Lighting",
      "label": { "en": "Lighting", "de": "Beleuchtung", "fr": "Éclairage" },
      "designView": "electrical",
      "type": "enumInstance",
      "instanceOf": "dhc:CircuitType"
    }
  ],
  "edges": [
    {
      "source": "dhc:DistributionBoard",
      "target": "dhc:Circuit",
      "property": "dhc:hasCircuit",
      "label": { "en": "has circuit" }
    }
  ]
}
```

### §6.2 — New in v2: `governedByNorms` Array

For each T-Box class, the Modeller scans all C-Box shape files to find which norms reference that class via `sh:targetClass`. The resulting norm IDs are collected into the `governedByNorms` array on each node.

This is the data source for the C-Box overlay in the 3D viewer (§7).

### §6.3 — Extraction Logic

```
For each triple (?class a owl:Class):
  node.id        = ?class
  node.label     = rdfs:label values by language tag
  node.designView = dhc:designView value
  node.superClass = rdfs:subClassOf value (if any)
  node.type      = "class"

For each triple (?instance a dhc:CircuitType) (or any enum class):
  node.type      = "enumInstance"
  node.instanceOf = the class URI

For each triple (?prop a owl:ObjectProperty):
  edge.source    = rdfs:domain
  edge.target    = rdfs:range
  edge.property  = ?prop
  edge.label     = rdfs:label values

For each C-Box shape with sh:targetClass ?class:
  Extract dhc:normId from the shape's ontology metadata
  Append normId to nodes[?class].governedByNorms
```

## §7 — C-Box Overlay on 3D Graph

### §7.1 — Visual Indicator

When a C-Box norm is **turned on** in the viewer, every node whose `governedByNorms` array includes that norm ID gets a visual marker — a location-pointer icon (📍) rendered as a Three.js sprite or HTML overlay at the node position.

### §7.2 — Norm Toggle UI

The viewer provides a toggle panel listing available norms (from `cbox-registry.json`). Starting with:

- ☐ NF C 14-100 (FR — Energy delivery)
- ☐ NF C 15-100 (FR — Installation)

When toggled on, the corresponding norm indicators appear on the graph.

### §7.3 — Interaction: Two Display Modes

| Mode | Trigger | Content |
|------|---------|---------|
| **Hover** | Mouse over a governed node | Tooltip showing: norm name, constraint count, summary (e.g., "5 SHACL shapes apply to Circuit under NF C 15-100") |
| **Inspector** | Click/select a governed node | Inspector panel (same as current) extended with a "Compliance" tab listing all active norm shapes, their constraints (maxPoints, ratedCurrent, crossSection…), and the default values |

### §7.4 — Data for Overlay

The `ontology-graph.json` carries the `governedByNorms` array per node. The detailed shape constraints are in `cbox-registry.json` (§11). The viewer cross-references both at runtime.

## §8 — Step 5: T-Box + C-Box → Blockly Blocks & Toolbox

This is the most significant change in the Modeller v2. The conversion must support two distinct use cases in the Designer.

### §8.1 — Design View → Blockly Workspace Mapping

| `dhc:designView` value | Blockly disposition | Notes |
|------------------------|---------------------|-------|
| `spatial` | **Not in Blockly.** Handled by SmartHome Manager (New SmartHome wizard, map/geo selection). | RealEstate, Area, Floor, Space, Zone |
| `building` | Blockly **Building** toolbox + workspace | Walls, windows, doors, roof, insulation |
| `electrical` | Blockly **Electrical** toolbox + workspace | Circuits, boards, protection, wiring, e-mobility |
| `plumbing` | Blockly **Plumbing** toolbox + workspace | Water supply, drainage, fixtures, pipes |
| `heating` | Blockly **Heating** toolbox + workspace | HVAC, heat sources, emitters, thermostats |
| `network` | Blockly **Network** toolbox + workspace | LAN, WiFi, ZigBee, gateways |
| `governance` | **Not in Blockly.** Integrated as forms/wizards in the SmartHome Manager. | Agents, roles, role assignments, projects |
| `automation` | Blockly **variables** (not blocks) available in **all** workspaces | Groups, scenarios — cross-cutting, assignable to any element |
| `compliance` | **Constrains** Blockly toolboxes + workspaces (not its own workspace) | Norms, governed-by relationships |

### §8.2 — Automation as Cross-Cutting Variables

Classes with `dhc:designView "automation"` (`dhc:Group`, `dhc:Scenario`, `dhc:Sensor`, `dhc:Actor`) are generated as **Blockly variables**, not blocks. They appear in the variable drawer of every workspace so that users can assign automation groups and scenarios to any element across domains.

```json
{
  "kind": "variable",
  "name": "Night Lighting",
  "type": "dhc:Group",
  "id": "var_group_01"
}
```

### §8.3 — Two Use Cases for C-Box in Blockly

#### Use Case 1: Retrofit / Audit (Norm OFF)

> "I map my existing installation to the A-Box using the Blockly designer. Then I validate against the norm and produce a gap report."

- The Designer loads blocks **without** norm constraints active.
- User freely places Circuit blocks, assigns CircuitTypes, sets properties.
- No warnings, no enforcement — pure mapping of existing reality.
- Separately, a **Validate** action runs the A-Box against selected C-Box SHACL shapes and produces a gap/compliance report.

**Modeller responsibility**: Generate blocks with **all** property fields visible but no constraints enforced. The validation step uses `cbox-registry.json` shapes against the A-Box — this happens in the Designer, not the Modeller.

#### Use Case 2: New Design (Norm ON)

> "I create a new house or new circuit. The norm is turned on and the Blockly designer provides support and alerts if the norm is not followed."

- The Designer loads blocks **with** C-Box constraints active for the selected norm(s).
- When a user creates a Lighting Circuit under NF C 15-100:
  - `maxPoints` field shows max=8 hint
  - `ratedCurrent` pre-fills with 10A
  - `crossSection` pre-fills with 1.5 (and shows min=1.5)
  - Inline warnings if constraints are violated

**Modeller responsibility**: Generate blocks that include constraint metadata from C-Box shapes. The `blockly-blocks.json` carries **both** the base block definition (from T-Box) and the norm-specific constraint overlays (from C-Box).

### §8.4 — Block Definition Structure

```json
{
  "blocks": [
    {
      "type": "dhc_Circuit",
      "designView": "electrical",
      "class": "dhc:Circuit",
      "label": { "en": "Circuit", "de": "Stromkreis", "fr": "Circuit" },
      "fields": [
        {
          "name": "hasCircuitType",
          "type": "dropdown",
          "options": [
            { "value": "dhc:CircuitType_Lighting", "label": { "en": "Lighting", "de": "Beleuchtung", "fr": "Éclairage" } },
            { "value": "dhc:CircuitType_Socket", "label": { "en": "Socket", "de": "Steckdose", "fr": "Prise" } }
          ]
        },
        {
          "name": "maxPoints",
          "type": "number",
          "label": { "en": "Max points", "de": "Max. Punkte", "fr": "Points max." }
        },
        {
          "name": "ratedCurrent",
          "type": "number",
          "unit": "A",
          "label": { "en": "Rated current (A)", "de": "Nennstrom (A)", "fr": "Courant nominal (A)" }
        },
        {
          "name": "crossSection",
          "type": "number",
          "unit": "mm²",
          "label": { "en": "Cross section (mm²)", "de": "Querschnitt (mm²)", "fr": "Section (mm²)" }
        },
        {
          "name": "wiring",
          "type": "text",
          "label": { "en": "Wiring", "de": "Verdrahtung", "fr": "Câblage" }
        },
        {
          "name": "phase",
          "type": "number",
          "label": { "en": "Phase", "de": "Phase", "fr": "Phase" }
        }
      ],
      "connections": {
        "parent": "dhc_DistributionBoard",
        "property": "dhc:hasCircuit"
      },
      "children": [
        { "accepts": "dhc_ProtectionDevice", "property": "dhc:hasProtection" },
        { "accepts": "dhc_Equipment", "property": "dhc:feedsEquipment" }
      ],
      "normConstraints": {
        "nfc15100": [
          {
            "condition": { "hasCircuitType": "dhc:CircuitType_Lighting" },
            "constraints": {
              "maxPoints": { "maxInclusive": 8 },
              "ratedCurrent": { "maxInclusive": 10 },
              "crossSection": { "minInclusive": 1.5 }
            },
            "defaults": {
              "ratedCurrent": 10,
              "crossSection": 1.5,
              "wiring": "3G1.5"
            },
            "messages": {
              "maxPoints": { "en": "NF C 15-100: max 8 points on lighting circuit", "de": "NF C 15-100: max. 8 Punkte am Beleuchtungsstromkreis", "fr": "NF C 15-100 : max. 8 points par circuit éclairage" }
            }
          },
          {
            "condition": { "hasCircuitType": "dhc:CircuitType_Socket" },
            "constraints": {
              "maxPoints": { "maxInclusive": 8 },
              "ratedCurrent": { "maxInclusive": 16 },
              "crossSection": { "minInclusive": 1.5 }
            },
            "defaults": {
              "ratedCurrent": 16,
              "crossSection": 1.5,
              "wiring": "3G1.5"
            }
          }
        ],
        "din-vde-0100": [
          {
            "condition": { "hasCircuitType": "dhc:CircuitType_Lighting" },
            "constraints": {
              "ratedCurrent": { "maxInclusive": 10 },
              "crossSection": { "minInclusive": 1.5 }
            },
            "defaults": {
              "ratedCurrent": 10,
              "crossSection": 1.5,
              "wiring": "NYM 3x1.5"
            }
          }
        ]
      }
    }
  ]
}
```

### §8.5 — Toolbox Structure

```json
{
  "toolbox": {
    "kind": "categoryToolbox",
    "contents": [
      {
        "kind": "category",
        "name": { "en": "Building", "de": "Gebäude", "fr": "Bâtiment" },
        "designView": "building",
        "colour": "#8B4513",
        "contents": [
          { "kind": "block", "type": "dhc_Wall" },
          { "kind": "block", "type": "dhc_Window" },
          { "kind": "block", "type": "dhc_Door" },
          { "kind": "block", "type": "dhc_Roof" },
          { "kind": "block", "type": "dhc_Insulation" }
        ]
      },
      {
        "kind": "category",
        "name": { "en": "Electrical", "de": "Elektro", "fr": "Électrique" },
        "designView": "electrical",
        "colour": "#DAA520",
        "contents": [
          { "kind": "block", "type": "dhc_EnergyDelivery" },
          { "kind": "block", "type": "dhc_EnergyMeter" },
          { "kind": "block", "type": "dhc_EmergencyDisconnect" },
          { "kind": "block", "type": "dhc_DistributionBoard" },
          { "kind": "block", "type": "dhc_Circuit" },
          { "kind": "block", "type": "dhc_ProtectionDevice" },
          { "kind": "block", "type": "dhc_WiringSegment" }
        ]
      },
      {
        "kind": "category",
        "name": { "en": "Plumbing", "de": "Sanitär", "fr": "Plomberie" },
        "designView": "plumbing",
        "colour": "#4682B4"
      },
      {
        "kind": "category",
        "name": { "en": "Heating", "de": "Heizung", "fr": "Chauffage" },
        "designView": "heating",
        "colour": "#CD5C5C"
      },
      {
        "kind": "category",
        "name": { "en": "Network", "de": "Netzwerk", "fr": "Réseau" },
        "designView": "network",
        "colour": "#2E8B57"
      }
    ]
  },
  "variables": [
    {
      "kind": "variable",
      "type": "dhc:Group",
      "label": { "en": "Group", "de": "Gruppe", "fr": "Groupe" }
    },
    {
      "kind": "variable",
      "type": "dhc:Scenario",
      "label": { "en": "Scenario", "de": "Szenario", "fr": "Scénario" }
    }
  ]
}
```

## §9 — C-Box Design Constraints: Extending the Ontology

### §9.1 — The Problem

The current C-Box shapes are **norm/validation constraints** — they tell the Designer "is this A-Box valid against NF C 15-100?". But the Modeller also needs **design constraints** — metadata that tells Blockly *how to render and connect blocks*:

- Which classes become blocks vs. variables vs. excluded?
- What is the parent-child nesting hierarchy?
- Which properties become fields, dropdowns, connections?
- What are the toolbox categories and colors?

### §9.2 — Proposal: `dhc:blockly*` Annotations in the T-Box

Rather than creating separate C-Box files for design constraints, we annotate the T-Box classes and properties with `dhc:blockly*` properties. These are **design-time metadata** intrinsic to the vocabulary, not norm-specific.

```turtle
# ── Blockly design annotations (in dhc-core.schema.ttl) ──

dhc:blocklyDisposition
    a owl:DatatypeProperty ;
    rdfs:label "blockly disposition"@en ;
    rdfs:domain owl:Class ;
    rdfs:range xsd:string ;
    rdfs:comment "How this class maps to Blockly: 'block', 'variable', 'excluded'."@en .

dhc:blocklyCategory
    a owl:DatatypeProperty ;
    rdfs:label "blockly category"@en ;
    rdfs:domain owl:Class ;
    rdfs:range xsd:string ;
    rdfs:comment "Toolbox category for this block. Matches dhc:designView unless overridden."@en .

dhc:blocklyColor
    a owl:DatatypeProperty ;
    rdfs:label "blockly color"@en ;
    rdfs:domain owl:Class ;
    rdfs:range xsd:string ;
    rdfs:comment "Hex color for the block in Blockly (e.g. '#DAA520')."@en .

dhc:blocklyParentProperty
    a owl:ObjectProperty ;
    rdfs:label "blockly parent property"@en ;
    rdfs:comment "The ObjectProperty connecting this block to its parent in the Blockly nesting hierarchy."@en .

dhc:blocklyFieldType
    a owl:DatatypeProperty ;
    rdfs:label "blockly field type"@en ;
    rdfs:domain owl:DatatypeProperty ;
    rdfs:range xsd:string ;
    rdfs:comment "Blockly field rendering: 'number', 'text', 'dropdown', 'checkbox'."@en .
```

Usage in T-Box:

```turtle
dhc:Circuit
    a owl:Class ;
    rdfs:label "Circuit"@en ;
    dhc:designView "electrical" ;
    dhc:blocklyDisposition "block" ;
    dhc:blocklyParentProperty dhc:hasCircuit ;
    dhc:blocklyColor "#DAA520" .

dhc:Group
    a owl:Class ;
    rdfs:label "Group"@en ;
    dhc:designView "automation" ;
    dhc:blocklyDisposition "variable" .

dhc:RealEstate
    a owl:Class ;
    rdfs:label "Real Estate"@en ;
    dhc:designView "spatial" ;
    dhc:blocklyDisposition "excluded" .

dhc:Agent
    a owl:Class ;
    rdfs:label "Agent"@en ;
    dhc:designView "governance" ;
    dhc:blocklyDisposition "excluded" .
```

### §9.3 — Alternative Considered: C-Box Design Shapes

A separate `schema/cbox/design/blockly-mapping.shapes.ttl` file could express design constraints as SHACL shapes. This was rejected because:

1. Design constraints are **intrinsic to the vocabulary** — they don't vary by country or norm.
2. They would add a third "kind" of C-Box (norm constraints vs. design constraints), muddying the model.
3. Keeping them as T-Box annotations means the Modeller reads one source (T-Box) for all Blockly generation, with C-Box overlaying norm constraints on top.

### §9.4 — Fallback Defaults

If a class lacks `dhc:blocklyDisposition`, the Modeller applies these defaults based on `dhc:designView`:

| `dhc:designView` | Default `blocklyDisposition` |
|-------------------|------------------------------|
| `spatial` | `excluded` |
| `governance` | `excluded` |
| `automation` | `variable` |
| `compliance` | `excluded` (constraints only) |
| Any other | `block` |

### §9.5 — Decision Note: §9.2 chosen over §9.3

**Recommendation.** Keep §9.2 — `dhc:blockly*` annotations live in the T-Box.

**Why §9.2 is the right choice:**

1. Design-time block mapping is vocabulary-intrinsic and country-invariant.
   C-Box is scoped to norm/governance profiles (DH-SPEC-200). Mixing
   design-mapping shapes into C-Box muddies the Multi-Box contract.
2. A single-source read (T-Box) for Blockly generation keeps the pipeline
   simple — §14 step 4 reads T-Box only, then overlays C-Box norm constraints.
   §9.3 would force the Modeller to merge two C-Box "flavours" and reason
   about which applies when.
3. The Multi-Box Model treats T-Box as the conceptual layer that tooling
   annotates; adding datatype properties to classes is its normal extension
   pattern.

**One refinement.** Drop `dhc:blocklyColor` from the T-Box example in §9.2.
Block colors are UI styling; they belong to the Modeller / Designer render
layer keyed off `dhc:designView`. Keep `dhc:blocklyDisposition`,
`dhc:blocklyCategory` (only when it differs from `dhc:designView`),
`dhc:blocklyParentProperty`, and `dhc:blocklyFieldType` — those are
structural, not cosmetic.

**When §9.3 would become right.** Only if design-mapping ever needs to vary
per country/norm (e.g., a norm mandates a different Blockly shape). No such
case is on the horizon; defer.

## §10 — Versioning Semantics

### §10.1 — Ontology Version X.Y.Z

| Segment | Scope | Trigger |
|---------|-------|---------|
| **X** (Major) | Full architectural change | T-Box restructure (e.g., 1.x → 2.0.0 Multi-Box) |
| **Y** (Minor) | T-Box structural change | New class, new property, renamed property, removed property. Always increments Y, resets Z. |
| **Z** (Patch) | C-Box rule change | New norm profile, updated constraint values, new SHACL shapes. T-Box unchanged. |

### §10.2 — Modeller Compatibility

The Modeller must declare which ontology version range it supports:

```json
{
  "name": "@dhc/modeller",
  "version": "2.0.0",
  "ontologyCompat": "^2.0.0"
}
```

When ingesting, the Modeller reads `owl:versionInfo` from `dhc-core.schema.ttl` and checks compatibility. If the major version doesn't match, the Modeller refuses to process and logs an error.

## §11 — C-Box Registry (cbox-registry.json)

The Modeller compiles all C-Box shape files + `cbox-manifest.json` into a single `cbox-registry.json` for the Designer.

```json
{
  "version": "2.0.0",
  "generatedAt": "2026-04-19T14:00:00Z",
  "profiles": [
    {
      "id": "nfc14100",
      "norm": "NF C 14-100",
      "country": "FR",
      "domain": "electrical",
      "normVersion": "2021",
      "description": {
        "en": "Energy delivery from provider to main board (France)",
        "de": "Energieeinspeisung vom Versorger zum Hauptverteiler (Frankreich)",
        "fr": "Livraison d'énergie du fournisseur au tableau principal (France)"
      },
      "requires": [],
      "targetClasses": ["dhc:EnergyMeter", "dhc:EmergencyDisconnect", "dhc:EnergyDelivery"],
      "shapes": [
        {
          "id": "nfc14100:EnergyMeterShape",
          "targetClass": "dhc:EnergyMeter",
          "constraints": [],
          "label": { "en": "Energy Meter (NF C 14-100)" }
        }
      ]
    },
    {
      "id": "nfc15100",
      "norm": "NF C 15-100",
      "country": "FR",
      "domain": "electrical",
      "normVersion": "2024",
      "description": {
        "en": "Residential electrical installation (France)",
        "de": "Elektroinstallation Wohngebäude (Frankreich)",
        "fr": "Installation électrique résidentielle (France)"
      },
      "requires": ["nfc14100"],
      "targetClasses": ["dhc:Circuit", "dhc:DistributionBoard", "dhc:ElectricalTechnicalSpace"],
      "shapes": [
        {
          "id": "nfc15100:LightingCircuitShape",
          "targetClass": "dhc:Circuit",
          "condition": { "hasCircuitType": "dhc:CircuitType_Lighting" },
          "constraints": [
            { "path": "dhc:maxPoints", "maxInclusive": 8 },
            { "path": "dhc:ratedCurrent", "maxInclusive": 10 },
            { "path": "dhc:crossSection", "minInclusive": 1.5 }
          ],
          "defaults": {
            "dhc:ratedCurrent": 10,
            "dhc:crossSection": 1.5,
            "dhc:wiring": "3G1.5"
          },
          "label": { "en": "Lighting Circuit (NF C 15-100)", "de": "Beleuchtungsstromkreis (NF C 15-100)", "fr": "Circuit éclairage (NF C 15-100)" },
          "messages": {
            "dhc:maxPoints": { "en": "NF C 15-100: max 8 points on lighting circuit" }
          }
        }
      ]
    }
  ]
}
```

## §12 — S3 Publication

### §12.1 — Artifact Manifest

| Artifact | S3 Key Pattern | Description |
|----------|---------------|-------------|
| `ontology-graph.json` | `ontology/{version}/ontology-graph.json` | 3D graph viewer data |
| `blockly-blocks.json` | `ontology/{version}/blockly-blocks.json` | Block definitions with norm constraint overlays |
| `blockly-toolbox.json` | `ontology/{version}/blockly-toolbox.json` | Toolbox categories + automation variables |
| `cbox-registry.json` | `ontology/{version}/cbox-registry.json` | Compiled norm profile metadata |
| `context.jsonld` | `ontology/{version}/context.jsonld` | JSON-LD context (copy from source) |

### §12.2 — Versioned Keys

All artifacts are published under a versioned prefix (`ontology/2.0.0/`). A `latest` alias symlink or redirect is maintained for the Designer's default fetch path.

## §13 — Designer Integration Points

This section documents how the Designer consumes the Modeller's artifacts. It is informational — the Designer spec is separate.

### §13.1 — Use Case 1: Retrofit (Norm OFF)

1. Designer fetches `blockly-blocks.json` + `blockly-toolbox.json`.
2. Designer renders Blockly workspace with **no norm constraints active**.
3. User maps existing installation → A-Box.
4. User triggers **Validate**: Designer fetches `cbox-registry.json`, selects active norm(s), evaluates SHACL shapes against A-Box.
5. Output: Gap report listing violations.

### §13.2 — Use Case 2: New Design (Norm ON)

1. Designer fetches `blockly-blocks.json` + `blockly-toolbox.json` + `cbox-registry.json`.
2. User selects active norm(s) in the norm panel.
3. Designer overlays `normConstraints` from `blockly-blocks.json` onto block fields:
   - Pre-fills defaults when CircuitType is selected
   - Shows constraint hints (max, min) on fields
   - Inline warnings on constraint violation
4. User designs → A-Box.
5. Continuous validation against active norm shapes.

### §13.3 — 3D Viewer

1. Designer fetches `ontology-graph.json`.
2. Renders Three.js graph.
3. Norm toggle panel (from `cbox-registry.json` profile list).
4. When norm toggled ON → nodes with matching `governedByNorms` get 📍 indicator.
5. Hover → tooltip with norm name + constraint summary.
6. Select → inspector Compliance tab with full constraint details.

## §14 — Modeller Processing Pipeline (Summary)

```
┌─────────────────────────────────────────────────────┐
│ 1. INGEST (Cognito login; dhc-modelers/dhc-admins)  │
│    Raw-read from selected branch via                 │
│    https://raw.githubusercontent.com/<org>/          │
│      digitalhome-cloud-core/<branch>/<path>          │
│      schema/tbox/*.ttl → T-Box quad store            │
│      schema/cbox/**/*.shapes.ttl → C-Box stores      │
│      schema/cbox/cbox-manifest.json                  │
│    Optional: skip re-parse if source fingerprints    │
│    match workdir build-meta.json (see §4.4).         │
├─────────────────────────────────────────────────────┤
│ 2. CONVERT                                          │
│    TTL → JSON-LD (workdir, using context.jsonld)     │
├─────────────────────────────────────────────────────┤
│ 3. GENERATE: ontology-graph.json                    │
│    T-Box classes → nodes                             │
│    T-Box ObjectProperties → edges                    │
│    C-Box sh:targetClass → governedByNorms per node   │
├─────────────────────────────────────────────────────┤
│ 4. GENERATE: blockly-blocks.json                    │
│    T-Box classes (blocklyDisposition="block") → blocks│
│    T-Box DatatypeProperties → fields                 │
│    T-Box ObjectProperties → connections              │
│    T-Box enum instances → dropdown options            │
│    C-Box shapes → normConstraints overlay per block   │
│    T-Box (blocklyDisposition="variable") → variables  │
├─────────────────────────────────────────────────────┤
│ 5. GENERATE: blockly-toolbox.json                   │
│    T-Box dhc:designView → toolbox categories         │
│    Exclude: spatial, governance, compliance, automation│
│    Automation classes → variables section             │
├─────────────────────────────────────────────────────┤
│ 6. GENERATE: cbox-registry.json                     │
│    cbox-manifest.json + parsed C-Box shapes           │
│    → compiled registry with constraints + defaults    │
├─────────────────────────────────────────────────────┤
│ 7. COPY: context.jsonld                             │
├─────────────────────────────────────────────────────┤
│ 8. PUBLISH                                          │
│    Upload all artifacts to S3 under ontology/{ver}/  │
└─────────────────────────────────────────────────────┘
```

## §15 — Open Items

1. **`dhc:blockly*` annotation properties**: These need to be added to `dhc-core.schema.ttl` in the v2.0.0 branch. This is a T-Box addition → minor version bump to 2.1.0. Alternatively, ship them with the initial 2.0.0 if the branch hasn't been tagged yet.

2. **`blockly-overrides.json`**: The v1 repo had a hand-maintained overrides file. With `dhc:blockly*` annotations in the T-Box, overrides should no longer be needed. Confirm this eliminates the override mechanism entirely, or identify remaining edge cases.

3. **Automation variable types**: `dhc:Group` and `dhc:Scenario` are clear. Should `dhc:Sensor` and `dhc:Actor` also be variables? They are `dhc:designView "network"` but are referenced by scenarios — clarify if they are blocks in the Network workspace AND variables in all workspaces.

4. **C-Box defaults extraction**: The SHACL shapes express constraints (`sh:maxInclusive`) but not defaults. Where do default values (e.g., "pre-fill crossSection=1.5 for Lighting") come from? Options:
   - A custom annotation `dhc:defaultValue` on the shape property
   - A dedicated `dhc:defaults` section in the shapes file
   - Hard-coded in `cbox-manifest.json` (current proposal in §11)

5. **Compliance view blocks**: The spec says `compliance` designView is excluded from Blockly. But the Designer needs a way to attach `dhc:governedBy` to A-Box elements. Should `dhc:Norm` instances appear as a special dropdown on blocks rather than as separate blocks?

6. **Branch selection for v2 cutover**: The raw-fetch paths in §4.1 assume the v2.0.0 `schema/` layout. Confirm which core-repo branch the Modeller Config UI points at on cutover, and whether the existing `main` / `stage` buttons need to become `v2.0.0` / `v2-stage` (or similar) while v2 is still being stabilised.

7. **Cache fingerprint strategy (§4.4)**: Pick one of commit-SHA, per-file SHA-256, or `ETag`-based fingerprinting. Commit-SHA is the cheapest (one extra GitHub API call) but unauthenticated `api.github.com` calls are rate-limited; per-file `ETag` avoids the API call entirely at the cost of N HEAD requests.

## §16 — References

- DH-SPEC-003: Ontology v2.0.0 Multi-Box Architecture
- DH-SPEC-002: SmartHome Manager — Create New Digital Home
- DH-SPEC-000: Access Tiers & Capability Matrix
- Multi-Box Model: *Architectural Framework: The Multi-Box Model for Modern Metadata Environments* (D-LAB-5, 2026)
- N3.js: https://github.com/rdfjs/N3.js
- jsonld.js: https://github.com/digitalbazaar/jsonld.js
- Blockly: https://developers.google.com/blockly
