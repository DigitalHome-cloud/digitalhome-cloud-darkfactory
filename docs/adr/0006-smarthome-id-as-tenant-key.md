# ADR 0006: SmartHome ID as Top-Level Tenant/Partition Key

## Status

Accepted

## Date

2025-01 (documented retroactively 2025-02)

## Context

The platform manages multiple smart homes for multiple users. We needed a stable, human-readable identifier that:
- Uniquely identifies a physical property across all services
- Works as a partition key in DynamoDB and S3 path prefix
- Can be passed between apps (portal, designer, operator) via URL
- Is meaningful to users (not just a UUID)

## Decision

We use a **SmartHome ID** as the top-level tenant/partition key with the format:

```
{country}-{zip}-{street3letter}{housenumber}-{nn}
```

Examples: `DE-80331-MAR12-01`, `FR-75001-RUE8-01`, `BE-1000-AVE5-01`

Key properties:
- **Human-readable**: encodes country, postal code, and street abbreviation
- **Unique**: the `-nn` suffix disambiguates multiple units at the same address
- **URL-safe**: uses only uppercase letters, digits, and hyphens
- **Cross-app**: passed via `?home=` query parameter; persisted to `localStorage`

Three demo SmartHomes are always available: `DE-DEMO`, `FR-DEMO`, `BE-DEMO`.

`SmartHomeContext` in each app manages the active selection and exposes `activeHome`, `setActiveHome(id)`, `isDemo`.

## Consequences

### Positive

- Partition key is immediately meaningful — you can tell what property it refers to
- Works naturally as S3 prefix (`s3://bucket/DE-80331-MAR12-01/...`) and DynamoDB partition key
- Demo homes (`*-DEMO`) are trivially identifiable
- Cross-app navigation is simple: append `?home=ID` to any URL

### Negative

- Format is opinionated — addresses that don't fit the pattern need adaptation
- Renaming/re-addressing a property requires migrating all data under the old key
- The 3-letter street abbreviation may collide in dense areas (mitigated by `-nn` suffix)
- Not a UUID — external systems may need a mapping layer
