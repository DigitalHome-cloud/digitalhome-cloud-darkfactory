# DH-SPEC-003 — Spatial Hierarchy Blocks

| Field | Value |
|---|---|
| Spec ID | `DH-SPEC-003` |
| Title | SmartHome Spatial Hierarchy — Blockly Block Design |
| Status | **Draft** — implemented in Designer, awaiting review |
| Version | 0.2.0 |
| Author | D-LAB-5 / DigitalHome.Cloud |
| Date | 2026-04-17 |
| Scope | Designer app. Defines the spatial block hierarchy, Zone variable mechanism, toolbox layout, connection checks, and A-Box serialization for the Blockly design workspace. |
| Related specs | DH-SPEC-000 (Access Tiers), DH-SPEC-002 (SHM Create New — upstream, hands off `smartHomeId` + `realEstateUri`) |
| Ontology alignment | `dhc-core` v1.1.0 classes: `dhc:RealEstate`, `dhc:Area`, `dhc:Floor`, `dhc:Space`, `dhc:Zone` |

### Changelog
- **0.2.0** — Full spec aligned with implementation. Added backward compatibility section, serializer details, connection checker rules, color gradient rationale.
- **0.1.0** — Initial sketch (3-block JavaScript definitions + XML toolbox).

---

## 1. Purpose

Define a clear, enforceable spatial hierarchy for SmartHome design in the Blockly workspace:

**Real Estate → Area → Space**

With **Zone** as a Blockly Variable (many-to-many logical grouping).

This hierarchy replaces the original flat 5-block model (`RealEstate`, `Area`, `Floor`, `Space`, `Zone`) with a streamlined 3-block model where Floor becomes a field on Area and Zone becomes a variable dropdown on Space.

---

## 2. Glossary

| Term | Meaning |
|---|---|
| Block | A Blockly visual block representing an ontology class instance. |
| Statement input | A slot on a block where child blocks snap in (containment). |
| Connection check | A string type constraint on statement connections (`AreaType`, `SpaceType`). |
| FieldVariable | A Blockly dropdown field backed by workspace-scoped variables. |
| A-Box | Assertion box — instance data serialized as TTL or JSON from the workspace. |
| T-Box | Terminology box — the ontology schema (`dhc-core.schema.ttl`). |
| Design view | Ontology annotation (`dhc:designView`) categorizing blocks (spatial, electrical, shared). |

---

## 3. Hierarchy

### 3.1 Block hierarchy (new model)

```
dhc_real_estate (root)
  └── HASAREA [check: AreaType]
        └── dhc_area
              ├── FLOOR_LEVEL (number field — replaces dhc_floor block)
              └── HASSPACE [check: SpaceType]
                    └── dhc_space
                          ├── AREA_M2 (number field — surface in m²)
                          ├── ZONE_VAR (FieldVariable — type "Zone")
                          ├── HASBUILDINGELEMENT [check: dhc_BuildingElement]
                          └── HASEQUIPMENT [check: dhc_Equipment]
```

### 3.2 Design decisions

| Decision | Rationale |
|---|---|
| Floor merged into Area as a field | A floor is an attribute of an area, not a structural container. Reduces nesting depth by one level. |
| Zone as FieldVariable | Enables many-to-many: one Zone assigned to multiple Spaces, one Space can change Zone. No wrapper block needed. |
| Connection checks (`AreaType`, `SpaceType`) | Strict type enforcement prevents mis-nesting (e.g., Space directly inside RealEstate). |
| Color gradient (120 → 100 → 70) | Visual depth cue: darker green = higher in hierarchy, lighter = deeper/leaf. |

### 3.3 Comparison with previous model

