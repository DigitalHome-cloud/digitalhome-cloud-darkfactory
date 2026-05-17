# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working across the DigitalHome.Cloud platform.

## Project Overview

**digitalhome-cloud-darkfactory** is the umbrella workspace for the DigitalHome.Cloud platform. It aggregates all application repos as git submodules and provides platform-level documentation, specs, and helper scripts. This is the recommended directory to launch Claude Code from for cross-repo work.

## Repo Structure

```
digitalhome-cloud-darkfactory/
  CLAUDE.md              ← You are here
  README.md
  repos/
    core/                ← digitalhome-cloud-core (submodule) — ontology schema + the platform's Amplify Gen 2 backend (amplify/)
    portal/              ← digitalhome-cloud-portal (submodule)
    designer/            ← digitalhome-cloud-designer (submodule)
    modeler/             ← digitalhome-cloud-modeler (submodule)
  docs/
    architecture/        ← Platform architecture docs
    specs/               ← Feature specifications
    adr/                 ← Architecture Decision Records
    audits/              ← Security/quality audit reports
  scripts/               ← Cross-repo helper scripts
  archive/               ← Historical files
```

> The umbrella root has **no** `amplify/`, `package.json`, or `tsconfig.json` —
> the Amplify Gen 2 backend and its toolchain live in `repos/core` (moved there
> to avoid two `amplify/` levels). See **Backend Ownership** below.

## Sub-Repos

Each sub-repo has its own `CLAUDE.md` with app-specific details. **Always read the sub-repo's CLAUDE.md** before making changes in that repo.

| App | Path | Port | Production URL | CLAUDE.md |
|-----|------|------|----------------|-----------|
| Core | `repos/core/` | — | — | `repos/core/CLAUDE.md` |
| Portal | `repos/portal/` | 8000 | `portal.digitalhome.cloud` | `repos/portal/CLAUDE.md` |
| Designer | `repos/designer/` | 8001 | `designer.digitalhome.cloud` | `repos/designer/CLAUDE.md` |
| Modeler | `repos/modeler/` | 8002 | `modeler.digitalhome.cloud` | `repos/modeler/CLAUDE.md` |

## Platform Architecture

### Tech Stack

All three apps are **Gatsby 5 / React 18** static sites deployed via **AWS Amplify Hosting**. They share:

- **Amazon Cognito** for authentication (User Pool + Identity Pool)
- **AWS AppSync** (GraphQL) for API access
- **Amazon DynamoDB** for data storage
- **Amazon S3** for ontology files and instance models
- **Amplify JS v6** (Gen2-style imports) on the frontend

### Backend Ownership

The **`repos/core` submodule owns the single Amplify Gen 2 backend** under `repos/core/amplify/` — defined in TypeScript (`backend.ts`, `auth/resource.ts`, `data/resource.ts`, `storage/resource.ts`, `functions/*/`). It was moved out of the umbrella root because having an `amplify/` at the umbrella *and* a submodule that Amplify Hosting builds caused "amplify on two levels of a repo" conflicts. `repos/core/package.json` is dual-purpose (ontology vitest harness + Amplify toolchain). Portal, Designer, and Modeler are frontend-only consumers — each commits a `src/amplify_outputs.json` produced by `npx ampx sandbox` (or by the deployed pipeline) that holds the public Cognito + AppSync + S3 IDs.

**Stage status:** the stage backend (`repos/core` branch `stage`) is live and the **stage Designer is wired to it and operational**. Portal and Modeler still point at the previous Cognito pool — re-pointing them is pending.

For backend authoring, sandbox workflow, and CDK escape-hatch patterns, see the `dhc-amplify-gen2` skill (`.claude/skills/dhc-amplify-gen2/SKILL.md`).

### Authentication

`AuthContext` in each app wraps the root element and exposes:
- `authState`: `"loading"` | `"demo"` | `"authenticated"`
- `user`, `groups`, `hasGroup(name)`, `signOut()`, `reloadSession()`

Cognito groups control feature access (defined in `repos/core/amplify/auth/resource.ts`):
- `dhc-admins` — full admin: Modeler editing, ontology library writes
- `dhc-modelers` — Modeler editing access
- `dhc-professional` — paid Designer tier
- `dhc-standard` — standard Designer tier
- `dhc-welcome` — auto-assigned to new sign-ups (via `postConfirmation` Lambda trigger)

### SmartHome ID

The SmartHome ID is the top-level tenant/partition key across the entire platform (like a SAP client). Format: `{country}-{zip}-{street3letter}{housenumber}-{nn}` (e.g. `DE-80331-MAR12-01`).

Three demo SmartHomes are always available: `DE-DEMO`, `FR-DEMO`, `BE-DEMO`. Cross-app navigation passes the active SmartHome via `?home=` query parameter.

### Ontology (Semantic Core)

The DHC core ontology lives in `repos/core/schema/` (`tbox/dhc-core.ttl` + module TTLs under `modules/`, with `draft/` for in-progress edits). It defines the domain vocabulary (classes like `RealEstate`, `Area`, `Space`, `Circuit`, `Sensor`) used by all apps. Build scripts in `repos/core/scripts/` parse the TTL and generate Blockly block definitions and ontology graph JSON. The ontology follows semantic versioning (`model-vX.Y.Z`).

## Key Rules

### No Double Maintenance

Documentation, specs, and config files must live in **exactly one place**. When content is moved to this umbrella repo, delete the original. Never maintain the same file in two repos. If an app-level CLAUDE.md references a doc, point to this repo's copy rather than duplicating.

### Single Source of Truth for Specs

