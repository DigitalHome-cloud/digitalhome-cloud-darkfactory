# Deployment & Development Lifecycle

This document describes how application code and ontology models
(T-Box and A-Box) move through the development, staging, and production
tiers of the DigitalHome.Cloud platform.

---

## 1. Environment Tiers

| Tier | Branch | URLs | Purpose |
|------|--------|------|---------|
| **DEV** | any (local) | `localhost:8000/8001/8002` | Local development and testing |
| **STAGE** | `stage` | `stage-portal/designer/modeler.digitalhome.cloud` | Pre-production validation |
| **PROD** | `main` | `portal/designer/modeler.digitalhome.cloud` | Live users |

All three apps (Portal, Designer, Modeler) deploy independently via
**AWS Amplify Hosting** with branch-to-environment mapping.

---

## 2. Application Deployment

### What Is Automated (CI/CD)

Every push to `stage` or `main` in any sub-repo triggers an Amplify
build-and-deploy pipeline:

```
git push origin stage
  └─ Amplify detects push
     └─ Runs amplify.yml build spec
        ├─ npm install
        ├─ [modeler only] npm run parse-ontology
        ├─ [modeler only] npm run generate-blockly-toolbox
        ├─ npm run build (gatsby build)
        └─ Deploys public/ to CloudFront
```

| App | Build Steps | Artifacts |
|-----|-------------|-----------|
| **Portal** | `npm install` → `gatsby build` | Static site |
| **Designer** | `npm install` → `gatsby build` | Static site (with local block JSON fallback) |
| **Modeler** | `npm install` → `parse-ontology` → `generate-blockly-toolbox` → `gatsby build` | Static site with ontology graph + block definitions baked in |

The portal also installs the Amplify CLI during build (it owns the
backend). Designer and modeler are frontend-only builds.

### What Is Manual

| Action | How | When |
|--------|-----|------|
| Merge `stage` → `main` | `git merge` or PR | After stage validation, to promote to production |
| Amplify backend changes | `amplify push` from portal repo (local CLI with admin creds) | Schema changes, new Lambda functions, auth config |
| Submodule pointer updates | Commit in umbrella repo after sub-repo pushes | After sub-repo changes to keep umbrella in sync |

### Typical Workflow

```
1. Developer works locally on a sub-repo (e.g. repos/designer)
2. yarn develop — test at localhost:8001
3. git commit + git push origin stage
4. Amplify auto-deploys to stage-designer.digitalhome.cloud
5. Validate on stage (cross-app testing with stage-portal, stage-modeler)
6. git checkout main && git merge stage && git push origin main
7. Amplify auto-deploys to designer.digitalhome.cloud (production)
8. Update umbrella submodule pointers, push umbrella to stage/main
```

---

## 3. T-Box (Ontology) Lifecycle

The T-Box is the domain vocabulary — classes, properties, and
constraints defined in Turtle (TTL) source files. It lives in
`repos/modeler/semantic-core/`.

### Authoring (DEV)

```
repos/modeler/semantic-core/
  ontology/
    dhc-core.schema.ttl          <-- Core ontology (manually authored)
    context.jsonld               <-- JSON-LD context (manually authored)
  modules/
    module-manifest.json         <-- Module registry (manually authored)
    dhc-nfc14100-electrical.ttl  <-- Norm module (manually authored)
    dhc-nfc15100-electrical.ttl  <-- Norm module (manually authored)
```

T-Box authoring is a manual process. The author edits TTL files,
runs the build pipeline locally to verify, and commits.

### Build Pipeline (Automated on Push)

When the modeler repo is pushed to `stage` or `main`, Amplify runs:

```
parse-ontology.js
  TTL source files → src/data/ontology-graph.json
  (reads Core + all modules from manifest, generates node/link graph)

generate-blockly-toolbox.js
  ontology-graph.json + blockly-overrides.json → blockly-blocks.json + blockly-toolbox.json
  (generates Blockly block definitions and toolbox categories from T-Box classes)

gatsby build
  (bakes ontology-graph.json, blockly-blocks.json, blockly-toolbox.json into the static site)
```

After build, the artifacts exist in two places:
- **In the deployed Gatsby site** — baked into the modeler's static JS bundles
- **Not yet on S3** — must be published separately (see below)

### Publishing to S3 (Manual)

The Designer fetches block definitions from S3 at runtime (`ontology/latest/`).
Publishing to S3 is a separate step from deploying the modeler site.

