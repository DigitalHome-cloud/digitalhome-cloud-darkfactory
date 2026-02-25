# ADR 0007: Semantic Core Ontology Lives in the Modeler Repo

## Status

Accepted

## Date

2025-02

## Context

The DHC core ontology (`dhc-core.schema.ttl`) defines the domain vocabulary used across the platform — classes like `RealEstate`, `Room`, `Circuit`, `Sensor`, and their properties and design view annotations. Initially it lived in a separate `digitalhome-cloud-semantic-core` repo.

We needed to decide where the ontology source of truth should live, considering:
- The modeler is the primary tool for viewing and (eventually) editing the ontology
- The modeler parses the TTL at build time to generate its 3D graph data
- The designer consumes the ontology at runtime (from S3) to populate Blockly toolboxes
- Ontology changes should be atomic with their visualization

## Decision

We **merged semantic-core into the modeler repo** under `repos/modeler/semantic-core/`:

```
semantic-core/
  ontology/
    dhc-core.schema.ttl    ← core ontology (classes, properties, design views)
    context.jsonld          ← JSON-LD context for runtime use
  instances/
    DE-DEMO.ttl             ← demo instance data
  shapes/                   ← SHACL validation shapes
```

The modeler's build pipeline (`yarn parse-ontology`) reads the TTL and generates `src/data/ontology-graph.json`. CI/CD publishes compiled artifacts to versioned S3 paths for runtime consumption by other apps.

The former `digitalhome-cloud-semantic-core` repo was archived.

## Consequences

### Positive

- Ontology changes and their visualization are always in sync (same commit)
- Single PR to update both ontology and viewer
- Build pipeline is simpler — no cross-repo dependency for the parse step
- Versioned S3 publishing decouples runtime consumers from the source repo

### Negative

- The modeler repo is now responsible for both application code and domain vocabulary
- Other apps (designer) depend on published S3 artifacts rather than importing directly
- Ontology governance (review, approval) happens in the modeler repo's PR process
