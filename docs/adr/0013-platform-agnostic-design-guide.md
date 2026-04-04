# ADR 0013: Platform-Agnostic Design Guide

## Status

Accepted

## Date

2026-04-04

## Context

The three DigitalHome.Cloud Gatsby apps (Portal, Designer, Modeler) share a consistent dark slate/blue design language, but it exists only as implicit convention — hardcoded across three separate `global.css` files with no shared reference. Minor inconsistencies have crept in (container widths, button class names, font sizes). As the platform extends to new surfaces (Node-RED dashboards, mobile apps, IoT displays), there is no authoritative document describing what the DHC visual language *is*.

## Decision

Create a platform-agnostic design guide at `docs/design/` in the umbrella repo. The guide consists of:

1. **JSON design token files** (`tokens/`) — machine-readable source of truth for colors, typography, spacing, radii, shadows, motion, and borders
2. **Markdown foundation docs** (`foundations/`) — rationale and usage guidelines
3. **Markdown component docs** (`components/`) — component specs with variants, states, and sizing
4. **Markdown pattern docs** (`patterns/`) — cross-cutting patterns (layout, accessibility, semantic views, dark theme)
5. **Markdown adaptation guides** (`adaptation/`) — platform-specific implementation guidelines (web, Node-RED, mobile, IoT)

Key decisions within the guide:
- **Dark-only theme** — permanent, no light mode
- **1280px container width** — standardized across all apps (Portal updated from 1120px)
- **`.dhc-button-{variant}` naming** — standardized (Portal aligned from `.dhc-btn-primary`)
- **2.25rem hero title** — standardized (Portal from 2.2rem, Designer from 2.1rem)

## Consequences

- All new UI work references the design guide rather than copying from existing CSS
- Inconsistencies between apps should be resolved to match the guide
- The JSON token files can be consumed by build scripts to generate CSS custom properties, React Native style objects, or Node-RED theme files
- The guide must be maintained alongside the apps — stale documentation is worse than no documentation
- No code changes are required by this ADR itself; it documents the design language as-is with minor normalization

## Alternatives Considered

- **Figma design system**: Rejected — the team is developer-driven with no dedicated designers. Markdown + JSON is version-controlled, reviewable in PRs, and accessible to all contributors.
- **Shared CSS package (`@dhc/design-tokens`)**: Deferred — the guide establishes the spec first. A generated CSS package is a recommended future step documented in `adaptation/web-gatsby.md`.
- **Tailwind CSS adoption**: Rejected — the existing plain CSS approach is simple, has no build dependencies, and works. Tailwind would add complexity without proportional benefit for three apps.