Release specs live in `docs/specs/vX.Y.Z.md` — one living document per target release. See `docs/specs/TEMPLATE.md` for the format. Feature specs use the `DH-SPEC-{NNN}_{slug}.md` naming convention (e.g., `DH-SPEC-000_access-tiers.md`). Feature specs define cross-cutting concerns or feature-specific designs referenced by release specs.

### ADRs for Architectural Decisions

Significant architectural decisions are documented in `docs/adr/` using numbered ADR files. When making a decision that affects multiple repos or sets a lasting pattern, write an ADR.

## Cross-Repo Conventions

### Branches

All repos use the same branching model:
- `main` → production
- `stage` → staging (pre-production)
- `beta`, `alpha` → optional for major features

### Environment Variables

Backend connection details (Cognito User Pool, AppSync endpoint, S3 bucket, etc.) are NOT carried in env vars anymore — each app commits `src/amplify_outputs.json` and imports it directly in `gatsby-browser.js` / `gatsby-ssr.js`. Updating outputs after a backend change is a file copy from `repos/core`'s sandbox output (see the `dhc-amplify-gen2` skill).

`.env.development` (gitignored) is reserved for **cross-app URLs only**:
- `GATSBY_PORTAL_URL` → `https://portal.digitalhome.cloud`
- `GATSBY_DESIGNER_URL` → `https://designer.digitalhome.cloud`
- `GATSBY_MODELER_URL` → `https://modeler.digitalhome.cloud`

Locally these get overridden to `http://localhost:8000/8001/8002`.

### Files That Must Never Be Committed (any repo)

- `.env.development` — local URL overrides
- `repos/core/amplify_outputs.json` — written per developer by `npx ampx sandbox`
- `repos/core/.amplify/` — sandbox state cache
- `.amplify/` — sandbox state cache
- `node_modules/`, `.cache/`, `public/`

### Local Dev Setup

```bash
cd ~/digitalhomeCloud/digitalhome-cloud-darkfactory/repos/core
npm install                     # core deps: vitest harness + Amplify Gen 2 toolchain
npx ampx sandbox                # boot personal sandbox stack (one per developer)
                                # writes repos/core/amplify_outputs.json

# Propagate outputs to each app on first deploy or after a backend change
# (run from repos/core):
cp amplify_outputs.json ../portal/src/
cp amplify_outputs.json ../designer/src/
cp amplify_outputs.json ../modeler/src/

# Then in each app:
cd ../portal && yarn develop             # 8000
cd ../designer && yarn develop           # 8001
cd ../modeler && yarn develop            # 8002

# Or all at once from the umbrella (seeds outputs from repos/core automatically):
./scripts/dev-start-all.sh
./scripts/dev-stop-all.sh
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/dev-start-all.sh` | Preflight checks + start all 3 Gatsby dev servers detached (ports 8000, 8001, 8002). Logs in `/tmp/dhc-*.log` |
| `scripts/dev-stop-all.sh` | Stop all 3 dev servers started by `dev-start-all.sh` |
| `scripts/status.sh` | Git status and recent log across all repos |
| `scripts/pull-all.sh` | Git pull in each sub-repo |

## Working with Submodules

```bash
# Clone with all sub-repos
git clone --recurse-submodules <url>

# After cloning without --recurse-submodules
git submodule update --init --recursive

# Update all sub-repos to latest
git submodule update --remote

# Work inside a sub-repo (it's a normal git repo)
cd repos/portal
git checkout stage
# ... make changes, commit, push ...
```

## Documentation

- `docs/architecture/` — Platform architecture (environment strategy, auth flow, Amplify backend integration, data model)
- `docs/specs/` — Release specs (`vX.Y.Z.md`) and feature specs (`DH-SPEC-{NNN}_{slug}.md`). Key feature specs:
  - DH-SPEC-000: Access Tiers & Capability Matrix
  - DH-SPEC-002: SmartHome Manager — Create New Digital Home
  - DH-SPEC-003: Spatial Hierarchy Blocks
- `docs/design/` — Platform-agnostic UX design guide (tokens, foundations, components, patterns, adaptation guides). See `docs/design/README.md`.
- `docs/adr/` — Architecture Decision Records:
  - 0001: Multi-repo with shared backend
  - 0002: Gatsby 5 + React 18 frontend stack
  - 0003: Amplify Gen 2 backend (TypeScript-defined, lives in `repos/core`; supersedes prior Gen 1 ADR)
  - 0004: Environment-variable-driven configuration
  - 0005: Cognito auth with group-based access control
  - 0006: SmartHome ID as tenant partition key
  - 0007: Semantic core ontology in core repo (migrated from modeler)
  - 0008: Umbrella repo with git submodules (backend relocated into `repos/core`)
  - 0009: Single spec document per target release
  - 0010: S3 bucket structure for global and tenant content
  - 0011: All GraphQL types in portal backend schema
  - 0012: Modular ontology architecture (Core + Norm Modules)
  - 0013: Platform-agnostic design guide

## Deployment

Each app deploys independently via Amplify Hosting:
- Push to `main` → production deploy
- Push to `stage` → staging deploy

The backend deploys from its own Amplify Hosting app: `repos/core/amplify.yml` runs `npm install` + `npx ampx pipeline-deploy --branch $AWS_BRANCH` on push to `repos/core` (a backend-only app — its `frontend` phase only emits a stub `index.html`). Each frontend app's own `amplify.yml` pulls the deployed config via `npx ampx generate outputs --branch $AMPLIFY_BACKEND_APP_BRANCH --app-id $AMPLIFY_BACKEND_APP_ID --out-dir ./src` in `preBuild`, then builds. Backend changes affect every app that points at the same stack since they share the Cognito User Pool, AppSync API, S3 bucket, and DDB tables — currently the stage Designer (Portal/Modeler re-point pending).
