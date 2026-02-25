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

The **portal repo owns the Amplify Gen1 backend** (`repos/portal/amplify/`). Designer and modeler are frontend-only consumers — they use the same `GATSBY_*` env vars and `aws-exports.deployment.js` pattern to connect to the shared backend.

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

The DHC core ontology (`dhc-core.schema.ttl`) lives in `repos/modeler/semantic-core/`. It defines the domain vocabulary (classes like `RealEstate`, `Room`, `Circuit`, `Sensor`) used by all apps. The ontology follows semantic versioning (`model-vX.Y.Z`) and is parsed at build time.

## Key Rules

### No Double Maintenance

Documentation, specs, and config files must live in **exactly one place**. When content is moved to this umbrella repo, delete the original. Never maintain the same file in two repos. If an app-level CLAUDE.md references a doc, point to this repo's copy rather than duplicating.

### Single Source of Truth for Specs

Release specs live in `docs/specs/vX.Y.Z.md` — one living document per target release. See `docs/specs/TEMPLATE.md` for the format. Existing non-release-specific specs (design docs, ontology extensions) remain as standalone files.

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

### Local Dev Setup (per app)

1. Run `amplify pull` (or copy `src/aws-exports.js` from portal)
2. Run `node scripts/generate-aws-config-from-master.js`
3. Run `yarn develop`

Or use `./scripts/dev-start-all.sh` to start all three simultaneously.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/dev-start-all.sh` | Start all 3 Gatsby dev servers (ports 8000, 8001, 8002) |
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
- `docs/specs/` — Release specs (`vX.Y.Z.md`) and standalone feature specs. See `TEMPLATE.md` for format.
- `docs/adr/` — Architecture Decision Records:
  - 0001: Multi-repo with shared backend
  - 0002: Gatsby 5 + React 18 frontend stack
  - 0003: Amplify Gen1 backend with Gen2 frontend imports
  - 0004: Environment-variable-driven configuration
  - 0005: Cognito auth with group-based access control
  - 0006: SmartHome ID as tenant partition key
  - 0007: Semantic core ontology in modeler repo
  - 0008: Umbrella repo with git submodules
  - 0009: Single spec document per target release

## Deployment

Each app deploys independently via Amplify Hosting:
- Push to `main` → production deploy
- Push to `stage` → staging deploy

The portal's Amplify backend changes (Cognito, AppSync, etc.) affect all apps since they share the backend.
