# ADR 0004: Environment-Variable-Driven Configuration

## Status

Accepted

## Date

2024-12 (documented retroactively 2025-02)

## Context

Amplify Gen1's `amplify pull` generates `src/aws-exports.js` with hardcoded values (User Pool IDs, AppSync endpoints, OAuth settings). This file cannot be committed because:
- It contains environment-specific values (different per branch/environment)
- It may contain API keys not intended for public frontend bundles
- Multiple repos need the same config but deploy independently

We needed a way to share backend config across repos and environments without committing secrets.

## Decision

We use an **environment-variable-driven config pattern**:

1. `src/aws-exports.js` (gitignored) — the Gen1 master config, local only
2. `scripts/generate-aws-config-from-master.js` — reads the master and generates:
   - `src/aws-exports.deployment.js` (committed) — reads `process.env.GATSBY_*` at build time
   - `.env.development` (gitignored) — local dev values for Gatsby's dotenv loader
3. Amplify Hosting provides the same `GATSBY_*` vars via its console for deployed builds

All apps use the same script, same env var names, and same `aws-exports.deployment.js` structure.

## Consequences

### Positive

- Single source of truth: one `aws-exports.js` generates config for all repos
- No secrets in git — committed file only contains `process.env.*` references
- Works identically in local dev (`.env.development`) and CI/CD (Amplify Console env vars)
- Adding a new backend resource = add one env var, no code changes needed

### Negative

- Developers must run the generator script after `amplify pull` — easy to forget
- 12+ env vars to keep in sync across Amplify Console environments
- Gatsby's `GATSBY_` prefix requirement means env var names are verbose
