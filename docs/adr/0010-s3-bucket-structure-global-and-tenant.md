# ADR 0010: S3 Bucket Structure for Global and Tenant Content

## Status

Accepted

## Date

2026-02

## Context

The platform uses a single Amplify-managed S3 bucket (`digitalhome-cloudec099-main`) for file storage. Amplify creates three default prefixes with Cognito Identity-based access control:

- `public/` — any authenticated user can read/write
- `protected/{identityId}/` — owner writes, any authenticated user reads
- `private/{identityId}/` — owner only

We need to store two categories of content:

1. **Global content** — ontology artifacts, library assets. Read by all apps, written by admins/CI.
2. **Tenant content** — SmartHome instance data (A-Box TTL, floor plans, configs). Scoped by SmartHome ID, shared among users with access to that SmartHome.

The challenge is that Amplify's access model is per-user (Cognito Identity), not per-tenant (SmartHome ID).

Options considered:

1. **Option A: `public/` prefix + API-level access control** — Store tenant data under `public/smarthomes/{smartHomeId}/`. Any authenticated user can technically reach the S3 path; access control is enforced by AppSync resolvers and application logic.
2. **Option B: Custom prefix outside Amplify defaults + Lambda/CloudFront** — Store tenant data under a `smarthomes/` prefix at the bucket root, outside Amplify's three folders. Requires custom S3 bucket policy or Lambda@Edge for access control. Tighter security but significantly more infrastructure work.

## Decision

**Option A: Use `public/` prefix with API-level access control.**

Bucket structure:

```
digitalhome-cloudec099-main/
  public/
    ontology/                        ← Global: compiled ontology artifacts
      v{VERSION}/
        ontology-graph.json
        context.jsonld
      latest/
        ontology-graph.json
        context.jsonld
    library/                         ← Global: library assets (future)
    smarthomes/                      ← Tenant: per-SmartHome instance data
      {smartHomeId}/
        instance.ttl
        floorplan.json
        ...
  protected/{identityId}/           ← Per-user content others can see
  private/{identityId}/             ← Per-user private data
```

Access control for tenant data is enforced at the application layer:
- AppSync resolvers check SmartHome membership before returning data
- The app only requests files for SmartHomes the user has access to
- Demo SmartHomes (`DE-DEMO`, `FR-DEMO`, `BE-DEMO`) are readable by all authenticated users

## Consequences

- Simple to implement — no custom bucket policies or Lambda functions needed
- Ontology and library assets are globally readable, matching their public nature
- Tenant data is technically accessible via direct S3 path if a user has the SmartHome ID — acceptable risk for now since demo data is not sensitive and real tenant access control comes through AppSync
- If stricter S3-level isolation is needed later (e.g. regulated data, multi-tenant compliance), we can migrate to Option B without changing the path structure — just move the `smarthomes/` prefix out of `public/` and add a Lambda authorizer
- All apps use the same bucket, keeping infrastructure simple
