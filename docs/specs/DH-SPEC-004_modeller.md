# DH-SPEC-004 — Modeler App Overhaul

| Field | Value |
|---|---|
| Spec ID | `DH-SPEC-004` |
| Title | Modeler — Live Ontology Builder & Publisher |
| Status | **Draft** — awaiting review |
| Version | 0.1.0 |
| Author | D-LAB-5 / DigitalHome.Cloud |
| Date | 2026-04-17 |
| Scope | Modeler app. Transforms the static ontology viewer into a live authoring tool that reads from GitHub, builds Blockly artifacts in-browser, and publishes directly to S3. |
| Related specs | DH-SPEC-000 (Access Tiers), DH-SPEC-003 (Spatial Hierarchy Blocks) |
| Depends on | `repos/core` submodule (GitHub: `DigitalHome-cloud/digitalhome-cloud-core`) |

---

## 1. Purpose & Goals

The Modeler currently works as a **static viewer**: ontology TTL is parsed by local Node.js scripts, output is committed to `src/data/`, baked into Gatsby at build time, and manually published to S3 by an admin.

This spec transforms the Modeler into a **live authoring tool** where:

1. The ontology source is read **directly from GitHub** (no local clone needed).
2. The T-Box → Blockly mapping is built **in the browser** (no local scripts).
3. Modelers can test blocks in a **live Blockly workspace** before publishing.
4. Admins promote tested artifacts to **versioned S3 releases** consumed by the Designer.

**Primary goals:**
- Eliminate the local build → commit → deploy → publish pipeline.
- Enable modelers to iterate on block definitions without touching code or CLI tools.
- Separate concerns: modelers own the mapping, admins own the release.
- Keep the 3D ontology viewer as the primary exploration tool.

**Non-goals:**
- Editing TTL files (ontology authoring stays in the core repo via git).
- Runtime block generation in the Designer (Designer still fetches pre-built artifacts from S3).
- Library module (removed from navigation — see §12).

---

## 2. Glossary

| Term | Meaning |
|---|---|
| T-Box | Terminology box — the ontology schema (`dhc-core.schema.ttl` + module TTLs). |
| A-Box | Assertion box — instance data created by the Designer. |
| Blockly artifact | Generated JSON files: `blockly-blocks.json` (block definitions) + `blockly-toolbox.json` (toolbox config). |
| Workdir | S3 staging area for in-progress builds (`public/ontology/workdir/{branch}/`). |
| Versioned release | S3 path consumed by the Designer (`public/ontology/v{VERSION}/` + `latest/`). |
| Core repo | `digitalhome-cloud-core` on GitHub — source of truth for ontology TTL. |

---

## 3. Navigation

### 3.1 New menu structure

| Menu item | Route | Purpose |
|---|---|---|
| Config Manager | `/config/` | Select ontology branch/version from GitHub |
| Model | `/` | 3D ontology viewer (existing, modified to load from GitHub/S3) |
| Blockly Builder | `/builder/` | T-Box → Blockly mapping, build, test, adjust |
| Publisher | `/publish/` | Promote workdir → versioned S3 release |
| Sign In | `/signin/` | Authentication (existing) |

### 3.2 Removed

- **Library** (`/library/`) — removed from navigation. Page and components kept in code for potential future use. DynamoDB LibraryItems remain untouched.

### 3.3 Cross-app link

- **Portal** link remains in the header (external, via `getAppUrl()`).

---

## 4. Auth Model

The Modeler requires authentication for all features. No demo/guest access.

| Cognito group | Config Manager | Model (3D Viewer) | Blockly Builder | Publisher |
|---|---|---|---|---|
| `dhc-modelers` | Select branch | View + interact | Build, test, recompile, save to workdir | View only (browse S3 versions) |
| `dhc-admins` | Select branch | View only | View only (read-only inspection) | Promote workdir → versioned release |
| Authenticated (no group) | Redirect to "request access" | — | — | — |
| Guest (unauthenticated) | Redirect to sign-in | — | — | — |

**Separation of concerns:**
- **Modelers** own the ontology-to-Blockly mapping. They can build, test, iterate, and save to the S3 workdir.
- **Admins** own the final publication. They can inspect what modelers built and promote it to a versioned release. They cannot modify the mapping.

