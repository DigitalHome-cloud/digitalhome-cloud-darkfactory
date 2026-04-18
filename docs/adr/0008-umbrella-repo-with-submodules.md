# ADR 0008: Umbrella Repo with Git Submodules

## Status

Accepted

## Date

2025-02

## Context

With three independent application repos and platform-level documentation/specs scattered across directories, we needed a single workspace to:
- Launch Claude Code with full platform context
- Store cross-repo documentation, specs, and ADRs
- Provide scripts for multi-repo operations (status, pull, dev startup)
- Offer a single `git clone` for new developers to get the full platform

Options considered:
1. **Monorepo** — move all code into one repo (rejected: too disruptive, loses independent deployment)
2. **Meta tool** (e.g., `meta`, `mr`) — CLI that manages multiple repos (rejected: adds tooling dependency)
3. **Git submodules** — standard git feature, repos remain independent

## Decision

We created `digitalhome-cloud-darkfactory` as an **umbrella repo using git submodules**:

- Application repos are submodules under `repos/` (portal, designer, modeler)
- Platform docs, specs, ADRs, and scripts live at the top level
- `CLAUDE.md` provides the master guide for Claude Code, pointing to each sub-repo's CLAUDE.md
- Helper scripts (`sync-env.sh`, `dev-start-all.sh`, `dev-stop-all.sh`, `status.sh`, `pull-all.sh`) operate across all repos
- The umbrella owns the single `amplify/` directory; per-repo copies are symlinks created by `sync-env.sh`

## Consequences

### Positive

- Single `git clone --recurse-submodules` gives the full platform
- Each app repo remains fully independent — submodules don't affect their workflows
- Platform-level docs have a clear home (no more loose files in parent directories)
- Claude Code launched from darkfactory root has access to all code and docs
- Reproducible: submodule pointers pin exact commits

### Negative

- Git submodules have a learning curve — `git submodule update` is easy to forget
- Submodule pointers must be updated when sub-repos advance (manual step or CI)
- Nested git repos can confuse some IDE tools
