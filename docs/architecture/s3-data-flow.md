# S3 Data Flow — DigitalHome.Cloud Platform

This document describes how the three DigitalHome.Cloud applications
(Portal, Designer, Modeler) use the shared S3 bucket for ontology
artifacts and tenant design data.

**Bucket:** `digitalhome-cloudec099-main` (eu-central-1)
**Access prefix:** All paths use the Amplify `public/` prefix (readable by
any authenticated user or Cognito guest; writeable by authenticated users).

---

## Bucket Layout

```
public/
  ontology/
    latest/                          <-- alias, always mirrors current version
      ontology-graph.json
      context.jsonld
      blockly-blocks.json
      blockly-toolbox.json
      modules/
        module-manifest.json
        dhc-nfc14100-electrical.ttl
        dhc-nfc15100-electrical.ttl
    v1.1.1/                          <-- versioned snapshot (model-v1.1.1)
      (same structure as latest/)
  smarthomes/
    DE-DEMO/
      design/
        workspace.json               <-- Blockly workspace state
        abox.ttl                     <-- A-Box instance data (RDF Turtle)
        abox.json                    <-- A-Box graph (nodes + links)
    FR-DEMO/
      design/
        ...
    DE-80331-MAR12-01/               <-- real tenant SmartHome
      design/
        ...
  library/                           <-- reserved for future use
```

---

## Data Flow Diagram

```
 MODELER                          S3 BUCKET                          DESIGNER
 (build-time + runtime)           (public/)                          (runtime)

 +-----------------------+        +---------------------------+      +------------------------+
 | TTL source files      |        | ontology/                 |      | toolboxLoader.js       |
 |                       |        |                           |      |                        |
 | dhc-core.schema.ttl   |        | latest/                   | ---> | fetchToolboxFromS3()   |
 | modules/*.ttl         |        |   blockly-blocks.json     | read |   blockly-blocks.json  |
 | module-manifest.json  |        |   blockly-toolbox.json    |      |   blockly-toolbox.json |
 |                       |        |   ontology-graph.json     |      |                        |
 | scripts/              |        |   context.jsonld          |      | Falls back to local    |
 |  parse-ontology.js    |        |   modules/                |      | src/data/ on localhost |
 |  generate-blockly-    |        |     module-manifest.json  |      +------------------------+
 |    toolbox.js         |        |     *.ttl                 |
 +-----------------------+        |                           |
                                  | v1.1.1/                   |
  Amplify CI/CD (build-time):     |   (same as latest/)       |
    parse-ontology                |                           |
    generate-blockly-toolbox      +---------------------------+
    gatsby build                         ^
                                         | write (Amplify Storage)
  In-app Publish (runtime):              |
    /publish/ page ----------------------+
    (admin-only, Cognito creds)
    uploads: ontology-graph.json,
             blockly-blocks.json,
             blockly-toolbox.json
    to both v{VERSION}/ and latest/

  CI/CD-only artifacts (not from browser):
    context.jsonld, module TTLs, module-manifest.json


                                  +---------------------------+      +------------------------+
                                  | smarthomes/{id}/design/   |      | DESIGNER               |
                                  |                           |      |                        |
                                  |   workspace.json   <------+----> | saveDesignToS3()       |
                                  |   abox.ttl         <------+----> | fetchDesignFromS3()    |
                                  |   abox.json        <------+----> | fetchABoxFromS3()      |
                                  |                           |      |                        |
                                  +---------------------------+      | Also written by:       |
                                         ^                           |  shellGenerator.js     |
                                         | read                      |  (initial skeleton)    |
                                         |                           +------------------------+
                                  +------+-------+
                                  | 3D A-Box     |
                                  | Viewer       |
                                  | (designer    |
                                  |  /viewer/)   |
                                  +--------------+
```

---

## Who Writes What

| S3 Path | Writer | Trigger |
|---------|--------|---------|
| `ontology/latest/*` (JSON) | Modeler | Admin clicks "Publish to S3" on `/publish/` page |
| `ontology/v{X.Y.Z}/*` (JSON) | Modeler | Admin clicks "Publish to S3" on `/publish/` page |
| `ontology/latest/*` (TTL, JSONLD) | Modeler | `scripts/publish-ontology.js` run manually (local CLI) |
| `ontology/v{X.Y.Z}/*` (TTL, JSONLD) | Modeler | `scripts/publish-ontology.js` run manually (local CLI) |
| `smarthomes/{id}/design/*` | Designer | User saves workspace or shell generator runs |