**Option A: In-app Publisher (recommended for JSON artifacts)**

1. Navigate to `modeler.digitalhome.cloud/publish/` (or stage equivalent)
2. Sign in as a `dhc-admins` group member
3. Review local version vs. deployed version in the Publish section
4. Click "Publish to S3"
5. Uploads `ontology-graph.json`, `blockly-blocks.json`, `blockly-toolbox.json`
   to both `ontology/v{VERSION}/` and `ontology/latest/`

This uses Amplify Storage v6 with Cognito credentials — no AWS CLI needed.

**Option B: CLI script (for TTL, context.jsonld, and module files)**

```bash
cd repos/modeler
yarn publish-ontology
```

This uploads all artifacts (JSON + TTL + context.jsonld + modules) using
the AWS SDK with local credentials (`~/.aws` or env vars). Used when
TTL source files or context.jsonld need to be published to S3.

### T-Box Versioning

The T-Box version is embedded in `ontology-graph.json` at `meta.version`
(e.g. `"1.1.0"`). The version is set in the TTL source via
`owl:versionInfo`. Each publish creates a versioned snapshot on S3
(`ontology/v1.1.0/`) and updates the `ontology/latest/` alias.

```
S3: public/ontology/
  v1.0.0/        <-- historical snapshot
  v1.1.0/        <-- historical snapshot
  v1.1.1/        <-- current version
  latest/        <-- alias, mirrors v1.1.1
```

### T-Box Flow Summary

```
                DEV                    STAGE / PROD              S3
          +--------------+         +-----------------+    +------------------+
 Author → | Edit TTL     |         |                 |    |                  |
          | yarn parse   |  push   | Amplify build:  |    | ontology/latest/ |
          | yarn generate| ------> |   parse + gen   |    |   blocks.json    |
          | yarn develop |         |   gatsby build  |    |   toolbox.json   |
          +--------------+         |   deploy site   |    |   graph.json     |
                                   +-----------------+    +------------------+
                                          |                       ^
                                          | admin visits          | upload
                                          | /publish/ page -------+
                                          | (Amplify Storage)
```

---

## 4. A-Box (Instance Data) Lifecycle

The A-Box is the instance data — individual SmartHome designs created
by users in the Designer's Blockly workspace. A-Box data lives
exclusively on S3 (not in git).

### Creation

When a user creates a SmartHome or generates a shell:
1. `shellGenerator.js` creates an initial Blockly workspace skeleton
2. `saveDesignToS3()` writes `workspace.json`, `abox.ttl`, `abox.json`
   to `public/smarthomes/{smartHomeId}/design/`

### Editing

1. User opens the Blockly workspace at `/design/?home={id}`
2. `fetchDesignFromS3()` loads the saved workspace
3. User edits blocks (with edit lock to prevent concurrent writes)
4. On save: `aboxSerializer.js` generates `abox.ttl` + `abox.json`
5. `saveDesignToS3()` writes all three files back to S3

### A-Box Artifacts

```
S3: public/smarthomes/{smartHomeId}/design/
  workspace.json   <-- Blockly workspace state (blocks, positions, connections)
  abox.ttl         <-- A-Box instance data in RDF Turtle format
  abox.json        <-- A-Box graph (nodes + links) for 3D viewer
```

### A-Box Versioning

A-Box data is **not version-controlled in git**. It lives only on S3.
The SmartHome ID is the partition key. Each save overwrites the previous
version. There is currently no A-Box version history or undo.

The `SmartHomeDesign` DynamoDB record tracks metadata (owner, lock state,
last modified) but the actual design artifacts are on S3.

### A-Box vs. T-Box Relationship

The A-Box references T-Box classes. When the T-Box is updated (e.g. a
class is renamed or removed), existing A-Box instances may become
invalid. The validation engine checks A-Box blocks against T-Box
constraints at design time.

```
T-Box (ontology)           A-Box (instance)
dhc:Room                   myHome:LivingRoom a dhc:Room
dhc:Circuit                myHome:Circuit1 a dhc-nfc15100:LightingCircuit
dhc:hasCircuit             myHome:LivingRoom dhc:hasCircuit myHome:Circuit1
```

---

## 5. Environment Matrix