---

## 5. Config Manager

### 5.1 Purpose

Select the ontology source (GitHub branch) and display its metadata. Serves as the "project selector" for the Modeler, analogous to the Designer's SmartHome Manager.

### 5.2 UI

```
┌─────────────────────────────────────────────────┐
│ Config Manager                                   │
│                                                   │
│ Source: digitalhome-cloud-core (GitHub)           │
│ Branch: [main ▾]  [stage]  [Fetch]              │
│                                                   │
│ ┌─ Fetched Ontology ───────────────────────────┐ │
│ │ Version: 1.2.0                                │ │
│ │ Classes: 76  Properties: 91  Links: 120       │ │
│ │ Label: DigitalHome.Cloud Core Ontology        │ │
│ └───────────────────────────────────────────────┘ │
│                                                   │
│ ┌─ Modules ─────────────────────────────────────┐ │
│ │ ✓ NF C 14-100 Electrical Delivery   v1.0.0   │ │
│ │ ✓ NF C 15-100 Electrical Install.   v1.0.0   │ │
│ └───────────────────────────────────────────────┘ │
│                                                   │
│ ┌─ Published on S3 ────────────────────────────┐ │
│ │ Latest: v1.2.0 (2026-04-15)                  │ │
│ │ Workdir (stage): v1.2.0 (2026-04-17 14:30)   │ │
│ │ Status: workdir AHEAD of latest               │ │
│ └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 5.3 Behavior

1. On page load: restore last-selected branch from `localStorage`.
2. User selects branch (`main` or `stage`) and clicks **Fetch**.
3. App fetches from GitHub (§10): `dhc-core.schema.ttl` → `module-manifest.json` → module TTLs.
4. Parsed metadata displayed: version, class/property counts, module list.
5. Comparison with S3: fetch `latest/ontology-graph.json` meta and `workdir/{branch}/` meta.
6. Selected config persisted to `localStorage` and React context for use by other pages.

---

## 6. Model (3D Viewer)

### 6.1 Changes from current

The 3D viewer currently loads from baked-in `src/data/ontology-graph.json`. After this spec:

1. **Primary source**: Parse the TTL fetched via Config Manager into the graph format (same structure as `ontology-graph.json`).
2. **If no TTL is fetched** (Config Manager not visited): prompt the user to visit Config Manager first.
3. **If GitHub is unreachable**: display an error message ("Cannot fetch ontology from GitHub. Please check your network and try again."). No fallback chain — GitHub unavailability is a low-probability event that does not warrant offline/fallback complexity.

### 6.2 Existing components (no structural changes)

- `WorkspaceShell` — 3-panel layout
- `OntologyGraph` — 3D force graph
- `OntologySidebar` — View filter + node list
- `OntologyInspector` — Selected node details

### 6.3 Auth gating

- `dhc-modelers`: Full interaction (rotate, zoom, select, filter).
- `dhc-admins`: View only (same interaction, read-only context).

---

## 7. Blockly Builder

### 7.1 Purpose

The core new feature. Replaces the local `generate-blockly-toolbox.js` script with an in-browser tool that:

1. Shows the T-Box → Blockly mapping as a reviewable table.
2. Generates `blockly-blocks.json` and `blockly-toolbox.json` in the browser.
3. Provides a live Blockly workspace for testing the generated blocks.
4. Allows adjustments via a configurator panel.
5. Saves build artifacts to the S3 workdir.

### 7.2 Layout

```
┌──────────────────────────────────────────────────────────────┐
│ Blockly Builder                    [Build] [Save to Workdir] │
│ ┌─────────────────────────────┬──────────────────────────────┐
│ │ T-Box → Blockly Mapping     │ Blockly Test Workspace       │
│ │                             │                              │
│ │ Spatial (3 blocks)          │  ┌─────────────────────────┐ │
│ │  ◉ RealEstate → dhc_real..  │  │ (live Blockly canvas)   │ │
│ │  ◉ Area → dhc_area          │  │                         │ │
│ │  ◉ Space → dhc_space        │  │  [toolbox]  [workspace] │ │
│ │                             │  │                         │ │
│ │ Electrical (18 blocks)      │  └─────────────────────────┘ │
│ │  ◉ Circuit → dhc_circuit    │                              │
│ │  ◉ DistributionBoard → ...  │ ┌──────────────────────────┐ │
│ │  ...                        │ │ Block Configurator       │ │
│ │                             │ │ (selected block details)  │ │
│ │ NFC 15-100 (21 blocks)     │ │ Fields, colors, checks   │ │
│ │  ◉ GTL → dhc_nfc15100_gtl  │ │ [Recompile]              │ │
│ │  ...                        │ └──────────────────────────┘ │
│ └─────────────────────────────┴──────────────────────────────┘
└──────────────────────────────────────────────────────────────┘
```

### 7.3 T-Box → Blockly Mapping Table (left panel)

Grouped by design view, color-coded. Each row shows:

| Column | Content |
|---|---|
| Ontology class | `dhc:RealEstate` (prefixed IRI) |
| Block type | `dhc_real_estate` (generated snake_case) |
| Design view | Badge: Spatial / Electrical / Shared |
| SuperClass | `→ dhc:Equipment` (if subclass) |
| Fields | `LABEL (text), FLOOR_LEVEL (number)` |
| Containment inputs | `HASAREA [AreaType], HASSPACE [SpaceType]` |
| Reference inputs | `BELONGSTOZONE [Zone]` |

Clicking a row selects it in the Block Configurator (right panel).

### 7.4 Build logic (in-browser)

Replicate `generate-blockly-toolbox.js` as a browser module (`src/utils/blocklyGenerator.js`):

1. **Input**: Parsed TTL entities (classes, datatype properties, object properties) + overrides JSON.
2. **Process**:
   - Filter classes by design view scope (`spatial`, `electrical`, `shared`).
   - For each class: generate block definition with fields, statement inputs, value inputs.
   - Apply overrides: dropdown values, module defaults, label overrides.
   - Module classes inherit properties from their Core superclass.
   - Generate toolbox config grouped by design view with module subcategories.
3. **Output**: `{ blocks: [...], toolbox: {...} }` — same JSON format as current files.

The overrides (`blockly-overrides.json`) are fetched from GitHub alongside the TTL (path: `repos/core/scripts/blockly-overrides.json`).

### 7.5 Blockly Test Workspace (right panel, top)

A live Blockly workspace (same setup as the Designer's `WorkspaceShell`) loaded with the generated toolbox and block definitions. Allows the modeler to:

- Drag blocks from the toolbox.
- Test nesting (connection checks).
- Verify field types, defaults, and dropdown values.
- Verify color coding by design view.

### 7.6 Block Configurator (right panel, bottom)

When a block type is selected (from the mapping table or the workspace), shows its editable properties:

| Property | Editable by modeler | Effect |
|---|---|---|
| Label (display name) | Yes | Updates `message0` first segment |
| Colour (hue) | Yes | Updates block hue |
| Tooltip | Yes | Updates tooltip text |
| Field defaults | Yes | Updates `field_input.text`, `field_number.value` |
| Dropdown options | Yes | Updates `field_dropdown.options` |
| Connection checks | Read-only | Derived from ontology (informational) |

**Recompile** button: Re-runs the build with current adjustments → reloads the test workspace.

### 7.7 Save to Workdir

Writes the current build output to S3:
- `public/ontology/workdir/{branch}/blockly-blocks.json`
- `public/ontology/workdir/{branch}/blockly-toolbox.json`
- `public/ontology/workdir/{branch}/ontology-graph.json`
- `public/ontology/workdir/{branch}/build-meta.json` — `{ builtBy, builtAt, branch, version, overrides }`

Only accessible to `dhc-modelers`.

### 7.8 Load from Workdir

On page load, the Builder checks the S3 workdir for the selected branch. If a workdir build exists:

1. Fetch `blockly-blocks.json` and `blockly-toolbox.json` from `public/ontology/workdir/{branch}/`.
2. Load these into the **test workspace** — this shows what was actually saved, not the freshly generated in-memory artifacts.
3. Display a source indicator: "Showing workdir (saved)" vs "Showing fresh build (unsaved)".

The modeler can toggle between workdir and fresh build to compare.

### 7.9 Promote Workdir

The workdir is part of the modeler's domain. Promotion to a versioned S3 release is triggered from the Builder, not the Publisher.

1. Modeler clicks **Promote workdir → v{VERSION}**.
2. App copies workdir files to `public/ontology/v{VERSION}/` and `public/ontology/latest/`.
3. Also publishes: `context.jsonld`, `module-manifest.json`, module TTL files (fetched from GitHub).
4. Success confirmation with version number and file count.

Only accessible to `dhc-modelers`.

---

## 8. Publisher

### 8.1 Purpose

Browse published versioned S3 releases that the Designer reads from. Provides rollback capability for admins.

### 8.2 UI

```
┌────────────────────────────────────────────────────────────┐
│ Publisher                                                   │
│                                                             │
│ ┌─ Published Versions ─────────────────────────────────────┐│
│ │ latest → v1.2.0 (2026-04-15)                             ││
│ │ v1.2.0   3 files   2026-04-15 10:23                      ││
│ │ v1.1.0   3 files   2026-03-28 09:15                      ││
│ │ v1.0.0   3 files   2026-03-01 14:00                      ││
│ └──────────────────────────────────────────────────────────┘│
│                                                             │
│ [Rollback latest → v1.1.0]                                 │
│                                                             │
│ (Only dhc-admins can rollback)                              │
└────────────────────────────────────────────────────────────┘
```

### 8.3 Rollback

Admin can point `latest/` back to any prior version by copying that version's files to `latest/`.

### 8.4 Auth gating

- `dhc-modelers`: Can view published versions. Cannot rollback.
- `dhc-admins`: Full access — rollback, view.

---

## 9. S3 Structure

```
public/ontology/
├── latest/                          ← alias, always points to active version
│   ├── ontology-graph.json
│   ├── blockly-blocks.json
│   ├── blockly-toolbox.json
│   ├── context.jsonld
│   └── modules/
│       ├── module-manifest.json
│       ├── dhc-nfc14100-electrical.ttl
│       └── dhc-nfc15100-electrical.ttl
├── v1.2.0/                          ← versioned snapshot (immutable)
│   └── (same structure as latest/)
├── v1.1.0/
│   └── ...
├── workdir/                         ← staging area (mutable)
│   ├── main/
│   │   ├── blockly-blocks.json
│   │   ├── blockly-toolbox.json
│   │   ├── ontology-graph.json
│   │   └── build-meta.json
│   └── stage/
│       └── (same structure)
```

---

## 10. GitHub API Integration

### 10.1 Endpoints

All fetches use the GitHub Raw Content API (unauthenticated for public repos):

```
Base: https://raw.githubusercontent.com/DigitalHome-cloud/digitalhome-cloud-core/{branch}/