| Aspect | Previous (v1.0) | DH-SPEC-003 (v1.1+) |
|---|---|---|
| Hierarchy depth | RealEstate → Area → Floor → Space | RealEstate → Area → Space |
| Floor | Standalone block (`dhc_floor`) | Number field on Area (`FLOOR_LEVEL`) |
| Zone | Standalone block with value input | Blockly Variable (`FieldVariable`, type `"Zone"`) |
| Space fields | LABEL, AREA_M2 | LABEL, AREA_M2 (Surface), ZONE_VAR |
| Area fields | LABEL | LABEL, FLOOR_LEVEL |
| Colors | All hue 142 (uniform green) | Gradient: 120 (dark) → 100 (medium) → 70 (light) |
| Connection checks | `dhc_Area`, `dhc_Floor`, `dhc_Space` | `AreaType`, `SpaceType` |

---

## 4. Block definitions

All blocks use the JSON block definition format (`jsonInit`), loaded from `src/data/blockly-blocks.json`.

### 4.1 `dhc_real_estate`

| Property | Value |
|---|---|
| Ontology class | `dhc:RealEstate` |
| Design view | `spatial` |
| Colour | `120` (darkest green) |
| Fields | `LABEL` (text), `SMART_HOME_ID` (text) |
| Statement inputs | `HASAREA` (check: `AreaType`) |
| Connections | `previousStatement: "dhc_real_estate"`, `nextStatement: null` |

### 4.2 `dhc_area`

| Property | Value |
|---|---|
| Ontology class | `dhc:Area` |
| Design view | `spatial` |
| Colour | `100` (medium green) |
| Fields | `LABEL` (text), `FLOOR_LEVEL` (number, default 0, precision 1) |
| Statement inputs | `HASSPACE` (check: `SpaceType`), `HASFLOOR` (check: `dhc_Floor`, backward compat) |
| Connections | `previousStatement: "AreaType"`, `nextStatement: "AreaType"` |

The `HASFLOOR` input preserves backward compatibility with saved workspaces that contain `dhc_floor` blocks nested inside Area (see §8).

### 4.3 `dhc_space`

| Property | Value |
|---|---|
| Ontology class | `dhc:Space` |
| Design view | `spatial` |
| Colour | `70` (lightest green) |
| Fields | `LABEL` (text), `AREA_M2` (number, default 15, min 0) |
| Variable fields | `ZONE_VAR` (FieldVariable, variableTypes: `["Zone"]`, defaultType: `"Zone"`) |
| Statement inputs | `HASBUILDINGELEMENT` (check: `dhc_BuildingElement`), `HASEQUIPMENT` (check: `dhc_Equipment`) |
| Connections | `previousStatement: "SpaceType"`, `nextStatement: "SpaceType"` |

### 4.4 `dhc_floor` (legacy)

Retained for backward compatibility. Existing workspaces that use `dhc_floor` blocks will continue to load and function. New designs should use Area's `FLOOR_LEVEL` field instead.

| Property | Value |
|---|---|
| Ontology class | `dhc:Floor` |
| Design view | `spatial` |
| Colour | `110` |
| Tooltip | `"A floor level within a building. Legacy — new designs use the Floor field on Area."` |
| Statement inputs | `HASSPACE` (check: `SpaceType`) |
| Connections | `previousStatement: "dhc_Floor"`, `nextStatement: "dhc_Floor"` |

### 4.5 `dhc_zone` (legacy)

Retained for backward compatibility. New designs use the Zone variable dropdown on Space.

| Property | Value |
|---|---|
| Ontology class | `dhc:Zone` |
| Design view | `spatial` |
| Colour | `90` |
| Tooltip | `"A logical grouping of Spaces. Legacy — new designs assign Zones via the dropdown on Space blocks."` |

---

## 5. Toolbox layout

### 5.1 Spatial category

```json
{
  "kind": "category",
  "name": "Spatial",
  "colour": 120,
  "contents": [
    { "kind": "block", "type": "dhc_real_estate" },
    { "kind": "block", "type": "dhc_area" },
    { "kind": "block", "type": "dhc_space" }
  ]
}
```

Legacy blocks (`dhc_floor`, `dhc_zone`) are removed from the default toolbox. They remain registered and loadable from saved workspaces.

### 5.2 Zones variable category

```json
{
  "kind": "category",
  "name": "Zones",
  "colour": 90,
  "custom": "ZONE_VARIABLE"
}
```

