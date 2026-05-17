# ADR 0003: Amplify Backend Generation (Gen 1 → Gen 2)

## Status

**Superseded by the Update below (2026-05-15).** The platform now runs a pure
Amplify **Gen 2** backend (TypeScript / CDK) defined in the `repos/core`
submodule. The Gen 1 + `aws-exports.deployment.js` hybrid recorded further down
is **historical** and must not be followed.

## Update (2026-05-15): Gen 2 backend, located in `repos/core`

- The backend is now **Amplify Gen 2** — a TypeScript `amplify/` defined with
  `@aws-amplify/backend` + CDK, deployed via `npx ampx pipeline-deploy`.
  Frontends consume a committed `src/amplify_outputs.json` (public IDs only).
  The `aws-exports.js` / `aws-exports.deployment.js` /
  `generate-aws-config-from-master.js` / `sync-env.sh` bridge is **gone**.
- The backend definition lives in the **`repos/core` submodule**
  (`repos/core/amplify/`), not the umbrella root — moved there to avoid two
  `amplify/` levels in one checkout (see ADR 0008 and
  `docs/architecture/amplify-backend.md`).
- The frontend was already Amplify JS v6 (the original decision below) and did
  **not** change — the migration path predicted in "Consequences → Positive"
  held.

## Date

2024-11 (documented retroactively 2025-02); updated 2026-05-15

## Context

AWS Amplify has two generations:
- **Gen1**: CLI-driven backend provisioning (`amplify add auth`, `amplify push`). Generates `aws-exports.js` with hardcoded config.
- **Gen2**: CDK-based backend, new JS library (`aws-amplify/auth`, `aws-amplify/api`) with tree-shakeable imports.

We started with Gen1 for backend provisioning. When Amplify JS v6 (the Gen2 frontend library) became available, we needed to decide whether to stay on the older v5 client library or adopt v6.

## Decision

We use a **hybrid approach**:
- **Backend**: Amplify Gen1 CLI for provisioning (Cognito, AppSync, DynamoDB, S3, Lambda)
- **Frontend**: Amplify JS v6 (Gen2-style imports like `aws-amplify/auth`, `@aws-amplify/ui-react`)

The bridge between them is the `aws-exports.deployment.js` pattern: a script reads the Gen1-generated `aws-exports.js` and produces an environment-variable-driven config file that works with v6's `Amplify.configure()`.

## Consequences

### Positive

- Gen1 backend gives us battle-tested CloudFormation provisioning with `amplify push`
- v6 frontend gives us tree-shaking (smaller bundles), modern API, and the latest `<Authenticator>` component
- The env-var config pattern keeps secrets out of the committed codebase
- Migration path: if we move to Gen2 backend later, the frontend code won't need to change

### Negative

- Hybrid setup is not well-documented by AWS — we had to figure out the config bridge ourselves
- Some Amplify v6 features assume Gen2 backend conventions that don't exist in our Gen1 setup
- The `generate-aws-config-from-master.js` script is a custom build step — now automated via `scripts/sync-env.sh` at the umbrella level