| What | DEV (local) | STAGE | PROD |
|------|-------------|-------|------|
| **App deploy** | `yarn develop` | Auto on push to `stage` | Auto on push to `main` |
| **T-Box build** | `yarn parse-ontology && yarn generate-blockly-toolbox` | Automated in Amplify build | Automated in Amplify build |
| **T-Box → S3** | `yarn publish-ontology` (local creds) | Admin uses `/publish/` page | Admin uses `/publish/` page |
| **A-Box read/write** | S3 (same bucket, same data) | S3 (same bucket) | S3 (same bucket) |
| **Ontology source** | Local fallback (`src/data/`) if S3 fails | S3 (`ontology/latest/`), error if fails | S3 (`ontology/latest/`), error if fails |
| **Backend changes** | `amplify push` from portal repo | Auto (portal Amplify manages backend) | Auto (portal Amplify manages backend) |
| **Cross-app nav** | `localhost:800x` (auto-detected) | `stage-*.digitalhome.cloud` | `*.digitalhome.cloud` |

---

## 6. What Is Automated vs. Manual

### Fully Automated (on every push)

- Application build and deploy (all three apps)
- T-Box parse (TTL → ontology-graph.json)
- Blockly toolbox generation (ontology-graph.json → blocks + toolbox JSON)
- SSL certificates and CDN invalidation (managed by Amplify Hosting)

### Manual (requires human action)

| Action | Who | How | Frequency |
|--------|-----|-----|-----------|
| T-Box authoring | Ontology author | Edit TTL files in `semantic-core/` | Per ontology change |
| T-Box publish to S3 (JSON) | `dhc-admins` member | Modeler `/publish/` page | After each modeler deploy with ontology changes |
| T-Box publish to S3 (TTL) | Developer | `yarn publish-ontology` (local AWS creds) | When TTL/context.jsonld files need updating on S3 |
| Stage → Prod promotion | Developer | Merge `stage` → `main` + push | After stage validation |
| Backend schema changes | Developer | `amplify push` from portal repo | Per schema change |
| Umbrella submodule sync | Developer | Commit updated pointers in umbrella | After sub-repo pushes |

### Known Gaps

1. **No automated T-Box → S3 publish in CI/CD.** The Amplify build role
   lacks `s3:PutObject` permission. Publishing is manual via `/publish/`
   page or local CLI. Adding the IAM permission would allow re-adding
   `publish-ontology` to `amplify.yml`.

2. **No A-Box version history.** Each save overwrites the previous
   design. No undo, no diff, no audit trail beyond the DynamoDB
   `updatedAt` timestamp.

3. **Single S3 bucket for all tiers.** DEV, STAGE, and PROD all read/write
   the same S3 bucket. A design saved on localhost is visible in
   production. T-Box artifacts published from stage are immediately live
   for production designers. This is by design (shared data layer) but
   means there is no isolated staging for S3 data.

4. **TTL/context.jsonld publish requires local AWS credentials.** The
   in-app publisher only handles JSON artifacts available as static
   webpack imports. Full ontology publishing (TTL source files, module
   manifests) still requires running the CLI script locally.

---

## 7. Release Checklist

When releasing a new ontology version:

```
1. [ ] Edit TTL source files in repos/modeler/semantic-core/
2. [ ] Run yarn parse-ontology + yarn generate-blockly-toolbox locally
3. [ ] Verify in yarn develop (modeler + designer)
4. [ ] Commit and push to stage
5. [ ] Amplify builds and deploys modeler to stage
6. [ ] Admin visits stage-modeler.digitalhome.cloud/publish/
7. [ ] Verify S3 browser shows current versions
8. [ ] Click "Publish to S3" to upload JSON artifacts
9. [ ] Verify designer loads new blocks from S3 on stage
10. [ ] (Optional) Run yarn publish-ontology locally for TTL/context.jsonld
11. [ ] Merge stage → main in all affected repos
12. [ ] Amplify deploys to production
13. [ ] Admin visits modeler.digitalhome.cloud/publish/ and publishes
14. [ ] Update umbrella submodule pointers
```

---

*See also:*
- [S3 Data Flow](s3-data-flow.md) — Bucket layout and read/write details
- [ADR 0010](../adr/0010-s3-bucket-structure-global-and-tenant.md) — S3 bucket structure
- [ADR 0007](../adr/0007-semantic-core-in-modeler-repo.md) — Semantic core location
- [ADR 0012](../adr/0012-modular-ontology-architecture.md) — Modular ontology architecture