The `ZONE_VARIABLE` category is a dynamic toolbox category registered via `workspace.registerToolboxCategoryCallback()`. It provides:

1. A **"Create New Zone"** button — triggers `Blockly.Variables.createVariableButtonHandler()` with type `"Zone"`.
2. A **variable getter block** for the most recently created Zone variable.

Users create Zone variables (e.g., "Day Zone", "Night Zone", "Service Zone") and then assign them to Space blocks via the `ZONE_VAR` dropdown.

---

## 6. Connection checking

### 6.1 Blockly-level checks (connection types)

| Block | `previousStatement` | `nextStatement` | Effect |
|---|---|---|---|
| `dhc_real_estate` | `"dhc_real_estate"` | `null` | Cannot stack; standalone root. |
| `dhc_area` | `"AreaType"` | `"AreaType"` | Only snaps into `HASAREA` (check: `AreaType`). Stackable with siblings. |
| `dhc_space` | `"SpaceType"` | `"SpaceType"` | Only snaps into `HASSPACE` (check: `SpaceType`). Stackable with siblings. |

### 6.2 Soft validation (connectionCheckers.js)

Additional runtime validation beyond Blockly's built-in type checks:

| Block type | Valid parent | Warning if violated |
|---|---|---|
| `dhc_area` | `dhc_real_estate` | "Area should be inside a Real Estate." |
| `dhc_space` | `dhc_floor` or `dhc_area` | "Space should be inside a Floor or Area." |
| `dhc_electrical_technical_space` / `dhc_nfc15100_gtl` | `dhc_floor`, `dhc_area`, or `dhc_space` | "... should be inside a Floor, Area, or Space." |
| Equipment (`dhc_socket`, `dhc_switch`, `dhc_light`, `dhc_heater`, `dhc_equipment`) | `dhc_space` or any circuit type | "... should be inside a Space or Circuit." |
| `dhc_protection_device` | Any circuit type | "... should be attached to a Circuit." |
| Circuit types (`dhc_circuit`, `dhc_nfc15100_*`) | `dhc_distribution_board` | "... should be inside a Distribution Board." |

---

## 7. A-Box serialization

### 7.1 Zone variable → TTL

When a Space block has a `ZONE_VAR` field set to a value other than `"None"`, the serializer emits:

```turtle
dhc-instance:{smartHomeId}/dhc_space/{blockId}
  a dhc:Space ;
  rdfs:label "Kitchen" ;
  dhc:areaM2 15 ;
  dhc:belongsToZone dhc-instance:{smartHomeId}/zone/{encodedZoneName} ;
  .
```

After all blocks are processed, unique Zone instances are emitted:

```turtle
dhc-instance:{smartHomeId}/zone/{encodedZoneName}
  a dhc:Zone ;
  rdfs:label "{zoneName}" .
```

### 7.2 Zone variable → JSON

In the JSON graph format (`serializeToJSON`):

- **Zone link**: `{ source: spaceIri, target: zoneIri, label: "belongsToZone", type: "reference" }`
- **Zone node**: `{ id: zoneIri, blockId: null, type: "dhc:Zone", label: zoneName, designView: "spatial", properties: {} }`

Zone nodes have `blockId: null` since they are derived from variables, not blocks.

### 7.3 Instance IRI patterns

| Entity | IRI pattern |
|---|---|
| Spatial block | `dhc-instance:{smartHomeId}/{blockType}/{blockId}` |
| Zone (from variable) | `dhc-instance:{smartHomeId}/zone/{encodeURIComponent(zoneName)}` |

---

## 8. Backward compatibility

### 8.1 Legacy `dhc_floor` block

- Block definition retained with `previousStatement: "dhc_Floor"`.
- `dhc_area` retains a `HASFLOOR` statement input (check: `"dhc_Floor"`) so existing saved workspaces with Floor blocks nested inside Area continue to load.
- `connectionCheckers.js` accepts `dhc_floor` as a valid parent for Space: `if (parent.type !== "dhc_floor" && parent.type !== "dhc_area")`.
- The 3D viewer and A-Box serializer handle `dhc_floor` blocks identically to before.

