# ADR 0009: Single Living Spec Document Per Target Release

## Status

Accepted

## Date

2025-02

## Context

As the platform matures beyond the initial prototype, we need a structured way to define what goes into each release — both the big picture and feature details. Spec files were previously scattered (parent directory, modeler repo, etc.) with no clear lifecycle.

Options considered:
1. **Per-release folders** with multiple spec files (`docs/specs/v0.2.0/*.md`)
2. **Flat files with version prefix** (`docs/specs/v0.2.0-feature.md`)
3. **Single living document per release** (`docs/specs/v0.2.0.md`)

## Decision

We use a **single living spec document per target release** at `docs/specs/vX.Y.Z.md`.

Each spec document contains:
- Release goals and big picture
- Feature details organized by app/area
- Acceptance criteria
- Open questions and decisions

The document is "living" — it evolves during planning and development. Once the release ships, the spec is frozen and becomes historical documentation of what was delivered.

Existing specs that are not release-specific (e.g., `dhc-modeler-block-design.md`, `tbox-stakeholders-extension.md`) remain as standalone files in `docs/specs/`.

## Consequences

### Positive

- One place to look for "what's in the next release"
- Big picture and details live together — no navigating multiple files
- Easy to review and discuss in PRs (single file diff)
- Clear lifecycle: living during development, frozen after release

### Negative

- Large releases may produce long documents — mitigated by clear section structure
- Concurrent editing of one file can cause merge conflicts — mitigated by section ownership
- Non-release-specific specs still exist alongside release specs (two patterns coexist)