## Who Reads What

| S3 Path | Reader | When |
|---------|--------|------|
| `ontology/latest/blockly-blocks.json` | Designer | Workspace init (toolboxLoader.js) |
| `ontology/latest/blockly-toolbox.json` | Designer | Workspace init (toolboxLoader.js) |
| `ontology/latest/ontology-graph.json` | Modeler | 3D viewer (if fetching from S3) |
| `smarthomes/{id}/design/workspace.json` | Designer | Opening a SmartHome design |
| `smarthomes/{id}/design/abox.json` | Designer | 3D viewer page (/viewer/) |
| `smarthomes/{id}/design/abox.ttl` | — | Available for external RDF tools |

---

## Artifact Lifecycle

### Ontology Artifacts (T-Box)

```
1. Author edits TTL in repos/modeler/semantic-core/
2. Push to stage/main triggers Amplify build
3. Amplify build pipeline (automated):
     npm run parse-ontology          --> src/data/ontology-graph.json
     npm run generate-blockly-toolbox --> src/data/blockly-blocks.json
                                         src/data/blockly-toolbox.json
     npm run build                   --> Gatsby static site with artifacts baked in
4. Admin publishes to S3 via the Modeler /publish/ page:
     ontology-graph.json, blockly-blocks.json, blockly-toolbox.json
     --> S3: ontology/v{ver}/* + ontology/latest/*
     (uses Amplify Storage with Cognito credentials, gated by dhc-admins group)
5. TTL source files and context.jsonld:
     --> Published via scripts/publish-ontology.js (manual, local CLI with AWS creds)
     --> Or added to CI/CD once Amplify build role has S3 write permissions
6. Designer fetches latest from S3 at runtime
7. Local fallback files in designer/src/data/ used only on localhost
```

### Design Artifacts (A-Box)

```
1. User creates SmartHome in Manager
     --> shellGenerator.js creates initial workspace.json
     --> saveDesignToS3() writes workspace.json + empty abox.ttl/json
     --> auto-navigate to /design/?home={id}

2. User edits in Blockly workspace
     --> acquires edit lock (useDesignLock.js)
     --> on save: aboxSerializer.js generates abox.ttl + abox.json
     --> saveDesignToS3() writes all 3 files
     --> releases edit lock

3. User views in 3D Viewer
     --> fetchABoxFromS3() reads abox.json
     --> renders force-directed graph
```

---

## Environment Behavior (v1.1.2+)

| Environment | Ontology source | Design data |
|-------------|----------------|-------------|
| **localhost** | Local fallback (`src/data/`) if S3 fails | S3 (same bucket) |
| **stage** | S3 (`ontology/latest/`) — error if fails | S3 (same bucket) |
| **production** | S3 (`ontology/latest/`) — error if fails | S3 (same bucket) |

In deployed environments (stage, production), the designer logs
`console.error` if the S3 ontology fetch fails — the local fallback
files may be stale. On localhost, it silently falls back to local files.

---

## Key Source Files

| File | App | Role |
|------|-----|------|
| `modeler/scripts/publish-ontology.js` | Modeler | Uploads all ontology artifacts to S3 (manual CLI) |
| `modeler/src/utils/s3.js` | Modeler | Amplify Storage operations (list, download, upload) |
| `modeler/src/components/OntologyPublisher.js` | Modeler | In-app S3 browser + admin publish controls |
| `modeler/scripts/parse-ontology.js` | Modeler | Generates ontology-graph.json from TTL |
| `modeler/scripts/generate-blockly-toolbox.js` | Modeler | Generates blockly-blocks/toolbox.json |
| `designer/src/utils/s3.js` | Designer | All S3 read/write operations |
| `designer/src/blockly/toolboxLoader.js` | Designer | Fetches toolbox from S3 with fallback |
| `designer/src/blockly/aboxSerializer.js` | Designer | Generates A-Box TTL + JSON |
| `designer/src/utils/shellGenerator.js` | Designer | Creates initial workspace skeleton |

---

*See also:* [ADR 0010 — S3 Bucket Structure](../adr/0010-s3-bucket-structure-global-and-tenant.md)
