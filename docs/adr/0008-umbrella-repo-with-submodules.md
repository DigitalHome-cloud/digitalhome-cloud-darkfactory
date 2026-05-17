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
- Helper scripts (`dev-start-all.sh`, `dev-stop-all.sh`, `status.sh`, `pull-all.sh`) operate across all repos
- The umbrella owned the single `amplify/` directory (**see 2026-05 Update — the
  Gen 2 backend now lives in the `repos/core` submodule**)

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

## Update (2026-05-15): Amplify Gen 2 backend relocated into `repos/core`

The original decision had the **umbrella** own the single `amplify/` directory
(with `sync-env.sh` symlinking it per app — Gen 1 era). That no longer holds:

- The Amplify **Gen 2** backend now lives in the **`repos/core` submodule**
  (`repos/core/amplify/`), with its own `amplify.yml`, `package.json`, and
  `tsconfig.json`. The umbrella root has **no** `amplify/` / `package.json` /
  `tsconfig.json`.
- Reason: an `amplify/` at the umbrella root *and* a submodule that Amplify
  Hosting builds caused "amplify on two levels of a repo" tooling conflicts.
  Consolidating to one `amplify/` level (owned by `core`) resolves them.
- `sync-env.sh` and the `aws-exports.js` symlink/codegen flow were removed (Gen
  1 leftovers). Apps now commit `src/amplify_outputs.json`; CI pulls it via
  `npx ampx generate outputs`.
- Negative consequence reinforced: a backend change is now a `repos/core`
  commit **plus** an umbrella submodule-pointer bump — two steps, easy to
  forget the second.

See ADR 0003 (Gen 2 backend) and `docs/architecture/amplify-backend.md`.
