# ADR 0011: All GraphQL Types Live in the Portal Backend Schema

## Status

Accepted

## Date

2026-02

## Context

The DigitalHome.Cloud platform uses AWS AppSync (GraphQL) backed by DynamoDB for its data layer. Per ADR 0001, the portal repo owns the Amplify Gen1 backend — including the `schema.graphql` that defines all DynamoDB-backed types.

As the platform grows beyond user profiles and library items, new domain types are needed:

- **SmartHome** — tenant-level entity representing a physical home, the partition key for all downstream data.
- **SmartHomeDesign** — workspace metadata for the Designer's Blockly-based A-Box design, including edit lock state.
- **LibraryItem updates** — additional capability fields (actor, sensor, controller) for the global component library.

We needed to decide where these types are defined:

1. **Option A: All types in the portal's `schema.graphql`** — maintain the existing single-backend pattern. Designer and modeler remain frontend-only consumers that use the shared AppSync endpoint.
2. **Option B: Per-app backend extensions** — each app adds its own GraphQL types via separate Amplify backends or AppSync data sources. More autonomous but creates infrastructure sprawl and cross-API coordination issues.

## Decision

**Option A: All GraphQL types (including those primarily consumed by designer or modeler) live in the portal's `amplify/backend/api/digitalhomecloudback/schema.graphql`.**

Designer and modeler remain frontend-only consumers. They access the shared AppSync API using the same `GATSBY_*` environment variables and `aws-exports.deployment.js` pattern established in ADR 0001 and ADR 0004.

When portal schema changes are needed for another app's feature:
1. Schema changes are made in the portal repo's `schema.graphql`.
2. `amplify push` deploys the backend changes.
3. `amplify codegen` regenerates `src/graphql/{queries,mutations,subscriptions}.js`.
4. The generated files are copied to the consuming repos (designer, modeler).

## Consequences

### Positive

- Single source of truth for all data types — no schema fragmentation across repos.
- One AppSync API endpoint — no cross-API calls or federation needed.
- DynamoDB tables are co-located and managed by one Amplify environment.
- Auth rules (Cognito groups, owner-based access) are defined consistently in one place.
- Aligns with ADR 0010's single-bucket S3 strategy — data is unified, not distributed.

### Negative

- Portal repo becomes a coordination bottleneck for schema changes needed by other apps.
- Developers working on designer or modeler features must also make PRs in the portal repo for schema changes.
- Generated GraphQL operation files must be manually copied to consuming repos after codegen.

### Mitigations

- Schema changes are staged on the `stage` branch first, giving all apps time to adapt.
- The darkfactory umbrella repo enables cross-repo development in a single Claude Code session.
- A future shared npm package could automate distribution of generated GraphQL operations.
