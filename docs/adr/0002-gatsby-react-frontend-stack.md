# ADR 0002: Gatsby 5 + React 18 as Frontend Stack

## Status

Accepted

## Date

2024-11 (documented retroactively 2025-02)

## Context

We needed a frontend framework for three web applications (Portal, Designer, Modeler) that would support:

- Static site generation for fast initial loads
- Rich client-side interactivity (3D graphs, Blockly editor, auth flows)
- Per-branch deployments via Amplify Hosting
- Internationalization (multiple languages)
- Plugin ecosystem for common needs (i18n, image processing, SEO)

## Decision

We chose **Gatsby 5** with **React 18** for all three applications.

Key factors:
- Gatsby's static generation + client hydration fits our "mostly static shell with dynamic auth" pattern
- Amplify Hosting has first-class Gatsby support with automatic branch deployments
- `gatsby-plugin-react-i18next` provides file-based i18n with language-prefixed routes out of the box
- React 18 is the standard for component libraries we depend on (Amplify UI, Blockly, react-force-graph-3d)

## Consequences

### Positive

- All three apps share the same build tooling, patterns, and conventions
- Developers can move between repos without learning new frameworks
- Static builds are fast to serve and cache-friendly
- Rich plugin ecosystem handles i18n, image optimization, GraphQL data layer

### Negative

- Gatsby's GraphQL data layer adds complexity for simple data needs
- Build times grow with page count (mitigated by incremental builds)
- SSR/SSG boundary requires care with browser-only libraries (Three.js, Blockly need dynamic imports)
- Gatsby 5 has a smaller community than Next.js — fewer resources for troubleshooting