Files:
  src/ontology/dhc-core.schema.ttl
  src/ontology/dhc-roles.ttl
  src/ontology/context.jsonld
  src/modules/module-manifest.json
  src/modules/{moduleFile}              (per manifest entry)
  scripts/blockly-overrides.json
```

### 10.2 Fetch chain

1. Fetch `dhc-core.schema.ttl` → parse version, classes, properties.
2. Fetch `module-manifest.json` → discover modules.
3. Fetch each module TTL → parse module classes/properties.
4. Fetch `blockly-overrides.json` → load build overrides.
5. Fetch `context.jsonld` → store for publish.

### 10.3 Caching

- In-memory (React context): parsed entities cached for the session.
- `localStorage`: last-fetched branch + version (for display, not data).
- S3 workdir: persisted build output (survives sessions).

### 10.4 Error handling

No fallback chain. GitHub is the single source of truth.

| Scenario | Behavior |
|---|---|
| GitHub unreachable | Error message: "Cannot fetch ontology from GitHub. Please check your network and try again." |
| Fetch returns invalid TTL | Error message with parse error details. User can retry or switch branch. |
| Config Manager not visited | Other pages prompt: "Please visit Config Manager to select an ontology branch first." |

---

## 11. In-Browser Build Pipeline

### 11.1 TTL Parser (`src/utils/ttlParser.js`)

Ported from `repos/core/scripts/parse-ontology.js`. Pure string/regex processing — no Node.js APIs.

**Input**: TTL string.
**Output**: `{ meta: { version, label }, entities: [{ id, type, label, comment, view, superClass, domain, range }] }`.

### 11.2 Blockly Generator (`src/utils/blocklyGenerator.js`)

Ported from `repos/core/scripts/generate-blockly-toolbox.js`. Pure logic — no `fs` calls.

**Input**: `{ coreEntities, moduleEntities, overrides }`.
**Output**: `{ blocks: [...blockDefs], toolbox: {...toolboxConfig} }`.

### 11.3 Validation

On first port, run both Node.js script and browser module against the same TTL input and diff the JSON output. They must produce identical results.

---

## 12. Migration Plan

### 12.1 Phase 1 — New pages (additive)

1. Create Config Manager, Blockly Builder pages.
2. Port TTL parser and block generator to browser modules.
3. Add GitHub fetch utility.
4. Update navigation header.

### 12.2 Phase 2 — Update existing pages

1. Update Model viewer to load from GitHub/context (with S3 fallback).
2. Update Publisher to read from S3 workdir instead of local files.
3. Add workdir S3 operations.

### 12.3 Phase 3 — Remove deprecated

1. Remove Library from navigation (keep page code).
2. Remove `repos/modeler/semantic-core/` (already migrated to `repos/core`).
3. Remove `repos/modeler/scripts/parse-ontology.js` (replaced by in-app parser).
4. Remove `repos/modeler/scripts/generate-blockly-toolbox.js` (replaced by in-app generator).
5. Remove `repos/modeler/scripts/publish-ontology.js` (replaced by in-app publisher).
6. Update `package.json` scripts (remove `parse-ontology`, `generate-blockly-toolbox`, `publish-ontology`).
7. Update `amplify.yml` build spec (no longer runs parse/generate before gatsby build).

### 12.4 Auth change

1. Remove demo mode fallback — require authentication on all pages.
2. Add group-based gating: `dhc-modelers` for build, `dhc-admins` for publish.
3. Update `AuthContext` or add `useModelerAuth()` hook for group checks.

---

## 13. Exit Criteria

- [ ] Config Manager can fetch ontology from GitHub `main` and `stage` branches
- [ ] Config Manager displays version, class count, module list
- [ ] Config Manager compares fetched vs published versions
- [ ] Model viewer loads graph from GitHub-fetched TTL (with S3 fallback)
- [ ] Blockly Builder shows T-Box → Blockly mapping table for all in-scope classes
- [ ] Blockly Builder generates `blockly-blocks.json` identical to Node.js script output
- [ ] Blockly Builder generates `blockly-toolbox.json` identical to Node.js script output
- [ ] Blockly Builder test workspace loads generated blocks, toolbox is functional
- [ ] Block Configurator allows adjusting labels, colors, defaults, dropdowns
- [ ] Recompile reflects configurator changes in the test workspace
- [ ] Save to Workdir writes artifacts to `public/ontology/workdir/{branch}/`
- [ ] Publisher can promote workdir to `v{VERSION}/` and `latest/`
- [ ] Publisher can rollback `latest/` to a prior version
- [ ] `dhc-modelers` can build but not publish; `dhc-admins` can publish but not build
- [ ] Guest/unauthenticated users see sign-in redirect
- [ ] Library page removed from navigation
- [ ] Local build scripts removed from modeler repo
- [ ] `semantic-core/` directory removed from modeler repo
- [ ] Designer still loads blocks from S3 `latest/` without changes

---

## 14. Open Items

| # | Item | Blocker? |
|---|---|---|
| O-1 | Confirm `digitalhome-cloud-core` repo is public (GitHub raw API access) | **Yes** — blocks GitHub fetch |
| O-2 | Create `dhc-modelers` Cognito group | **Yes** — blocks auth gating |
| O-3 | Decide if Library page should be fully deleted or just hidden | No |
| O-4 | Decide if specific git tags/SHA should be selectable (beyond branches) | No |
| O-5 | Decide if `blockly-overrides.json` should be editable in-app or always fetched from GitHub | No — fetch from GitHub first, in-app editing as future enhancement |
| O-6 | Rate limiting on GitHub raw API (60 req/hour unauthenticated) — sufficient? | No — low volume expected |
| O-7 | CORS on GitHub raw API — verify `raw.githubusercontent.com` allows browser fetch | **Yes** — must verify before implementation |

---

*End of DH-SPEC-004 v0.1.0*
