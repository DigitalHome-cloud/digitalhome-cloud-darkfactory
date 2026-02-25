# ADR 0001: Multi-Repo Architecture with Shared Amplify Backend

## Status

Accepted

## Date

2025-02-25

## Context

The DigitalHome.Cloud platform consists of multiple frontend applications (Portal, Designer, Modeler) that need to share authentication, data storage, and API infrastructure. We needed to decide between:

1. **Monorepo** — all apps in a single repository
2. **Multi-repo with independent backends** — each app owns its own infrastructure
3. **Multi-repo with shared backend** — separate repos for each app, one shared backend

## Decision

We chose **multi-repo with a shared Amplify Gen1 backend**, where:

- Each app lives in its own GitHub repository (`digitalhome-cloud-portal`, `digitalhome-cloud-designer`, `digitalhome-cloud-modeler`)
- The **portal repo owns the Amplify backend** (`amplify/` directory) — Cognito User Pool, Identity Pool, AppSync, DynamoDB, S3
- Other repos are **frontend-only consumers** that connect to the shared backend via environment variables
- An **umbrella repo** (`digitalhome-cloud-darkfactory`) aggregates all app repos as git submodules for cross-repo development

### Configuration pattern

All apps use the same `aws-exports.deployment.js` pattern:
1. `amplify pull` generates `src/aws-exports.js` (gitignored, hardcoded values)
2. `generate-aws-config-from-master.js` produces `src/aws-exports.deployment.js` (committed, env-var-driven) and `.env.development` (gitignored)
3. Amplify Hosting injects `GATSBY_*` env vars at build time

## Consequences

### Positive

- **Independent deployments** — each app can be deployed, versioned, and scaled independently
- **Shared auth** — single Cognito User Pool means one login across all apps; groups control per-app access
- **Clear ownership** — portal team owns the backend; other teams focus on frontend
- **Flexible development** — developers can work on one app without cloning the others
- **Umbrella workspace** — darkfactory repo provides a single entry point for platform-wide Claude Code sessions

### Negative

- **Backend changes require coordination** — schema changes in the portal's Amplify backend affect all apps
- **Submodule complexity** — developers must understand git submodules for cross-repo work
- **Duplicated context code** — `AuthContext` and `SmartHomeContext` are copied across repos (not shared as a package)
- **Environment variable sync** — all apps must maintain compatible `GATSBY_*` env vars

### Mitigations

- Backend changes go through `stage` branch first, giving all apps time to adapt
- The darkfactory umbrella repo provides scripts (`status.sh`, `pull-all.sh`) to manage all repos together
- A future shared npm package could eliminate context code duplication