### 8.2 Legacy `dhc_zone` block

- Block definition retained.
- Existing workspaces with `dhc_zone` blocks connected via value inputs to Space blocks continue to load and serialize.
- New zone assignments use the FieldVariable; old value-input zones coexist.

### 8.3 Migration path

No automated migration. Existing workspaces work as-is. Users creating new designs naturally use the updated blocks. Over time, `dhc_floor` and `dhc_zone` blocks can be deprecated once all saved workspaces have been migrated.

---

## 9. Visual design

### 9.1 Color gradient

| Block | Hue | Hex (approximate) | Rationale |
|---|---|---|---|
| `dhc_real_estate` | 120 | `#22c55e` (dark green) | Root — visually anchors the hierarchy |
| `dhc_area` | 100 | `#4ade80` (medium green) | Mid-level container |
| `dhc_floor` (legacy) | 110 | `#34d399` (between root and mid) | Legacy, positioned between RealEstate and Area |
| `dhc_space` | 70 | `#a3e635` (yellow-green) | Leaf — lightest, most numerous |
| `dhc_zone` (legacy) | 90 | `#65a30d` (olive green) | Logical grouping, distinct from physical hierarchy |

The gradient encodes nesting depth: darker = higher in hierarchy, lighter = deeper/leaf. This provides immediate visual feedback about block position.

### 9.2 Block labels

| Block | Message pattern |
|---|---|
| Real Estate | `🏠 Real Estate {LABEL}\nSmartHome ID {SMART_HOME_ID}` |
| Area | `📍 Area {LABEL}\nFloor {FLOOR_LEVEL}` |
| Space | `🚪 Space {LABEL}\nSurface {AREA_M2} m²` + `🌐 Zone {ZONE_VAR}` |
| Floor (legacy) | `🏢 Floor {LABEL}\nLevel {FLOOR_LEVEL}` |

---

## 10. Files modified

| File | Change |
|---|---|
| `src/data/blockly-blocks.json` | Updated 5 spatial block definitions (colors, fields, connection checks) |
| `src/data/blockly-toolbox.json` | Spatial category simplified to 3 blocks; added Zones variable category |
| `src/blockly/workspace.js` | Registered `ZONE_VARIABLE` category callback and `CREATE_ZONE` button callback |
| `src/blockly/aboxSerializer.js` | Zone variable → `dhc:belongsToZone` triple (TTL + JSON) |
| `src/blockly/connectionCheckers.js` | Added Area parent validation rule |

---

## 11. Exit criteria

- [ ] Real Estate → Area → Space nesting enforced by connection checks
- [ ] Space cannot snap directly into Real Estate (only into Area)
- [ ] Area cannot snap into Space or Floor (only into Real Estate)
- [ ] Zone variable dropdown appears on Space blocks
- [ ] "Create New Zone" button works in the Zones toolbox category
- [ ] Multiple Spaces can reference the same Zone (many-to-many)
- [ ] TTL export includes `dhc:belongsToZone` triples and Zone instances
- [ ] JSON export includes Zone nodes and `belongsToZone` links
- [ ] Color gradient visible: dark green (root) → light green (leaf)
- [ ] Existing FR-DEMO workspace loads without errors (backward compat)
- [ ] Legacy `dhc_floor` and `dhc_zone` blocks still function in saved workspaces

---

## 12. Open items

| # | Item | Blocker? |
|---|---|---|
| O-1 | Update S3-hosted block definitions to match local `blockly-blocks.json` | Yes — runtime loads from S3 |
| O-2 | Regenerate block definitions from ontology (Modeler script) | No — can be done post-launch |
| O-3 | Add SHACL shape for Zone variable cardinality | No |
| O-4 | Deprecation timeline for `dhc_floor` / `dhc_zone` blocks | No |
| O-5 | Integration test: create full hierarchy + export TTL + validate against ontology | No |

---

*End of DH-SPEC-003 v0.2.0*
