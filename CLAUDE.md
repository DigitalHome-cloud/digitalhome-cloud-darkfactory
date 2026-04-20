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
    core/                ← digitalhome-cloud-core (submodule) — ontology, modules, build tooling
    portal/              ← digitalhome-cloud-portal (submodule)
    designer/            ← digitalhome-cloud-designer (submodule)
    modeler/             ← digitalhome-cloud-modeler (submodule)
  docs/
    architecture/        ← Platform architecture docs
    specs/               ← Feature specifications
    adr/                 ← Architecture Decision Records
  scripts/               ← Cross-repo helper scripts
  archive/               ← Historical files
```

## Sub-Repos

Each sub-repo has its own `CLAUDE.md` with app-specific details. **Always read the sub-repo's CLAUDE.md** before making changes in that repo.

| App | Path | Port | Production URL | CLAUDE.md |
|-----|------|------|----------------|-----------|
| Core | `repos/core/` | — | — | `repos/core/CLAUDE.md` |
| Portal | `repos/portal/` | 8000 | `portal.digitalhome.cloud` | `repos/portal/CLAUDE.md` |
| Designer | `repos/designer/` | 8001 | `designer.digitalhome.cloud` | `repos/designer/CLAUDE.md` |
| Modeler | `repos/modeler/` | 8002 | `modeler.digitalhome.cloud` | `repos/modeler/CLAUDE.md` |
| Digital Twin Demo | `repos/digital-twin-demo/` | — | GitHub repo | `repos/digital-twin-demo/CLAUDE.md` |

## Platform Architecture

### Tech Stack

All three apps are **Gatsby 5 / React 18** static sites deployed via **AWS Amplify Hosting**. They share:

- **Amazon Cognito** for authentication (User Pool + Identity Pool)
- **AWS AppSync** (GraphQL) for API access
- **Amazon DynamoDB** for data storage
- **Amazon S3** for ontology files and instance models
- **Amplify JS v6** (Gen2-style imports) on the frontend

### Backend Ownership

The **umbrella repo owns the single Amplify Gen1 backend** (`amplify/`). Per-repo `amplify/` folders and `src/aws-exports.js` files are **symlinks** created by `scripts/sync-env.sh`. Designer and modeler are frontend-only consumers — they use the same `GATSBY_*` env vars and `aws-exports.deployment.js` pattern to connect to the shared backend.

### Authentication

`AuthContext` in each app wraps the root element and exposes:
- `authState`: `"loading"` | `"demo"` | `"authenticated"`
- `user`, `groups`, `hasGroup(name)`, `signOut()`, `reloadSession()`

Cognito groups control feature access:
- `dhc-users` — SmartHome Designer access
- `dhc-operators` — SmartHome Operator access (future)
- `dhc-admins` — Modeler editing access (future)

### SmartHome ID

The SmartHome ID is the top-level tenant/partition key across the entire platform (like a SAP client). Format: `{country}-{zip}-{street3letter}{housenumber}-{nn}` (e.g. `DE-80331-MAR12-01`).

Three demo SmartHomes are always available: `DE-DEMO`, `FR-DEMO`, `BE-DEMO`. Cross-app navigation passes the active SmartHome via `?home=` query parameter.

### Ontology (Semantic Core)

The DHC core ontology (`dhc-core.schema.ttl`) lives in `repos/core/src/ontology/`. It defines the domain vocabulary (classes like `RealEstate`, `Area`, `Space`, `Circuit`, `Sensor`) used by all apps. Build scripts in `repos/core/scripts/` parse the TTL and generate Blockly block definitions and ontology graph JSON into `repos/core/build/`. The ontology follows semantic versioning (`model-vX.Y.Z`).

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

All apps use `GATSBY_*` env vars configured identically:
- Locally: `.env.development` (gitignored, generated from `aws-exports.js`)
- Deployed: set in Amplify Console

Cross-app URLs use env vars with sensible defaults:
- `GATSBY_PORTAL_URL` → `https://portal.digitalhome.cloud`
- `GATSBY_DESIGNER_URL` → `https://designer.digitalhome.cloud`
- `GATSBY_MODELER_URL` → `https://modeler.digitalhome.cloud`

### Files That Must Never Be Committed (any repo)

- `src/aws-exports.js` — Amplify-generated config with hardcoded values
- `.env.development` — local env vars with actual secrets

### Local Dev Setup

The umbrella repo owns the single Amplify backend and `src/aws-exports.js`. Per-repo `amplify/` folders and `src/aws-exports.js` files are **symlinks** pointing to the umbrella master — no copies.

**First-time / after `amplify pull`:**

```bash
amplify pull                    # run once at umbrella root
./scripts/sync-env.sh           # symlinks amplify/ + aws-exports.js into each repo,
                                # generates .env.development, runs amplify codegen
```

**Daily:**

```bash
./scripts/dev-start-all.sh      # preflight checks, kills stale ports, starts all 3 servers detached
./scripts/dev-stop-all.sh       # stops all 3 servers
```

Pass `--clean` to `dev-start-all.sh` to wipe `.cache/`, `public/`, and `node_modules/.cache` before starting.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/sync-env.sh` | Symlink `amplify/` + `aws-exports.js` from umbrella into each repo, generate `.env.development`, run `amplify codegen` |
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
  - 0003: Amplify Gen1 backend with Gen2 frontend imports
  - 0004: Environment-variable-driven configuration
  - 0005: Cognito auth with group-based access control
  - 0006: SmartHome ID as tenant partition key
  - 0007: Semantic core ontology in core repo (migrated from modeler)
  - 0008: Umbrella repo with git submodules
  - 0009: Single spec document per target release
  - 0010: S3 bucket structure for global and tenant content
  - 0011: All GraphQL types in portal backend schema
  - 0012: Modular ontology architecture (Core + Norm Modules)
  - 0013: Platform-agnostic design guide

## Deployment

Each app deploys independently via Amplify Hosting:
- Push to `main` → production deploy
- Push to `stage` → staging deploy

The portal's Amplify backend changes (Cognito, AppSync, etc.) affect all apps since they share the backend.
